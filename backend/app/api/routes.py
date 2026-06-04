import os
import re
import uuid
import glob
import asyncio
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks, Request
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from ..config import config
from ..services.video_processor import VideoProcessor

app = FastAPI(title=config.APP_NAME, version=config.VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

processing_jobs = {}

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend", "public")


# ── HTML Routes ───────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    file_path = os.path.join(FRONTEND_DIR, "index.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/upload", response_class=HTMLResponse)
async def serve_upload():
    file_path = os.path.join(FRONTEND_DIR, "upload.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/history", response_class=HTMLResponse)
async def serve_history():
    file_path = os.path.join(FRONTEND_DIR, "history.html")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


# ── API Routes ────────────────────────────────────────────────

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "gpu_available": config.USE_GPU}


def process_video_sync(job_id, input_path, output_path):
    """Synchronous video processing with progress updates"""
    try:
        print(f"Starting processing for job {job_id}")

        processing_jobs[job_id]["status"] = "processing"
        processing_jobs[job_id]["progress"] = 0
        processing_jobs[job_id]["count"] = 0
        processing_jobs[job_id]["fps"] = 0

        processor = VideoProcessor(input_path, output_path)

        def progress_callback(progress, fps, count):
            processing_jobs[job_id]["progress"] = progress
            processing_jobs[job_id]["count"] = count
            processing_jobs[job_id]["fps"] = fps
            print(f"Job {job_id}: Progress {progress}%, FPS: {fps:.1f}, Count: {count}")

        result = processor.process(progress_callback=progress_callback)

        processing_jobs[job_id]["status"] = "completed"
        processing_jobs[job_id]["result"] = result
        processing_jobs[job_id]["count"] = result["total_count"]
        processing_jobs[job_id]["progress"] = 100
        processing_jobs[job_id]["events"] = result.get("events", [])
        processing_jobs[job_id]["line_stats"] = result.get("line_stats", [])
        processing_jobs[job_id]["vehicle_breakdown"] = result.get("vehicle_breakdown", {})

        print(f"Job {job_id} completed. Total count: {result['total_count']}")

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        import traceback
        traceback.print_exc()
        processing_jobs[job_id]["status"] = "failed"
        processing_jobs[job_id]["error"] = str(e)


@app.post("/api/upload")
async def upload_video(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {config.ALLOWED_EXTENSIONS}"
        )

    job_id = str(uuid.uuid4())
    input_path = os.path.join(config.UPLOAD_DIR, f"{job_id}_input{ext}")
    output_path = os.path.join(config.PROCESSED_DIR, f"{job_id}_output.mp4")

    content = await file.read()
    if len(content) > config.MAX_VIDEO_SIZE:
        raise HTTPException(status_code=400, detail="File too large")

    with open(input_path, "wb") as f:
        f.write(content)

    processing_jobs[job_id] = {
        "job_id": job_id,
        "status": "uploaded",
        "input_path": input_path,
        "output_path": output_path,
        "progress": 0,
        "count": 0,
        "fps": 0,
        "result": None,
        "events": [],
        "line_stats": [],
        "vehicle_breakdown": {},
        "error": None
    }

    background_tasks.add_task(process_video_sync, job_id, input_path, output_path)

    return {"job_id": job_id, "status": "processing", "message": "Video uploaded and processing started"}


@app.get("/api/status/{job_id}")
async def get_status(job_id: str):
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[job_id]
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "count": job.get("count", 0),
        "fps": job.get("fps", 0),
        "result": job.get("result", None),
        "events": job.get("events", []),
        "line_stats": job.get("line_stats", []),
        "vehicle_breakdown": job.get("vehicle_breakdown", {}),
        "error": job.get("error", None)
    }


@app.get("/api/download/{job_id}")
async def download_result(job_id: str):
    if job_id not in processing_jobs:
        raise HTTPException(status_code=404, detail="Job not found")

    job = processing_jobs[job_id]
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Processing not completed")

    if not os.path.exists(job["output_path"]):
        raise HTTPException(status_code=404, detail="Output file not found")

    return FileResponse(
        job["output_path"],
        filename=f"processed_{job_id}.mp4",
        media_type="video/mp4"
    )


@app.get("/api/watch/{job_id}")
async def watch_video(job_id: str, request: Request):
    """
    Serve video with full HTTP Range request support.
    This is REQUIRED for <video> elements to play in the browser.
    Plain FileResponse does not support byte ranges — browsers
    need 206 Partial Content responses to seek and buffer video.
    """
    clean_job_id = job_id.replace("_output", "")
    file_path = os.path.join(config.PROCESSED_DIR, f"{clean_job_id}_output.mp4")

    print(f"[WATCH] job_id: {clean_job_id}")
    print(f"[WATCH] file_path: {file_path}")
    print(f"[WATCH] file_exists: {os.path.exists(file_path)}")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"Video not found: {file_path}")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", None)

    if range_header is None:
        # No range header — serve the full file from byte 0
        start = 0
        end   = file_size - 1
    else:
        # Parse Range header format: "bytes=START-END"
        match = re.search(r"bytes=(\d+)-(\d*)", range_header)
        if not match:
            raise HTTPException(status_code=416, detail="Invalid Range header")

        start = int(match.group(1))
        end   = int(match.group(2)) if match.group(2) else file_size - 1

    # Make sure end does not exceed the actual file size
    end            = min(end, file_size - 1)
    content_length = end - start + 1

    def iter_file_range(path: str, start: int, end: int, chunk_size: int = 1024 * 256):
        """
        Generator function that reads only the requested byte range.
        Yields chunks of 256 KB at a time to keep memory usage low.
        """
        with open(path, "rb") as f:
            f.seek(start)
            remaining = end - start + 1
            while remaining > 0:
                read_size = min(chunk_size, remaining)
                data      = f.read(read_size)
                if not data:
                    break
                remaining -= len(data)
                yield data

    headers = {
        "Content-Range":  f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges":  "bytes",
        "Content-Length": str(content_length),
        "Content-Type":   "video/mp4",
    }

    # Return 206 Partial Content when a Range was requested, 200 for full file
    status_code = 206 if range_header else 200

    return StreamingResponse(
        iter_file_range(file_path, start, end),
        status_code=status_code,
        headers=headers,
        media_type="video/mp4",
    )


@app.get("/api/videos")
async def list_videos():
    """List all processed video files from the folder"""
    print(f"[VIDEOS] Scanning folder: {config.PROCESSED_DIR}")
    video_files = glob.glob(os.path.join(config.PROCESSED_DIR, "*_output.mp4"))
    print(f"[VIDEOS] Found {len(video_files)} video files")

    videos = []
    for file_path in sorted(video_files, key=os.path.getmtime, reverse=True):
        filename = os.path.basename(file_path)
        job_id   = filename.replace("_output.mp4", "")
        size_mb  = round(os.path.getsize(file_path) / (1024 * 1024), 2)
        mod_time = os.path.getmtime(file_path)
        videos.append({
            "job_id":  job_id,
            "size_mb": size_mb,
            "date":    mod_time
        })

    return {"videos": videos}


@app.get("/api/jobs")
async def list_jobs():
    jobs = []
    for job_id, job in processing_jobs.items():
        jobs.append({
            "job_id":   job_id,
            "status":   job["status"],
            "count":    job.get("count", 0),
            "progress": job.get("progress", 0),
            "result":   job.get("result", None)
        })
    return {"jobs": jobs}