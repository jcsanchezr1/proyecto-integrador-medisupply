export PROJECT_ID=proyecto-integrador-medisupply
export REGION=us-central1
export API_ID=medi-supply-authz-api
export CONFIG_ID=medi-supply-authz-config
export GATEWAY_ID=medi-supply-authz-gw


gcloud config set project "$PROJECT_ID"

# Crear nueva config desde el YAML corregido
gcloud api-gateway api-configs create "$CONFIG_ID" \
  --api="$API_ID" \
  --openapi-spec="$(pwd)/api-gateway/openapi-gateway.yaml" \
  --project="$PROJECT_ID"

# Actualizar el gateway para usar esta config
gcloud api-gateway gateways create "$GATEWAY_ID" \
  --api="$API_ID" \
  --api-config="$CONFIG_ID" \
  --location="$REGION" \
  --project="$PROJECT_ID"
