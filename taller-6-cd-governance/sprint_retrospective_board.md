# Guía Oficial y Dinámica: Sprint Retrospective en Flujo Continuo

**Módulo:** Taller 6 - Inspección del Flujo de Valor, Salud del Pipeline y Disciplina TBD  
**Facilitador:** Agile Coach / Scrum Master / Tech Lead  
**Formato de Tablero:** Plantilla Miro para Equipos de Alto Rendimiento CD  
**Fecha:** 2026-10-24  

---

## 1. El Nuevo Enfoque de la Sprint Retrospective

En Continuous Deployment, la Retrospectiva deja de ser una conversación general sobre sentimientos o relaciones personales y se transforma en una **auditoría objetiva y técnica del sistema de entrega**. 

Los tres pilares de inspección obligatoria son:
1. **Salud del Pipeline de CI/CD** (Estabilidad, velocidad de feedback y confiabilidad).
2. **Disciplina de Trunk-Based Development (TBD)** (Frecuencia de integración, tamaño de batches y longevidad de ramas).
3. **Flujo de Valor Real** (Lead Time, Cycle Time y eliminación de desperdicios en producción).

---

## 2. Métricas Reales del Sprint Analizado (Caso "Pagos Express")

Antes de abrir el tablero de discusión en Miro, el facilitador presenta el panel de telemetría del sprint:

```text
+----------------------------------------------------------------------------------------------------+
|                         PANEL DE SALUD DEL PIPELINE Y DISCIPLINA TBD                                |
+----------------------------------------------------------------------------------------------------+
| Métrica                                | Valor Real del Sprint     | Meta / Benchmark TBD          |
+----------------------------------------------------------------------------------------------------+
| Integraciones diarias a main           | 4 integraciones en 10 días | >= 3 integraciones POR DÍA    |
| Longevidad promedio de ramas (PR life) | 3.5 días (Máx: 4 días)    | < 24 horas (Same-day merge)   |
| CI Failure Rate (Tests en rojo)        | 38% de los builds         | < 5% de fallos                |
| Causa raíz de fallos de CI             | 1 Test Flaky recurrente   | 0 tolerancia a tests flaky    |
| Tiempo promedio de Deploy a Render     | 4.2 minutos               | < 10 minutos                  |
| Incidentes en Producción               | 1 fallo health check (11m)| 0 fallos con auto-rollback    |
| Toggles activos sin retirar (>30 días) | 3 toggles obsoletos       | 0 toggles expirados           |
| Lead Time for Changes                  | 9 días (Pagos Express)    | < 2 días                      |
+----------------------------------------------------------------------------------------------------+
```

---

## 3. Tablero de Retrospectiva (Estructura Miro)

El equipo utiliza 4 cuadrantes claramente delimitados para plasmar post-its con observaciones reales:

```text
+-----------------------------------+-----------------------------------+
|  🟢 LO QUE FUNCIONÓ BIEN          |  🟡 LO QUE GENERÓ FRICCIÓN        |
|  - El auto-deploy a Render        |  - Esperar 4 días con una rama    |
|    funciona de forma transparente.|    abierta por culpa del CI.      |
|  - ConfigCat permitió desplegar   |  - Presión comercial para activar |
|    código a main sin exponerlo    |    en viernes sin telemetría.     |
|    antes de tiempo.               |  - No saber si los 3 toggles      |
|  - El DoD técnico garantizó que   |    viejos aún se usan en el       |
|    la funcionalidad tuviera tests |    frontend o si son código       |
|    unitarios completos.           |    muerto.                        |
+-----------------------------------+-----------------------------------+
|  🔴 LO QUE ROMPIÓ EL FLUJO / MIEDO|  🚀 ACCIONES DE MEJORA (MÁXIMO 3) |
|  - El fallo de 11 minutos del     |  1. Cuarentena y erradicación del |
|    health check que requirió      |     test flaky en el CI.          |
|    rollback manual a ciegas.      |  2. Dashboard de métricas y      |
|  - Cero observabilidad en pagos:  |     alertas antes de activar      |
|    nadie se atreve a prender el   |     'pagos-express-v1'.           |
|    toggle porque no sabríamos si  |  3. Política y sprint de limpieza |
|    está cobrando bien o mal.      |     de Feature Toggles obsoletos. |
+-----------------------------------+-----------------------------------+
```

