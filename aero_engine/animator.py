import subprocess
import shutil
from pathlib import Path
from typing import List, Literal, Optional, Dict
import numpy as np
from PIL import Image, ImageOps, ImageFilter
from pydantic import BaseModel

Side = Literal["left", "right"]

SPRITE_ALIASES = {
    "neutral": "nova_neutral_transparent.png",
    "thinking": "nova_arms_crossed_thinking.png",
    "arms_crossed": "nova_arms_crossed_thinking.png",
    "explaining": "nova_explaining_both_hands.png",
    "pointing": "nova_pointing_left_screen.png",
    "pointing_left": "nova_pointing_left_screen.png",
    "pointing_up": "nova_pointing_up.png",
    "shocked": "nova_shocked.png",
    "confused": "nova_shrugging_confused.png",
    "shrugging": "nova_shrugging_confused.png",
    "smug": "nova_smug_smirk.png",
    "smirk": "nova_smug_smirk.png",
    "waving": "nova_waving.png",
    "outro": "nova_waving.png",
    "whispering": "nova_whispering_secret.png",
    "whisper": "nova_whispering_secret.png",
    "facepalm": "nova_facepalm_disbelief.png",
    "disbelief": "nova_facepalm_disbelief.png",
    "mindblown": "nova_mindblown.png",
    "laughing": "nova_laughing_giggle.png"
}

SPRITES_DIR = Path("/home/sapista/aero_influencer/assets/pngtuber_sprites")

class CharacterCue(BaseModel):
    start: float
    end: float
    emotion: str
    side: Side = "right"
    description: str = ""

def resolve_sprite_path(emotion: str) -> Path:
    clean = emotion.lower().strip().replace(" ", "_")
    filename = SPRITE_ALIASES.get(clean)
    if not filename:
        for k, v in SPRITE_ALIASES.items():
            if k in clean:
                filename = v
                break
    if not filename:
        direct_file = SPRITES_DIR / f"{clean}.png"
        if direct_file.exists():
            return direct_file
        filename = "nova_neutral_transparent.png"
    return SPRITES_DIR / filename

def assign_smart_sides(cues: List[CharacterCue]) -> List[CharacterCue]:
    """
    Intelligent Contextual Side-Switching Rules:
    1. Hook starts on right (familiar anchor).
    2. Whispering / Smug / Secret / Sarcastic asides switch to left (breaking 4th wall pattern interrupt).
    3. Minimum dwell time >= 3.5s to prevent frantic hopping.
    4. Outro returns to right with waving.
    """
    updated = []
    current_side: Side = "right"
    last_switch_time = 0.0

    for i, cue in enumerate(cues):
        is_last = (i == len(cues) - 1)
        dur_since_switch = cue.start - last_switch_time

        # Outro always finishes on right
        if is_last:
            cue.side = "right"
            updated.append(cue)
            continue

        # Pattern-interrupt emotions that justify moving to the other side
        is_interrupt_emotion = any(e in cue.emotion.lower() for e in ["whisper", "smug", "facepalm", "mindblown"])
        
        # If enough time has passed and emotion warrants it, switch
        if is_interrupt_emotion and dur_since_switch >= 3.5:
            current_side = "left" if current_side == "right" else "right"
            last_switch_time = cue.start
        elif dur_since_switch >= 12.0 and not is_last:
            # Pacing reset after long time on one side
            current_side = "left" if current_side == "right" else "right"
            last_switch_time = cue.start

        cue.side = current_side
        updated.append(cue)

    return updated

