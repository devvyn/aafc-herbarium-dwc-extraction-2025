
from __future__ import annotations
import argparse, json, os
from tqdm import tqdm
from dataset_tool.manifest import read_jsonl
from dataset_tool.config import SETTINGS
from dataset_tool.uploader import upload_file, upload_manifest

def build_sha_to_local_map(src_dir: str):
    # map sha256 -> local path by recomputing sha; for 3k files it's fine.
    from dataset_tool.hashutil import sha256_file
    m = {}
    for root, _, files in os.walk(src_dir):
        for name in files:
            p = os.path.join(root, name)
            sha = sha256_file(p)
            m[sha] = p
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Local source directory of images")
    ap.add_argument("--manifest", required=True, help="Local manifest to upload")
    args = ap.parse_args()

    entries = read_jsonl(args.manifest)
    sha_to_path = build_sha_to_local_map(args.src)

    missing = [e for e in entries if e["sha256"] not in sha_to_path]
    if missing:
        raise SystemExit(f"{len(missing)} entries missing locally; ensure --src matches manifest")

    for e in tqdm(entries, desc="Uploading files"):
        upload_file(sha_to_path[e["sha256"]], e)

    upload_manifest(args.manifest)
    print(f"Uploaded manifest to s3://{SETTINGS.bucket}/{SETTINGS.manifest_key}")

if __name__ == "__main__":
    main()
