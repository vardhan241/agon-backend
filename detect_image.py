"""CLI image detection entrypoint.

Usage:
    python detect_image.py --image samples/car.jpg --engine both
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2

from detector import LicensePlateDetector, detection_to_dict
from ocr_utils import run_ocr


def detect_image(image_path: Path, engine: str = "both") -> list[dict]:
    detector = LicensePlateDetector()
    image = cv2.imread(str(image_path))
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")
    detections = detector.detect(image)
    results: list[dict] = []
    for detection in detections:
        ocr_results = run_ocr(detection.crop, engine=engine)  # type: ignore[arg-type]
        best = ocr_results[0] if ocr_results else None
        results.append({
            "detection": detection_to_dict(detection),
            "ocr": [result.__dict__ | {"cleaned": result.cleaned.__dict__} for result in ocr_results],
            "best_plate": best.cleaned.corrected_text if best else "",
            "best_confidence": best.confidence if best else 0,
        })
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--engine", default="both", choices=["easyocr", "paddleocr", "both"])
    args = parser.parse_args()
    print(json.dumps(detect_image(args.image, args.engine), indent=2))
