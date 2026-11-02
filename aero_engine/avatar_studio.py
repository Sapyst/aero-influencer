import os
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
import numpy as np

from aero_engine.config import ASSETS_DIR

AVATARS_DIR = ASSETS_DIR / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)

BASE_EXPRESSIONS = [
    {"name": "neutral", "label": "Neutro (Padrão)", "prompt": "standing neutral, relaxed expression, slight pleasant smile"},
    {"name": "shocked", "label": "Chocado / Espanto", "prompt": "shocked open mouth, eyes wide, hands reacting in disbelief"},
    {"name": "pointing_left", "label": "Apontando para a Tela", "prompt": "pointing sideways with index finger towards the screen/evidence"},
    {"name": "thinking", "label": "Pensativo / Braços Cruzados", "prompt": "arms crossed, looking up thoughtfully, pondering expression"},
    {"name": "facepalm", "label": "Descrença / Facepalm", "prompt": "one hand pressed on forehead in exasperated facepalm, eyes closed in disbelief"},
    {"name": "whispering", "label": "Sussurro / Segredo", "prompt": "hand cupping mouth whispering a juicy conspiratorial secret"},
    {"name": "smug", "label": "Deboche / Smug Smirk", "prompt": "confident cheeky smug smirk, one eyebrow raised, hand on hip"},
    {"name": "mindblown", "label": "Choque Mental / Mindblown", "prompt": "both hands clutching sides of head in total shock and mindblown realization, mouth in an 'O' gasp"},
    {"name": "confused", "label": "Confuso / Dando de Ombros", "prompt": "shrugging both shoulders with open palms, head tilted in confusion"},
    {"name": "waving", "label": "Tchau / Despedida (Outro)", "prompt": "smiling cheerfully, waving one hand goodbye to the viewer"}
]

def chroma_cutout(img_path: Path, out_path: Path) -> Path:
    """
    Strips solid lime green chroma key (#00FF00) and tightly crops the transparent silhouette.
    """
    img = Image.open(img_path).convert("RGBA")
    arr = np.array(img)
    r, g, b, a = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2], arr[:, :, 3]
    # Green chroma threshold
    green_mask = (g > 155) & (r < 115) & (b < 115)
    arr[green_mask, 3] = 0
    res = Image.fromarray(arr)
    bbox = res.getbbox()
    if bbox:
        res = res.crop(bbox)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    res.save(out_path)
    return out_path

def list_avatars() -> List[Dict]:
    avatars = []
    # Always include Nova as the primary built-in avatar
    avatars.append({
        "id": "nova",
        "name": "Nova (Oficial)",
        "description": "Garota 2D doodle com coques lilás, óculos redondos e hoodie pastel",
        "sprites_count": 14,
        "is_builtin": True,
        "preview_url": "/api/avatar/preview/nova"
    })
    
    if AVATARS_DIR.exists():
        for d in AVATARS_DIR.iterdir():
            if d.is_dir() and (d / "mascot.json").exists():
                try:
                    with open(d / "mascot.json", "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    sprites = list((d / "sprites").glob("*.png"))
                    avatars.append({
                        "id": d.name,
                        "name": meta.get("name", d.name),
                        "description": meta.get("description", ""),
                        "sprites_count": len(sprites),
                        "is_builtin": False,
                        "preview_url": f"/api/avatar/preview/{d.name}"
                    })
                except Exception:
                    pass
    return avatars

def generate_avatar_concept(
    avatar_id: str,
    character_description: str,
    api_key: Optional[str]
) -> Dict:
    """
    Generates a new concept candidate for a custom avatar with iteration history.
    """
    char_dir = AVATARS_DIR / avatar_id
    versions_dir = char_dir / "versions"
    versions_dir.mkdir(parents=True, exist_ok=True)
    
    existing_versions = sorted(list(versions_dir.glob("version_*.png")))
    v_num = len(existing_versions) + 1
    out_file = versions_dir / f"version_{v_num}.png"
    
    prompt = (
        f"2D minimalist comic doodle character art: {character_description}. "
        "Character standing in full body or 3/4 view, clean bold black ink outlines, flat cell shading, "
        "CRITICAL INSTRUCTION: PURE CHARACTER ONLY. Absolutely NO stars, NO floating lines, NO speed lines, "
        "NO symbols or background doodles outside the character. "
        "Pure solid lime green chroma key background (#00FF00) for clean cutout."
    )
    
    if api_key and len(api_key.strip()) > 15:
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config={"number_of_images": 1, "aspect_ratio": "1:1"}
            )
            if result and result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                temp_raw = versions_dir / f"raw_{v_num}.jpg"
                with open(temp_raw, "wb") as f:
                    f.write(img_bytes)
                chroma_cutout(temp_raw, out_file)
                if temp_raw.exists():
                    temp_raw.unlink()
        except Exception as e:
            print(f"Concept generation error: {e}")

    # Fallback if no key or error: clone nova reference as candidate
    if not out_file.exists():
        fallback_ref = ASSETS_DIR / "pngtuber_sprites" / "nova_neutral_transparent.png"
        from shutil import copyfile
        copyfile(fallback_ref, out_file)
        
    # Save/update meta
    meta = {
        "id": avatar_id,
        "description": character_description,
        "current_version": v_num,
        "approved": False,
        "created_at": time.time()
    }
    with open(char_dir / "draft_meta.json", "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return {
        "avatar_id": avatar_id,
        "version": v_num,
        "total_versions": v_num,
        "image_url": f"/api/avatar/version/{avatar_id}/{v_num}"
    }

