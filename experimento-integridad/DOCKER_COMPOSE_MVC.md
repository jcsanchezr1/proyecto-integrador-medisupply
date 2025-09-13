# Docker Compose con Arquitectura MVC

Este documento explica cómo usar Docker Compose con la nueva arquitectura MVC implementada en los servicios.

## Estructura de Servicios

### 1. Base de Datos (PostgreSQL)
- **Puerto**: 5432
- **Base de datos**: inventorydb
- **Usuario**: inv_user
- **Contraseña**: inv_pass

### 2. Inventory Service (Puerto 8080)
- **URL**: http://localhost:8080
- **Arquitectura**: MVC
- **Endpoints**:
  - `GET /healthz` - Health check
  - `POST /inventory/products` - Crear/actualizar producto
  - `GET /inventory/products/<sku>` - Obtener producto por SKU
  - `GET /inventory/products` - Obtener todos los productos

### 3. Validador Service (Puerto 8081)
- **URL**: http://localhost:8081
- **Arquitectura**: MVC
- **Endpoints**:
  - `POST /` - Validación de integridad y proxy

## Comandos Docker Compose

### Iniciar todos los servicios
```bash
docker-compose up -d
```

### Ver logs de todos los servicios
```bash
docker-compose logs -f
```

### Ver logs de un servicio específico
```bash
docker-compose logs -f inventory
docker-compose logs -f validador
docker-compose logs -f db
```

### Detener todos los servicios
```bash
docker-compose down
```

### Reconstruir y reiniciar servicios
```bash
docker-compose up --build -d
```

### Verificar estado de los servicios
```bash
docker-compose ps
```

## Pruebas de Integración

### Ejecutar script de pruebas
```bash
python test_mvc_integration.py
```

### Pruebas manuales

#### 1. Health Check del Inventory Service
```bash
curl http://localhost:8080/healthz
```

#### 2. Crear producto a través del validador
```bash
# Datos del producto
PRODUCT_DATA='{"sku":"TEST-001","name":"Producto Test","lot_number":"LOT123","expiration_date":"2025-12-31"}'

# Computar checksum
CHECKSUM=$(echo -n "$PRODUCT_DATA" | sha256sum | cut -d' ' -f1)

# Enviar petición
curl -X POST http://localhost:8081/ \
  -H "Content-Type: application/json" \
  -H "X-Message-Integrity: sha256=$CHECKSUM" \
  -d "$PRODUCT_DATA"
```

#### 3. Verificar producto creado
```bash
curl http://localhost:8080/inventory/products/TEST-001
```

## Arquitectura MVC en Docker

### Inventory Service
```
inventory-service/
├── app.py                 # Punto de entrada
├── models/
│   └── product_model.py   # Modelo de datos
├── controllers/
│   ├── product_controller.py
│   └── health_controller.py
└── views/
    └── response_view.py   # Formateo de respuestas
```

### Validador Service
```
cf-validador/
├── main.py               # Punto de entrada
├── models/
│   └── validation_model.py  # Lógica de validación
├── controllers/
│   └── validation_controller.py
└── views/
    └── response_view.py  # Formateo de respuestas
```

## Variables de Entorno

### Inventory Service
- `DATABASE_URL`: URL de conexión a PostgreSQL
- `PORT`: Puerto del servicio (8080)

### Validador Service
- `INVENTORY_BASE_URL`: URL del inventory service
- `CHECKSUM_ALGO`: Algoritmo de checksum (sha256)
- `CHECKSUM_HEADER`: Nombre del header de checksum
- `FORWARD_PATH`: Ruta para proxy
- `PORT`: Puerto del servicio (8081)

## Troubleshooting

### Problemas comunes

1. **Error de conexión a base de datos**
   - Verificar que PostgreSQL esté ejecutándose
   - Revisar logs: `docker-compose logs db`

2. **Error de importación en servicios**
   - Verificar que los Dockerfiles incluyan todas las carpetas MVC
   - Reconstruir imágenes: `docker-compose up --build`

3. **Error de validación de integridad**
   - Verificar que el checksum sea correcto
   - Asegurar que el JSON esté en formato canónico

4. **Servicios no se comunican**
   - Verificar que los nombres de contenedores coincidan
   - Revisar la configuración de red en docker-compose

### Comandos de diagnóstico

```bash
# Ver estado de contenedores
docker-compose ps

# Ver logs de errores
docker-compose logs --tail=50

# Entrar a un contenedor
docker-compose exec inventory bash
docker-compose exec validador bash

# Verificar conectividad de red
docker-compose exec validador ping inventory
```

## Monitoreo

### Health Checks
- **Database**: `pg_isready` cada 5 segundos
- **Inventory**: Endpoint `/healthz`
- **Validador**: Verificar logs de functions-framework

### Métricas útiles
- Tiempo de respuesta de validación
- Tasa de éxito de validación
- Uso de memoria de contenedores
- Conectividad entre servicios
