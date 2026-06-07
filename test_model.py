from ultralytics import YOLO

# Load trained model
model = YOLO(
    "runs/detect/models/license_plate_detector/weights/best.pt"
)

# Detect license plate
results = model(
    "raw_dataset/images/Cars0.png",
    show=True,
    save=True,
    conf=0.25
)

print(results)