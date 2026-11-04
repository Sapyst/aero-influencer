import asyncio
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel
from aero_engine.compat import model_to_dict

from aero_engine.config import get_config
from aero_engine.pipeline import run_pipeline
from aero_engine.publisher import generate_seo_package, upload_to_youtube_direct

SCHEDULER_CONFIG = Path.home() / ".aeroinfluencer" / "scheduler.json"

class SchedulerConfig(BaseModel):
    enabled: bool = False
    alarm_times: List[str] = ["09:00", "14:00", "19:00"]
    categories: List[str] = ["Cibersegurança e Hacker News", "Inteligência Artificial", "Astronomia e Ciência"]
    auto_publish_youtube: bool = False
    skip_test_mode: bool = True  # Direct production without asking for approval
    last_run_timestamp: Optional[float] = None

_SCHEDULER_TASK = None
_RUNNING = False

def get_scheduler_config() -> SchedulerConfig:
    if not SCHEDULER_CONFIG.exists():
        SCHEDULER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        default_sc = SchedulerConfig()
        save_scheduler_config(default_sc)
        return default_sc
    try:
        import json
        with open(SCHEDULER_CONFIG, "r", encoding="utf-8") as f:
            return SchedulerConfig(**json.load(f))
    except Exception:
        return SchedulerConfig()

def save_scheduler_config(sc: SchedulerConfig):
    import json
    SCHEDULER_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(SCHEDULER_CONFIG, "w", encoding="utf-8") as f:
        json.dump(model_to_dict(sc), f, indent=2)

async def _scheduler_loop():
    global _RUNNING
    _RUNNING = True
    print("⏰ [AeroScheduler] Motor de automação contínua ativado em segundo plano.")
    
    last_minute_checked = ""
    
    while _RUNNING:
        try:
            cfg = get_scheduler_config()
            if not cfg.enabled:
                await asyncio.sleep(10)
                continue
                
            now = datetime.now()
            cur_time = now.strftime("%H:%M")
            
            if cur_time in cfg.alarm_times and cur_time != last_minute_checked:
                last_minute_checked = cur_time
                print(f"⏰ [AeroScheduler] TRIGGER DISPARADO às {cur_time}! Iniciando ciclo autônomo...")
                
                # Pick topic from categories
                category = cfg.categories[now.day % len(cfg.categories)]
                topic = f"{category} notícias recentes em destaque"
                
                print(f"  Produzindo vídeo autônomo: {topic}")
                out_path = await run_pipeline(
                    topic=topic,
                    aspect_ratio="vertical",
                    video_type="shorts",
                    image_gen_mode="AUTO"
                )
                print(f"  Vídeo produzido: {out_path.name}")
                
                cfg.last_run_timestamp = time.time()
                save_scheduler_config(cfg)
                
        except Exception as e:
            print(f"Scheduler loop error: {e}")
            
        await asyncio.sleep(20)

def start_background_scheduler():
    global _SCHEDULER_TASK
    if _SCHEDULER_TASK is None or _SCHEDULER_TASK.done():
        _SCHEDULER_TASK = asyncio.create_task(_scheduler_loop())

def stop_background_scheduler():
    global _RUNNING
    _RUNNING = False
