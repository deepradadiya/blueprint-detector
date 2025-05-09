from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from PIL import Image, ImageDraw
import io
import numpy as np
import cv2
from ultralytics import YOLO
import pdf2image
import boto3
import uuid
import os
from typing import List, Dict
import logging

app = FastAPI(title="Blueprint Symbol Detector")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize YOLO model (assuming best.pt is in the same directory)
model = YOLO("best.pt")

# AWS S3 configuration (replace with your credentials)
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
BUCKET_NAME = os.getenv('S3_BUCKET_NAME', 'blueprint-detections')

class Detection:
    def __init__(self, label: str, confidence: float, bbox: List[float]):
        self.label = label
        self.confidence = confidence
        self.bbox = bbox

def process_image(image: Image.Image) -> tuple[List[Dict], Image.Image]:
    """Process image and return detections with overlay"""
    # Convert PIL image to numpy array for YOLO
    img_array = np.array(image)
    img_array = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    
    # Run detection
    results = model(img_array)
    
    detections = []
    draw = ImageDraw.Draw(image)
    
    for result in results:
        boxes = result.boxes
        for box in boxes:
            confidence = float(box.conf)
            if confidence < 0.3:
                continue
                
            # Get bounding box coordinates
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            width = x2 - x1
            height = y2 - y1
            x = x1
            y = y1
            
            # Get label
            label_idx = int(box.cls)
            label = model.names[label_idx]
            
            detections.append({
                "label": label,
                "confidence": confidence,
                "bbox": [x, y, width, height]
            })
            
            # Draw rectangle on overlay image
            color = {
                'evse': 'red',
                'panel': 'blue',
                'gfi': 'green'
            }.get(label, 'yellow')
            
            draw.rectangle([x1, y1, x2, y2], outline=color, width=2)
            
            # Add label text
            draw.text((x1, y1-20), f"{label} {confidence:.2f}", fill=color)
    
    return detections, image

def upload_to_s3(image: Image.Image) -> str:
    """Upload overlay image to S3 and return URL"""
    output = io.BytesIO()
    image.save(output, format='PNG')
    image_key = f"overlays/{uuid.uuid4()}.png"
    
    s3_client.put_object(
        Body=output.getvalue(),
        Bucket=BUCKET_NAME,
        Key=image_key,
        ContentType='image/png'
    )
    
    return f"https://{BUCKET_NAME}.s3.amazonaws.com/{image_key}"

@app.post("/detect")
async def detect_symbols(file: UploadFile = File(...)):
    try:
        # Validate file size (10MB limit)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
        
        # Process file based on type
        if file.content_type == 'application/pdf':
            # Convert first page of PDF to image
            images = pdf2image.convert_from_bytes(content, dpi=150)
            if not images:
                raise HTTPException(status_code=400, detail="Invalid PDF")
            image = images[0]
        elif file.content_type in ['image/png', 'image/jpeg']:
            image = Image.open(io.BytesIO(content)).convert('RGB')
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        # Process image and get detections
        detections, overlay_image = process_image(image)
        
        # Upload overlay image to S3
        image_url = upload_to_s3(overlay_image)
        
        return JSONResponse({
            "detections": detections,
            "image_url": image_url
        })
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error processing file: {str(e)}")
    
    finally:
        await file.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)