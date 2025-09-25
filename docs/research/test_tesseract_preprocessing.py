#!/usr/bin/env python3
"""Advanced Tesseract preprocessing test for herbarium specimens.

This script tests various preprocessing techniques to give Tesseract the best
possible chance at reading herbarium specimen labels before making final
OCR engine recommendations.
"""

import argparse
import cv2
import numpy as np
import pytesseract
from pathlib import Path
from PIL import Image, ImageEnhance, ImageFilter
import sys
import time
from typing import Dict, List, Tuple


class TesseractPreprocessor:
    """Advanced preprocessing techniques for herbarium specimen OCR."""

    def __init__(self):
        self.preprocessing_methods = [
            'raw',
            'grayscale',
            'threshold_binary',
            'threshold_adaptive',
            'contrast_enhance',
            'denoise',
            'morphological',
            'gaussian_blur',
            'unsharp_mask',
            'combined_best'
        ]

    def preprocess_raw(self, image: np.ndarray) -> np.ndarray:
        """No preprocessing - baseline."""
        return image

    def preprocess_grayscale(self, image: np.ndarray) -> np.ndarray:
        """Convert to grayscale."""
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image

    def preprocess_threshold_binary(self, image: np.ndarray) -> np.ndarray:
        """Binary threshold."""
        gray = self.preprocess_grayscale(image)
        _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
        return binary

    def preprocess_threshold_adaptive(self, image: np.ndarray) -> np.ndarray:
        """Adaptive threshold for varying lighting."""
        gray = self.preprocess_grayscale(image)
        adaptive = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        return adaptive

    def preprocess_contrast_enhance(self, image: np.ndarray) -> np.ndarray:
        """Enhance contrast using CLAHE."""
        gray = self.preprocess_grayscale(image)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(gray)
        return enhanced

    def preprocess_denoise(self, image: np.ndarray) -> np.ndarray:
        """Denoise the image."""
        if len(image.shape) == 3:
            denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        else:
            denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        return denoised

    def preprocess_morphological(self, image: np.ndarray) -> np.ndarray:
        """Morphological operations to clean up text."""
        gray = self.preprocess_grayscale(image)

        # Apply binary threshold first
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        # Morphological operations
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        morph = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        return morph

    def preprocess_gaussian_blur(self, image: np.ndarray) -> np.ndarray:
        """Gaussian blur to reduce noise."""
        gray = self.preprocess_grayscale(image)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        return blurred

    def preprocess_unsharp_mask(self, image: np.ndarray) -> np.ndarray:
        """Unsharp masking for text sharpening."""
        gray = self.preprocess_grayscale(image)

        # Create unsharp mask
        gaussian = cv2.GaussianBlur(gray, (0, 0), 2.0)
        unsharp = cv2.addWeighted(gray, 1.5, gaussian, -0.5, 0)

        return unsharp

    def preprocess_combined_best(self, image: np.ndarray) -> np.ndarray:
        """Combination of best techniques for herbarium specimens."""
        # Start with contrast enhancement
        gray = self.preprocess_grayscale(image)

        # CLAHE for contrast
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

    def test_preprocessing_method(self, image_path: Path, method: str) -> Dict:
        """Test a specific preprocessing method."""
        start_time = time.time()

        try:
            # Load image
            image = cv2.imread(str(image_path))
            if image is None:
                return {'error': f'Could not load image: {image_path}'}

            # Apply preprocessing
            preprocess_func = getattr(self, f'preprocess_{method}')
            processed = preprocess_func(image)

            # Run OCR with different PSM modes
            best_result = {'text': '', 'char_count': 0, 'psm_mode': None}

            # Try different Page Segmentation Modes
            psm_modes = [6, 7, 8, 11, 12, 13]  # Various text recognition modes

            for psm in psm_modes:
                try:
                    config = f'--oem 3 --psm {psm}'
                    text = pytesseract.image_to_string(processed, config=config)
                    char_count = len([c for c in text if c.isalnum()])

                    if char_count > best_result['char_count']:
                        best_result = {
                            'text': text.strip(),
                            'char_count': char_count,
                            'psm_mode': psm
                        }
                except Exception:
                    continue

            processing_time = time.time() - start_time

            # Analyze results
            text = best_result['text']
            lines = [line.strip() for line in text.split('\\n') if line.strip()]

            return {
                'method': method,
                'text': text,
                'text_length': len(text),
                'char_count': best_result['char_count'],
                'line_count': len(lines),
                'psm_mode': best_result['psm_mode'],
                'processing_time': processing_time,
                'lines': lines[:5]  # First 5 lines for inspection
            }

        except Exception as e:
            return {'error': str(e), 'method': method}

    def test_all_methods(self, image_path: Path) -> List[Dict]:
        """Test all preprocessing methods on an image."""
        results = []

        print(f"\\n🔍 Testing preprocessing methods on {image_path.name}")

        for method in self.preprocessing_methods:
            print(f"  🔄 Testing {method}...")
            result = self.test_preprocessing_method(image_path, method)
            results.append(result)

            if 'error' in result:
                print(f"    ❌ Error: {result['error']}")
            else:
                char_count = result.get('char_count', 0)
                psm = result.get('psm_mode', 'N/A')
                print(f"    ✅ {char_count} chars (PSM {psm})")

        return results

    def analyze_best_method(self, results: List[Dict]) -> Dict:
        """Analyze which preprocessing method worked best."""
        valid_results = [r for r in results if 'error' not in r]

        if not valid_results:
            return {'error': 'No valid results'}

        # Sort by character count (more characters = better extraction)
        sorted_results = sorted(valid_results, key=lambda x: x['char_count'], reverse=True)
        best = sorted_results[0]

        return {
            'best_method': best['method'],
            'best_char_count': best['char_count'],
            'best_text_preview': best['text'][:200] + '...' if len(best['text']) > 200 else best['text'],
            'best_psm_mode': best['psm_mode'],
            'improvement_over_raw': best['char_count'] - next((r['char_count'] for r in valid_results if r['method'] == 'raw'), 0),
            'all_results': {r['method']: r['char_count'] for r in valid_results}
        }


