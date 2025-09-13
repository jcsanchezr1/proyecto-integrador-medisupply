# Implementación del Patrón MVC

Este documento describe la implementación del patrón Model-View-Controller (MVC) en los componentes `cf-validador` e `inventory-service`.

## Arquitectura MVC Implementada

### cf-validador

```
cf-validador/
├── main.py                    # Punto de entrada de la aplicación
├── models/
│   ├── __init__.py
│   └── validation_model.py    # Lógica de validación y checksum
├── controllers/
│   ├── __init__.py
│   └── validation_controller.py # Controlador de validación y proxy
└── views/
    ├── __init__.py
    └── response_view.py       # Formateo de respuestas
```

**Modelos (Models):**
- `ValidationModel`: Maneja la lógica de validación, computación de checksum y verificación de integridad

**Controladores (Controllers):**
- `ValidationController`: Gestiona la lógica de negocio para validación y proxy hacia el servicio de inventario

**Vistas (Views):**
- `ResponseView`: Se encarga del formateo y serialización de las respuestas

### inventory-service

```
inventory-service/
├── app.py                     # Punto de entrada de la aplicación
├── models/
│   ├── __init__.py
│   └── product_model.py       # Modelo de datos y lógica de negocio
├── controllers/
│   ├── __init__.py
│   ├── product_controller.py  # Controlador de productos
│   └── health_controller.py   # Controlador de health checks
└── views/
    ├── __init__.py
    └── response_view.py       # Formateo de respuestas
```

**Modelos (Models):**
- `Product`: Modelo de datos para productos con métodos de validación y operaciones CRUD

**Controladores (Controllers):**
- `ProductController`: Gestiona las operaciones de productos (crear, actualizar, consultar)
- `HealthController`: Maneja las verificaciones de salud del servicio

**Vistas (Views):**
- `ResponseView`: Se encarga del formateo y serialización de las respuestas

## Beneficios de la Implementación MVC

1. **Separación de Responsabilidades**: Cada capa tiene una responsabilidad específica y bien definida
2. **Mantenibilidad**: El código es más fácil de mantener y modificar
3. **Testabilidad**: Cada componente puede ser probado de forma independiente
4. **Escalabilidad**: Facilita la adición de nuevas funcionalidades
5. **Reutilización**: Los componentes pueden ser reutilizados en diferentes contextos

## Flujo de Datos

1. **Request** → **Controller**: El controlador recibe la petición HTTP
2. **Controller** → **Model**: El controlador utiliza el modelo para procesar la lógica de negocio
3. **Model** → **Controller**: El modelo retorna los datos procesados al controlador
4. **Controller** → **View**: El controlador pasa los datos a la vista para formateo
5. **View** → **Response**: La vista formatea la respuesta y la retorna al cliente

## Endpoints Disponibles

### cf-validador
- `POST /` - Validación de integridad y proxy hacia inventory-service

### inventory-service
- `GET /healthz` - Health check del servicio
- `POST /inventory/products` - Crear o actualizar producto
- `GET /inventory/products/<sku>` - Obtener producto por SKU
- `GET /inventory/products` - Obtener todos los productos

## Consideraciones de Seguridad

- El `cf-validador` valida la integridad de los mensajes usando checksums SHA256
- El `inventory-service` requiere el header `X-Integrity-Validated: true` para procesar peticiones
- Se mantiene la validación de fechas de expiración para lotes de productos
