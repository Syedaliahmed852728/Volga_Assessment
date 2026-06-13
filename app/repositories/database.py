from __future__ import annotations

import sqlite3
import threading
from contextlib import contextmanager
from typing import Iterator

from app.config import settings

_LOCK = threading.Lock()


def init_database() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS transcriptions (
                file_hash TEXT PRIMARY KEY,
                language TEXT,
                text TEXT NOT NULL,
                segments TEXT NOT NULL,
                duration REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                file_hash TEXT,
                status TEXT NOT NULL,
                error TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    with _LOCK:
        conn = sqlite3.connect(settings.database_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()
