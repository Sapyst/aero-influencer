import sys
import json
import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field
from aero_engine.compat import model_to_dict

def get_base_dir() -> Path:
    if "AERO_BASE_DIR" in os.environ and Path(os.environ["AERO_BASE_DIR"]).exists():
        return Path(os.environ["AERO_BASE_DIR"])
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return Path(sys._MEIPASS)
        return Path(sys.executable).parent
    engine_dir = Path(__file__).resolve().parent
    if (engine_dir.parent / "assets").exists():
        return engine_dir.parent
    if (engine_dir / "assets").exists():
        return engine_dir
    return engine_dir.parent

BASE_DIR = get_base_dir()
ASSETS_DIR = BASE_DIR / "assets"

def get_config_dir() -> Path:
    if "AERO_DATA_DIR" in os.environ:
        return Path(os.environ["AERO_DATA_DIR"]) / ".aeroinfluencer"
    return Path.home() / ".aeroinfluencer"

def get_default_export_dir() -> Path:
    if "AERO_EXPORT_DIR" in os.environ:
        return Path(os.environ["AERO_EXPORT_DIR"])
    # Support Android gallery paths
    for candidate in [Path("/storage/emulated/0/Movies/AeroInfluencer"), Path("/storage/emulated/0/Download/AeroInfluencer")]:
        try:
            if candidate.parent.exists():
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate
        except Exception:
            pass
    return Path.home() / "AeroInfluencer_Videos"

CONFIG_DIR = get_config_dir()
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_EXPORT_DIR = get_default_export_dir()
TEMP_DIR = CONFIG_DIR / "temp"

def get_ffmpeg_bin() -> str:
    import shutil
    if "FFMPEG_PATH" in os.environ and Path(os.environ["FFMPEG_PATH"]).exists():
        return os.environ["FFMPEG_PATH"]
    for candidate in [BASE_DIR / "bin" / "ffmpeg", BASE_DIR / "ffmpeg"]:
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    return "ffmpeg"

FFMPEG_BIN = get_ffmpeg_bin()

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
        json.dump(model_to_dict(cfg), f, indent=2)

def validate_gemini_api_key(api_key: str) -> dict:
    if not api_key or len(api_key.strip()) < 15:
        return {"valid": False, "message": "Chave de API parece curta ou inválida."}
    
    # 1. Try universal HTTP REST request first (pure Python, zero extra dependencies)
    import requests
    for model_candidate in ["gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-flash-latest"]:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_candidate}:generateContent?key={api_key.strip()}"
            r = requests.post(url, json={"contents": [{"parts": [{"text": "Say OK in one word"}]}]}, timeout=10)
            if r.status_code == 200:
                return {"valid": True, "message": f"Chave validada com sucesso com o modelo {model_candidate}!"}
        except Exception:
            continue

    # 2. Try SDK fallback if installed
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
    except Exception:
        pass

    return {"valid": False, "message": "Não foi possível conectar à API do Gemini. Verifique a chave e conexão."}
