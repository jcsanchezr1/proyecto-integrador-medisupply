#!/usr/bin/env bash
set -euo pipefail

# === Descubre rutas absolutas, independientemente de dónde ejecutes ===
SCRIPT_DIR="$(cd -- "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
BUILD_CONTEXT="${ROOT_DIR}/keycloak"

# === Variables (con defaults) ===
: "${PROJECT_ID:?export PROJECT_ID=tu-proyecto}"
: "${REGION:=us-central1}"
: "${AR_REPO:=ms-experimentos}"
: "${KEYCLOAK_ADMIN:=admin}"
: "${KEYCLOAK_ADMIN_PASSWORD:=admin}"

if [[ ! -f "${BUILD_CONTEXT}/Dockerfile" ]]; then
  echo "No se encontró Dockerfile en ${BUILD_CONTEXT}. Revisa la estructura."
  exit 1
fi

gcloud config set project "${PROJECT_ID}"

# Crea repo de Artifact Registry si no existe
if ! gcloud artifacts repositories describe "${AR_REPO}" --location="${REGION}" --format="value(name)" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format=docker --location="${REGION}" \
    --description="Repo Docker MediSupply"
fi

IMG="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/keycloak:23.0"

# Construye y sube la imagen desde la carpeta correcta
gcloud builds submit "${BUILD_CONTEXT}" --tag "${IMG}"

# Despliega Keycloak (dev, sin persistencia)
gcloud run deploy keycloak \
  --image="${IMG}" \
  --region="${REGION}" \
  --allow-unauthenticated \
  --memory=1Gi \
  --args="start-dev" \
  --set-env-vars KEYCLOAK_ADMIN="${KEYCLOAK_ADMIN}",KEYCLOAK_ADMIN_PASSWORD="${KEYCLOAK_ADMIN_PASSWORD}",KC_HTTP_ENABLED=true,KC_HTTP_PORT=8080,KC_PROXY=edge

KEYCLOAK_URL="$(gcloud run services describe keycloak --region "${REGION}" --format='value(status.url)')"
echo "KEYCLOAK_URL=${KEYCLOAK_URL}"
echo "Admin console: ${KEYCLOAK_URL}/admin  (user=${KEYCLOAK_ADMIN})"
echo
echo "Configura el autorizador con:"
echo "  JWT_ISS=${KEYCLOAK_URL}/realms/medisupply"
echo "  JWKS_URL=${KEYCLOAK_URL}/realms/medisupply/protocol/openid-connect/certs"
echo "  JWT_AUD=medisupply-client"
