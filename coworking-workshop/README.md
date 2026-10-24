# Coworking Space - Arquitectura de Microservicios y Chaos Engineering

Este módulo contiene la implementación completa de los **Laboratorios 1 al 5** del diplomado, enfocados en el diseño, orquestación, resiliencia y pruebas de caos en sistemas distribuidos con Python y FastAPI.

---

## 🏛️ Arquitectura del Sistema

```text
+-----------------------+                    +-----------------------+
|    catalog-service    | <--- HTTP:8001 --- |    orders-service     |
|       (FastAPI)       |                    |       (FastAPI)       |
|      Puerto: 8001     |                    |      Puerto: 8002     |
+-----------------------+                    +-----------------------+
            |                                            |
            +-------------------+------------------------+
                                |
                    +-----------------------+
                    |     Docker Network    |
                    | (coworking-network)   |
                    +-----------------------+
```

El sistema consta de:
1. **`catalog-service` (Puerto 8001):** Gestiona los espacios de coworking disponibles, precios por hora, capacidades y ubicaciones.
2. **`orders-service` (Puerto 8002):** Maneja las órdenes de reserva de los usuarios. Antes de confirmar una reserva, consulta de forma síncrona vía HTTP al catálogo para validar existencia, disponibilidad y tarifas.
3. **`coworking-network`:** Red interna Docker puente que permite la resolución de nombres DNS (`http://catalog-service:8001`).

---

## 📁 Estructura del Repositorio

```text
coworking-workshop/
├── README.md                           # Documentación técnica completa
├── docker-compose.yml                  # Orquestación de contenedores y red
├── chaos-test.sh                       # Script Bash para prueba de Caos (LAB 4)
├── chaos-test.ps1                      # Script PowerShell para Windows (LAB 4)
├── chaos-report.md                     # Informe técnico de resiliencia y lecciones aprendidas
├── architecture-diagram.png            # Diagrama de arquitectura del sistema
├── coworking.postman_collection.json   # Colección Postman con tests automáticos
├── catalog-service/
│   ├── main.py                         # API FastAPI del catálogo
│   ├── requirements.txt                # Dependencias (FastAPI, Uvicorn, Pydantic)
│   └── Dockerfile                      # Imagen de contenedor Python 3.11-slim
└── orders-service/
    ├── main.py                         # API FastAPI de órdenes con cliente HTTP
    ├── requirements.txt                # Dependencias (FastAPI, Uvicorn, HTTPX)
    └── Dockerfile                      # Imagen de contenedor Python 3.11-slim
```

---

## 🚀 Guía de Ejecución

### Opción A: Orquestación con Docker Compose (Recomendada)

1. **Construir y levantar ambos servicios:**
   ```bash
   docker-compose up --build
   ```
   *(Para ejecutar en segundo plano agrega la bandera `-d`)*

2. **Probar el flujo completo en otra terminal:**
   * **Paso 1: Ver espacios disponibles en el catálogo:**
     ```bash
     curl http://localhost:8001/spaces
     ```
   * **Paso 2: Consultar un espacio específico (ID: 1):**
     ```bash
     curl http://localhost:8001/spaces/1
     ```
   * **Paso 3: Crear una reserva (orders-service consulta internamente a catalog-service):**
     ```bash
     curl -X POST "http://localhost:8002/orders?space_id=1&user_email=test@example.com&hours=2"
     ```
   * **Paso 4: Listar todas las reservas realizadas:**
     ```bash
     curl http://localhost:8002/orders
     ```

---

### Opción B: Ejecución Local Directa con Python

Si prefieres ejecutar sin Docker:

1. **Levantar `catalog-service` (Terminal 1):**
   ```bash
   cd catalog-service
   pip install -r requirements.txt
   python main.py
   ```
   *Estará disponible en:* `http://localhost:8001` (Documentación Swagger en `http://localhost:8001/docs`)

2. **Levantar `orders-service` (Terminal 2):**
   ```bash
   cd orders-service
   pip install -r requirements.txt
   python main.py
   ```
   *Estará disponible en:* `http://localhost:8002` (Documentación Swagger en `http://localhost:8002/docs`)

---

## 💥 Laboratorios de Chaos Engineering

### LAB 4: Apagar el Catálogo (Caída de Servicio Dependiente)

Evalúa cómo reacciona `orders-service` cuando su dependencia síncrona deja de responder.

* **En Linux / macOS / Git Bash:**
  ```bash
  chmod +x chaos-test.sh
  ./chaos-test.sh
  ```

* **En Windows (PowerShell):**
  ```powershell
  .\chaos-test.ps1
  ```

**Resultados esperados:**
* **Con catálogo activo:** Petición responde `HTTP 201 Created` con el ID de orden y cálculo de tarifa.
* **Con catálogo caído (`docker-compose stop catalog-service`):** `orders-service` intercepta el fallo de conexión y responde `HTTP 503 Service Unavailable` con `{"detail": "Catalog service unavailable"}`.
* **Tras reiniciar el catálogo (`docker-compose start catalog-service`):** El sistema se auto-recupera de inmediato sin requerir reinicio del servicio de órdenes.

---

### LAB 5: Romper el Contrato sin Avisar

Simula el escenario donde `catalog-service` renombra unilateralmente el campo `price_per_hour` por `hourly_rate`.

1. **Activar simulación de contrato roto:**
   * En `catalog-service/main.py`, la variable `BREAK_CONTRACT` o el parámetro de consulta `break_contract=true` permite simular este fallo directamente.
   * O en `docker-compose.yml`, configurar en `catalog-service`:
     ```yaml
     environment:
       - BREAK_CONTRACT=true
     ```
   * Reconstruir:
     ```bash
     docker-compose up --build -d
     ```

2. **Ejecutar petición de orden:**
   ```bash
   curl -X POST "http://localhost:8002/orders?space_id=1&user_email=contract@test.com&hours=2"
   ```

3. **Resultado:**
   Respuesta `HTTP 500` con `Contract Violation Error`: El servicio de órdenes esperaba `price_per_hour` pero recibió `hourly_rate`.
   
4. **Informe Técnico:** Consulta el análisis de causa raíz y soluciones de arquitectura en [`chaos-report.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/coworking-workshop/chaos-report.md).

---

## 🛠️ Comandos de Debugging Útiles

```bash
# Ver logs en tiempo real de todos los servicios
docker-compose logs -f

# Ver logs de un servicio en particular
docker-compose logs -f orders-service

# Ver estado de los contenedores y puertos
docker-compose ps

# Entrar al shell de un contenedor en ejecución
docker-compose exec orders-service bash

# Inspeccionar la red Docker compartida
docker network inspect coworking_coworking-network

# Probar conectividad y resolución DNS entre contenedores
docker-compose exec orders-service ping catalog-service

# Reconstruir imágenes limpiando caché
docker-compose build --no-cache
```
