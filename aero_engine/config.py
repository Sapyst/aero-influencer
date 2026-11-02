import sys
import json
import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field

def get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    engine_dir = Path(__file__).resolve().parent
    if (engine_dir.parent / "assets").exists():
        return engine_dir.parent
    return engine_dir

BASE_DIR = get_base_dir()
ASSETS_DIR = BASE_DIR / "assets"
CONFIG_DIR = Path.home() / ".aeroinfluencer"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_EXPORT_DIR = Path.home() / "AeroInfluencer_Videos"
TEMP_DIR = CONFIG_DIR / "temp"

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
    export_dir: str = Field(default_factory=lambda: str(DEFAULT_EXPORT_DIR), description="Directory to export rendered videos")

def get_config() -> AeroConfig:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    DEFAULT_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    
    cfg = None
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cfg = AeroConfig(**data)
        except Exception:
            cfg = AeroConfig()
    else:
        cfg = AeroConfig()

    # Sanitize and migrate old or hardcoded paths
    if not cfg.export_dir or "/home/sapista" in cfg.export_dir or not Path(cfg.export_dir).is_absolute():
        cfg.export_dir = str(DEFAULT_EXPORT_DIR)
        save_config(cfg)

    # Check environment variable if key is empty
    if not cfg.google_gemini_api_key:
        env_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if env_key:
            cfg.google_gemini_api_key = env_key.strip()
            save_config(cfg)
            
    return cfg

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
        for model_candidate in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]:
            try:
                response = client.models.generate_content(
                    model=model_candidate,
                    contents="Say 'OK' in one word."
                )
                if response and response.text:
                    return {"valid": True, "message": f"Chave validada com sucesso com o modelo {model_candidate}!"}
            except Exception:
                continue
        return {"valid": False, "message": "Não foi possível obter resposta dos modelos Gemini."}
    except Exception as e:
        return {"valid": False, "message": f"Erro ao validar chave: {str(e)}"}
