
from __future__ import annotations
import os
import mimetypes
from pathlib import Path
from typing import Iterable, Optional
from tqdm import tqdm

try:
    from PIL import Image  # optional
except Exception:
    Image = None  # width/height omitted if Pillow missing

from .hashutil import sha256_file
from .manifest import ManifestEntry, write_jsonl
from .s3_client import s3_client
from .config import SETTINGS

def iter_images(src_dir: str) -> Iterable[str]:
    exts = {'.jpg','.jpeg','.png','.tif','.tiff'}
    for root, _, files in os.walk(src_dir):
        for name in files:
            if os.path.splitext(name)[1].lower() in exts:
                yield os.path.join(root, name)

def _object_key_from_sha(sha: str, ext: str) -> str:
    return f"images/{sha[:2]}/{sha[2:4]}/{sha}{ext}"

def _content_type(path: str) -> str:
    t, _ = mimetypes.guess_type(path)
    return t or "application/octet-stream"

def _maybe_dims(path: str) -> tuple[Optional[int], Optional[int]]:
    if Image is None:
        return None, None
    try:
        with Image.open(path) as img:
            w, h = img.size
            return int(w), int(h)
    except Exception:
        return None, None

def build_manifest(src_dir: str, logical_map: dict[str, str] | None = None):
    entries: list[ManifestEntry] = []
    for path in tqdm(list(iter_images(src_dir)), desc="Hashing"):
        sha = sha256_file(path)
        ext = os.path.splitext(path)[1].lower()
        if ext == ".jpeg":
            ext = ".jpg"
        key = _object_key_from_sha(sha, ext)
        size = os.path.getsize(path)
        ctype = _content_type(path)
        w, h = _maybe_dims(path)
        logical_id = None
        if logical_map:
            fname = os.path.basename(path)
            logical_id = logical_map.get(fname) or logical_map.get(path)
        entries.append(ManifestEntry(
            sha256=sha, path=key, bytes=size, content_type=ctype,
            width=w, height=h, logical_id=logical_id
        ))
    return entries

def upload_entries(entries: list[ManifestEntry]):
    s3 = s3_client()
    for e in tqdm(entries, desc="Uploading"):
        extra = {
            "ContentType": e.content_type,
            "CacheControl": "public, max-age=31536000, immutable"
        }
        # Only upload if absent (idempotent by hash)
        try:
            s3.head_object(Bucket=SETTINGS.bucket, Key=e.path)
            continue
        except Exception:
            pass
        # Upload from local file derived from sha (not stored here; caller supplies)
        # We need a mapping sha -> local path; simplest approach is to re-derive it during upload.
        # For this toolkit, we assume the uploader runs right after build_manifest so we can locate files by sha.
        raise RuntimeError("upload_entries requires upload_dataset script which maps sha->source path.")

def upload_file(local_path: str, entry: ManifestEntry):
    s3 = s3_client()
    with open(local_path, "rb") as f:
        s3.put_object(
            Bucket=SETTINGS.bucket,
            Key=entry.path,
            Body=f,
            ContentType=entry.content_type,
            CacheControl="public, max-age=31536000, immutable"
        )

def write_manifest(entries: list[ManifestEntry], out_path: str):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    write_jsonl(entries, out_path)

def upload_manifest(local_manifest_path: str):
    s3 = s3_client()
    with open(local_manifest_path, "rb") as f:
        s3.put_object(
            Bucket=SETTINGS.bucket,
            Key=SETTINGS.manifest_key,
            Body=f,
            ContentType="application/json",
            CacheControl="no-cache"
        )
