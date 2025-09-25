#!/usr/bin/env python3
"""Comprehensive Vision API comparison for herbarium specimen OCR.

Tests all major vision APIs including Claude 3.5 Sonnet, GPT-4 Vision,
Google Vision, Apple Vision, and optimized Tesseract to determine the
best OCR engine for herbarium digitization.
"""

import argparse
import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pytesseract
from PIL import Image

# Try importing API clients
try:
    import anthropic
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False

try:
    import openai
    GPT4V_AVAILABLE = True
except ImportError:
    GPT4V_AVAILABLE = False

try:
    from google.cloud import vision
    GOOGLE_VISION_AVAILABLE = True
except ImportError:
    GOOGLE_VISION_AVAILABLE = False


class ComprehensiveVisionTester:
    """Test multiple vision APIs for herbarium OCR accuracy."""

    def __init__(self):
        self.engines = {
            'tesseract_raw': True,
            'tesseract_optimized': True,
            'apple_vision': self._check_apple_vision(),
            'claude_vision': CLAUDE_AVAILABLE and bool(os.getenv('ANTHROPIC_API_KEY')),
            'gpt4_vision': GPT4V_AVAILABLE and bool(os.getenv('OPENAI_API_KEY')),
            'google_vision': GOOGLE_VISION_AVAILABLE and bool(os.getenv('GOOGLE_APPLICATION_CREDENTIALS')),
        }

        # Initialize API clients
        if self.engines['claude_vision']:
            self.claude_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

        if self.engines['gpt4_vision']:
            self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        if self.engines['google_vision']:
            self.google_client = vision.ImageAnnotatorClient()

    def _check_apple_vision(self) -> bool:
        """Check if Apple Vision Swift package is available."""
        pkg_dir = Path(__file__).resolve().parent.parent / "engines" / "vision_swift"
        return pkg_dir.exists()

    def _encode_image_base64(self, image_path: Path) -> str:
        """Encode image to base64 for API calls."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')

    def _preprocess_for_tesseract(self, image_path: Path) -> np.ndarray:
        """Apply best preprocessing for Tesseract (from previous testing)."""
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Could not load image: {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)

        # Denoise
        denoised = cv2.fastNlMeansDenoising(enhanced, None, 10, 7, 21)

        # Unsharp mask for sharpening
        gaussian = cv2.GaussianBlur(denoised, (0, 0), 1.0)
        sharpened = cv2.addWeighted(denoised, 1.5, gaussian, -0.5, 0)

        # Adaptive threshold
        adaptive = cv2.adaptiveThreshold(
            sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )

        return adaptive

    def test_tesseract_raw(self, image_path: Path) -> Dict:
        """Test basic Tesseract OCR."""
        start_time = time.time()
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image)

            return {
                'engine': 'tesseract_raw',
                'text': text.strip(),
                'processing_time': time.time() - start_time,
                'text_length': len(text.strip()),
                'cost_per_1000': 0
            }
        except Exception as e:
            return {'error': str(e), 'engine': 'tesseract_raw'}

    def test_tesseract_optimized(self, image_path: Path) -> Dict:
        """Test optimized Tesseract with preprocessing."""
        start_time = time.time()
        try:
            # Apply best preprocessing
            processed = self._preprocess_for_tesseract(image_path)

            # Try best PSM mode from previous testing
            config = '--oem 3 --psm 6'
            text = pytesseract.image_to_string(processed, config=config)

            return {
                'engine': 'tesseract_optimized',
                'text': text.strip(),
                'processing_time': time.time() - start_time,
                'text_length': len(text.strip()),
                'cost_per_1000': 0,
                'preprocessing': 'CLAHE + denoise + unsharp + adaptive_threshold'
            }
        except Exception as e:
            return {'error': str(e), 'engine': 'tesseract_optimized'}

    def test_apple_vision(self, image_path: Path) -> Dict:
        """Test Apple Vision Swift OCR."""
        if not self.engines['apple_vision']:
            return {'error': 'Apple Vision not available', 'engine': 'apple_vision'}

        start_time = time.time()
        try:
            pkg_dir = image_path.parent.parent / "engines" / "vision_swift"
            cmd = [
                "swift", "run", "--package-path", str(pkg_dir),
                "vision_swift", str(image_path)
            ]

            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            results = json.loads(proc.stdout)

            # Extract text
            tokens = [r["text"] for r in results]
            text = " ".join(tokens)

            return {
                'engine': 'apple_vision',
                'text': text,
                'processing_time': time.time() - start_time,
                'text_length': len(text),
                'cost_per_1000': 0,
                'tokens_detected': len(tokens)
            }
        except Exception as e:
            return {'error': str(e), 'engine': 'apple_vision'}

    def test_claude_vision(self, image_path: Path) -> Dict:
        """Test Claude 3.5 Sonnet vision capabilities."""
        if not self.engines['claude_vision']:
            return {'error': 'Claude Vision not available (API key missing)', 'engine': 'claude_vision'}

        start_time = time.time()
        try:
            # Encode image
            image_data = self._encode_image_base64(image_path)

            # Create message with botanical context
            message = self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data
                            }
                        },
                        {
                            "type": "text",
                            "text": """Extract all text from this herbarium specimen label. Focus on:
