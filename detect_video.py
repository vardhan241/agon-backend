"""Video/CCTV ANPR runner with annotated output."""

from __future__ import annotations

import argparse
from pathlib import Path

import cv2

from detector import LicensePlateDetector
from ocr_utils import run_ocr


def run_video(source: str, output_path: Path, engine: str = "easyocr", frame_stride: int = 5) -> None:
    detector = LicensePlateDetector()
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        raise RuntimeError(f"Could not open video/CCTV source: {source}")
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25
    writer = cv2.VideoWriter(str(output_path), cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
    frame_idx = 0
    detections = []
    labels: list[str] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        frame_idx += 1
        if frame_idx % frame_stride == 0:
            detections = detector.detect(frame)
            labels = []
            for detection in detections:
                ocr = run_ocr(detection.crop, engine=engine)  # type: ignore[arg-type]
                best = ocr[0] if ocr else None
                labels.append(f"{best.cleaned.corrected_text if best else 'plate'} {best.confidence:.1f}%" if best else "plate")
        writer.write(detector.draw(frame, detections, labels))
    cap.release()
    writer.release()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, help="Video file path or RTSP/CCTV URL")
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--engine", default="easyocr", choices=["easyocr", "paddleocr", "both"])
    parser.add_argument("--stride", type=int, default=5)
    args = parser.parse_args()
    run_video(args.source, args.output, args.engine, args.stride)
