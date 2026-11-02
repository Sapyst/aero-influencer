import asyncio
import subprocess
import shutil
import wave
from pathlib import Path
from typing import List, Dict, Tuple
import numpy as np
from aero_engine.config import FFMPEG_BIN
try:
    from faster_whisper import WhisperModel
    HAS_WHISPER = True
except ImportError:
    WhisperModel = None
    HAS_WHISPER = False

_WHISPER_MODEL = None

def get_whisper():
    global _WHISPER_MODEL
    if HAS_WHISPER and _WHISPER_MODEL is None:
        _WHISPER_MODEL = WhisperModel("base", device="cpu", compute_type="int8")
    return _WHISPER_MODEL

def format_ass_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    centis = int(round((seconds - int(seconds)) * 100))
    if centis >= 100:
        secs += 1
        centis = 0
    return f"{hrs:d}:{mins:02d}:{secs:02d}.{centis:02d}"

def trim_silence_wav(in_wav: Path, out_wav: Path, threshold_db: float = -38.0, pad_end_ms: int = 100) -> float:
    with wave.open(str(in_wav), "rb") as wf:
        n_channels = wf.getnchannels()
        sampwidth = wf.getsampwidth()
        framerate = wf.getframerate()
        frames = wf.readframes(wf.getnframes())

    audio = np.frombuffer(frames, dtype=np.int16)
    if n_channels == 2:
        mono = np.mean(np.abs(audio.reshape(-1, 2)), axis=1)
    else:
        mono = np.abs(audio)

    threshold = 32767 * (10 ** (threshold_db / 20))
    active = np.where(mono > threshold)[0]
    if len(active) == 0:
        shutil.copy(in_wav, out_wav)
        return len(audio) / (framerate * n_channels)

    pad_samples = int(framerate * (pad_end_ms / 1000.0))
    start_idx = max(0, active[0] - int(framerate * 0.05))
    end_idx = min(len(mono), active[-1] + pad_samples)

    trimmed = audio[start_idx:end_idx]
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(n_channels)
        wf.setsampwidth(sampwidth)
        wf.setframerate(framerate)
        wf.writeframes(trimmed.tobytes())

    trimmed_dur = len(trimmed) / (framerate * n_channels)
    return trimmed_dur

async def synthesize_voice_segments(
    script_segments: List[str],
    work_dir: Path,
    voice: str = "en-GB-MaisieNeural"
) -> List[Path]:
    work_dir.mkdir(parents=True, exist_ok=True)
    out_wavs = []

    for idx, text in enumerate(script_segments, 1):
        raw_mp3 = work_dir / f"seg_raw_{idx:02d}.mp3"
        raw_wav = work_dir / f"seg_raw_{idx:02d}.wav"
        trimmed_wav = work_dir / f"seg_trimmed_{idx:02d}.wav"

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(str(raw_mp3))

        subprocess.run([
            FFMPEG_BIN, "-y", "-i", str(raw_mp3),
            "-ar", "44100", "-ac", "1",
            str(raw_wav)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        trim_silence_wav(raw_wav, trimmed_wav, pad_end_ms=90)
        out_wavs.append(trimmed_wav)

    return out_wavs

def assemble_master_audio(
    segment_wavs: List[Path],
    out_master_wav: Path,
    inter_gap_sec: float = 0.12
) -> float:
    work_dir = out_master_wav.parent
    gap_wav = work_dir / "inter_gap.wav"
    subprocess.run([
        FFMPEG_BIN, "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-t", f"{inter_gap_sec:.3f}", str(gap_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    concat_txt = work_dir / "concat_master.txt"
    with open(concat_txt, "w", encoding="utf-8") as f:
        for i, wav in enumerate(segment_wavs):
            f.write(f"file '{wav.resolve()}'\n")
            if i < len(segment_wavs) - 1:
                f.write(f"file '{gap_wav.resolve()}'\n")

    subprocess.run([
        FFMPEG_BIN, "-y", "-f", "concat", "-safe", "0", "-i", str(concat_txt),
        "-ar", "44100", "-ac", "2", str(out_master_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    try:
        with wave.open(str(out_master_wav), "rb") as wf:
            return float(wf.getnframes()) / float(wf.getframerate())
    except Exception:
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(out_master_wav)
        ], stdout=subprocess.PIPE, text=True, check=True)
        return float(res.stdout.strip())

def align_words(audio_wav: Path, script_text: str = "", language: str = "en") -> List[Dict]:
    if HAS_WHISPER:
        try:
            whisper = get_whisper()
            if whisper:
                segments, _ = whisper.transcribe(str(audio_wav), word_timestamps=True, language=language)
                words = []
                for s in segments:
                    for w in s.words:
                        words.append({
                            "word": w.word.strip(),
                            "clean": w.word.strip().lower().replace(",", "").replace(".", "").replace("!", "").replace("?", ""),
                            "start": float(w.start),
                            "end": float(w.end)
                        })
                if words:
                    return words
        except Exception as e:
            print(f"Whisper alignment note: {e}")

    # Fallback: estimate word timings evenly across actual wav duration
    try:
        with wave.open(str(audio_wav), "rb") as wf:
            total_sec = wf.getnframes() / float(wf.getframerate())
    except Exception:
        total_sec = 30.0

    raw_words = [w.strip() for w in script_text.split() if w.strip()] if script_text else ["Aero", "Influencer", "Video"]
    dur_per_word = max(0.15, total_sec / max(1, len(raw_words)))
    words = []
    cur_t = 0.0
    for w in raw_words:
        words.append({
            "word": w,
            "clean": w.lower().replace(",", "").replace(".", "").replace("!", "").replace("?", ""),
            "start": round(cur_t, 3),
            "end": round(cur_t + dur_per_word * 0.9, 3)
        })
        cur_t += dur_per_word
    return words

def build_ass_subtitles(
    words: List[Dict],
    out_ass_path: Path,
    aspect_ratio: str = "vertical"
) -> Path:
    is_vertical = (aspect_ratio == "vertical")
    res_x = 576 if is_vertical else 1280
    res_y = 1024 if is_vertical else 720
    
    # In vertical Shorts, subtitles sit in upper center (MarginV=520, clear of Nova)
    # In horizontal Video, subtitles sit comfortably in lower third (MarginV=65)
    margin_v = 520 if is_vertical else 65
    font_size = 46 if is_vertical else 38
    
    header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {res_x}
PlayResY: {res_y}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: AeroSubtitle,Impact,{font_size},&H00F8B4D8,&H00FFFFFF,&H00000000,&H80000000,-1,0,0,0,100,100,1,0,1,5,2,2,30,30,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    chunks = []
    current_chunk = []
    for i, w in enumerate(words):
        current_chunk.append(w)
        is_last = (i == len(words) - 1)
        if is_last:
            chunks.append(current_chunk)
            break
        next_w = words[i + 1]
        gap = next_w["start"] - w["end"]
        has_punct = any(w["word"].endswith(p) for p in ['?', '!', '.', ',', ';', ':'])
        chunk_limit = 2 if is_vertical else 4
        if gap > 0.28 or has_punct or len(current_chunk) >= chunk_limit:
            chunks.append(current_chunk)
            current_chunk = []

    events = []
    for chunk in chunks:
        t_start = format_ass_time(chunk[0]["start"])
        t_end = format_ass_time(chunk[-1]["end"])
        phrase = " ".join([w["word"].upper() for w in chunk])
        events.append(f"Dialogue: 0,{t_start},{t_end},AeroSubtitle,,0,0,0,,{phrase}")

    with open(out_ass_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events) + "\n")

    return out_ass_path
