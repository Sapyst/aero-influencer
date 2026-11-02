import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import edge_tts

VOICES_DIR = Path("/home/sapista/aero_influencer/assets/voices")
VOICES_DIR.mkdir(parents=True, exist_ok=True)

CURATED_VOICES = [
    {"id": "en-GB-MaisieNeural", "name": "Maisie (Britânica Jovem / Ágil)", "lang": "Inglês", "gender": "Feminino", "tone": "Expressiva, curiosa, ritmo acelerado"},
    {"id": "en-GB-SoniaNeural", "name": "Sonia (Britânica Elegante)", "lang": "Inglês", "gender": "Feminino", "tone": "Polida, jornalística, clara"},
    {"id": "en-US-JennyNeural", "name": "Jenny (Americana Natural)", "lang": "Inglês", "gender": "Feminino", "tone": "Conversacional, amigável"},
    {"id": "en-US-GuyNeural", "name": "Guy (Americano Dinâmico)", "lang": "Inglês", "gender": "Masculino", "tone": "Narrativa documental, firme"},
    {"id": "pt-BR-FranciscaNeural", "name": "Francisca (Brasileira Expressiva)", "lang": "Português", "gender": "Feminino", "tone": "Natural, animada, comunicativa"},
    {"id": "pt-BR-AntonioNeural", "name": "Antônio (Brasileiro Narrador)", "lang": "Português", "gender": "Masculino", "tone": "Jornalismo investigativo, encorpado"}
]

def list_available_voices() -> List[Dict]:
    return CURATED_VOICES

async def generate_voice_sample(voice_id: str, sample_text: Optional[str] = None) -> Path:
    text = sample_text or "Olá! Esta é uma demonstração de como a minha voz soa no AeroInfluencer. Ritmo dinâmico e sem pausas mortas!"
    out_file = VOICES_DIR / f"sample_{voice_id}.mp3"
    comm = edge_tts.Communicate(text, voice_id)
    await comm.save(str(out_file))
    return out_file

def save_reference_audio(audio_bytes: bytes, filename: str) -> Dict:
    """
    Saves user-uploaded reference audio for voice profiling.
    """
    out_file = VOICES_DIR / f"custom_ref_{int(time.time())}_{filename}"
    with open(out_file, "wb") as f:
        f.write(audio_bytes)
        
    return {
        "status": "saved",
        "file_path": str(out_file),
        "filename": out_file.name,
        "message": "Áudio de referência salvo com sucesso! Analisando perfil acústico..."
    }

async def generate_benchmark_short(
    avatar_id: str,
    voice_id: str,
    topic: str = "O Teste de Calibração do AeroInfluencer"
) -> Path:
    """
    Produces a quick 10-second benchmark Short with the selected avatar & voice,
    allowing the user to evaluate tone, lip-sync, and presence before scaling up.
    """
    from aero_engine.pipeline import run_pipeline
    test_topic = f"{topic} (Benchmark de Teste Rápido)"
    out_video = await run_pipeline(
        topic=test_topic,
        aspect_ratio="vertical",
        video_type="shorts",
        image_gen_mode="NEVER"
    )
    return out_video
