from __future__ import annotations

import json
from typing import Optional

from app.repositories.database import get_connection


class TranscriptionRepository:
    def get(self, file_hash: str) -> Optional[dict]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT file_hash, language, text, segments, duration"
                " FROM transcriptions WHERE file_hash = ?",
                (file_hash,),
            ).fetchone()

        if row is None:
            return None

        return {
            "file_hash": row["file_hash"],
            "language": row["language"],
            "text": row["text"],
            "segments": json.loads(row["segments"]) if row["segments"] else [],
            "duration": row["duration"],
        }

    def save(
        self,
        file_hash: str,
        language: Optional[str],
        text: str,
        segments: list[dict],
        duration: Optional[float] = None,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO transcriptions
                    (file_hash, language, text, segments, duration)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(file_hash) DO UPDATE SET
                    language = excluded.language,
                    text = excluded.text,
                    segments = excluded.segments,
                    duration = excluded.duration
                """,
                (file_hash, language, text, json.dumps(segments), duration),
            )
