from ultralytics import YOLO
import cv2
import easyocr
from plate_cleaner import clean_plate_text

# =========================
# Load YOLO model
# =========================
model = YOLO(
    "runs/detect/models/license_plate_detector/weights/best.pt"
)

# =========================
# Load OCR
# =========================
reader = easyocr.Reader(['en'])

# =========================
# Load image
# =========================
img = cv2.imread(
    "raw_dataset/images/Cars0.png"
)

if img is None:
    print("Image not found")
    exit()

# =========================
# Detect plate
# =========================
results = model(img)

for r in results:

    boxes = r.boxes.xyxy.cpu().numpy()

    for box in boxes:

        x1, y1, x2, y2 = map(int, box)

        plate = img[y1:y2, x1:x2]

        if plate.size == 0:
            continue

        cv2.imwrite(
            "plate_crop.jpg",
            plate
        )

        # =========================
        # Preprocess
        # =========================
        plate = cv2.resize(
            plate,
            None,
            fx=3,
            fy=3
        )

        gray = cv2.cvtColor(
            plate,
            cv2.COLOR_BGR2GRAY
        )

        _, thresh = cv2.threshold(
            gray,
            0,
            255,
            cv2.THRESH_BINARY + cv2.THRESH_OTSU
        )

        cv2.imwrite(
            "plate_processed.jpg",
            thresh
        )

        # =========================
        # OCR
        # =========================
        text = reader.readtext(
            thresh,
            allowlist='ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        )

        if len(text) == 0:
            print("No text detected")
            continue

        ocr_text = text[0][1]
        confidence = text[0][2]

        cleaned = clean_plate_text(
            ocr_text
        )

        print("\n----------------------")
        print("Raw OCR:", ocr_text)
        print("Confidence:", confidence)
        print("Normalized:", cleaned.normalized_text)
        print("Final Plate:", cleaned.corrected_text)
        print("Valid:", cleaned.is_valid)

        cv2.rectangle(
            img,
            (x1, y1),
            (x2, y2),
            (0, 255, 0),
            2
        )

        cv2.putText(
            img,
            cleaned.corrected_text,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

cv2.imwrite(
    "final_output.jpg",
    img
)

print("\nSaved: final_output.jpg")