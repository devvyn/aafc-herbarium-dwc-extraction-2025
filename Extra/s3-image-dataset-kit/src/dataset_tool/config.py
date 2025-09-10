
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Settings:
    bucket: str = os.getenv("S3_BUCKET", "")
    region: str = os.getenv("AWS_REGION", "us-east-1")
    endpoint_url: str | None = os.getenv("S3_ENDPOINT_URL") or None
    cache_dir: str = os.getenv("CACHE_DIR", "/tmp/imgcache")
    manifest_key: str = os.getenv("MANIFEST_KEY", "manifests/inventory-v1.jsonl")
    logical_map_csv: str | None = os.getenv("DATASET_LOGICAL_MAP") or None

    def validate(self):
        if not self.bucket:
            raise ValueError("S3_BUCKET is required")
        return self

SETTINGS = Settings().validate()
