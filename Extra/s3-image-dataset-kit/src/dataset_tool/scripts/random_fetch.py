
from __future__ import annotations
import argparse, random, sys
from dataset_tool.manifest import read_jsonl
from dataset_tool.client import fetch_entry

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="./manifests/inventory-v1.jsonl")
    ap.add_argument("--n", type=int, default=5)
    args = ap.parse_args()

    records = read_jsonl(args.manifest)
    if not records:
        print("Manifest is empty. Did you build it?", file=sys.stderr)
        raise SystemExit(1)

    for rec in random.sample(records, min(args.n, len(records))):
        p = fetch_entry(rec)
        print(p)

if __name__ == "__main__":
    main()
