"""YOLOv8 license plate detector wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_MODEL_PATH = BASE_DIR / "models" / "license_plate_detector.pt"

@dataclass
class PlateDetection:
    xyxy: tuple[int, int, int, int]
    confidence: float
    class_id: int
    crop: np.ndarray


class LicensePlateDetector:
    def __init__(self, model_path: Path | str = DEFAULT_MODEL_PATH, conf_threshold: float = 0.35):
        self.model_path = Path(model_path)
        self.conf_threshold = conf_threshold
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"YOLOv8 model not found at {self.model_path}. Place your trained license_plate_detector.pt here."
            )
        self.model = YOLO(str(self.model_path))

    def detect(self, image_bgr: np.ndarray) -> list[PlateDetection]:
        if image_bgr is None or image_bgr.size == 0:
            raise ValueError("Empty image received")
        results = self.model.predict(image_bgr, conf=self.conf_threshold, verbose=False)
        detections: list[PlateDetection] = []
        h, w = image_bgr.shape[:2]
        for result in results:
            boxes = result.boxes
            if boxes is None:
                continue
            for box in boxes:
                conf = float(box.conf[0])
                if conf < self.conf_threshold:
                    continue
                x1, y1, x2, y2 = [int(v) for v in box.xyxy[0].tolist()]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)
                if x2 <= x1 or y2 <= y1:
                    continue
                crop = image_bgr[y1:y2, x1:x2].copy()
                detections.append(PlateDetection((x1, y1, x2, y2), conf, int(box.cls[0]), crop))
        return sorted(detections, key=lambda item: item.confidence, reverse=True)

    @staticmethod
    def draw(image_bgr: np.ndarray, detections: list[PlateDetection], labels: list[str] | None = None) -> np.ndarray:
        output = image_bgr.copy()
        for idx, det in enumerate(detections):
            x1, y1, x2, y2 = det.xyxy
            label = labels[idx] if labels and idx < len(labels) else f"plate {det.confidence:.2f}"
            cv2.rectangle(output, (x1, y1), (x2, y2), (0, 220, 80), 2)
            cv2.putText(output, label, (x1, max(20, y1 - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 220, 80), 2)
        return output


def detection_to_dict(detection: PlateDetection) -> dict[str, Any]:
    return {"xyxy": detection.xyxy, "confidence": detection.confidence, "class_id": detection.class_id}
