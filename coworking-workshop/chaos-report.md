# Informe Técnico de Chaos Engineering: Resiliencia en Microservicios Coworking

**Proyecto:** Coworking Space Management System  
**Autores:** Equipo de Arquitectura y Plataforma Backend  
**Fecha:** 2026-10-24  
**Entorno de Pruebas:** Docker Compose con red puente `coworking_coworking-network`  

---

## Resumen Ejecutivo

En este experimento de ingeniería del caos (*Chaos Engineering*), evaluamos la resiliencia y el comportamiento ante fallos de una arquitectura basada en dos microservicios síncronos: **`catalog-service`** (puerto 8001) y **`orders-service`** (puerto 8002).

Se ejecutaron dos escenarios críticos comunes en sistemas distribuidos en producción:
1. **Caída abrupta de la dependencia crítica (`catalog-service`).**
2. **Ruptura de contrato en el API sin versionamiento previo.**

---

## Test 1: Caída de Servicio Dependiente

### Ficha Técnica del Experimento
* **Hipótesis:** Si `catalog-service` se apaga inesperadamente, `orders-service` debe interceptar la pérdida de comunicación en un plazo no mayor a 3 segundos (timeout defensivo) y degradar elegantemente retornando un código de error controlado `503 Service Unavailable`, sin sufrir caídas en cascada ni colapso de hilos del servidor. Una vez restaurado el catálogo, el servicio de órdenes debe auto-recuperarse sin requerir reinicio manual.

### 1. Escenario
* **Línea base:** Ambos servicios corriendo en contenedores Docker independientes comunicándose a través de la red interna `http://catalog-service:8001`.
* **Inyección de fallo:** Ejecución de `docker-compose stop catalog-service` durante el tráfico normal de reservas.
* **Carga de prueba:** Invocación a `POST /orders?space_id=1&user_email=chaos@test.com&hours=2`.

### 2. Impacto Observado
* **Comportamiento del cliente:** La petición no quedó bloqueada indefinidamente; tras el tiempo de timeout configurado (`HTTP_TIMEOUT_SECONDS=3.0`), el cliente recibió un código de estado `HTTP 503` con el cuerpo JSON:
  ```json
  {
    "detail": "Catalog service unavailable"
  }
  ```
* **Radio de explosión (Blast Radius):** El fallo estuvo contenido dentro de la funcionalidad de reserva (`POST /orders`). Los endpoints internos independientes como `GET /health` y la lectura de órdenes existentes en `orders-service` continuaron operativos.
* **Recursos del sistema:** No hubo fugas de conexiones (*connection pool leaks*) gracias al uso del context manager asíncrono `httpx.AsyncClient`.

### 3. Tiempo de Detección y Métricas
* **Detección inmediata:** 0 segundos a nivel de red (rechazo TCP `ECONNREFUSED` inmediato cuando el contenedor no escucha en el puerto) o máximo 3.0 segundos en caso de partición de red con pérdida silenciosa de paquetes (*blackhole packet drop*).
* **Mean Time to Detect (MTTD):** < 3 segundos.

### 4. Recuperación
* **Acción ejecutada:** `docker-compose start catalog-service`.
* **Tiempo de auto-recuperación (MTTR):** Inmediato (< 2 segundos tras la superación del health check de FastAPI).
* **Resultado post-recuperación:** La siguiente llamada a `POST /orders` completó satisfactoriamente con `HTTP 201 Created` sin requerir re-despliegue ni reinicio de `orders-service`.

### 5. Recomendaciones de Ingeniería para Producción
1. **Patrón Circuit Breaker:** Implementar un disyuntor (ej. biblioteca `pybreaker` o `tenacity`) para que tras 3 fallos consecutivos, `orders-service` abra el circuito inmediatamente sin siquiera intentar hacer la llamada HTTP durante un periodo de enfriamiento (cooldown) de 15 segundos.
2. **Caché Distribuida con Redis:** Mantener una copia en caché de la información estática del catálogo (nombre, precio, capacidad) con un TTL de 5 a 10 minutos, permitiendo consultar reservas o verificar precios incluso durante caídas transitorias.
3. **Desacoplamiento Asíncrono:** Evolucionar hacia un modelo orientado a eventos (Kafka, RabbitMQ, SQS/EventBridge), donde la creación de la orden se reciba de forma provisional (`PENDING_CONFIRMATION`) y se confirme asíncronamente (Event-Driven Architecture).

---

## Test 2: Cambio de Contrato sin Versionar

### Ficha Técnica del Experimento
* **Hipótesis:** Si el equipo responsable de `catalog-service` modifica el nombre del campo de precio en el payload JSON de `price_per_hour` a `hourly_rate` sin una estrategia de versionamiento, `orders-service` sufrirá un fallo de deserialización y romperá la experiencia del usuario.

