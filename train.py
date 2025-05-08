from ultralytics import YOLO
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def train_model():
    try:
        # Initialize YOLOv8-nano model
        model = YOLO("yolov8n.pt")  # Start with pre-trained nano model
        
        # Train the model
        results = model.train(
            data="data.yaml",
            epochs=100,
            imgsz=640,
            batch=16,
            device="cpu",  # Use '0' for GPU if available
            patience=20,
            project="runs/train",
            name="blueprint_detector",
            exist_ok=True,
            pretrained=True,
            optimizer="AdamW",
            lr0=0.001,
            augment=True
        )
        
        # Evaluate the model
        metrics = model.val()
        logger.info(f"mAP@50: {metrics.box.map50}")
        
        # Export the best model
        model.export(format="torchscript")
        os.rename("runs/train/blueprint_detector/weights/best.pt", "best.pt")
        logger.info("Training completed and model saved as best.pt")
        
    except Exception as e:
        logger.error(f"Error during training: {str(e)}")
        raise

if __name__ == "__main__":
    train_model()