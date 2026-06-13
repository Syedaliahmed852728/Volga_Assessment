from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO

from app.config import settings


class FileStorage:
    chunk_size: int = 1024 * 1024

    def __init__(self) -> None:
        self.upload_dir = settings.upload_dir
        self.normalized_dir = settings.normalized_dir

    def save_upload(self, stream: BinaryIO, filename: str) -> tuple[Path, str]:
        digest = hashlib.sha256()
        suffix = Path(filename).suffix.lower()
        tmp_path = self.upload_dir / f"_incoming{suffix}"

        with open(tmp_path, "wb") as f:
            while True:
                chunk = stream.read(self.chunk_size)
                if not chunk:
                    break
                digest.update(chunk)
                f.write(chunk)

        file_hash = digest.hexdigest()
        final_path = self.upload_dir / f"{file_hash}{suffix}"
        tmp_path.replace(final_path)
        return final_path, file_hash

    def normalized_path(self, file_hash: str) -> Path:
        return self.normalized_dir / f"{file_hash}.wav"
