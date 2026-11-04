import os
import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from fastapi import FastAPI, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from aero_engine.compat import model_to_dict
from aero_engine.config import get_config, save_config, validate_gemini_api_key, AeroConfig, ASSETS_DIR
from aero_engine.pipeline import run_pipeline
from aero_engine.avatar_studio import (
    list_avatars,
    generate_avatar_concept,
    approve_avatar_concept,
    generate_avatar_expression,
    AVATARS_DIR,
    BASE_EXPRESSIONS
)
from aero_engine.voice_studio import (
    list_available_voices,
    generate_voice_sample,
    save_reference_audio,
    generate_benchmark_short,
    VOICES_DIR
)
from aero_engine.publisher import generate_seo_package, upload_to_youtube_direct
from aero_engine.scheduler import (
    get_scheduler_config,
    save_scheduler_config,
    start_background_scheduler,
    stop_background_scheduler,
    SchedulerConfig
)

app = FastAPI(title="AeroInfluencer API", version="2.5.0")

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
    tone: Optional[str] = "sarcastic"
    reference_urls: Optional[List[str]] = []
    aspect_ratio: Optional[str] = "vertical"
    video_type: Optional[str] = "shorts"
    image_gen_mode: Optional[str] = "AUTO"
    music_volume: Optional[float] = 0.14
    avatar_id: Optional[str] = "nova"
    voice_id: Optional[str] = "en-GB-MaisieNeural"

class AvatarConceptRequest(BaseModel):
    avatar_id: str
    description: str

class AvatarApproveRequest(BaseModel):
    avatar_id: str
    version_num: int

class AvatarExpressionRequest(BaseModel):
    avatar_id: str
    expression_name: str
    custom_prompt_tweak: Optional[str] = None

class VoiceSampleRequest(BaseModel):
    voice_id: str
    sample_text: Optional[str] = None

class BenchmarkRequest(BaseModel):
    avatar_id: str
    voice_id: str
    topic: Optional[str] = "Teste de Calibração"

# ----------------- Core Config & Key -----------------
@app.get("/api/config")
def api_get_config():
    cfg = get_config()
    data = model_to_dict(cfg)
    raw_key = data.pop("google_gemini_api_key", None)  # nunca devolver a chave inteira
    if raw_key:
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

# ----------------- Production Pipeline -----------------
async def _bg_run_pipeline(job_id: str, req: GenerateRequest):
    JOBS[job_id]["status"] = "processing"
    
    def on_progress(msg: str, pct: int):
        JOBS[job_id]["message"] = msg
        JOBS[job_id]["progress"] = pct

    try:
        combined_topic = req.topic
        if req.reference_urls:
            combined_topic += " (Fontes: " + ", ".join(req.reference_urls) + ")"
            
        out_path = await run_pipeline(
            topic=combined_topic,
            aspect_ratio=req.aspect_ratio,
            video_type=req.video_type,
            image_gen_mode=req.image_gen_mode,
            progress_callback=on_progress
        )
        
        # Auto-generate SEO package
        seo = generate_seo_package(
            topic=req.topic,
            script_beats=[],
            sources=req.reference_urls or ["Web News"],
            video_type=req.video_type or "shorts"
        )
        seo_file = out_path.parent / f"{out_path.stem}_seo.json"
        with open(seo_file, "w", encoding="utf-8") as f:
            json.dump(seo, f, indent=2, ensure_ascii=False)
            
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["video_path"] = str(out_path)
        JOBS[job_id]["video_filename"] = out_path.name
        JOBS[job_id]["seo"] = seo
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
        "status": "queued",
        "progress": 0,
        "message": "Inicializando pipeline...",
        "video_path": None,
        "video_filename": None
    }
    bg_tasks.add_task(_bg_run_pipeline, job_id, req)
    return {"job_id": job_id, "status": "queued"}