- Scientific names (genus species)
- Collector names and numbers
- Collection dates
- Geographic locations
- Institution names
- Any handwritten or typed text on labels

Return only the extracted text, preserving original formatting and spelling exactly as shown."""
                        }
                    ]
                }]
            )

            text = message.content[0].text

            return {
                'engine': 'claude_vision',
                'text': text,
                'processing_time': time.time() - start_time,
                'text_length': len(text),
                'cost_per_1000': 15,  # Estimated cost per 1000 images
                'model': 'claude-3-5-sonnet'
            }

        except Exception as e:
            return {'error': str(e), 'engine': 'claude_vision'}

    def test_gpt4_vision(self, image_path: Path) -> Dict:
        """Test GPT-4 Vision OCR."""
        if not self.engines['gpt4_vision']:
            return {'error': 'GPT-4 Vision not available (API key missing)', 'engine': 'gpt4_vision'}

        start_time = time.time()
        try:
            # Encode image
            image_data = self._encode_image_base64(image_path)

            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Extract all text from this herbarium specimen label. Focus on:
- Scientific names (genus species)
- Collector names and numbers
- Collection dates
- Geographic locations
- Institution names
- Any handwritten or typed text on labels

Return only the extracted text, preserving original formatting and spelling exactly as shown."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }],
                max_tokens=1000
            )

            text = response.choices[0].message.content

            return {
                'engine': 'gpt4_vision',
                'text': text,
                'processing_time': time.time() - start_time,
                'text_length': len(text),
                'cost_per_1000': 50,  # Estimated cost per 1000 images
                'model': 'gpt-4o'
            }

        except Exception as e:
            return {'error': str(e), 'engine': 'gpt4_vision'}

    def test_google_vision(self, image_path: Path) -> Dict:
        """Test Google Cloud Vision API."""
        if not self.engines['google_vision']:
            return {'error': 'Google Vision not available (credentials missing)', 'engine': 'google_vision'}

        start_time = time.time()
        try:
            with open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            response = self.google_client.text_detection(image=image)

            if response.text_annotations:
                text = response.text_annotations[0].description
            else:
                text = ""

            return {
                'engine': 'google_vision',
                'text': text,
                'processing_time': time.time() - start_time,
                'text_length': len(text),
                'cost_per_1000': 1.5,  # Estimated cost per 1000 images
                'annotations_count': len(response.text_annotations)
            }

        except Exception as e:
            return {'error': str(e), 'engine': 'google_vision'}

    def test_all_engines(self, image_path: Path) -> Dict:
        """Test all available engines on a single image."""
        print(f"\\n🔍 Testing all engines on {image_path.name}")

        results = {
            'image_path': str(image_path),
            'image_name': image_path.name,
            'engines': {},
            'timestamp': time.time()
        }

        # Test each available engine
        test_methods = {
            'tesseract_raw': self.test_tesseract_raw,
            'tesseract_optimized': self.test_tesseract_optimized,
            'apple_vision': self.test_apple_vision,
            'claude_vision': self.test_claude_vision,
            'gpt4_vision': self.test_gpt4_vision,
            'google_vision': self.test_google_vision
        }

        for engine_name, available in self.engines.items():
            if not available:
                print(f"  ⚠️  {engine_name}: Not available")
                results['engines'][engine_name] = {'error': 'Not available'}
                continue

            print(f"  🔄 Testing {engine_name}...")

            try:
                result = test_methods[engine_name](image_path)

                if 'error' in result:
                    print(f"    ❌ Error: {result['error']}")
                else:
                    text_len = result.get('text_length', 0)
                    time_taken = result.get('processing_time', 0)
                    cost = result.get('cost_per_1000', 0)
                    print(f"    ✅ {text_len} chars, {time_taken:.2f}s, ${cost}/1k")

                results['engines'][engine_name] = result

            except Exception as e:
                error_result = {'error': str(e), 'engine': engine_name}
                results['engines'][engine_name] = error_result
                print(f"    ❌ Exception: {e}")

        return results

    def analyze_results(self, results: Dict) -> Dict:
        """Analyze and rank engine performance."""
        valid_engines = []

        for engine_name, result in results['engines'].items():
            if 'error' not in result:
                valid_engines.append({
                    'name': engine_name,
                    'text_length': result.get('text_length', 0),
                    'processing_time': result.get('processing_time', 0),
                    'cost_per_1000': result.get('cost_per_1000', 0),
                    'text_preview': result.get('text', '')[:100] + '...' if result.get('text', '') else ''
                })

        # Sort by text length (more text = better extraction)
        valid_engines.sort(key=lambda x: x['text_length'], reverse=True)

        return {
            'best_engine': valid_engines[0]['name'] if valid_engines else None,
            'ranking': valid_engines,
            'total_engines_tested': len(valid_engines),
            'available_engines': list(self.engines.keys())
        }


def main():
    parser = argparse.ArgumentParser(description="Comprehensive vision API testing for herbarium OCR")
    parser.add_argument('image', type=Path, help='Path to herbarium specimen image')
    parser.add_argument('--output', type=Path, help='Save detailed results to JSON file')

    args = parser.parse_args()

    if not args.image.exists():
        print(f"Image not found: {args.image}")
        return 1

    tester = ComprehensiveVisionTester()

    print("🚀 Comprehensive Vision API Testing for Herbarium OCR")
    print(f"📋 Available engines: {[k for k, v in tester.engines.items() if v]}")

    # Test all engines
    results = tester.test_all_engines(args.image)
    analysis = tester.analyze_results(results)

    # Print analysis
    print(f"\\n📊 ANALYSIS RESULTS:")
    print(f"🏆 Best engine: {analysis['best_engine']}")
    print(f"📈 Engines tested: {analysis['total_engines_tested']}")

    print(f"\\n📋 Performance Ranking:")
    for i, engine in enumerate(analysis['ranking'], 1):
        name = engine['name']
        chars = engine['text_length']
        time_taken = engine['processing_time']
        cost = engine['cost_per_1000']
        print(f"{i}. {name}: {chars} chars, {time_taken:.2f}s, ${cost}/1k")
        if i <= 2:  # Show preview for top 2
            print(f"   Preview: {engine['text_preview']}")

    # Save detailed results if requested
    if args.output:
        with open(args.output, 'w') as f:
            json.dump({'results': results, 'analysis': analysis}, f, indent=2, default=str)
        print(f"\\n💾 Detailed results saved to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())