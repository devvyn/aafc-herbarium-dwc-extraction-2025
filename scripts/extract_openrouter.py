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
import logging
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import requests
from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils.environment import save_environment_snapshot  # noqa: E402

# Load approved API keys
sys.path.insert(0, str(Path.home() / "Secrets" / "approved-for-agents"))
try:
    from load_keys import load_api_keys

    load_api_keys()  # Load OPENROUTER_API_KEY into os.environ
except ImportError:
    pass  # Fallback to manual key or env var


# OpenRouter model registry
OPENROUTER_MODELS = {
    # FREE Models (test first!)
    "qwen-vl-72b-free": {
        "id": "qwen/qwen-2.5-vl-72b-instruct:free",
        "name": "Qwen 2.5 VL 72B (FREE)",
        "cost": 0.0,
        "notes": "Top-rated OCR model, FREE tier",
    },
    "qwen-vl-32b-free": {
        "id": "qwen/qwen-2.5-vl-32b-instruct:free",
        "name": "Qwen 2.5 VL 32B (FREE)",
        "cost": 0.0,
        "notes": "Compact vision model, FREE",
    },
    "llama-vision-free": {
        "id": "meta-llama/llama-3.2-11b-vision-instruct:free",
        "name": "Llama 3.2 11B Vision (FREE)",
        "cost": 0.0,
        "notes": "Strong OCR, 128K context, FREE",
    },
    # Paid Models
    "qwen-vl-72b": {
        "id": "qwen/qwen-2.5-vl-72b-instruct",
        "name": "Qwen 2.5 VL 72B",
        "cost": 0.0036,  # Estimated per specimen
        "notes": "Top OCR performer, paid tier",
    },
    "claude-sonnet": {
        "id": "anthropic/claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "cost": 0.025,  # Estimated per specimen
        "notes": "Premium quality",
    },
    "gemini-flash": {
        "id": "google/gemini-2.0-flash-exp:free",
        "name": "Gemini 2.0 Flash (FREE)",
        "cost": 0.0,
        "notes": "Google vision model, FREE",
    },
}


