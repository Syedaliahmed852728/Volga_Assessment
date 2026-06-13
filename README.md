# Audio Transcription Pipeline

A small, production-shaped service that turns audio files into text using **OpenAI Whisper**, served over **FastAPI**, organised in a strict **3-tier architecture** (API → Services → Repositories). Auto-detects GPU; falls back to CPU.

## Features

- Upload **any common audio format** (MP3, WAV, M4A, FLAC, OGG, MP4, WebM, AAC) — normalized via `ffmpeg`.
- Returns plain text **or** segment-level timestamps.
- **Async job mode** for long files: `POST /transcribe/async` → `GET /jobs/{id}`.
- **Content-addressed caching**: re-uploading the same file is instant.
- **GPU autoselect** — uses CUDA if available, otherwise CPU. No code changes needed.
- Configurable via environment variables (`APP_WHISPER_MODEL`, `APP_DEVICE`, ...).

## Architecture (3-tier)

```
app/
├── api/            # Presentation layer  (FastAPI routes, schemas, DI)
├── services/       # Business layer       (audio normalize, transcribe, jobs)
├── repositories/   # Data layer           (SQLite, file storage)
└── core/           # Cross-cutting        (device detect, model loader, errors)
```

## Requirements

- Python 3.10 – 3.12
- [`uv`](https://docs.astral.sh/uv/) (replaces pip)
- `ffmpeg` on PATH (used for format conversion)

```bash
# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# install ffmpeg
sudo apt-get install -y ffmpeg          # Debian/Ubuntu
brew install ffmpeg                     # macOS
```

## Quick start

```bash
git clone <this-repo>
cd <this-repo>

uv sync                                 # creates .venv and installs deps
uv run serve                            # boots FastAPI on :8000
```

Open Swagger UI at **http://localhost:8000/docs**.

## Usage

```bash
# Plain text
curl -F "audio=@sample.mp3" http://localhost:8000/transcribe

# With segment timestamps
curl -F "audio=@sample.mp3" http://localhost:8000/transcribe/segments

# Async (long files)
curl -F "audio=@long_lecture.mp3" http://localhost:8000/transcribe/async
# → { "job_id": "abc...", "status": "pending" }

curl http://localhost:8000/jobs/abc...
```

## Configuration

All settings overrideable via env vars (prefix `APP_`):

| Variable                 | Default   | Notes                                    |
|--------------------------|-----------|------------------------------------------|
| `APP_WHISPER_MODEL`      | `base`    | `tiny` / `base` / `small` / `medium` / `large-v3` |
| `APP_DEVICE`             | `auto`    | `auto` / `cuda` / `cpu`                  |
| `APP_FP16`               | `true`    | Half precision (GPU only)                |
| `APP_MAX_UPLOAD_MB`      | `500`     | Reject larger uploads                    |
| `APP_DATABASE_PATH`      | `data/transcriptions.db` |                           |

Example: `APP_WHISPER_MODEL=small APP_DEVICE=cuda uv run serve`

## GPU vs CPU

The service calls `torch.cuda.is_available()` at startup; same code runs on either. To force CPU: `APP_DEVICE=cpu`. To force GPU (and fail fast if missing): `APP_DEVICE=cuda`.

## Endpoints

| Method | Path                     | Purpose                              |
|--------|--------------------------|--------------------------------------|
| GET    | `/health`                | Liveness + active model & device     |
| POST   | `/transcribe`            | Full text                            |
| POST   | `/transcribe/segments`   | Text + per-segment timestamps        |
| POST   | `/transcribe/async`      | Enqueue background job → `job_id`    |
| GET    | `/jobs/{job_id}`         | Poll job status + result             |
