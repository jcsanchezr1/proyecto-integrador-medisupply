PROJECT_ID=proyecto-integrador-medisupply
REGION=us-central1
API_ID=medi-supply-api
CONFIG_ID=medi-supply-config-v4
GATEWAY_ID=medi-supply-gw

gcloud config set project "$PROJECT_ID"

# Crear nueva config desde el YAML corregido
gcloud api-gateway api-configs create "$CONFIG_ID" \
  --api="$API_ID" \
  --openapi-spec="$(pwd)/api-gateway/openapi-gateway.yaml" \
  --project="$PROJECT_ID"

# Actualizar el gateway para usar esta config
gcloud api-gateway gateways update "$GATEWAY_ID" \
  --api="$API_ID" \
  --api-config="$CONFIG_ID" \
  --location="$REGION" \
  --project="$PROJECT_ID"
