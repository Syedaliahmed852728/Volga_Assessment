from __future__ import annotations

import torch


def resolve_device(preference: str = "auto") -> str:
    pref = preference.lower()
    if pref == "cpu":
        return "cpu"
    if pref == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA requested but no GPU is available")
        return "cuda"
    return "cuda" if torch.cuda.is_available() else "cpu"


def supports_fp16(device: str) -> bool:
    return device == "cuda"
