
from __future__ import annotations
import argparse, json, sys
from jsonschema import validate, Draft202012Validator

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--schema", default="schema/inventory-v1.schema.json")
    args = ap.parse_args()

    schema = json.load(open(args.schema, "r", encoding="utf-8"))
    errors = []
    with open(args.manifest, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            v = Draft202012Validator(schema)
            for err in v.iter_errors(obj):
                errors.append(f"Line {i}: {err.message}")
    if errors:
        print("\n".join(errors), file=sys.stderr)
        raise SystemExit(1)
    print("Manifest valid.")

if __name__ == "__main__":
    main()
