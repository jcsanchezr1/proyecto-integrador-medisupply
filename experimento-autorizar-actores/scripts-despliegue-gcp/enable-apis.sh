#!/usr/bin/env bash
set -euo pipefail
gcloud config set project "${PROJECT_ID}"
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com
# Crea repo Docker si no existe
if ! gcloud artifacts repositories describe "${AR_REPO}" --location="${REGION}" --format="value(name)" >/dev/null 2>&1; then
  gcloud artifacts repositories create "${AR_REPO}" \
    --repository-format=docker --location="${REGION}" \
    --description="Repo Docker MediSupply"
fi
