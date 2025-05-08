from pdf2image import convert_from_path
import os

def convert_pdf_to_images(pdf_path, output_dir):
    try:
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Convert PDF to images
        images = convert_from_path(pdf_path, dpi=150)
        
        # Save images
        for i, image in enumerate(images):
            image_path = os.path.join(output_dir, f"E00{i+3}.jpg")
            image.save(image_path, "JPEG")
            print(f"Saved image: {image_path}")
            
    except Exception as e:
        print(f"Error converting PDF: {str(e)}")
        raise

if __name__ == "__main__":
    pdf_path = "The Egyptian EV - Sample Data.pdf"
    output_dir = "dataset/train/images"
    convert_pdf_to_images(pdf_path, output_dir)