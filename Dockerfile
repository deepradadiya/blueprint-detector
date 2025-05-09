FROM python:3.8-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN apt-get update && apt-get install -y poppler-utils

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]