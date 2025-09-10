
from __future__ import annotations
import argparse, csv, os, sys
from dataset_tool.uploader import build_manifest, write_manifest
from dataset_tool.config import SETTINGS

def load_logical_map(maybe_csv: str | None):
    if not maybe_csv or not os.path.exists(maybe_csv):
        return {}
    m = {}
    with open(maybe_csv, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            # expects headers: filename,logical_id
            m[row['filename']] = row['logical_id']
    return m

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True, help="Source directory of images")
    ap.add_argument("--out", required=True, help="Output manifest path")
    ap.add_argument("--logical-map", default=SETTINGS.logical_map_csv, help="CSV mapping filename->logical_id")
    args = ap.parse_args()

    logical_map = load_logical_map(args.logical_map)
    entries = build_manifest(args.src, logical_map=logical_map)
    write_manifest(entries, args.out)
    print(f"Wrote manifest to {args.out}")

if __name__ == "__main__":
    main()
