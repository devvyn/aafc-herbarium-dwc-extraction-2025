#!/usr/bin/env python
"""
Create OpenAI Batch API Request File

Generates a JSONL file with batch requests for herbarium specimen extraction.
Each request includes a base64-encoded image and extraction prompts.

Usage:
    python scripts/create_batch_request.py --input /tmp/imgcache --output full_dataset_processing/gpt4omini_batch

    # Test with subset:
    python scripts/create_batch_request.py --input /tmp/imgcache --output test_batch --limit 5

Output:
    - batch_input.jsonl (OpenAI Batch API format)
    - image_manifest.json (metadata for result processing)
"""

import argparse
import base64
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA256 hash of image file."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def load_prompt_messages(prompt_dir: Path, task: str) -> List[Dict[str, str]]:
    """Load prompt messages from system and user prompt files.

    Args:
        prompt_dir: Directory containing prompt files
        task: Task name (e.g., "image_to_dwc_v2")

    Returns:
        List of message dicts with role and content
    """
    messages = []

    # Load system prompt
    system_file = prompt_dir / f"{task}.system.prompt"
    if system_file.exists():
        messages.append({"role": "system", "content": system_file.read_text(encoding="utf-8")})

    # Load user prompt (will be converted to vision format)
    user_file = prompt_dir / f"{task}.user.prompt"
    if user_file.exists():
        messages.append({"role": "user", "content": user_file.read_text(encoding="utf-8")})
    else:
        # Fallback to legacy format
        legacy_file = prompt_dir / f"{task}.prompt"
        if legacy_file.exists():
            messages.append({"role": "user", "content": legacy_file.read_text(encoding="utf-8")})

    if not messages or messages[-1]["role"] != "user":
        raise ValueError(f"No user prompt found for task: {task}")

    return messages


def create_batch_request(
    image_path: Path,
    sha256: str,
    messages: List[Dict[str, str]],
    model: str = "gpt-4o-mini",
    use_structured_output: bool = False,
    schema_path: Path = None,
    temperature: float = None,
) -> Dict:
    """Create a single batch request for an image.

    Args:
        image_path: Path to image file
        sha256: SHA256 hash of image (used as custom_id)
        messages: Prompt messages (system + user)
        model: OpenAI model name
        use_structured_output: Use JSON Schema structured outputs
        schema_path: Path to JSON schema file

    Returns:
        Batch request dict in OpenAI format
    """
    # Base64 encode image
    with open(image_path, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("ascii")

    # Convert user message to vision format
    vision_messages = messages[:-1].copy()  # All except last message
    vision_messages.append(
        {
            "role": "user",
            "content": [
                {"type": "text", "text": messages[-1]["content"]},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}},
            ],
        }
    )

    # Build request body
    body = {"model": model, "messages": vision_messages}

    # Only set temperature if explicitly provided
    if temperature is not None:
        body["temperature"] = temperature

    # Add response format
    if use_structured_output and schema_path:
        # Load JSON schema
        with open(schema_path, "r") as f:
            schema = json.load(f)
        body["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "darwin_core_extraction", "schema": schema, "strict": True},
        }
    else:
        # Fallback to basic JSON mode
        body["response_format"] = {"type": "json_object"}

    # Create batch request
    return {
        "custom_id": f"specimen-{sha256}",
        "method": "POST",
        "url": "/v1/chat/completions",
        "body": body,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Create OpenAI Batch API request file for herbarium extraction"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input directory containing specimen images"
    )
    parser.add_argument(
        "--output", type=Path, required=True, help="Output directory for batch files"
    )
    parser.add_argument(
        "--prompt-dir",
        type=Path,
        default=Path("config/prompts"),
        help="Directory containing prompt files",
    )
    parser.add_argument("--task", type=str, default="image_to_dwc_v2", help="Prompt task name")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI model name")
    parser.add_argument("--limit", type=int, help="Limit number of images to process (for testing)")
    parser.add_argument(
        "--offset", type=int, default=0, help="Skip first N images (for batch splitting)"
    )
    parser.add_argument(
        "--structured-output",
        action="store_true",
        help="Use JSON Schema structured outputs (enforces field names)",
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=Path("config/schemas/darwin_core_extraction.json"),
        help="Path to JSON schema file",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="Temperature setting (0-2). If not set, uses OpenAI default (1.0)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.input.exists():
        print(f"Error: Input directory not found: {args.input}")
        sys.exit(1)

    if not args.prompt_dir.exists():
        print(f"Error: Prompt directory not found: {args.prompt_dir}")
        sys.exit(1)

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Load prompt messages
    print(f"Loading prompt messages from: {args.prompt_dir}")
    try:
        messages = load_prompt_messages(args.prompt_dir, args.task)
        print(
            f"✅ Loaded {len(messages)} prompt messages ({', '.join(m['role'] for m in messages)})"
        )
    except Exception as e:
        print(f"Error loading prompts: {e}")
        sys.exit(1)

    # Find all image files
    all_image_files = sorted(args.input.glob("*.jpg"))
    total_available = len(all_image_files)

    # Apply offset and limit for batch splitting
    image_files = all_image_files[args.offset :]
    if args.limit:
        image_files = image_files[: args.limit]

    if args.offset > 0 or args.limit:
        print(f"\n⚠️  Batch slice: offset={args.offset}, limit={args.limit}")
        print(
            f"   Processing specimens {args.offset + 1} to {args.offset + len(image_files)} of {total_available}"
        )

    print(f"\nFound {len(image_files)} images to process")

    # Display configuration
    print("\n📋 Configuration:")
    print(f"   Model: {args.model}")
    if args.temperature is not None:
        print(f"   Temperature: {args.temperature}")
    else:
        print("   Temperature: default (1.0)")
    if args.structured_output:
        print("   Response Format: JSON Schema (strict=True)")
        print(f"   Schema: {args.schema}")
    else:
        print("   Response Format: JSON Object (basic mode)")

    # Create batch requests
    batch_input_path = args.output / "batch_input.jsonl"
    manifest_path = args.output / "image_manifest.json"

    manifest = {}
    processed = 0

    print("\nCreating batch requests...")
    print(f"Output: {batch_input_path}")

    with open(batch_input_path, "w", encoding="utf-8") as f:
        for i, image_path in enumerate(image_files, 1):
            try:
                # Calculate SHA256
                sha256 = calculate_sha256(image_path)

                # Create batch request
                request = create_batch_request(
                    image_path,
                    sha256,
                    messages,
                    args.model,
                    args.structured_output,
                    args.schema if args.structured_output else None,
                    args.temperature,
                )

                # Write JSONL line
                f.write(json.dumps(request) + "\n")

                # Update manifest
                manifest[sha256] = {
                    "filename": image_path.name,
                    "custom_id": f"specimen-{sha256}",
                    "path": str(image_path),
                }

                processed += 1

                # Progress indicator
                if i % 100 == 0:
                    print(f"  Processed {i}/{len(image_files)} images...")

            except Exception as e:
                print(f"  ⚠️  Error processing {image_path.name}: {e}")
                continue

    # Save manifest
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    print("\n✅ Batch request file created:")
    print(f"   - {batch_input_path}")
    print(f"   - {processed:,} requests")
    print(f"   - {batch_input_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("\n✅ Manifest created:")
    print(f"   - {manifest_path}")
    print(f"   - {len(manifest):,} images mapped")

    print("\n📤 Next step:")
    print(f"   python scripts/submit_batch.py --input {batch_input_path}")


if __name__ == "__main__":
    main()
