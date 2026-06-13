from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from app.config import settings
from app.core.exceptions import UnsupportedFormatError


class AudioService:
    def __init__(self) -> None:
        if shutil.which("ffmpeg") is None:
            raise RuntimeError("ffmpeg is required but was not found on PATH")
        self._ffprobe = shutil.which("ffprobe")

    def validate_extension(self, filename: str) -> None:
        suffix = Path(filename).suffix.lower()
        if not suffix:
            raise UnsupportedFormatError("File has no extension")
        if suffix not in settings.allowed_extensions:
            raise UnsupportedFormatError(f"Unsupported extension: {suffix}")

    def normalize(self, src: Path, dst: Path) -> Path:
        if dst.exists():
            return dst
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            subprocess.run(
                [
                    "ffmpeg",
                    "-y",
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-i",
                    str(src),
                    "-vn",
                    "-ac",
                    str(settings.target_channels),
                    "-ar",
                    str(settings.target_sample_rate),
                    "-c:a",
                    "pcm_s16le",
                    str(dst),
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode(errors="ignore") if e.stderr else "ffmpeg failed"
            raise UnsupportedFormatError(err.strip().splitlines()[-1] if err else "ffmpeg failed") from e
        return dst

    def probe_duration(self, path: Path) -> float | None:
        if self._ffprobe is None:
            return None
        try:
            result = subprocess.run(
                [
                    self._ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "json",
                    str(path),
                ],
                capture_output=True,
                check=True,
            )
            data = json.loads(result.stdout.decode() or "{}")
            return float(data.get("format", {}).get("duration") or 0.0) or None
        except (subprocess.CalledProcessError, ValueError, json.JSONDecodeError):
            return None
