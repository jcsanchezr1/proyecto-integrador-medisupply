FROM python:3.11-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .
COPY models/ ./models/
COPY controllers/ ./controllers/
COPY views/ ./views/
CMD exec gunicorn --bind :8080 --workers 2 --threads 8 --timeout 0 app:app