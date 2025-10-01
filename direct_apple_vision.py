import sys
import os
from pathlib import Path

try:
    import Vision
    import Quartz
    from Foundation import NSURL

    def extract_text_from_image(image_path):
        # Load image
        image_url = NSURL.fileURLWithPath_(str(image_path))
        image = Quartz.CIImage.imageWithContentsOfURL_(image_url)

        if not image:
            return None

        # Create text recognition request
        request = Vision.VNRecognizeTextRequest.alloc().init()
        request.setRecognitionLevel_(Vision.VNRequestTextRecognitionLevelAccurate)

        # Perform request
        handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(image, {})
        success = handler.performRequests_error_([request], None)

        if not success[0]:
            return None

        # Extract text
        observations = request.results()
        if not observations:
            return None

        text_lines = []
        for observation in observations:
            text_lines.append(observation.text())

        return '\n'.join(text_lines)

    if __name__ == "__main__":
        image_path = sys.argv[1]
        text = extract_text_from_image(image_path)
        print(text if text else "[No text detected]")

except ImportError:
    print("[Apple Vision not available]")