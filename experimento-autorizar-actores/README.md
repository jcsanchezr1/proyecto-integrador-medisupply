# MediSupply — Experimento de Autenticación/Autorización (GCP)

Solución de autenticación y autorización basada en JWT (Keycloak) con mediación en un microservicio Autorizador, expuesta vía API Gateway. Incluye un servicio de Autenticador (fachada a Keycloak) y un microservicio de Historial protegido de acceso directo.

## 🏗️ Arquitectura

```
Flujo de autenticación (obtener token)
Cliente → API Gateway → Autenticador → Keycloak (/token)

Flujo de acceso a recurso protegido
Cliente + Bearer token → API Gateway → Autorizador (valida JWT por JWKS) → Historial Service
```

### Componentes

- API Gateway (Google API Gateway): Entrada única; enruta a Autenticador y Autorizador
- Autenticador (Cloud Run): Fachada a Keycloak para emisión de tokens (Password Grant)
- Autorizador (Cloud Run): Valida JWT (issuer/audience/firma RS256 vía JWKS) y autoriza por roles/permisos; reenvía al Historial
- Historial Service (Cloud Run): Microservicio de negocio protegido, solo responde si recibe `X-Auth-Validated: true`
- Keycloak (Cloud Run): Proveedor OIDC/JWT (realm/roles/usuarios)

Archivos clave:
- `api-gateway/openapi-gateway.yaml` (spec GW)
- `autenticador/app.py`, `autorizador/app.py`, `historial-service/app.py`
- `docker-compose.yml` (entorno local con Nginx como API GW)
- `scripts-despliegue-gcp/*.sh` (despliegue en GCP)

### Principios implementados

- Separación de responsabilidades: autenticación vs autorización vs negocio
- Zero-trust en microservicios: el Historial verifica `X-Auth-Validated`
- Autorización basada en claims (roles/permissions desde Keycloak)
- Defensa en profundidad: validaciones en gateway, autorizador y servicio
- Rotación de llaves: validación RS256 con JWKS (PyJWKClient cachea y refresca)

---

## 🚀 Despliegue en GCP

### Prerrequisitos

- Google Cloud SDK configurado (proyecto y permisos)
- Docker y Cloud Build habilitado
- Cuenta con permisos para Artifact Registry, Cloud Run y API Gateway
- Opcional: Postman para pruebas

### 0) Habilitar APIs y preparar repositorio de imágenes

Ejecuta desde `experimento-autorizar-actores/scripts-despliegue-gcp` (usa Bash, por ejemplo Git Bash o Cloud Shell):

```bash
export PROJECT_ID="proyecto-integrador-medisupply"; export REGION="us-central1"; export AR_REPO="ms-experimentos"
./enable-apis.sh
```

### 1) Desplegar Keycloak (dev)

```bash
export PROJECT_ID="proyecto-integrador-medisupply"; export REGION="us-central1"; export AR_REPO="ms-experimentos"
./deploy-keycloak-dev.sh
```

Al finalizar, toma nota de `KEYCLOAK_URL` impreso. Luego crea realm, cliente y usuarios demo con:

```bash
# Variables por defecto: KC_REALM=medisupply, JWT_AUD=medisupply-client
export KEYCLOAK_URL="<KEYCLOAK_URL impreso arriba>"
./bootstrap-keycloak.sh
```

Usuarios demo creados:
- gerente@demo.com / demo123 (roles: GerenteCuenta, historial.read)
- vendedor@demo.com / demo123 (rol: Vendedor)

### 2) Construir y publicar imágenes

```bash
./10-build-push.sh
```

El script publica en Artifact Registry con tags por timestamp y configura variables como `JWT_ISS`, `JWKS_URL`, `JWT_AUD`.

### 3) Desplegar servicios en Cloud Run

```bash
./20-deploy-services.sh
```

Se imprimen las URLs desplegadas:
- AUTENTICADOR_URL
- AUTORIZADOR_URL
- HISTORIAL_URL
- KEYCLOAK_URL

### 4) Desplegar API Gateway

```bash
# Si el API no existe aún, créalo una vez:
# gcloud api-gateway apis create medi-supply-authz-api --project=proyecto-integrador-medisupply

./30-deploy-apigw.sh
```

La spec `api-gateway/openapi-gateway.yaml` define:
- POST `/auth/token` → Autenticador (proxy)
- GET `/historial/{clienteId}` → Autorizador (forward de path; mantiene Authorization del cliente)
- OPTIONS `/historial/{clienteId}` → CORS preflight

Obtén la URL del Gateway con:

```bash
gcloud api-gateway gateways describe medi-supply-authz-gw --location=us-central1 --format='value(defaultHostname)'
```

---

## 📋 Uso de la API (GCP)