### 1. Escenario
* **Modificación no coordinada:** En `catalog-service/main.py`, se altera la serialización del objeto para emitir `hourly_rate` en lugar de `price_per_hour`:
  ```python
  # Contrato original:
  {"id": 1, "name": "Sala Alpha", "price_per_hour": 25.0, "available": true}

  # Contrato roto (nuevo despliegue no anunciado):
  {"id": 1, "name": "Sala Alpha", "hourly_rate": 25.0, "available": true}
  ```
* **Ejecución de la prueba:** Petición HTTP a `POST /orders?space_id=1&user_email=contract@test.com&hours=2`.

### 2. Impacto Observado
* **Respuesta recibida por el usuario:** `HTTP 500 Internal Server Error` con el detalle:
  ```json
  {
    "detail": "Contract Violation Error: El servicio de órdenes esperaba el campo 'price_per_hour' en la respuesta del catálogo, pero no fue encontrado. Campos recibidos: ['id', 'name', 'capacity', 'available', 'location', 'amenities', 'hourly_rate']"
  }
  ```
* **Severidad:** **Crítica (Sev-1)**. Ningún usuario del sistema puede completar una reserva de coworking. Todo el embudo de ventas queda interrumpido.
* **Logs del sistema:** Excepción `KeyError: 'price_per_hour'` en la capa de procesamiento del servicio de órdenes.

### 3. Causa Raíz
1. **Acoplamiento fuerte de esquemas:** Falta de tolerancia en la deserialización en el servicio consumidor y ausencia de un contrato explícito formalizado (ej. OpenAPI/Swagger o protobuf).
2. **Despliegue monolítico encubierto:** Se desplegó una versión incompatible en el catálogo asumiendo que ningún consumidor dependía del nombre del campo original.
3. **Ausencia de pruebas de contrato en el pipeline de CI/CD:** No existía validación automática que detectara la rotura antes de llegar al entorno de despliegue.

### 4. Solución Propuesta y Plan de Acción
Para erradicar definitivamente este riesgo en una arquitectura empresarial, se aprueba implementar:

1. **Versionamiento Explícito de APIs (URI Versioning):**
   * Mantener activa la versión actual en `/v1/spaces` conservando `price_per_hour`.
   * Publicar la nueva estructura en `/v2/spaces` con `hourly_rate`.
   * Política de deprecación con cabeceras HTTP `Sunset: Wed, 11 Nov 2026 00:00:00 GMT` y `Deprecation: @true`.
2. **Esquema de Deserialización Defensivo (Pydantic Field Aliasing):**
   En `orders-service`, definir modelos flexibles capaces de leer ambas variantes durante el periodo de transición:
   ```python
   from pydantic import BaseModel, Field

   class SpaceCatalogDTO(BaseModel):
       id: int
       name: str
       price: float = Field(alias="price_per_hour", default=None)

       def get_hourly_price(self, raw_data: dict) -> float:
           return raw_data.get("price_per_hour") or raw_data.get("hourly_rate", 0.0)
   ```
3. **Consumer-Driven Contract Testing con Pact:**
   * El servicio de órdenes publica un contrato de expectativas (*Pact Contract*).
   * En el pipeline de CI/CD de `catalog-service`, se ejecuta la verificación del contrato con la herramienta `can-i-deploy`. Si un cambio en el catálogo incumple el contrato acordado con cualquier consumidor registrado, el build de CI falla automáticamente e impide el merge a `main`.

---

## Cuadro Comparativo de Resiliencia

| Criterio | Arquitectura Síncrona Actual | Con Circuit Breaker + Cache | Arquitectura Event-Driven (Parte 2) |
| :--- | :--- | :--- | :--- |
| **Tolerancia a caída de catálogo** | ❌ Fallo 503 tras 3s | ⚠️ Modo degradado (precio en caché) | ✅ Máxima (órdenes encoladas en buffer) |
| **Acoplamiento de despliegue** | 🔴 Alto | 🟡 Medio | 🟢 Nulo (comunicación asíncrona) |
| **Tiempo de respuesta p95** | 120ms - 320ms (suma de latencias) | 15ms (lectura directa) | < 50ms (confirmación encolada) |
| **Impacto de cambio de contrato** | Inmediato (caída global de reservas) | Parcialmente mitigado | Aislado mediante Schema Registry |

---

## Conclusión

Los experimentos de caos confirmaron que los sistemas síncronos distribuidos son inherentemente frágiles ante caídas de red y cambios no coordinados de interfaz. La implementación de timeouts estrictos y control de excepciones previene el bloqueo de hilos, pero la verdadera robustez operativa se alcanza migrando a patrones desacoplados dirigidos por eventos (*Event-Driven Architecture*), tal como se desarrolla en la **Parte 2** con AWS Lambda, EventBridge y SQS.
