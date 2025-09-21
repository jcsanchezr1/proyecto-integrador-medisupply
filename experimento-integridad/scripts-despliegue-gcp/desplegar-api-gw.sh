PROJECT_ID=proyecto-integrador-medisupply
REGION=us-central1
API_ID=medi-supply-api
CONFIG_ID=medi-supply-config-v2
GATEWAY_ID=medi-supply-gw

gcloud config set project "$PROJECT_ID"
gcloud services enable apigateway.googleapis.com

# Crea la API si no existe (si ya existe, continúa)
gcloud api-gateway apis create "$API_ID" --project="$PROJECT_ID" 2>/dev/null || true

# Crea la configuración desde el Swagger 2.0
gcloud api-gateway api-configs create "$CONFIG_ID" \
  --api="$API_ID" \
  --openapi-spec="$(pwd)/api-gateway/openapi-gateway.yaml" \
  --project="$PROJECT_ID"

# Crea el gateway (si falló antes, vuelve a intentarlo ahora que ya existe el config)
gcloud api-gateway gateways create "$GATEWAY_ID" \
  --api="$API_ID" \
  --api-config="$CONFIG_ID" \
  --location="$REGION" \
  --project="$PROJECT_ID"

# Obtén la URL pública del gateway
gcloud api-gateway gateways describe "$GATEWAY_ID" \
  --location="$REGION" --project="$PROJECT_ID" \
  --format="value(defaultHostname)"