def generate_cue_clip(
    sprite_path: Path,
    duration: float,
    side: Side,
    out_path: Path,
    aspect_ratio: str = "vertical",
    fps: int = 30
) -> Path:
    """
    Renders a single cue with:
    - Directional orientation (facing inward: default if right, horizontally mirrored if left)
    - Elastic bump squash & stretch (1.07x) on entry
    - Two-layer composition:
      Layer 1: Subtle Gaussian-blurred drop shadow (radius=5, opacity=58%, offset flipped for side)
      Layer 2: Pristine original sprite with solid unblurred black ink contour
    - Responsive to aspect_ratio: vertical (576x1024) or horizontal (1280x720)
    """
    sprite = Image.open(sprite_path).convert("RGBA")
    bbox = sprite.getbbox()
    cropped = sprite.crop(bbox) if bbox else sprite

    # If standing on the LEFT side, mirror horizontally so Nova faces inward towards content
    if side == "left":
        cropped = ImageOps.mirror(cropped)

    is_vertical = (aspect_ratio == "vertical")
    canvas_w = 576 if is_vertical else 1280
    canvas_h = 1024 if is_vertical else 720
    base_height = 430 if is_vertical else 360

    base_w = int(base_height * (cropped.width / cropped.height))
    base_img = cropped.resize((base_w, base_height), Image.Resampling.LANCZOS)

    total_frames = max(1, int(round(duration * fps)))
    frames_dir = out_path.parent / f"frames_{out_path.stem}"
    frames_dir.mkdir(parents=True, exist_ok=True)

    bump_dur = 0.20
    shadow_offset_x = -6 if side == "left" else 6
    shadow_offset_y = 6

    for f_idx in range(total_frames):
        t = f_idx / fps
        if t < bump_dur:
            p = t / bump_dur
            stretch_y = 1.0 + 0.07 * np.sin(p * np.pi)
            squash_x = 1.0 - 0.03 * np.sin(p * np.pi)
        else:
            stretch_y = 1.0
            squash_x = 1.0

        cur_w = max(1, int(base_w * squash_x))
        cur_h = max(1, int(base_height * stretch_y))
        frame_sprite = base_img.resize((cur_w, cur_h), Image.Resampling.LANCZOS)

        canvas = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))

        # Horizontal anchor: left edge or right edge
        margin_x = 10 if is_vertical else 30
        floor_offset = 15 if is_vertical else 10
        pos_x = margin_x if side == "left" else (canvas_w - cur_w - margin_x)
        pos_y = canvas_h - cur_h + floor_offset  # Floor anchor

        # Two-layer Shadow Generation
        alpha = frame_sprite.split()[3]
        blurred_alpha = alpha.filter(ImageFilter.GaussianBlur(radius=5))
        shadow_alpha = blurred_alpha.point(lambda pt: int(pt * 0.58))

        shadow_layer = Image.new("RGBA", (cur_w, cur_h), (0, 0, 0, 255))
        shadow_img = Image.new("RGBA", (cur_w, cur_h), (0, 0, 0, 0))
        shadow_img.paste(shadow_layer, (0, 0), shadow_alpha)

        # 1. Back Layer: Gaussian drop shadow
        canvas.paste(shadow_img, (pos_x + shadow_offset_x, pos_y + shadow_offset_y), shadow_img)
        # 2. Front Layer: Solid character sprite with razor-sharp black outline
        canvas.paste(frame_sprite, (pos_x, pos_y), frame_sprite)

        canvas.save(frames_dir / f"f_{f_idx:05d}.png")

    cmd = [
        "ffmpeg", "-y", "-framerate", str(fps),
        "-i", str(frames_dir / "f_%05d.png"),
        "-c:v", "qtrle", "-pix_fmt", "argb",
        str(out_path)
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    shutil.rmtree(frames_dir, ignore_errors=True)
    return out_path

def render_character_track(
    cues: List[CharacterCue],
    work_dir: Path,
    out_mov: Path,
    aspect_ratio: str = "vertical",
    fps: int = 30
) -> Path:
    clips_dir = work_dir / "char_clips"
    clips_dir.mkdir(parents=True, exist_ok=True)
    clip_files = []

    for idx, cue in enumerate(cues, 1):
        dur = cue.end - cue.start
        if dur <= 0.05:
            continue
        clip_path = clips_dir / f"char_cue_{idx:02d}.mov"
        sprite_path = resolve_sprite_path(cue.emotion)
        print(f"  [Nova Cue {idx:02d}] {cue.emotion} on {cue.side.upper()} ({cue.start:.2f}s -> {cue.end:.2f}s | dur {dur:.2f}s)")
        generate_cue_clip(sprite_path, dur, cue.side, clip_path, aspect_ratio=aspect_ratio, fps=fps)
        clip_files.append(clip_path)

    concat_file = work_dir / "concat_char.txt"
    with open(concat_file, "w", encoding="utf-8") as f:
        for cp in clip_files:
            f.write(f"file '{cp.resolve()}'\n")

    subprocess.run([
        "ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_file),
        "-c:v", "qtrle", str(out_mov)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    return out_mov
