# MediSupply — Experimento de Integridad (GCP)

Validador de integridad (SHA-256) en Cloud Function (Gen2) que valida `X-Message-Integrity` contra el body canónico y, si pasa, reenvía al microservicio de Inventario (Cloud Run). API Gateway publica `/inventory/products` y delega primero en la Function.

## Despliegue (resumen)
1) Cloud Run (Inventario)
```bash
gcloud services enable run.googleapis.com artifactregistry.googleapis.com
cd inventory-service
gcloud builds submit --tag "us-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/inventory:latest"
gcloud run deploy inventory-service --image "us-docker.pkg.dev/$PROJECT_ID/cloud-run-source-deploy/inventory:latest" --region $REGION --allow-unauthenticated
```

2) Cloud Function Gen2 (Validador)
```bash
gcloud services enable cloudfunctions.googleapis.com
cd ../cf-validador
gcloud functions deploy validador-checksum --gen2 --region $REGION \
  --runtime python311 --source . --entry-point app --trigger-http \
  --set-env-vars INVENTORY_BASE_URL="https://<URL-Cloud-Run>",CHECKSUM_ALGO="sha256",CHECKSUM_HEADER="X-Message-Integrity",FORWARD_PATH="/inventory/products" \
  --allow-unauthenticated
```

3) API Gateway
Editar `api-gateway/openapi-gateway.yaml` (PROJECT_ID, REGION, CF_NAME=validador-checksum) y crear gateway:
```bash
gcloud services enable apigateway.googleapis.com
cd ../api-gateway
gcloud api-gateway apis create medi-supply-api
gcloud api-gateway api-configs create medi-supply-config --api=medi-supply-api --openapi-spec=openapi-gateway.yaml
gcloud api-gateway gateways create medi-supply-gw --api=medi-supply-api --api-config=medi-supply-config --location=$REGION
```

4) Prueba
```bash
BODY='{"expiration_date":"2099-12-31","lot_number":"L-001","name":"Jeringa 5ml","sku":"SKU-001"}'
CHECKSUM=$(echo -n $BODY | openssl dgst -sha256 | sed 's/^.* //')
curl -i -X POST "https://medi-supply-gw-$REGION.gateway.dev/inventory/products" \
  -H "Content-Type: application/json" \
  -H "X-Message-Integrity: sha256=$CHECKSUM" \
  -d "$BODY"
```