from __future__ import annotations

import math
from pathlib import Path
from typing import Iterable, List

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".gif", ".tiff", ".tif"}


def list_image_files(source_dir: str) -> List[Path]:
    root = Path(source_dir)
    files = [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS]
    files.sort()
    return files


def chunked(items: Iterable[Path], size: int) -> Iterable[List[Path]]:
    batch: List[Path] = []
    for item in items:
        batch.append(item)
        if len(batch) == size:
            yield batch
            batch = []
    if batch:
        yield batch


def format_seconds(total_seconds: float) -> str:
    if total_seconds <= 0 or math.isinf(total_seconds) or math.isnan(total_seconds):
        return "--:--"
    total = int(total_seconds)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