def approve_avatar_concept(avatar_id: str, version_num: int) -> Dict:
    """
    Locks the chosen concept version as the Master Reference for this character.
    """
    char_dir = AVATARS_DIR / avatar_id
    versions_dir = char_dir / "versions"
    chosen = versions_dir / f"version_{version_num}.png"
    if not chosen.exists():
        return {"status": "error", "message": f"Versão {version_num} não encontrada."}
    
    master_file = char_dir / "master_reference.png"
    from shutil import copyfile
    copyfile(chosen, master_file)
    
    sprites_dir = char_dir / "sprites"
    sprites_dir.mkdir(parents=True, exist_ok=True)
    # Master automatically becomes neutral sprite
    copyfile(master_file, sprites_dir / "neutral.png")
    
    # Save official mascot.json
    desc = "Personagem Personalizado"
    draft_meta = char_dir / "draft_meta.json"
    if draft_meta.exists():
        try:
            with open(draft_meta) as f:
                desc = json.load(f).get("description", desc)
        except Exception:
            pass

    mascot_meta = {
        "id": avatar_id,
        "name": avatar_id.replace("_", " ").title(),
        "description": desc,
        "master_version": version_num,
        "sprites": {
            "neutral": "neutral.png"
        }
    }
    with open(char_dir / "mascot.json", "w", encoding="utf-8") as f:
        json.dump(mascot_meta, f, indent=2)

    return {"status": "ok", "message": f"Conceito v{version_num} aprovado como Modelo Mestre!", "avatar_id": avatar_id}

def generate_avatar_expression(
    avatar_id: str,
    expression_name: str,
    custom_prompt_tweak: Optional[str],
    api_key: Optional[str]
) -> Dict:
    """
    Generates a specific pose/expression keeping strict style consistency with master reference.
    """
    char_dir = AVATARS_DIR / avatar_id
    master_file = char_dir / "master_reference.png"
    if not master_file.exists():
        return {"status": "error", "message": "Aprove o Modelo Mestre primeiro antes de gerar expressões."}

    sprites_dir = char_dir / "sprites"
    sprites_dir.mkdir(parents=True, exist_ok=True)
    out_sprite = sprites_dir / f"{expression_name}.png"

    # Find base prompt
    base_info = next((e for e in BASE_EXPRESSIONS if e["name"] == expression_name), None)
    pose_desc = base_info["prompt"] if base_info else expression_name.replace("_", " ")
    if custom_prompt_tweak:
        pose_desc += f". Specific refinement: {custom_prompt_tweak}"

    prompt = (
        f"Maintain the exact same 2D cartoon doodle character design, clothing, colors, face, hairstyle and linework "
        f"as the reference image: character is {pose_desc}. "
        "CRITICAL INSTRUCTION: PURE CHARACTER ONLY. Absolutely NO stars, NO floating lines, NO speed lines, "
        "NO symbols or exterior marks outside the character. "
        "Pure solid lime green chroma key background (#00FF00) for clean cutout."
    )

    if api_key and len(api_key.strip()) > 15:
        try:
            from google import genai
            client = genai.Client(api_key=api_key.strip())
            # In Imagen 3 or Gemini multimodal image-to-image
            result = client.models.generate_images(
                model="imagen-3.0-generate-002",
                prompt=prompt,
                config={"number_of_images": 1, "aspect_ratio": "1:1"}
            )
            if result and result.generated_images:
                img_bytes = result.generated_images[0].image.image_bytes
                temp_raw = sprites_dir / f"temp_{expression_name}.jpg"
                with open(temp_raw, "wb") as f:
                    f.write(img_bytes)
                chroma_cutout(temp_raw, out_sprite)
                if temp_raw.exists():
                    temp_raw.unlink()
        except Exception as e:
            print(f"Expression generation error: {e}")

    # Fallback if no key
    if not out_sprite.exists():
        from shutil import copyfile
        copyfile(master_file, out_sprite)

    # Update mascot.json catalog
    mascot_json = char_dir / "mascot.json"
    if mascot_json.exists():
        with open(mascot_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "sprites" not in data:
            data["sprites"] = {}
        data["sprites"][expression_name] = f"{expression_name}.png"
        with open(mascot_json, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    return {
        "status": "ok",
        "avatar_id": avatar_id,
        "expression": expression_name,
        "url": f"/api/avatar/sprite/{avatar_id}/{expression_name}"
    }
