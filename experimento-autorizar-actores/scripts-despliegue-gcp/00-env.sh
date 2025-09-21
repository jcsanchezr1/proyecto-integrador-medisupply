#!/usr/bin/env bash
set -euo pipefail

# ---- PROYECTO Y REGIÓN ----
export PROJECT_ID="proyecto-integrador-medisupply"
export REGION="us-central1"

gcloud config set project "$PROJECT_ID" >/dev/null

# ---- ARTIFACT REGISTRY ----
export REPO="ms-experimentos"
export AR_HOST="${REGION}-docker.pkg.dev"
export AR_PATH="${AR_HOST}/${PROJECT_ID}/${REPO}"

# Tags con timestamp (evitan colisiones de caché)
TS="$(date +%Y%m%d-%H%M%S)"
export IMG_AUTENTICADOR="${AR_PATH}/autenticador:${TS}"
export IMG_AUTORIZADOR="${AR_PATH}/autorizador:${TS}"
export IMG_HISTORIAL="${AR_PATH}/historial-service:${TS}"

# ---- KEYCLOAK ya desplegado en Cloud Run ----
export REALM="medisupply"
export KEYCLOAK_URL="$(gcloud run services describe keycloak --region "$REGION" --format='value(status.url)')"
export JWT_ISS="${KEYCLOAK_URL}/realms/${REALM}"
export JWKS_URL="${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/certs"
export JWT_AUD="medisupply-client"
export REQUIRED_PERMISSION=historial.read

# Cliente de Keycloak usado por el Autenticador (si el cliente es público, CLIENT_SECRET queda vacío)
export KC_TOKEN_URL="${KEYCLOAK_URL}/realms/${REALM}/protocol/openid-connect/token"
export CLIENT_ID="medisupply-client"
export CLIENT_SECRET=""     # deja vacío si tu cliente es público

echo "PROJECT_ID=$PROJECT_ID"
echo "REGION=$REGION"
echo "KEYCLOAK_URL=$KEYCLOAK_URL"
echo "AR_PATH=$AR_PATH"
