#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-env.sh"
export TAGS="20250920-175756"
# 4.1 Historial (no requiere Keycloak)
gcloud run deploy historial-service \
  --region "$REGION" \
  --image  "us-central1-docker.pkg.dev/proyecto-integrador-medisupply/ms-experimentos/historial-service:$TAGS" \
  --allow-unauthenticated \
  --port 8080

HIST_URL="$(gcloud run services describe historial-service --region "$REGION" --format='value(status.url)')"
echo "HISTORIAL_URL=$HIST_URL"

# 4.2 Autorizador (valida JWT y llama al Historial)
gcloud run deploy autorizador \
  --region "$REGION" \
  --image  "us-central1-docker.pkg.dev/proyecto-integrador-medisupply/ms-experimentos/autorizador:$TAGS" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "JWT_ISS=${JWT_ISS},JWKS_URL=${JWKS_URL},JWT_AUD=${JWT_AUD},HISTORIAL_BASE=${HIST_URL}"

AUTHZ_URL="$(gcloud run services describe autorizador --region "$REGION" --format='value(status.url)')"
echo "AUTORIZADOR_URL=$AUTHZ_URL"

# 4.3 Autenticador (opcional: fachada a /token de Keycloak)
gcloud run deploy autenticador \
  --region "$REGION" \
  --image  "us-central1-docker.pkg.dev/proyecto-integrador-medisupply/ms-experimentos/autenticador:$TAGS" \
  --allow-unauthenticated \
  --port 8080 \
  --set-env-vars "KEYCLOAK_TOKEN_URL=${KC_TOKEN_URL},CLIENT_ID=${CLIENT_ID},CLIENT_SECRET=${CLIENT_SECRET}"

AUT_URL="$(gcloud run services describe autenticador --region "$REGION" --format='value(status.url)')"
echo "AUTENTICADOR_URL=$AUT_URL"

# Deja a mano las URLs para el gateway
echo
echo "------------------------------------------------"
echo "Servicios desplegados:"
echo "  Autenticador:   $AUT_URL"
echo "  Autorizador:    $AUTHZ_URL"
echo "  Historial:      $HIST_URL"
echo "  Keycloak:       $KEYCLOAK_URL"
echo "------------------------------------------------"
