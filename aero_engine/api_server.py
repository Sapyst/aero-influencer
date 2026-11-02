import os
import asyncio
from pathlib import Path
from typing import Optional, Dict
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from aero_engine.config import get_config, save_config, validate_gemini_api_key, AeroConfig
from aero_engine.pipeline import run_pipeline

app = FastAPI(title="AeroInfluencer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

JOBS: Dict[str, Dict] = {}

class KeyValidationRequest(BaseModel):
    api_key: str

class GenerateRequest(BaseModel):
    topic: str
    aspect_ratio: Optional[str] = "vertical"
    video_type: Optional[str] = "shorts"
    image_gen_mode: Optional[str] = "AUTO"

@app.get("/api/config")
def api_get_config():
    cfg = get_config()
    data = cfg.model_dump()
    # Mask API key if set for security
    if data.get("google_gemini_api_key"):
        raw_key = data["google_gemini_api_key"]
        data["has_api_key"] = True
        data["masked_key"] = raw_key[:4] + "..." + raw_key[-4:] if len(raw_key) > 8 else "***"
    else:
        data["has_api_key"] = False
        data["masked_key"] = ""
    return data

@app.post("/api/config")
def api_save_config(new_cfg: AeroConfig):
    save_config(new_cfg)
    return {"status": "ok", "message": "Configurações salvas com sucesso!"}

@app.post("/api/validate-key")
def api_validate_key(req: KeyValidationRequest):
    res = validate_gemini_api_key(req.api_key)
    if res.get("valid"):
        cfg = get_config()
        cfg.google_gemini_api_key = req.api_key.strip()
        save_config(cfg)
    return res

async def _bg_run_pipeline(job_id: str, topic: str, aspect_ratio: str, video_type: str, image_gen_mode: str):
    JOBS[job_id]["status"] = "processing"
    
    def on_progress(msg: str, pct: int):
        JOBS[job_id]["message"] = msg
        JOBS[job_id]["progress"] = pct

    try:
        out_path = await run_pipeline(
            topic=topic,
            aspect_ratio=aspect_ratio,
            video_type=video_type,
            image_gen_mode=image_gen_mode,
            progress_callback=on_progress
        )
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["video_path"] = str(out_path)
        JOBS[job_id]["video_filename"] = out_path.name
        JOBS[job_id]["message"] = "Renderização concluída com sucesso!"
        JOBS[job_id]["progress"] = 100
    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
        JOBS[job_id]["message"] = f"Falha na renderização: {str(e)}"

@app.post("/api/generate")
async def api_generate(req: GenerateRequest, bg_tasks: BackgroundTasks):
    job_id = f"job_{len(JOBS) + 1}_{int(asyncio.get_event_loop().time())}"
    JOBS[job_id] = {
        "job_id": job_id,
        "topic": req.topic,
        "aspect_ratio": req.aspect_ratio,
        "video_type": req.video_type,
        "image_gen_mode": req.image_gen_mode,
        "status": "queued",
        "progress": 0,
        "message": "Inicializando pipeline...",
        "video_path": None,
        "video_filename": None
    }
    bg_tasks.add_task(_bg_run_pipeline, job_id, req.topic, req.aspect_ratio, req.video_type, req.image_gen_mode)
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/status/{job_id}")
def api_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/videos")
def api_list_videos():
    cfg = get_config()
    out_dir = Path(cfg.export_dir)
    if not out_dir.exists():
        return []
    
    videos = []
    for f in sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        videos.append({
            "filename": f.name,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "created_at": f.stat().st_mtime,
            "url": f"/api/video/{f.name}"
        })
    return videos

@app.get("/api/video/{filename}")
def api_get_video(filename: str):
    cfg = get_config()
    v_path = Path(cfg.export_dir) / filename
    if not v_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(str(v_path), media_type="video/mp4")

# UI static mount
UI_DIR = Path(__file__).parent / "ui"
UI_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")
