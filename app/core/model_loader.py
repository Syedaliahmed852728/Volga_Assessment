from __future__ import annotations

from functools import lru_cache
from typing import Any

import whisper

from app.config import settings
from app.core.device import resolve_device


@lru_cache(maxsize=1)
def get_model() -> Any:
    device = resolve_device(settings.device)
    return whisper.load_model(settings.whisper_model, device=device)