---

## 4. Discusión Profunda de las Preguntas Guía del Facilitador

### 1. ¿Qué nos impidió integrar más veces a `main`?
* **Respuesta del Equipo:** *"El test flaky en la suite de integración de pagos. Cada vez que hacíamos push a una rama pequeña, el CI fallaba de manera intermitente. Como los desarrolladores no confiaban en el CI, acumularon código localmente durante 4 días para correr las pruebas manualmente en lugar de integrar por pequeños trozos (small batches)."*

### 2. ¿El auto-deploy nos dio más confianza o más miedo?
* **Respuesta del Equipo:** *"Al principio generó miedo tras el incidente del health check caído durante 11 minutos. La falta de un rollback automático configurado en Render provocó angustia. Sin embargo, aprendimos que el problema no es el auto-deploy, sino la falta de sondas liveness/readiness inteligentes y la falta de observabilidad antes de encender los toggles."*

### 3. ¿Los Feature Toggles nos ayudaron o se volvieron deuda?
* **Respuesta del Equipo:** *"Ambas cosas. Nos ayudaron enormemente a integrar Pagos Express a `main` hace 9 días sin interrumpir la operación actual. Pero se volvieron deuda técnica peligrosa con los 3 toggles que llevan más de 45 días sin retirar. Tenemos código lleno de `if (toggle)` anidados que nadie se atreve a borrar."*

### 4. ¿El DoD (Definition of Done) se respetó realmente?
* **Respuesta del Equipo:** *"Se respetó el DoD a nivel de código y tests unitarios, pero nuestro DoD actual tiene un vacío crítico: **no exige que una funcionalidad cuente con métricas de observabilidad en producción antes de considerarse Done**. Una historia no puede estar Done si no podemos monitorear su salud."*

---

## 5. Las 3 Acciones Concretas de Mejora Aprobadas (Regla de Oro: Máximo 3)

Para evitar planes de acción sobrecargados que nunca se cumplen, el equipo acordó por consenso estricto enfocar el 100% de la energía de mejora en estas 3 acciones con responsables y fechas límite:

### Acción 1: Política de Tolerancia Cero a Tests Flaky y Estabilización de CI
* **Problema que resuelve:** La rama de 4 días y la caída a solo 4 integraciones en el sprint.
* **Solución Técnica:**
  * Cuarentena inmediata del test intermitente de pagos (mover a suite `quarantined_tests` que corre en background sin bloquear el pipeline).
  * Refactorización del test eliminando esperas arbitrarias (`sleep`) y usando aserciones asíncronas basadas en eventos.
* **Responsable:** Tech Lead / Senior Dev.
* **Criterio de Éxito:** CI en verde con tiempo de ejecución < 3 minutos y 0 fallos falsos positivos durante 7 días consecutivos.

---

### Acción 2: Instrumentación de Observabilidad y Dashboard para Pagos Express
* **Problema que resuelve:** El miedo a activar el toggle y la ceguera de negocio.
* **Solución Técnica:**
  * Implementar telemetría con métricas de contador y latencia: `payment_express_attempts_total`, `payment_express_success_total`, `payment_express_errors_total` y `payment_express_latency_ms`.
  * Configurar dashboard en vivo y alerta PagerDuty si `errors / total > 1.5%`.
* **Responsable:** Backend Engineer & DevOps.
* **Criterio de Éxito:** Dashboard visible con datos en tiempo real antes de iniciar la Fase 1 del Canary Rollout el lunes.

---

### Acción 3: Saneamiento de Deuda Técnica de Toggles y Protocolo de TTL
* **Problema que resuelve:** Los 3 toggles obsoletos de más de 45 días en ConfigCat.
* **Solución Técnica:**
  * Auditoría en ConfigCat: Retirar los 2 toggles que ya están al 100% para todos los usuarios, eliminando los bloques `if/else` del código.
  * Modificar el DoD en el Playbook para exigir que todo nuevo toggle incluya una fecha de expiración (TTL máximo: 14 días tras el 100% de rollout).
* **Responsable:** Equipo completo de Desarrollo (Asignación en el próximo refinamiento).
* **Criterio de Éxito:** 0 toggles con más de 30 días en ConfigCat y reducción de 150 líneas de código muerto.
