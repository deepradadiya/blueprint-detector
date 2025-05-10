# Blueprint Symbol Detector

This is a FastAPI-based service for detecting electrical symbols in construction blueprint images/PDFs. It identifies EV charger blocks (`evse`), electrical panelboards (`panel`), and GFI receptacles (`gfi`) using a YOLOv8 model.

## Prerequisites

- Python 3.8+
- Poppler (for `pdf2image`): Install via `conda install poppler` or system package manager.
- AWS S3 account for storing overlay images.
- Git for version control.
- Annotation tool (e.g., LabelImg or Roboflow).

## Setup Instructions

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/blueprint-detector.git
   cd blueprint-detector
   ```

2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set AWS S3 Environment Variables**:
   ```bash
   export AWS_ACCESS_KEY_ID='your-access-key'
   export AWS_SECRET_ACCESS_KEY='your-secret-key'
   export S3_BUCKET_NAME='your-bucket-name'
   ```
   Alternatively, set these in a `.env` file and use `python-dotenv`.

4. **Prepare the Dataset**:
   - Convert the sample PDF to images:
     ```bash
     python convert_pdf.py
     ```
     This creates `E003.jpg` and `E004.jpg` in `dataset/train/images/`.
   - Annotate images for `evse`, `panel`, and `gfi` using LabelImg or Roboflow:
     - Install LabelImg: `pip install labelImg`
     - Run: `labelImg dataset/train/images/`
     - Save annotations in YOLO format (`E003.txt`, `E004.txt`) in `dataset/train/labels/`.
     - Example annotation (`E003.txt`):
       ```
       0 0.5 0.5 0.1 0.1  # evse
       1 0.3 0.7 0.15 0.2  # panel
       2 0.6 0.4 0.05 0.05  # gfi
       ```
     - Create a validation set by copying one image (e.g., a cropped `E003.jpg`) to `dataset/val/images/` with its labels in `dataset/val/labels/`.
     - Ensure 25-30 bounding boxes across the dataset.

5. **Train the Model**:
   ```bash
   python train.py
   ```
   - Trains a YOLOv8-nano model for 100 epochs (early stopping after 20 epochs of no improvement).
   - Saves the trained model as `best.pt`.
   - Targets mAP@50 ≥ 0.50.

6. **Run the FastAPI Server Locally**:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   - Access at `http://localhost:8000/docs` for the API interface.

## Sample Usage

Test the endpoint with a curl command:

```bash
curl -X POST "http://localhost:8000/detect" \
     -F "file=@dataset/train/images/E003.jpg" \
     -H "Content-Type: multipart/form-data"
```

Response format:
```json
{
  "detections": [
    {
      "label": "evse",
      "confidence": 0.85,
      "bbox": [x, y, width, height]
    },
    ...
  ],
  "image_url": "https://your-bucket.s3.amazonaws.com/overlays/uuid.png"
}
```

## Deployment

Deploy to Hugging Face Spaces or Railway for public access.

### Hugging Face Spaces

1. Create a new Space on Hugging Face:
   - Choose "Docker" as the Space type.
   - Select "Python" SDK.

2. Create a `Dockerfile`:
   ```dockerfile
   FROM python:3.8-slim

   WORKDIR /app
   COPY . .
   RUN pip install -r requirements.txt
   RUN apt-get update && apt-get install -y poppler-utils

   CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

3. Push to Hugging Face:
   - Initialize a git repository in the project folder.
   - Add the repository URL: `git remote add origin https://huggingface.co/spaces/your-username/blueprint-detector`
   - Commit and push:
     ```bash
     git add .
     git commit -m "Initial commit"
     git push origin main
     ```

4. Configure Secrets:
   - In the Space settings, add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `S3_BUCKET_NAME` as secrets.

5. Build and Deploy:
   - The Space will build and deploy automatically.
   - Access the endpoint at `https://your-username-blueprint-detector.hf.space/detect`.

### Railway

1. Create a new project on Railway:
   - Link your GitHub repository.
   - Select the repository and branch.

2. Configure Environment Variables:
   - Add `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `S3_BUCKET_NAME`.

3. Add a `Procfile`:
   ```plaintext
   web: uvicorn main:app --host 0.0.0.0 --port $PORT
   ```

4. Deploy:
   - Railway will detect the Python environment and install dependencies.
   - Ensure Poppler is installed by adding a `nixpacks.toml`:
     ```toml
     [phases.setup]
     aptPkgs = ['poppler-utils']
     ```

5. Access the endpoint at the provided Railway URL.

## Project Structure

- `main.py`: FastAPI application code
- `train.py`: YOLOv8 training script
- `convert_pdf.py`: PDF to image conversion script
- `data.yaml`: Dataset configuration
- `requirements.txt`: Python dependencies
- `classes.txt`: Symbol classes definition
- `best.pt`: Trained YOLOv8 model weights (generated after training)
- `dataset/`: Directory for training and validation images/labels
  - `train/images/`: Training images (`E003.jpg`, `E004.jpg`)
  - `train/labels/`: Training annotations (`E003.txt`, `E004.txt`)
  - `val/images/`: Validation images
  - `val/labels/`: Validation annotations
- `labels/`: Empty directory for additional annotations
- `runs/`: Directory for training logs and weights

## Notes

- **File Support**: Accepts PNG/JPG images or single-page PDFs (≤10MB).
- **Detection Threshold**: Minimum confidence of 0.30.
- **Overlay Colors**: Red (evse), blue (panel), green (gfi).
- **Performance**: Inference completes in <30 seconds on CPU.
- **Model Accuracy**: Trained to achieve mAP@50 ≥ 0.50.
- **Annotation**: Manual annotation required. Use LabelImg for YOLO-format labels.
- **AWS S3**: Ensure the bucket exists and credentials are valid.