Asumiendo que `https://<gw-hostname>` es tu API Gateway:

### 1) Obtener token (Password Grant vía Autenticador)

```bash
curl -X POST "https://<gw-hostname>/auth/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=gerente@demo.com&password=demo123"
```

Respuesta (ejemplo):

```json
{"access_token":"<JWT>","token_type":"Bearer","expires_in":3600}
```

### 2) Acceder al historial protegido

```bash
TOKEN="<pega_access_token>"
curl -H "Authorization: Bearer $TOKEN" \
  "https://<gw-hostname>/historial/CL-001"
```

Respuesta (si autorizado):

```json
{"clienteId":"CL-001","resumen":"Historial clínico simulado","visiblePara":"<sub|email>"}
```

Errores comunes:
- 401 firma/aud/iss inválidos (revisa `JWT_ISS`, `JWKS_URL`, `JWT_AUD` en el Autorizador)
- 403 sin permisos (requiere `historial.read` o rol `GerenteCuenta`)

---

## 🧪 Desarrollo local (Docker Compose)

Levanta todo localmente (Nginx como Gateway):

```bash
docker-compose up --build
```

Puertos locales:
- Gateway (Nginx): http://localhost:9000
- Autenticador: http://localhost:9001
- Autorizador: http://localhost:9002
- Historial: http://localhost:9003
- Keycloak: http://localhost:9080 (dev)

Pruebas rápidas:
- Token local (emisión interna del Autenticador):
  - POST http://localhost:9001/token con JSON `{ "username":"gerente@demo.com", "password":"demo123" }`
- Acceso al historial vía Gateway local:
  - GET http://localhost:9000/historial/CL-001 con `Authorization: Bearer <token>`

Nota: El `default.conf` de Nginx enruta `/historial/` al Autorizador. Para login vía gateway local, usa directamente el Autenticador (puerto 9001) o añade una ruta en Nginx si necesitas `/auth/token`.

---

## 🔧 Configuración de entorno

Autorizador (`autorizador/app.py`):
- `JWT_ISS`: `https://<keycloak-host>/realms/medisupply`
- `JWKS_URL`: `${JWT_ISS}/protocol/openid-connect/certs`
- `JWT_AUD`: `medisupply-client`
- `HISTORIAL_BASE`: URL del Historial (Cloud Run)
- `UPSTREAM_AUTH`: `none` (por defecto) o `gcp` si el Historial es privado y requieres ID Token de GCP

Autenticador (`autenticador/app.py`):
- `KEYCLOAK_TOKEN_URL`: `${KEYCLOAK_URL}/realms/medisupply/protocol/openid-connect/token`
- `CLIENT_ID`: `medisupply-client`
- `CLIENT_SECRET`: (vacío si cliente público)

Historial (`historial-service/app.py`):
- Requiere header `X-Auth-Validated: true` y propaga `X-User-Id`

---

## 📦 Postman

En esta carpeta encontrarás:
- `MediSupply - Confidencialidad.postman_collection.json`
- `MediSupply - Local.postman_environment.json`

Úsalos como base para:
- POST `/auth/token` (obtener `access_token`)
- GET `/historial/{clienteId}` con `Authorization: Bearer {{access_token}}`

---

## 🗂️ Estructura de directorios

```
experimento-autorizar-actores/
├── api-gateway/
│   ├── default.conf             # Nginx local
│   └── openapi-gateway.yaml     # Spec API Gateway (GCP)
├── autenticador/                # Fachada Keycloak (token)
│   ├── app.py
│   └── Dockerfile
├── autorizador/                 # Autorización por JWT/JWKS
│   ├── app.py
│   └── Dockerfile
├── historial-service/           # Servicio protegido
│   ├── app.py
│   └── Dockerfile
├── keycloak/                    # Imagen base para Cloud Run
│   └── Dockerfile
├── docker-compose.yml           # Entorno local
└── scripts-despliegue-gcp/      # Despliegue GCP (Cloud Run, API GW, Keycloak)
```

---

## 📝 Notas y solución de problemas

- 401 issuer/audience: Asegura que `JWT_ISS` y `JWT_AUD` coinciden con el realm/cliente de Keycloak.
- 401 firma inválida: Revisa `JWKS_URL` y la rotación de llaves en Keycloak. El Autorizador intenta refrescar JWKS automáticamente.
- 403 forbidden: El token debe incluir `historial.read` o el rol `GerenteCuenta`.
- CORS: La ruta `OPTIONS /historial/{clienteId}` está definida en el API Gateway.
- Cloud Run privado: define `UPSTREAM_AUTH=gcp` y `TARGET_AUDIENCE` en el Autorizador si el Historial es privado.

---

Actualizado: 2025-09-20
