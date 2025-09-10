
from __future__ import annotations
import os
from pathlib import Path
from typing import Iterable, Dict
from .s3_client import s3_client
from .config import SETTINGS

def _cache_path(sha: str, ext: str = ".jpg") -> Path:
    p = Path(SETTINGS.cache_dir) / sha[:2] / sha[2:4] / f"{sha}{ext}"
    p.parent.mkdir(parents=True, exist_ok=True)
    return p

def fetch_entry(entry: Dict) -> Path:
    sha = entry["sha256"]
    key = entry["path"]
    ext = os.path.splitext(key)[1].lower() or ".jpg"
    dst = _cache_path(sha, ext)
    if dst.exists():
        return dst
    s3 = s3_client()
    s3.download_file(SETTINGS.bucket, key, str(dst))
    return dst
