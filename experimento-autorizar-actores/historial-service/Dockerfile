FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run inyecta PORT; usa gthread para evitar timeout por GIL
ENV PYTHONUNBUFFERED=1
CMD exec gunicorn -k gthread -w ${GUNICORN_WORKERS:-2} -b 0.0.0.0:${PORT:-8080} app:app
