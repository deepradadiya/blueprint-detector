FROM python:3.8-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install system dependencies (including the missing libGL)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    poppler-utils

# Install Python dependencies from requirements.txt
RUN pip install -r requirements.txt

# Command to run your app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
