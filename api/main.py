import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from scanner import scan


app = FastAPI(title="Auto-patching")
logger = logging.getLogger(__name__)

UPLOAD_DIR = Path(__file__).resolve().parent.parent / "data" / "uploads"
LANGUAGES = {".py": "python",".c": "c"}
MAX_BYTES = 1_000_000 

CONTRACT_FIELDS = [
    "id", "status", "language", "filename",
    "findings", "diff", "explanation", "attempts", "decision",
]
UPLOADED = "uploaded"
SCANNING = "scanning"
CLEAN = "clean"
PATCHING = "patching"
VALIDATING = "validating"
ACCEPTED = "accepted"
NEEDS_HUMAN = "needs_human"
REJECTED = "rejected"

STATUSES = [
    UPLOADED, SCANNING, CLEAN, PATCHING,
    VALIDATING, ACCEPTED, NEEDS_HUMAN, REJECTED,
]

def to_contract(meta: dict) -> dict:
    if meta.get("status") not in STATUSES:
        raise ValueError(f"Invalid status: {meta.get('status')!r}")
    return {field: meta.get(field) for field in CONTRACT_FIELDS}

def read_meta(job_id: str) -> dict:
    return json.loads((UPLOAD_DIR / job_id / "meta.json").read_text())

def write_meta(job_id: str, meta: dict) -> None:
    path = UPLOAD_DIR / job_id / "meta.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(meta))
    tmp.replace(path)
    
def run_scan(job_id: str) -> None:
    """Background task: scan the saved upload and record the result."""
    meta = read_meta(job_id)
    meta["status"] = SCANNING
    write_meta(job_id, meta)

    original = UPLOAD_DIR / job_id / "original"
    try:
        findings = scan(str(original), meta["language"])
    except Exception:
        logger.exception("scan failed for job %s", job_id)
        meta["error"] = "scan failed"      
        write_meta(job_id, meta)
        return

    meta["findings"] = findings
    if not findings:
        meta["status"] = CLEAN             # nothing found: stop here, no model
    write_meta(job_id, meta)


@app.get("/health")
def health():
    return {"status": "ok"}
  
@app.post("/jobs")
async def create_job(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())
    filename = Path(file.filename or "unknown").name   # drop any folder part
    language = LANGUAGES.get(Path(filename).suffix.lower())

    folder = UPLOAD_DIR / job_id
    folder.mkdir(parents=True, exist_ok=True)


    status, message = UPLOADED, None
    if language is None:
        status, message = REJECTED, "Only .py and .c files are accepted."
    else:
        content = await file.read()
        if len(content) > MAX_BYTES:
            status, message = REJECTED, "File too large (max 1 MB)."
        else:
            (folder / "original").write_bytes(content)

    job = {
        "id": job_id,
        "status": status,
        "language": language,
        "filename": filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "message": message,
    }
    write_meta(job_id, job)

    if status == UPLOADED:                 
        background_tasks.add_task(run_scan, job_id)
    return to_contract(job)
  
@app.get("/jobs/{job_id}")
def get_job(job_id:str):
  try: 
    uuid.UUID(job_id)
  except ValueError:
    raise HTTPException(status_code=404, detail="job ID not found")
  meta_file = UPLOAD_DIR / job_id / "meta.json"
  if not meta_file.exists():
    raise HTTPException(status_code=404, detail="job ID not found")
  return to_contract(read_meta(job_id))
