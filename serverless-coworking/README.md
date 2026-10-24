# Arquitectura Serverless Event-Driven: Migración a AWS Lambda y EventBridge

Este módulo corresponde a la **Parte 2 (Clase 3: Serverless - Migración Event-Driven)** del diplomado.

---

## 🏛️ Diagrama de Arquitectura Serverless

```text
[Cliente HTTP]
       |
       v
+-------------------------------+
|  API Gateway (/catalog/spaces) |
+-------------------------------+
       | (HTTP Proxy)
       v
+-------------------------------+
|     Lambda catalog-fn         |
|  (lambda-catalog/handler.py)  |
+-------------------------------+
       | (events:PutEvents)
       v
+-------------------------------+
|   EventBridge Event Bus       |
|    (Rule: SpaceChanged)       |
+-------------------------------+
       | (Enrutamiento por patrón)
       v
+-------------------------------+
|       SQS Queue               |
|    (catalog-events-queue)     |  ---> [ Dead Letter Queue (DLQ) ]
+-------------------------------+
       | (Batch SQS Trigger)
       v
+-------------------------------+
|     Lambda consumer-fn        |
|  (lambda-consumer/handler.py) |
+-------------------------------+
       | (Webhook / Sincronización)
       v
+-------------------------------+
|   orders-service / DB / Logs  |
+-------------------------------+
```

---

## 🎯 Objetivos Técnicos Cumplidos

1. **LAB 6: `catalog-service` Serverless con AWS Lambda & API Gateway:**
   * Sustitución del contenedor FastAPI por una función Lambda ligera en Python 3.11 (`lambda-catalog/handler.py`).
   * Desacoplamiento de la disponibilidad: Cuando la disponibilidad de una sala cambia, la función ya no espera síncronamente a los consumidores; en su lugar, emite un evento a **Amazon EventBridge**.

2. **LAB 7: Consumidor Asíncrono Reactivo con SQS:**
   * Implementación de `lambda-consumer/handler.py` que consume lotes de mensajes de **Amazon SQS** alimentados por EventBridge.
   * Manejo de idempotencia para evitar procesamientos duplicados ante reintentos de red.
   * Configuración de Dead Letter Queue (DLQ) para aislamiento de mensajes corruptos sin pérdida de datos.

3. **Infraestructura como Código con AWS SAM (`template.yaml`):**
   * Definición declarativa de toda la topología en la nube: API Gateway HTTP API v2, EventBus, Reglas de EventBridge, Colas SQS con Redrive Policy, Funciones Lambda y Políticas de IAM con privilegios mínimos.

---

## 📁 Estructura del Módulo

```text
serverless-coworking/
├── template.yaml               # Plantilla de Infraestructura como Código (AWS SAM)
├── README.md                   # Guía de arquitectura y operaciones
├── lambda-catalog/
│   ├── handler.py              # Función productora (API Gateway + EventBridge)
│   └── requirements.txt        # Dependencia boto3==1.34.0
├── lambda-consumer/
│   ├── handler.py              # Función consumidora (Procesamiento SQS por lotes)
│   └── requirements.txt        # Dependencias boto3 y urllib3
├── events/
│   ├── eventbridge_sample.json # Carga útil de evento EventBridge para pruebas
│   └── sqs_sample.json         # Carga útil de mensaje SQS para emulación local
└── tests/
    └── test_lambdas.py         # Pruebas unitarias automatizadas con mocking
```

---

## 🚀 Guía de Despliegue en AWS con SAM CLI

### 1. Prerrequisitos
* Python 3.11+
* Cuenta de AWS con credenciales configuradas (`aws configure`)
* AWS SAM CLI instalado:
  ```bash
  pip install aws-sam-cli
  ```

### 2. Construcción del Proyecto
Empaqueta las dependencias y el código fuente de cada función Lambda:
```bash
sam build
```

### 3. Despliegue Guiado (Primera vez)
Despliega el stack de CloudFormation de forma interactiva:
```bash
sam deploy --guided
```
* Parámetros recomendados durante el asistente:
  * **Stack Name:** `coworking-serverless-dev`
  * **AWS Region:** `us-east-1` (o tu región de preferencia)
  * **Parameter EnvironmentName:** `dev`
  * **Confirm changes before deploy:** `Y`
  * **Allow SAM CLI IAM role creation:** `Y`
  * **Save arguments to configuration file:** `Y`

### 4. Despliegues Posteriores
Para actualizar la infraestructura tras cambios en el código:
```bash
sam deploy
```

---

## 🧪 Pruebas Locales (Sin Costo en AWS)

### A. Ejecución de Pruebas Unitarias
Ejecuta la suite de pruebas unitarias que simula EventBridge y SQS:
```bash
python -m unittest serverless-coworking/tests/test_lambdas.py -v
```

### B. Emulación Local con AWS SAM CLI
Puedes invocar las funciones localmente usando los eventos de prueba incluidos en la carpeta `events/`:

1. **Invocar localmente la Lambda Consumidora con un evento SQS simulado:**
   ```bash
   sam local invoke ConsumerFunction -e events/sqs_sample.json
   ```

2. **Levantar localmente la API HTTP de API Gateway:**
   ```bash
   sam local start-api --port 3000
   ```
   *Luego prueba en otra terminal:*
   ```bash
   curl http://localhost:3000/spaces
   curl -X PATCH http://localhost:3000/spaces/1/availability -H "Content-Type: application/json" -d '{"available": false}'
   ```
