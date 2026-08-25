FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 tesseract-ocr tesseract-ocr-eng && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PORT=10000 OMP_NUM_THREADS=1 MALLOC_ARENA_MAX=2
CMD ["sh","-c","gunicorn app:app --bind 0.0.0.0:${PORT} --workers 1 --threads 4 --timeout 180"]
