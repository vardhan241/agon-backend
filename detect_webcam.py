from ultralytics import YOLO
import cv2
from ocr_utils import extract_plate
from plate_cleaner import clean_plate_text
from api_client import park_vehicle

import csv
from datetime import datetime
import time

# ======================
# Load YOLO model
# ======================
model = YOLO(
    "runs/detect/models/license_plate_detector/weights/best.pt"
)

# ======================
# Webcam
# ======================
cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# ======================
# Variables
# ======================
frame_count = 0

plate_no = ""

last_plate = ""
last_time = 0

OCR_INTERVAL = 10
DUPLICATE_TIMEOUT = 5

# ======================
# CSV Setup
# ======================
CSV_FILE = "plates.csv"

try:
    with open(CSV_FILE, "x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp",
            "Plate_Number"
        ])
except FileExistsError:
    pass

# ======================
# Main Loop
# ======================
while True:

    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    results = model(
        frame,
        imgsz=320,
        conf=0.5,
        verbose=False
    )

    boxes = results[0].boxes.xyxy

    for box in boxes:

        x1, y1, x2, y2 = map(int, box)

        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        plate = frame[y1:y2, x1:x2]

        if plate.size == 0:
            continue

        # OCR every N frames
        if frame_count % OCR_INTERVAL == 0:

            detected_text = extract_plate(plate)

            if detected_text:

                cleaned = clean_plate_text(
                    detected_text
                )

                if cleaned.is_valid:

                    candidate_plate = (
                        cleaned.corrected_text
                    )

                    current_time = time.time()

                    # Prevent duplicates
                    if (
                        candidate_plate != last_plate
                        or
                        current_time - last_time > DUPLICATE_TIMEOUT
                    ):

                        plate_no = candidate_plate

                        last_plate = plate_no
                        last_time = current_time

                        print(
                            "\nDetected:",
                            plate_no
                        )

                        # ======================
                        # Save to API
                        # ======================
                        try:

                            response = park_vehicle(
                                plate_no,
                                "TEMP_BAY"
                            )

                            print(
                                "API:",
                                response
                            )

                        except Exception as e:

                            print(
                                "API Error:",
                                e
                            )

                        # ======================
                        # CSV Logging
                        # ======================
                        with open(
                            CSV_FILE,
                            "a",
                            newline=""
                        ) as f:

                            writer = csv.writer(f)

                            writer.writerow([
                                datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                                plate_no
                            ])

        if plate_no:

            cv2.putText(
                frame,
                plate_no,
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (0, 255, 0),
                2
            )

    cv2.imshow(
        "ANPR System",
        frame
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()