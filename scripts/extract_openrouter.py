#!/usr/bin/env python3
"""
OpenRouter API Integration for Multi-Model Herbarium Extraction

Supports vision models including:
- Qwen 2.5 VL 72B (FREE and paid tiers)
- Llama 3.2 Vision
- Claude 3.5 Sonnet
- Gemini models
- 400+ other models

Usage:
    python scripts/extract_openrouter.py \\
        --input /tmp/imgcache \\
        --output openrouter_results \\
        --model qwen/qwen-2.5-vl-72b-instruct:free \\
        --limit 100
"""

import argparse
import base64
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tqdm import tqdm


# OpenRouter model registry
OPENROUTER_MODELS = {
    # FREE Models (test first!)
    "qwen-vl-72b-free": {
        "id": "qwen/qwen-2.5-vl-72b-instruct:free",
        "name": "Qwen 2.5 VL 72B (FREE)",
        "cost": 0.0,
        "notes": "Top-rated OCR model, FREE tier"
    },
    "qwen-vl-32b-free": {
        "id": "qwen/qwen-2.5-vl-32b-instruct:free",
        "name": "Qwen 2.5 VL 32B (FREE)",
        "cost": 0.0,
        "notes": "Compact vision model, FREE"
    },
    "llama-vision-free": {
        "id": "meta-llama/llama-3.2-11b-vision-instruct:free",
        "name": "Llama 3.2 11B Vision (FREE)",
        "cost": 0.0,
        "notes": "Strong OCR, 128K context, FREE"
    },

    # Paid Models
    "qwen-vl-72b": {
        "id": "qwen/qwen-2.5-vl-72b-instruct",
        "name": "Qwen 2.5 VL 72B",
        "cost": 0.0036,  # Estimated per specimen
        "notes": "Top OCR performer, paid tier"
    },
    "claude-sonnet": {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "cost": 0.025,  # Estimated per specimen
        "notes": "Premium quality"
    },
    "gemini-flash": {
        "id": "google/gemini-2.0-flash-exp:free",
        "name": "Gemini 2.0 Flash (FREE)",
        "cost": 0.0,
        "notes": "Google vision model, FREE"
    }
}


def encode_image_base64(image_path: Path) -> str:
    """Encode image to base64 string for API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_vision_message(
    image_path: Path,
    system_prompt: str,
    user_prompt: str
) -> List[Dict]:
    """Create OpenRouter-compatible vision message."""
    # Encode image
    image_b64 = encode_image_base64(image_path)

    # OpenRouter vision format (OpenAI-compatible)
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_b64}"
                    }
                }
            ]
        }
    ]

    return messages


def call_openrouter(
    messages: List[Dict],
    model: str,
    api_key: str,
    max_retries: int = 3
) -> Dict:
    """Call OpenRouter API with retry logic."""
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025",
        "X-Title": "AAFC Herbarium Extraction",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"}
    }

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait = 2 ** attempt
                print(f"  Timeout, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    wait = 5 * (2 ** attempt)
                    print(f"  Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
            else:
                raise

    raise Exception("Max retries exceeded")


def extract_specimen(
    image_path: Path,
    model: str,
    api_key: str,
    system_prompt: str,
    user_prompt: str
) -> Dict:
    """Extract Darwin Core data from single specimen image."""
    try:
        # Create vision message
        messages = create_vision_message(image_path, system_prompt, user_prompt)

        # Call OpenRouter
        response = call_openrouter(messages, model, api_key)

        # Parse response
        content = response["choices"][0]["message"]["content"]
        dwc_data = json.loads(content)

        # Add metadata
        result = {
            "image": str(image_path.name),
            "model": model,
            "provider": "openrouter",
            "dwc": dwc_data,
            "timestamp": datetime.now().isoformat(),
            "usage": response.get("usage", {}),
        }

        return result

    except Exception as e:
        return {
            "image": str(image_path.name),
            "model": model,
            "provider": "openrouter",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def main():
    parser = argparse.ArgumentParser(
        description="Extract Darwin Core data using OpenRouter vision models"
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Input directory containing specimen images"
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Output directory for results"
    )
    parser.add_argument(
        "--model",
        type=str,
        default="qwen-vl-72b-free",
        choices=list(OPENROUTER_MODELS.keys()),
        help="Model to use (default: qwen-vl-72b-free)"
    )
    parser.add_argument(
        "--api-key",
        type=str,
        help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of images to process"
    )
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip first N images"
    )

    args = parser.parse_args()

    # Get API key
    import os
    api_key = args.api_key or os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OpenRouter API key required")
        print("Set OPENROUTER_API_KEY env var or use --api-key")
        sys.exit(1)

    # Get model config
    model_config = OPENROUTER_MODELS[args.model]
    model_id = model_config["id"]

    print("=" * 70)
    print("OPENROUTER HERBARIUM EXTRACTION")
    print("=" * 70)
    print(f"Model: {model_config['name']}")
    print(f"Model ID: {model_id}")
    print(f"Cost: ${model_config['cost']}/specimen ({model_config['notes']})")
    print()

    # Load prompts
    prompt_dir = Path("config/prompts")
    system_prompt = (prompt_dir / "image_to_dwc_few_shot.system.prompt").read_text()
    user_prompt = (prompt_dir / "image_to_dwc_few_shot.user.prompt").read_text()

    # Get images (handle both .jpg and .JPG)
    all_images = sorted(list(args.input.glob("*.jpg")) + list(args.input.glob("*.JPG")))
    images = all_images[args.offset:]
    if args.limit:
        images = images[:args.limit]

    print(f"Found {len(images)} images to process")
    if args.offset > 0 or args.limit:
        print(f"Processing specimens {args.offset + 1} to {args.offset + len(images)}")
    print()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Process images
    results = []

    for image_path in tqdm(images, desc="Extracting"):
        result = extract_specimen(
            image_path,
            model_id,
            api_key,
            system_prompt,
            user_prompt
        )
        results.append(result)

        # Small delay to avoid rate limits
        time.sleep(0.5)

    # Save results
    output_file = args.output / "raw.jsonl"
    with open(output_file, "w") as f:
        for result in results:
            f.write(json.dumps(result) + "\n")

    # Generate statistics
    successful = [r for r in results if "dwc" in r]
    failed = [r for r in results if "error" in r]

    print()
    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Total processed: {len(results)}")
    print(f"Successful: {len(successful)} ({len(successful)/len(results)*100:.1f}%)")
    print(f"Failed: {len(failed)}")
    print()
    print(f"Results saved: {output_file}")

    # Calculate field coverage
    if successful:
        all_fields = set()
        for r in successful:
            all_fields.update(r["dwc"].keys())

        print()
        print("Field coverage:")
        for field in sorted(all_fields):
            count = sum(1 for r in successful if field in r["dwc"] and r["dwc"][field])
            pct = count / len(successful) * 100
            print(f"  {field:30s} {pct:5.1f}% ({count}/{len(successful)})")


if __name__ == "__main__":
    main()
