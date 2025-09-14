FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8081

# Dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY main.py .

# (Opcional) ejecutar como usuario no root
RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 8081
# Escuchar en 0.0.0.0 para que el contenedor reciba tráfico externo
CMD ["functions-framework", "--target=validador_mediador", "--port=8081", "--host=0.0.0.0"]
