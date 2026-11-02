import subprocess
from pathlib import Path
from typing import List, Dict

from aero_engine.config import ASSETS_DIR, FFMPEG_BIN

MUSIC_DEFAULT = ASSETS_DIR / "music" / "ambient_tension.wav"

def build_background_track(
    scenes: List[Dict],
    work_dir: Path,
    aspect_ratio: str = "vertical"
) -> Path:
    """
    Stitches static or browser frame images into an unbroken background video track.
    """
    is_vertical = (aspect_ratio == "vertical")
    res_w = 576 if is_vertical else 1280
    res_h = 1024 if is_vertical else 720
    
    bg_clips_dir = work_dir / "bg_clips"
    bg_clips_dir.mkdir(parents=True, exist_ok=True)
    bg_clips = []

    for idx, sc in enumerate(scenes, 1):
        dur = sc["end"] - sc["start"]
        if dur <= 0.05:
            continue
        clip_file = bg_clips_dir / f"bg_{idx:02d}.mp4"
        cmd = [
            FFMPEG_BIN, "-y", "-loop", "1", "-i", str(sc["img"]),
            "-t", f"{dur:.3f}",
            "-vf", f"scale={res_w}:{res_h}:force_original_aspect_ratio=increase,crop={res_w}:{res_h}",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30",
            str(clip_file)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        bg_clips.append(clip_file)

    concat_bg = work_dir / "concat_bg.txt"
    with open(concat_bg, "w", encoding="utf-8") as f:
        for c in bg_clips:
            f.write(f"file '{c.resolve()}'\n")

    bg_full_track = work_dir / "bg_full_track.mp4"
    subprocess.run([
        FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_bg),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", str(bg_full_track)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    return bg_full_track

def compose_final_video(
    bg_video: Path,
    char_video: Path,
    voice_audio: Path,
    ass_subtitles: Path,
    total_duration: float,
    output_mp4: Path,
    music_audio: Path = MUSIC_DEFAULT,
    music_volume: float = 0.14
) -> Path:
    """
    Final Master FFmpeg compositing with:
    - Background layer
    - Character overlay layer
    - ASS Subtitle filter
    - Voice master track
    - Ambient background tension bed with smooth fade-in and fade-out ducking
    """
    output_mp4.parent.mkdir(parents=True, exist_ok=True)

    filter_complex = (
        "[0:v][1:v]overlay=0:0[v_composed];"
        f"[v_composed]subtitles={ass_subtitles.resolve()}[v_final];"
        "[2:a]volume=1.0[vocal];"
        f"[3:a]atrim=0:{total_duration:.2f},volume={music_volume},"
        f"afade=t=in:ss=0:d=1.5,afade=t=out:st={max(0, total_duration - 2.0):.2f}:d=2.0[music];"
        "[vocal][music]amix=inputs=2:duration=first:dropout_transition=2[a_final]"
    )

    cmd_final = [
        FFMPEG_BIN, "-y",
        "-i", str(bg_video),
        "-i", str(char_video),
        "-i", str(voice_audio),
        "-i", str(music_audio),
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "[a_final]",
        "-c:v", "libx264", "-preset", "fast", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-shortest",
        str(output_mp4)
    ]

    subprocess.run(cmd_final, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
    return output_mp4
