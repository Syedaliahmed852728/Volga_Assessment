from __future__ import annotations

from typing import Optional

from app.repositories.database import get_connection


class JobRepository:
    def create(self, job_id: str, file_hash: str) -> None:
        with get_connection() as conn:
            conn.execute(
                "INSERT INTO jobs (job_id, file_hash, status) VALUES (?, ?, ?)",
                (job_id, file_hash, "pending"),
            )

    def update_status(
        self,
        job_id: str,
        status: str,
        error: Optional[str] = None,
    ) -> None:
        with get_connection() as conn:
            conn.execute(
                "UPDATE jobs SET status = ?, error = ?, updated_at = CURRENT_TIMESTAMP"
                " WHERE job_id = ?",
                (status, error, job_id),
            )

    def get(self, job_id: str) -> Optional[dict]:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT job_id, file_hash, status, error, created_at, updated_at"
                " FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()

        if row is None:
            return None
        return dict(row)