@app.get("/api/status/{job_id}")
def api_status(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

# ----------------- Video Library & SEO -----------------
@app.get("/api/videos")
def api_list_videos():
    cfg = get_config()
    out_dir = Path(cfg.export_dir)
    if not out_dir.exists():
        return []
    
    videos = []
    for f in sorted(out_dir.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
        seo_path = out_dir / f"{f.stem}_seo.json"
        has_seo = seo_path.exists()
        videos.append({
            "filename": f.name,
            "size_mb": round(f.stat().st_size / (1024 * 1024), 2),
            "created_at": f.stat().st_mtime,
            "url": f"/api/video/{f.name}",
            "has_seo": has_seo
        })
    return videos

@app.get("/api/video/{filename}")
def api_get_video(filename: str):
    cfg = get_config()
    v_path = Path(cfg.export_dir) / filename
    if not v_path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(str(v_path), media_type="video/mp4")

@app.get("/api/video/{filename}/seo")
def api_get_video_seo(filename: str):
    cfg = get_config()
    base_stem = Path(filename).stem
    seo_file = Path(cfg.export_dir) / f"{base_stem}_seo.json"
    if seo_file.exists():
        with open(seo_file, "r", encoding="utf-8") as f:
            return json.load(f)
    # Generate on the fly if not existing
    return generate_seo_package(base_stem.replace("_", " "), [], ["Web Search"])

# ----------------- Avatar Studio -----------------
@app.get("/api/avatar/list")
def api_avatar_list():
    return list_avatars()

@app.get("/api/avatar/base-expressions")
def api_base_expressions():
    return BASE_EXPRESSIONS

@app.post("/api/avatar/generate-concept")
def api_avatar_generate_concept(req: AvatarConceptRequest):
    cfg = get_config()
    return generate_avatar_concept(req.avatar_id, req.description, cfg.google_gemini_api_key)

@app.post("/api/avatar/approve-concept")
def api_avatar_approve_concept(req: AvatarApproveRequest):
    return approve_avatar_concept(req.avatar_id, req.version_num)

@app.post("/api/avatar/generate-expression")
def api_avatar_generate_expression(req: AvatarExpressionRequest):
    cfg = get_config()
    return generate_avatar_expression(req.avatar_id, req.expression_name, req.custom_prompt_tweak, cfg.google_gemini_api_key)

@app.get("/api/avatar/preview/{avatar_id}")
def api_avatar_preview(avatar_id: str):
    if avatar_id == "nova":
        p = ASSETS_DIR / "pngtuber_sprites" / "nova_neutral_transparent.png"
    else:
        p = AVATARS_DIR / avatar_id / "master_reference.png"
        if not p.exists():
            p = AVATARS_DIR / avatar_id / "versions" / "version_1.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    raise HTTPException(status_code=404, detail="Preview not found")

@app.get("/api/avatar/version/{avatar_id}/{v_num}")
def api_avatar_version(avatar_id: str, v_num: int):
    p = AVATARS_DIR / avatar_id / "versions" / f"version_{v_num}.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    raise HTTPException(status_code=404, detail="Version not found")

@app.get("/api/avatar/sprite/{avatar_id}/{expr_name}")
def api_avatar_sprite(avatar_id: str, expr_name: str):
    p = AVATARS_DIR / avatar_id / "sprites" / f"{expr_name}.png"
    if p.exists():
        return FileResponse(str(p), media_type="image/png")
    raise HTTPException(status_code=404, detail="Sprite not found")

# ----------------- Voice Studio -----------------
@app.get("/api/voice/list")
def api_voice_list():
    return list_available_voices()

@app.post("/api/voice/sample")
async def api_voice_sample(req: VoiceSampleRequest):
    sample_path = await generate_voice_sample(req.voice_id, req.sample_text)
    return FileResponse(str(sample_path), media_type="audio/mpeg")

@app.post("/api/voice/upload-reference")
async def api_voice_upload_reference(file: UploadFile = File(...)):
    content = await file.read()
    return save_reference_audio(content, file.filename)

@app.post("/api/voice/benchmark")
async def api_voice_benchmark(req: BenchmarkRequest, bg_tasks: BackgroundTasks):
    job_id = f"bench_{int(asyncio.get_event_loop().time())}"
    JOBS[job_id] = {
        "job_id": job_id,
        "topic": req.topic,
        "status": "queued",
        "progress": 0,
        "message": "Inicializando Benchmark de Teste..."
    }
    
    async def _run():
        JOBS[job_id]["status"] = "processing"
        out_v = await generate_benchmark_short(req.avatar_id, req.voice_id, req.topic)
        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["video_filename"] = out_v.name
        JOBS[job_id]["progress"] = 100
        
    bg_tasks.add_task(_run)
    return {"job_id": job_id, "status": "queued"}

# ----------------- Scheduler & Autopilot -----------------
@app.get("/api/scheduler")
def api_get_scheduler():
    return model_to_dict(get_scheduler_config())

@app.post("/api/scheduler")
def api_save_scheduler(sc: SchedulerConfig):
    save_scheduler_config(sc)
    if sc.enabled:
        start_background_scheduler()
    else:
        stop_background_scheduler()
    return {"status": "ok", "config": model_to_dict(sc)}

# ----------------- Static UI Mount -----------------
UI_DIR = Path(__file__).parent / "ui"
UI_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/", StaticFiles(directory=str(UI_DIR), html=True), name="ui")

@app.on_event("startup")
def on_startup():
    sc = get_scheduler_config()
    if sc.enabled:
        start_background_scheduler()

def start_mobile_server(port: int = 8000):
    import uvicorn
    config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=port,
        log_level="error",
        access_log=False
    )
    server = uvicorn.Server(config)
    server.run()