def encode_image_base64(image_path: Path) -> str:
    """Encode image to base64 string for API."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def create_vision_message(image_path: Path, system_prompt: str, user_prompt: str) -> List[Dict]:
    """Create OpenRouter-compatible vision message."""
    # Encode image
    image_b64 = encode_image_base64(image_path)

    # OpenRouter vision format (OpenAI-compatible)
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_prompt},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}},
            ],
        },
    ]

    return messages


def provision_fresh_api_key() -> Optional[str]:
    """
    Automatically provision fresh OpenRouter API key.

    Uses provisioning script to create new key with $15 limit.
    Reloads keys into environment.

    Returns:
        New API key if successful, None otherwise
    """
    try:
        logger.warning("🔑 API key expired/invalid - attempting auto-rotation...")

        # Call provisioning script
        provision_script = Path.home() / "devvyn-meta-project/scripts/provision-openrouter-key.sh"

        if not provision_script.exists():
            logger.error(f"❌ Provisioning script not found: {provision_script}")
            return None

        result = subprocess.run(
            ["bash", str(provision_script), "--name", "auto-rotation", "--limit", "15.00"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.error(f"❌ Provisioning failed: {result.stderr}")
            return None

        logger.info("✅ New key provisioned successfully")

        # Reload keys into environment
        try:
            sys.path.insert(0, str(Path.home() / "Secrets" / "approved-for-agents"))
            from load_keys import load_api_keys

            load_api_keys()

            new_key = os.environ.get("OPENROUTER_API_KEY")
            if new_key:
                logger.info(f"✅ Fresh key loaded: {new_key[:20]}...")
                return new_key
            else:
                logger.error("❌ Key provisioned but not loaded into environment")
                return None

        except ImportError as e:
            logger.error(f"❌ Failed to reload keys: {e}")
            return None

    except subprocess.TimeoutExpired:
        logger.error("❌ Provisioning script timed out")
        return None
    except Exception as e:
        logger.error(f"❌ Auto-provisioning error: {e}")
        return None


def call_openrouter(
    messages: List[Dict], model: str, api_key: str, max_retries: int = 3, _key_rotated: bool = False
) -> Dict:
    """
    Call OpenRouter API with retry logic and automatic key rotation.

    Args:
        messages: API messages
        model: Model ID
        api_key: Current API key
        max_retries: Maximum retry attempts
        _key_rotated: Internal flag to prevent infinite rotation loops

    Returns:
        API response as dictionary
    """
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/devvyn/aafc-herbarium-dwc-extraction-2025",
        "X-Title": "AAFC Herbarium Extraction",
        "Content-Type": "application/json",
    }

    payload = {"model": model, "messages": messages, "response_format": {"type": "json_object"}}

    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                logger.warning(f"Timeout, retrying in {2**attempt}s...")
                time.sleep(2**attempt)
            else:
                raise

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:  # Unauthorized - API key expired/invalid
                if not _key_rotated:
                    # Attempt automatic key rotation (once only)
                    fresh_key = provision_fresh_api_key()
                    if fresh_key:
                        logger.info("🔄 Retrying with fresh API key...")
                        # Retry with fresh key (mark as rotated to prevent loops)
                        return call_openrouter(
                            messages, model, fresh_key, max_retries, _key_rotated=True
                        )
                    else:
                        logger.error("❌ Auto-rotation failed. Manual intervention required.")
                        logger.error(
                            "   Run: bash ~/devvyn-meta-project/scripts/provision-openrouter-key.sh"
                        )
                        raise
                else:
                    # Already tried rotation, don't loop
                    logger.error("❌ Fresh key also failed. Check OpenRouter service status.")
                    raise

            elif e.response.status_code == 429:  # Rate limit
                if attempt < max_retries - 1:
                    wait = 5 * (2**attempt)
                    logger.warning(f"Rate limited, waiting {wait}s...")
                    time.sleep(wait)
                else:
                    raise
            else:
                raise

    raise Exception("Max retries exceeded")


def extract_specimen(
    image_path: Path, model: str, api_key: str, system_prompt: str, user_prompt: str
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
            "timestamp": datetime.now().isoformat(),
        }


def main():
    parser = argparse.ArgumentParser(
        description="Extract Darwin Core data using OpenRouter vision models"
    )
    parser.add_argument(
        "--input", type=Path, required=True, help="Input directory containing specimen images"
    )
    parser.add_argument("--output", type=Path, required=True, help="Output directory for results")
    parser.add_argument(
        "--model",
        type=str,
        default="qwen-vl-72b-free",
        choices=list(OPENROUTER_MODELS.keys()),
        help="Model to use (default: qwen-vl-72b-free)",
    )
    parser.add_argument(
        "--api-key", type=str, help="OpenRouter API key (or set OPENROUTER_API_KEY env var)"
    )
    parser.add_argument("--limit", type=int, help="Limit number of images to process")
    parser.add_argument("--offset", type=int, default=0, help="Skip first N images")

    args = parser.parse_args()

    # Get API key

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

    # Load prompts (use AAFC-specific prompts)
    prompt_dir = Path("config/prompts")
    system_prompt = (prompt_dir / "image_to_dwc_v2_aafc.system.prompt").read_text()
    user_prompt = (prompt_dir / "image_to_dwc_v2_aafc.user.prompt").read_text()

    # Get images recursively (handle both .jpg and .JPG, including nested directories)
    all_images = sorted(list(args.input.glob("**/*.jpg")) + list(args.input.glob("**/*.JPG")))
    images = all_images[args.offset :]
    if args.limit:
        images = images[: args.limit]

    print(f"Found {len(images)} images to process")
    if args.offset > 0 or args.limit:
        print(f"Processing specimens {args.offset + 1} to {args.offset + len(images)}")
    print()

    # Create output directory
    args.output.mkdir(parents=True, exist_ok=True)

    # Capture environment snapshot for reproducibility
    run_id = args.output.name
    command = " ".join(sys.argv)
    env_snapshot_path = save_environment_snapshot(args.output, run_id=run_id, command=command)
    print(f"Environment snapshot: {env_snapshot_path}")
    print()

    # Process images with streaming + early validation
    output_file = args.output / "raw.jsonl"

    successful = 0
    failed = 0

    with open(output_file, "w") as f:
        for i, image_path in enumerate(tqdm(images, desc="Extracting")):
            result = extract_specimen(image_path, model_id, api_key, system_prompt, user_prompt)

            # Stream result immediately
            f.write(json.dumps(result) + "\n")
            f.flush()  # Force write to disk

            # Track success/failure
            if "dwc" in result and result["dwc"]:
                successful += 1
            else:
                failed += 1

            # EARLY VALIDATION: Check after first 5 specimens
            if i == 4:  # Zero-indexed, so 5th specimen
                success_rate = successful / 5
                if success_rate < 0.5:
                    print(
                        f"\n❌ EARLY FAILURE DETECTED: {successful}/5 successful ({success_rate:.0%})"
                    )
                    print("First 5 specimens show <50% success rate.")
                    print(
                        "Check prompts, API key, or configuration before processing all 2,885 specimens!"
                    )
                    sys.exit(1)
                else:
                    print(
                        f"\n✅ Early validation passed: {successful}/5 successful ({success_rate:.0%})"
                    )

            # Progress check every 50 specimens
            if i > 0 and (i + 1) % 50 == 0:
                current_rate = successful / (i + 1)
                print(f"\nProgress: {i+1}/{len(images)} - {current_rate:.1%} success rate")
                if current_rate < 0.7:
                    print(f"⚠️  WARNING: Success rate dropped to {current_rate:.1%}")

            # Small delay to avoid rate limits
            time.sleep(0.5)

    # Generate statistics from file
    results = []
    with open(output_file) as rf:
        for line in rf:
            results.append(json.loads(line))

    successful_results = [r for r in results if "dwc" in r and r["dwc"]]
    failed_results = [r for r in results if "error" in r or not r.get("dwc")]

    print()
    print("=" * 70)
    print("EXTRACTION COMPLETE")
    print("=" * 70)
    print(f"Total processed: {len(results)}")
    print(
        f"Successful: {len(successful_results)} ({len(successful_results)/len(results)*100:.1f}%)"
    )
    print(f"Failed: {len(failed_results)}")
    print()
    print(f"Results saved: {output_file}")

    # Calculate field coverage
    if successful_results:
        all_fields = set()
        for r in successful_results:
            all_fields.update(r["dwc"].keys())

        print()
        print("Field coverage:")
        for field in sorted(all_fields):
            count = sum(1 for r in successful_results if field in r["dwc"] and r["dwc"][field])
            pct = count / len(successful_results) * 100
            print(f"  {field:30s} {pct:5.1f}% ({count}/{len(successful_results)})")


if __name__ == "__main__":
    main()
