import asyncio
import time
from pathlib import Path
from typing import Callable, Optional, Dict, List

from aero_engine.config import get_config, AeroConfig, ASSETS_DIR, TEMP_DIR
from aero_engine.ai_director import generate_script, DirectorScript
from aero_engine.web_hunter import (
    search_duckduckgo_news,
    capture_smart_webpage,
    build_mobile_browser_frame,
    build_desktop_browser_frame
)
from aero_engine.voice_engine import (
    synthesize_voice_segments,
    assemble_master_audio,
    align_words,
    build_ass_subtitles
)
from aero_engine.animator import (
    CharacterCue,
    assign_smart_sides,
    render_character_track
)
from aero_engine.image_generator import should_generate_image, generate_scene_image
from aero_engine.renderer import build_background_track, compose_final_video

DEFAULT_FALLBACK_BG = ASSETS_DIR / "pngtuber_sprites" / "nova_neutral_transparent.png"

async def run_pipeline(
    topic: str,
    aspect_ratio: Optional[str] = None,
    video_type: Optional[str] = None,
    image_gen_mode: Optional[str] = None,
    progress_callback: Optional[Callable[[str, int], None]] = None
) -> Path:
    cfg = get_config()
    ar = aspect_ratio or cfg.aspect_ratio
    vt = video_type or cfg.video_type
    igm = image_gen_mode or cfg.image_gen_mode

    job_id = f"job_{int(time.time())}"
    work_dir = TEMP_DIR / job_id
    work_dir.mkdir(parents=True, exist_ok=True)

    def report(msg: str, pct: int):
        print(f"[{pct}%] {msg}")
        if progress_callback:
            progress_callback(msg, pct)

    # 1. AI Director Screenplay
    report("Roteirizando com o AI Director...", 10)
    script: DirectorScript = generate_script(
        topic=topic,
        api_key=cfg.google_gemini_api_key,
        video_type=vt,
        aspect_ratio=ar
    )

    # 2. Voice Generation
    report("Sintetizando narração e cortando pausas...", 25)
    spoken_texts = [beat.narration for beat in script.beats]
    seg_wavs = await synthesize_voice_segments(spoken_texts, work_dir, voice=cfg.default_voice)
    
    master_wav = work_dir / "master_audio.wav"
    total_dur = assemble_master_audio(seg_wavs, master_wav)
    report(f"Áudio mestre montado ({total_dur:.1f}s)", 35)

    # 3. Acoustic Word Alignment
    report("Alinhando sincronia labial e legendas (Whisper)...", 45)
    words = align_words(master_wav)
    ass_path = work_dir / "subtitles.ass"
    build_ass_subtitles(words, ass_path, aspect_ratio=ar)

    # 4. Web Hunting & Scenes
    report("Capturando notícias reais e enquadrando páginas...", 55)
    scene_images = []
    
    # Calculate cue timestamps based on segment durations
    seg_durs = []
    for w in seg_wavs:
        import wave
        with wave.open(str(w), "rb") as wf:
            seg_durs.append(wf.getnframes() / wf.getframerate())
    
    cues: List[CharacterCue] = []
    current_t = 0.0
    for idx, beat in enumerate(script.beats):
        b_dur = seg_durs[idx] + (0.12 if idx < len(script.beats) - 1 else 0.0)
        start_t = current_t
        end_t = min(total_dur, current_t + b_dur)
        current_t = end_t
        
        cues.append(CharacterCue(
            start=start_t,
            end=end_t,
            emotion=beat.emotion,
            side=beat.preferred_side,
            description=beat.narration[:30]
        ))

        # Visual Hunter
        shot_path = work_dir / f"web_shot_{idx:02d}.png"
        framed_path = work_dir / f"bg_framed_{idx:02d}.png"
        url = beat.target_url

        if not url and beat.news_search_query:
            results = search_duckduckgo_news(beat.news_search_query, max_results=1)
            if results:
                url = results[0]["url"]

        captured = None
        if url and igm != "ALWAYS":
            captured = capture_smart_webpage(url, shot_path, aspect_ratio=ar)

        final_img = None
        if captured:
            if ar == "vertical":
                final_img = build_mobile_browser_frame(captured, framed_path, url_label=f"🔒 {url[:28]}")
            else:
                final_img = build_desktop_browser_frame(captured, framed_path, url_label=url, tab_title=beat.narration[:20])
        else:
            # Fallback or AI Image Generation
            if should_generate_image(igm, web_shot_available=False, is_abstract=True):
                ai_img_path = work_dir / f"ai_gen_{idx:02d}.png"
                prompt = beat.image_prompt or f"{topic} editorial journalism"
                final_img = generate_scene_image(prompt, ai_img_path, cfg.google_gemini_api_key, aspect_ratio=ar)

        if not final_img or not final_img.exists():
            final_img = DEFAULT_FALLBACK_BG

        scene_images.append({"start": start_t, "end": end_t, "img": final_img})

    # 5. Character Animation & Side-Switching
    report("Animando a Nova (squash & stretch, sombra e troca de lados)...", 75)
    cues_with_smart_sides = assign_smart_sides(cues)
    char_mov = work_dir / "char_track.mov"
    render_character_track(cues_with_smart_sides, work_dir, char_mov, aspect_ratio=ar)

    # 6. Background Track
    report("Montando trilha de fundo...", 85)
    bg_video = build_background_track(scene_images, work_dir, aspect_ratio=ar)

    # 7. Final Master Render
    report("Compondo vídeo final com trilha sonora e legendas...", 92)
    clean_title = "".join(c for c in topic if c.isalnum() or c in (" ", "_", "-")).replace(" ", "_")
    out_dir = Path(cfg.export_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    final_mp4 = out_dir / f"Aero_{clean_title}_{ar}_{vt}_{int(time.time())}.mp4"

    compose_final_video(
        bg_video=bg_video,
        char_video=char_mov,
        voice_audio=master_wav,
        ass_subtitles=ass_path,
        total_duration=total_dur,
        output_mp4=final_mp4
    )

    report(f"Concluído com sucesso! Salvo em: {final_mp4.name}", 100)
    return final_mp4
