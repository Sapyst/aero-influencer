from pathlib import Path
from typing import Optional
from aero_engine.config import ImageGenMode

def should_generate_image(mode: ImageGenMode, web_shot_available: bool, is_abstract: bool = False) -> bool:
    if mode == "NEVER":
        return False
    if mode == "ALWAYS":
        return True
    # AUTO mode: generate only when web capture failed or abstract scene
    return (not web_shot_available) or is_abstract

def generate_scene_image(
    prompt: str,
    out_path: Path,
    api_key: Optional[str],
    aspect_ratio: str = "vertical"
) -> Optional[Path]:
    """
    Generates an illustration image using Google Gemini / Imagen when allowed by settings.
    """
    if not api_key or len(api_key.strip()) < 15:
        return None
    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        
        ratio = "9:16" if aspect_ratio == "vertical" else "16:9"
        enhanced_prompt = f"{prompt}, high quality documentary photojournalism, cinematic dramatic lighting, {ratio}"
        
        # Use imagen-3.0 or gemini-2.5-flash image tool
        result = client.models.generate_images(
            model="imagen-3.0-generate-002",
            prompt=enhanced_prompt,
            config={"number_of_images": 1, "aspect_ratio": ratio}
        )
        if result and result.generated_images:
            img_bytes = result.generated_images[0].image.image_bytes
            out_path.parent.mkdir(parents=True, exist_ok=True)
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            return out_path
    except Exception as e:
        print(f"Image generation error ({e})")
        return None
