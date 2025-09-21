# Variables básicas
PROJECT_ID=proyecto-integrador-medisupply
REGION=us-central1
gcloud config set project $PROJECT_ID

# (Una vez) habilitar API de Cloud Functions
gcloud services enable cloudfunctions.googleapis.com

# (Opcional) obtener la URL del servicio de Inventario en Cloud Run
INVENTORY_URL=https://inventory-service-159067324714.us-central1.run.app

# ===== Despliegue función PÚBLICA (más simple) =====
gcloud functions deploy validador-checksum \
  --gen2 --region $REGION --runtime python311 \
  --source "./cf-validador" \
  --entry-point validador_mediador \
  --trigger-http \
  --set-env-vars INVENTORY_BASE_URL="$INVENTORY_URL",FORWARD_PATH="/inventory/products",CHECKSUM_HEADER="X-Message-Integrity",CHECKSUM_ALGO="sha256" \
  --allow-unauthenticated
