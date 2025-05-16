import os
import uuid
import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO
import boto3
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI()

# Load YOLOv8 model
model = YOLO("best.pt")

# AWS S3 configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
s3_client = boto3.client(
    "s3",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
)

def upload_to_s3(image: Image.Image, bucket: str, filename: str) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    s3_client.upload_fileobj(buffer, bucket, filename, ExtraArgs={"ContentType": "image/png"})
    return f"https://{bucket}.s3.amazonaws.com/{filename}"

def draw_boxes(image: np.ndarray, detections: list) -> Image.Image:
    for det in detections:
        x1, y1, x2, y2 = map(int, det["bbox"])
        label = det["label"]
        confidence = det["confidence"]
        color = (0, 255, 0)  # Green
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        cv2.putText(
            image,
            f"{label} {confidence:.2f}",
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2
        )
    return Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

@app.get("/")
async def root():
    return {"message": "Welcome to the Blueprint Detector API! Use /docs to access the Swagger UI."}

@app.post("/detect")
async def detect_symbols(file: UploadFile = File(...)):
    # Validate file size and type
    max_size = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > max_size:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    # Load image
    image = Image.open(io.BytesIO(content))
    image_np = np.array(image)
    if image_np.shape[-1] == 4:  # Convert RGBA to RGB
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2RGB)

    # Perform inference
    results = model.predict(image_np, imgsz=640, conf=0.3, iou=0.45)

    # Process detections
    detections = []
    for result in results:
        boxes = result.boxes.xyxy.cpu().numpy()  # Bounding boxes
        confidences = result.boxes.conf.cpu().numpy()  # Confidence scores
        classes = result.boxes.cls.cpu().numpy()  # Class IDs
        for box, conf, cls in zip(boxes, confidences, classes):
            detections.append({
                "label": result.names[int(cls)],
                "confidence": float(conf),
                "bbox": box.tolist()
            })

    # Draw boxes on image
    overlay_image = draw_boxes(image_np.copy(), detections)

    # Upload to S3
    filename = f"overlays/{uuid.uuid4()}.png"
    image_url = upload_to_s3(overlay_image, S3_BUCKET_NAME, filename)

    return JSONResponse(content={"detections": detections, "image_url": image_url})