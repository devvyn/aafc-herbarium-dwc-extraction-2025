
from __future__ import annotations
import json
from dataclasses import dataclass, asdict
from typing import Optional, Iterable

@dataclass
class ManifestEntry:
    sha256: str
    path: str
    bytes: int
    content_type: str = "image/jpeg"
    width: Optional[int] = None
    height: Optional[int] = None
    logical_id: Optional[str] = None
    etag: Optional[str] = None

def write_jsonl(entries: Iterable[ManifestEntry], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps({k:v for k,v in asdict(e).items() if v is not None}) + "\n")

def read_jsonl(path: str) -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
