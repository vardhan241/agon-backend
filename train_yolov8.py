from ultralytics import YOLO

# Load base model
model = YOLO("yolov8n.pt")

# Train
model.train(
    data="dataset/data.yaml",
    epochs=100,
    imgsz=640,
    batch=8,
    project="models",
    name="license_plate_detector"
)