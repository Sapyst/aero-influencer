import json
import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field

CONFIG_DIR = Path.home() / ".aeroinfluencer"
CONFIG_FILE = CONFIG_DIR / "config.json"

ImageGenMode = Literal["NEVER", "AUTO", "ALWAYS"]
AspectRatio = Literal["vertical", "horizontal"]
VideoType = Literal["shorts", "full_video"]

class AeroConfig(BaseModel):
    google_gemini_api_key: Optional[str] = Field(default=None, description="Google AI Studio Gemini API Key")
    image_gen_mode: ImageGenMode = Field(default="AUTO", description="Image Generation Policy: NEVER (100% scraped/stock), AUTO (fill gaps), ALWAYS (100% AI)")
    aspect_ratio: AspectRatio = Field(default="vertical", description="Video orientation: vertical (9:16 Shorts) or horizontal (16:9 Full Desktop/Landscape)")
    video_type: VideoType = Field(default="shorts", description="Format: 'shorts' (fast, direct, 30-50s) or 'full_video' (in-depth, 2-6 min investigative)")
    default_voice: str = Field(default="en-GB-MaisieNeural", description="Narrator voice")
    mascot: str = Field(default="nova", description="Active mascot persona")
    export_dir: str = Field(default=str(Path("/home/sapista/aero_influencer/output")), description="Directory to export rendered videos")

def get_config() -> AeroConfig:
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        default_cfg = AeroConfig()
        save_config(default_cfg)
        return default_cfg
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return AeroConfig(**data)
    except Exception:
        return AeroConfig()

def save_config(cfg: AeroConfig) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg.model_dump(), f, indent=2)

def validate_gemini_api_key(api_key: str) -> dict:
    if not api_key or len(api_key.strip()) < 15:
        return {"valid": False, "message": "Chave de API parece curta ou inválida."}
    try:
        from google import genai
        client = genai.Client(api_key=api_key.strip())
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents="Say 'OK' in one word."
        )
        if response and response.text:
            return {"valid": True, "message": "Chave de API validada com sucesso no Google AI Studio!"}
        return {"valid": False, "message": "Não foi possível obter resposta do Gemini."}
    except Exception as e:
        return {"valid": False, "message": f"Erro ao validar chave: {str(e)}"}
