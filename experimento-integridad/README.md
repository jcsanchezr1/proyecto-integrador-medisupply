# MediSupply — Experimento de Integridad (GCP)

Sistema de validación de integridad implementado con arquitectura de microservicios en Google Cloud Platform, siguiendo el patrón MVC y principios de responsabilidad única.

## 🏗️ Arquitectura

```
Actor → API Gateway → cf-validador (Cloud Function) → Inventory Service (Cloud Run) → Cloud SQL
```

### Componentes

- **API Gateway**: Punto de entrada único con autenticación por API key
- **cf-validador (Cloud Function)**: Validación de integridad SHA256 y mediación/proxy
- **Inventory Service (Cloud Run)**: Lógica de negocio de inventario con patrón MVC
- **Cloud SQL (PostgreSQL)**: Base de datos persistente

### Principios Implementados

- ✅ **Responsabilidad Única**: Cada servicio tiene una responsabilidad específica
- ✅ **Patrón MVC**: Implementado en todos los servicios
- ✅ **Validación de Integridad**: Centralizada en cf-validador
- ✅ **Mediación/Proxy**: cf-validador actúa como mediador entre API Gateway y microservicios

## 🚀 Despliegue

### Prerrequisitos

1. **Google Cloud SDK** instalado y configurado
2. **Docker** instalado
3. **Python 3.11+** instalado
4. **Postman** (opcional, para pruebas con GUI)

### 1. Configuración Inicial

```bash
# Configurar proyecto
export PROJECT_ID="proyecto-integrador-medisupply"
export REGION="us-central1"
gcloud config set project proyecto-integrador-medisupply

# Habilitar APIs necesarias
gcloud services enable run.googleapis.com cloudfunctions.googleapis.com apigateway.googleapis.com servicemanagement.googleapis.com sqladmin.googleapis.com artifactregistry.googleapis.com
```

### 2. Base de Datos Cloud SQL

```bash
# Crear instancia de Cloud SQL
gcloud sql instances create medi-supply-db \
  --database-version=POSTGRES_15 \
  --tier=db-f1-micro \
  --region=us-central1\
  --root-password=admin123

# Crear base de datos
gcloud sql databases create inventorydb --instance=medi-supply-db

# Crear usuario
gcloud sql users create inv_user --instance=medi-supply-db --password=inv_pass

# Obtener IP pública
gcloud sql instances describe medi-supply-db --format="value(ipAddresses[0].ipAddress)"
```

### 3. Inventory Service (Cloud Run)

```bash
# Construir y desplegar
cd inventory-service
docker build -t gcr.io/proyecto-integrador-medisupply/inventory-service .
docker push gcr.io/proyecto-integrador-medisupply/inventory-service

# Desplegar en Cloud Run
gcloud run deploy inventory-service \
  --image=gcr.io/proyecto-integrador-medisupply/inventory-service \
  --region=us-central1\
  --platform=managed \
  --allow-unauthenticated \
  --port=8080 \
  --set-env-vars=DATABASE_URL=postgresql+psycopg2://inv_user:inv_pass@34.70.162.235:5432/inventorydb
```

### 4. cf-validador (Cloud Function)

```bash
# Desplegar Cloud Function con script
 desplegar-cf.sh
```

```bash
# Desplegar Cloud Function manualmente
cd ../cf-validador
gcloud functions deploy validador-checksum --source=./cf-validador --runtime=python311 --trigger-http --allow-unauthenticated --region=us-central1 
--set-env-vars=INVENTORY_BASE_URL=https://inventory-service-159067324714.us-central1.run.app 
--set-env-vars=CHECKSUM_ALGO=sha256 
--set-env-vars=CHECKSUM_HEADER=X-Message-Integrity 
--set-env-vars=FORWARD_PATH=/inventory/products
```

### 5. API Gateway

```bash
# Desplegar el Api Gateway con script
desplegar-api-gw.sh
```

```bash
# Crear API
cd ../api-gateway
gcloud api-gateway apis create medi-supply-api

# Crear configuración
gcloud api-gateway api-configs create medi-supply-config \
  --api=medi-supply-api \
  --openapi-spec=api-gateway-config.yaml

# Crear gateway
gcloud api-gateway gateways create medi-supply-gw \
  --api=medi-supply-api \
  --api-config=medi-supply-config \
  --location=us-central1

# Crear API key
gcloud services api-keys create --display-name="MediSupply API Key"
```

### Colección de Postman

Importa `experimento-integridad.postman_collection.json` - Con cálculo automático de checksum.

## 📋 URLs de Acceso

- **API Gateway**: `https://medi-supply-gw-212okt9m.uc.gateway.dev`
- **Cloud Function**: `https://validador-checksum-czl6jx3zfa-uc.a.run.app`
- **Inventory Service**: `https://inventory-service-159067324714.us-central1.run.app`

## 🔧 Uso de la API

### Crear Producto (vía API Gateway)

```bash
# Calcular checksum
BODY='{"sku":"MED-001","name":"Aspirin 100mg","lot_number":"LOT123456","expiration_date":"2025-12-31"}'
CHECKSUM=$(python -c "import json, hashlib; data=json.loads('$BODY'); canonical=json.dumps(data, separators=(',', ':'), sort_keys=True); print(hashlib.sha256(canonical.encode()).hexdigest())")

# Enviar petición
curl -X POST "https://medi-supply-gw-212okt9m.uc.gateway.dev/inventory/products" \
  -H "Content-Type: application/json" \
  -H "X-Message-Integrity: sha256=$CHECKSUM" \
    -d "$BODY"
```

### Headers Requeridos

- **Validación de Integridad**: `X-Message-Integrity: sha256=<checksum>`
- **Content-Type**: `application/json`

## 🏛️ Arquitectura MVC

### Estructura de Directorios

```
experimento-integridad/
├── cf-validador/
│    ── main.py
├── inventory-service/
│   ├── models/
│   │   └── product_model.py
│   ├── controllers/
│   │   ├── product_controller.py
│   │   ├── health_controller.py
│   ├── views/
│   │   └── response_view.py
│   └── app.py
└── api-gateway/
    └── openapi-gateway.yaml
```
## 🛠️ Desarrollo Local

### Docker Compose

```bash
# Ejecutar localmente
docker-compose up --build
```

### Estructura de Desarrollo

- **cf-validador**: Cloud Function con functions-framework
- **inventory-service**: Flask con Gunicorn
- **Base de datos**: PostgreSQL en Docker
