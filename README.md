# Diplomado en Arquitectura de Software, Cloud y Continuous Deployment

Este repositorio reúne el desarrollo profesional integral de los talleres y laboratorios prácticos del diplomado, abarcando desde microservicios contenerizados y pruebas de caos, hasta arquitecturas serverless orientadas a eventos y gobierno de despliegue continuo con Feature Flags.

---

## 🏛️ Mapa de Módulos y Entregables

```text
miniproyecto_python/
│
├── 🏢 coworking-workshop/              # PARTE 1: Microservicios & Chaos Engineering
│   ├── catalog-service/               # FastAPI en puerto 8001 + Dockerfile
│   ├── orders-service/                # FastAPI en puerto 8002 + Cliente HTTP + Dockerfile
│   ├── docker-compose.yml             # Red compartida y orquestación
│   ├── chaos-test.sh / .ps1           # Automatización de Caos (Apagado y auto-recuperación)
│   ├── chaos-report.md                # Informe técnico de resiliencia y contratos
│   ├── architecture-diagram.png       # Diagrama de arquitectura de red
│   ├── coworking.postman_collection   # Colección Postman con tests integrados
│   └── README.md                      # Guía completa de ejecución del Módulo 1
│
├── ☁️ serverless-coworking/            # PARTE 2: Migración Serverless Event-Driven
│   ├── lambda-catalog/                # Productor Lambda (API Gateway + EventBridge PutEvents)
│   ├── lambda-consumer/               # Consumidor Lambda reactivo desencadenado por SQS
│   ├── template.yaml                  # Infraestructura como Código (AWS SAM completa)
│   ├── events/                        # Payloads de prueba para EventBridge y SQS
│   ├── tests/test_lambdas.py          # Pruebas unitarias de las funciones Lambda
│   └── README.md                      # Guía de despliegue con SAM CLI y pruebas locales
│
├── 🚀 taller-6-cd-governance/         # TALLER 6: Continuous Deployment, TBD & Toggles
│   ├── SCRUM_TBD_PLAYBOOK_v3.md       # Playbook v3.0: Reglas TBD, DoD v3.0 y Fase 1 al 100%
│   ├── safe_release_pagos_express.md  # Estrategia de liberación para "Pagos Express"
│   ├── sprint_review_simulation.md    # Simulación del nuevo Sprint Review en CD
│   ├── sprint_retrospective_board.md  # Tablero Miro, métricas de pipeline y 3 acciones
│   ├── simulator/                     # Servicio interactivo de Feature Toggles y Kill-Switch
│   └── README.md                      # Resumen del Taller 6 y guía de pruebas
│
└── 📦 src/                            # Utilidades iniciales del repositorio
    ├── main.py, tests.py, requirements.txt, Dockerfile
```

---

## 🧭 Resumen de los Componentes Desarrollados

### 1. [Coworking Workshop (Parte 1)](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/coworking-workshop/README.md)
* **LAB 1:** `catalog-service` con FastAPI (`GET /spaces`, `GET /spaces/{id}`, `PATCH /availability`, `GET /health`).
* **LAB 2:** `orders-service` dependiente del catálogo con cálculo de tarifas y manejo defensivo de errores HTTP 503.
* **LAB 3:** Orquestación con `docker-compose.yml` en red interna puente `coworking-network`.
* **LAB 4:** Chaos Engineering inyectando caída de servicio y midiendo MTTR con `chaos-test.sh` / `chaos-test.ps1`.
* **LAB 5:** Chaos Engineering por rompimiento de contrato de API (`price_per_hour` -> `hourly_rate`), con análisis exhaustivo en [`chaos-report.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/coworking-workshop/chaos-report.md).

### 2. [Serverless Coworking (Parte 2)](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/serverless-coworking/README.md)
* **LAB 6:** Función AWS Lambda `catalog-fn` expuesta vía API Gateway HTTP API v2 que emite eventos de dominio `SpaceChanged` a **Amazon EventBridge**.
* **LAB 7:** Función AWS Lambda `consumer-fn` activada por **Amazon SQS** (con Dead Letter Queue DLQ) que consume lotes de eventos con soporte para idempotencia.
* **IaC con AWS SAM:** Topología completa declarada en [`template.yaml`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/serverless-coworking/template.yaml).
* **Pruebas:** Suite de tests unitarios [`test_lambdas.py`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/serverless-coworking/tests/test_lambdas.py) ejecutables localmente con 100% de éxito.

### 3. [Taller 6: Ceremonias y Liberación Segura en CD](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/README.md)
* **Caso Práctico:** *“La funcionalidad de ‘Pagos Express’ ya está en main, pero nadie se atreve a activarla”*.
* **Playbook v3.0:** Documento oficial [`SCRUM_TBD_PLAYBOOK_v3.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/SCRUM_TBD_PLAYBOOK_v3.md) con políticas de ramas efímeras (< 24h), TTL de Feature Toggles (14 días) y nuevo Definition of Done (DoD).
* **Estrategia Safe Release:** Plan Canary Rollout (Interno -> 1% -> 10% -> 50% -> 100%), cuadro de observabilidad y protocolo de Kill-Switch en ConfigCat en [`safe_release_pagos_express.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/safe_release_pagos_express.md).
* **Sprint Review:** Guión interactivo de demostración de valor en producción en [`sprint_review_simulation.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/sprint_review_simulation.md).
* **Sprint Retrospective:** Tablero de 4 cuadrantes Miro, auditoría de pipeline y las 3 acciones de mejora en [`sprint_retrospective_board.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/sprint_retrospective_board.md).
* **Simulador Funcional:** Microservicio interactivo [`feature_toggle_service.py`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/simulator/feature_toggle_service.py) con suite de pruebas pasando al 100%.

---

## ⚡ Comprobación Rápida de Pruebas Unitarias

```bash
# 1. Probar funciones Serverless (Módulo 2):
python serverless-coworking/tests/test_lambdas.py

# 2. Probar simulador de Feature Toggles y Kill-Switch (Módulo 3):
python taller-6-cd-governance/simulator/test_toggle_flow.py
```