def main():
    parser = argparse.ArgumentParser(
        description="Test advanced Tesseract preprocessing on herbarium specimens",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test single image with all preprocessing methods
  python test_tesseract_preprocessing.py single test_samples/sample1.jpg

  # Test all images in directory
  python test_tesseract_preprocessing.py batch test_samples/

  # Compare with Apple Vision results
  python test_tesseract_preprocessing.py compare test_samples/
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Testing modes')

    # Single image test
    single_parser = subparsers.add_parser('single', help='Test single image')
    single_parser.add_argument('image', type=Path, help='Path to image file')

    # Batch test
    batch_parser = subparsers.add_parser('batch', help='Test multiple images')
    batch_parser.add_argument('directory', type=Path, help='Directory containing images')

    # Compare with Apple Vision
    compare_parser = subparsers.add_parser('compare', help='Compare with Apple Vision')
    compare_parser.add_argument('directory', type=Path, help='Directory containing images')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    preprocessor = TesseractPreprocessor()

    if args.command == 'single':
        if not args.image.exists():
            print(f"Image not found: {args.image}")
            return 1

        results = preprocessor.test_all_methods(args.image)
        analysis = preprocessor.analyze_best_method(results)

        print(f"\\n📊 ANALYSIS RESULTS:")
        if 'error' in analysis:
            print(f"❌ {analysis['error']}")
        else:
            print(f"🏆 Best method: {analysis['best_method']}")
            print(f"📈 Character count: {analysis['best_char_count']}")
            print(f"⚡ Improvement over raw: +{analysis['improvement_over_raw']} chars")
            print(f"🔧 Best PSM mode: {analysis['best_psm_mode']}")
            print(f"\\n📝 Best text preview:")
            print(f"{analysis['best_text_preview']}")

            print(f"\\n📋 All methods comparison:")
            for method, count in analysis['all_results'].items():
                print(f"  {method}: {count} chars")

    elif args.command == 'batch':
        if not args.directory.exists():
            print(f"Directory not found: {args.directory}")
            return 1

        image_files = [f for f in args.directory.iterdir()
                      if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.tif', '.tiff']]

        if not image_files:
            print(f"No image files found in {args.directory}")
            return 1

        print(f"\\n🚀 Testing {len(image_files)} images with preprocessing...")

        batch_results = {}
        for image_file in image_files[:3]:  # Limit for testing
            results = preprocessor.test_all_methods(image_file)
            analysis = preprocessor.analyze_best_method(results)
            batch_results[image_file.name] = analysis

        print(f"\\n📊 BATCH ANALYSIS:")
        for filename, analysis in batch_results.items():
            if 'error' not in analysis:
                print(f"📁 {filename}: {analysis['best_method']} → {analysis['best_char_count']} chars")

    elif args.command == 'compare':
        print("\\n🔄 Comparison with Apple Vision coming soon...")
        print("Use the enhanced test_real_ocr_performance.py script for full comparison")

    return 0


if __name__ == "__main__":
    sys.exit(main())