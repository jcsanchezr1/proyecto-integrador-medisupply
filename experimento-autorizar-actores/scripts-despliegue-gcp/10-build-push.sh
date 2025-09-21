#!/usr/bin/env bash
set -euo pipefail
source "$(dirname "$0")/00-env.sh"

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

# Autenticador
gcloud builds submit "$ROOT/autenticador" \
  --tag "$IMG_AUTENTICADOR"

# Historial
gcloud builds submit "$ROOT/historial-service" \
  --tag "$IMG_HISTORIAL"

# Autorizador
gcloud builds submit "$ROOT/autorizador" \
  --tag "$IMG_AUTORIZADOR"

echo "IMG_AUTENTICADOR=$IMG_AUTENTICADOR"
echo "IMG_HISTORIAL=$IMG_HISTORIAL"
echo "IMG_AUTORIZADOR=$IMG_AUTORIZADOR"
