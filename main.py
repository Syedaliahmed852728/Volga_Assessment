from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.concurrency import run_in_threadpool
from pathlib import Path
import shutil
import subprocess
import hashlib
import whisper
from typing import List, Dict
import sqlite3
import json

app = FastAPI()

UPLOAD_DIR = Path("uploads")
NORMALIZED_DIR = Path("normalized")
UPLOAD_DIR.mkdir(exist_ok=True, parents=True)
NORMALIZED_DIR.mkdir(exist_ok=True, parents=True)

ALLOWED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm"}

MODEL = whisper.load_model("base", device="cpu")


DB_PATH = "transcriptions.db"


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcriptions (
            file_hash TEXT PRIMARY KEY,
            language TEXT,
            text TEXT,
            segments TEXT
        )
    """)

    conn.commit()
    conn.close()


init_db()


def db_get(hash_id: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT language, text, segments FROM transcriptions WHERE file_hash=?",
        (hash_id,),
    )
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "language": row[0],
        "text": row[1],
        "segments": json.loads(row[2]) if row[2] else None,
    }


def db_save(hash_id: str, language: str, text: str, segments: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT OR REPLACE INTO transcriptions
        (file_hash, language, text, segments)
        VALUES (?, ?, ?, ?)
    """,
        (hash_id, language, text, json.dumps(segments)),
    )

    conn.commit()
    conn.close()


def validate(file: UploadFile):
    if not file.filename:
        raise HTTPException(400, "Filename missing")

    if Path(file.filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, "Unsupported file type")


def save(file: UploadFile, path: Path):
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)


def compute_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def normalize(inp: Path, out: Path):
    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-i",
            str(inp),
            "-vn",
            "-ac",
            "1",
            "-ar",
            "16000",
            "-c:a",
            "pcm_s16le",
            str(out),
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True,
    )


def transcribe(path: Path):

    return MODEL.transcribe(str(path))


def process_pipeline(raw_path: Path, file_hash: str):
    norm_path = NORMALIZED_DIR / f"{file_hash}_16k.wav"

    if not norm_path.exists():
        normalize(raw_path, norm_path)

    result = transcribe(norm_path)
    segments: List[Dict] = [
        {
            "start": s["start"],
            "end": s["end"],
            "text": s["text"].strip(),
            "duration": s["end"] - s["start"],
        }
        for s in result.get("segments", [])
    ]

    db_save(file_hash, result.get("language"), result.get("text", ""), segments)
    return result, segments


@app.post("/transcribe/")
async def transcribe_audio(audio: UploadFile = File(...)):
    validate(audio)

    content = await audio.read()

    file_hash = hashlib.sha256(content).hexdigest()

    cached = db_get(file_hash)
    if cached and cached.get("text"):
        return {
            "file_hash": file_hash,
            "language": cached["language"],
            "text": cached["text"],
            "cached": True,
        }

    raw_path = UPLOAD_DIR / audio.filename

    with open(raw_path, "wb") as f:
        f.write(content)

    result, _ = await run_in_threadpool(process_pipeline, raw_path, file_hash)

    response = {
        "file_hash": file_hash,
        "language": result.get("language"),
        "text": result.get("text", "").strip(),
    }
    return response


@app.post("/transcribe/segments/")
async def transcribe_segments(audio: UploadFile = File(...)):
    validate(audio)

    content = await audio.read()
    file_hash = hashlib.sha256(content).hexdigest()
    cached = db_get(file_hash)

    if cached and cached.get("text"):
        return {
            "file_hash": file_hash,
            "language": cached["language"],
            "segments": cached["segments"],
            "cached": True,
        }

    raw_path = UPLOAD_DIR / audio.filename

    with open(raw_path, "wb") as f:
        f.write(content)

    result, segments = await run_in_threadpool(process_pipeline, raw_path, file_hash)

    response = {
        "file_hash": file_hash,
        "language": result.get("language"),
        "text": result.get("text", "").strip(),
        "segments": segments,
    }

    result = await run_in_threadpool(process_pipeline, raw_path, file_hash)

    return response
