# Guía Oficial y Simulación: Sprint Review en Continuous Deployment

**Módulo:** Taller 6 - Ceremonias Ágiles Adaptadas a CD y Trunk-Based Development  
**Audiencia:** Product Owners, Tech Leads, Desarrolladores y Stakeholders  
**Fecha:** 2026-10-24  

---

## 1. Principios del Nuevo Sprint Review (CD + TBD)

En un entorno de **Continuous Deployment (CD)** y **Trunk-Based Development (TBD)**, el código se integra a `main` múltiples veces al día y se despliega automáticamente a producción (Render) protegido por **Feature Toggles (ConfigCat)**. 

Por lo tanto, el Sprint Review ya **no es un evento de aceptación de código ni una ceremonia de aprobación de pase a producción**. Es una **sesión de inspección de valor entregado y retroalimentación estratégica sobre el producto real**.

### Matriz Comparativa: Review Clásico vs. Review en CD + TBD

| Dimensión | Review Clásico (Scrum Tradicional) | Review en CD + TBD (Flujo Moderno) |
| :--- | :--- | :--- |
| **Objeto de la Demo** | Demostración del incremento acumulado en ramas de desarrollo o ambiente local/staging. | Demostración de funcionalidades que **ya están en producción** (activas o detrás de toggle). |
| **Modalidad de Entrega** | "Todo o nada" al final del sprint (alto riesgo de sorpresas). | Entrega incremental continua protegida por Feature Toggles. |
| **Ciclo de Feedback** | Feedback tardío (15 o 30 días después de concebir la idea). | Feedback continuo en producción con datos reales y telemetría de usuarios. |
| **Foco de la Conversación** | "¿Qué construimos técnicamente en las últimas 2 semanas?" | "¿Qué valor recibieron los usuarios y qué métricas se movieron?" |
| **Rol de los Stakeholders** | Evaluar si el equipo "cumplió con los requerimientos". | Colaborar sobre el impacto comercial y decidir los siguientes pasos de activación. |
| **Manejo de Imprevistos** | Bloquear el despliegue de todo el sprint si algo falla. | Desactivar el toggle del feature problemático sin retrasar el resto del valor. |

---

## 2. Estructura Obligatoria de la Demo (Timebox: 4-5 minutos por ítem)

Cada ítem presentado durante el Sprint Review debe seguir estrictamente este formato de 5 pasos:

```text
+-----------------------------------------------------------------------------------------+
|                  ESTRUCTURA ESTÁNDAR DE DEMO DE VALOR (MÁX. 5 MINUTOS)                  |
+-----------------------------------------------------------------------------------------+
| 1. ¿Qué problema de usuario resuelve? (Contexto de dolor y valor esperado)              |
| 2. ¿Cuál es su estado de liberación? (100% público, detrás de Feature Toggle, Canary %) |
| 3. Demo en Vivo en Producción (Render) mostrando interacción real y Toggle ON/OFF       |
| 4. Evidencia de Valor y Métricas (Conversión, errores, tiempos de respuesta)            |
| 5. Pregunta Clave al Stakeholder/PO: "¿Esto genera el valor esperado?"                   |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Simulación en Vivo del Sprint Review (Guión Práctico)

### Roles Asignados
* **Developer (Demo Técnica):** Presenta el flujo en vivo en la aplicación de producción y manipula los toggles en ConfigCat.
* **Product Owner (Facilitador de Negocio):** Contextualiza el impacto en el negocio, modera el debate y captura feedback.
* **Stakeholder de Negocio / Operaciones:** Evalúa la usabilidad, formula preguntas comerciales y valida prioridades.
* **Observadores (Resto del Equipo):** Toman nota de fricciones en el flujo y aspectos a pulir en la Retrospectiva.

---

### Incremento 1: "Pagos Express con un solo clic" (Caso Crítico)

* **Tiempo asignado:** 5 minutos.
* **Estado:** En `main`, desplegado en Render, protegido por toggle `pagos-express-v1` en ConfigCat (0% público general, activo para usuarios internos).

#### Desarrollo de la Demostración:
1. **Problema del usuario (PO):**  
   *"Los usuarios que reservan salas de coworking recurrentemente abandonaban el proceso en un 28% debido a la fricción de reingresar datos bancarios y pasar por 3 pantallas de confirmación."*
2. **Estado de liberación (Developer):**  
   *"El código está integrado en `main` y desplegado en Render. Está protegido por el toggle `pagos-express-v1`. Cumple DoD técnico, pero por seguridad ante la falta de métricas previas está activo únicamente para el equipo interno."*
3. **Demo en vivo en Render y ConfigCat (Developer):**  
   * *Demostración con Toggle OFF (Vista de usuario general):* El Developer realiza una reserva; se observa el flujo clásico de 3 pasos.  
   * *Activación en vivo en ConfigCat:* El Developer añade una regla de segmentación para la cuenta de demostración (`qa-demo@coworking.com`). En menos de 10 segundos, recarga la aplicación en Render.  
   * *Demostración con Toggle ON:* Al pulsar "Reservar Sala Alpha", el botón cambia a "Pagar con 1-Clic ($25.00)". Se ejecuta la transacción y se emite la confirmación instantáneamente sin recargar la página.  
4. **Métricas y Evidencia (PO & Dev):**  
   *"Durante las pruebas internas de hoy, el tiempo de reserva disminuyó de 85 segundos a 4 segundos. El plan de liberación canary comenzará el lunes al 10% con dashboard de observabilidad en vivo."*
5. **Pregunta al Stakeholder (PO):**  
   *"¿Considera que esta experiencia de 1-clic reduce la fricción esperada para los clientes frecuentes?"*  
   * **Respuesta del Stakeholder:** *"La experiencia es excelente y muy limpia. Apoyo la decisión de no activar al 20% el viernes sin métricas; prefiero que iniciemos el lunes al 10% con observabilidad total."*

---

### Incremento 2: "Filtro Dinámico de Salas por Equipamiento"

* **Tiempo asignado:** 4 minutos.
* **Estado:** 100% activo en producción (desplegado hace 5 días).

#### Desarrollo de la Demostración:
1. **Problema del usuario (PO):**  
   *"Los clientes corporativos perdían tiempo buscando salas con proyector 4K o cabinas acústicas para videoconferencias."*
2. **Estado de liberación (Developer):**  
   *"Desplegado hace 5 días directo a `main`. Sin toggle (funcionalidad no riesgosa que cumplió DoD y tests E2E)."*
3. **Demo en vivo (Developer):**  
   * Demostración en la interfaz de catálogo de Render: Selecciona los chips "Proyector 4K" + "Capacidad > 6 personas". La lista filtra de inmediato sin latencia visual.
4. **Métricas de Valor (PO):**  
   *"En los últimos 5 días, el 62% de las reservas exitosas utilizaron al menos un filtro. El tiempo promedio de selección de sala bajó de 3.2 minutos a 48 segundos."*
5. **Pregunta al Stakeholder:**  
   *"¿El orden de los filtros responde a las salas más demandadas por los clientes B2B?"*

---

### Incremento 3: "Notificaciones Asíncronas de Cancelación vía EventBridge"

* **Tiempo asignado:** 4 minutos.
* **Estado:** Arquitectura Serverless Event-Driven (Canary 10%).

#### Desarrollo de la Demostración:
1. **Problema del usuario (PO):**  
   *"Cuando una sala se desocupaba anticipadamente, los usuarios en lista de espera tardaban hasta 2 horas en enterarse."*
2. **Estado de liberación (Developer):**  
   *"Conectado al bus de EventBridge y a la cola SQS implementados en la Parte 2 del proyecto."*
3. **Demo en vivo (Developer):**  
   * Desde `catalog-service`, se libera la "Sala Creativa Alpha". En menos de 800 ms, la Lambda consumidora procesa el evento desde SQS y actualiza el estado visible para los usuarios.
4. **Métricas de Valor:**  
   *"El 100% de los eventos de cambio de sala se procesaron en menos de 1.2 segundos sin impacto en la CPU del API Gateway."*
5. **Feedback y cierre:** Validado satisfactoriamente por el equipo.

---

## 4. Acuerdos y Formato Institucional Acordado

Como resultado de esta simulación, el equipo aprueba formalmente las siguientes reglas para todos los futuros Sprint Reviews:
1. **Prohibido hacer demos en `localhost`:** Toda demostración debe ejecutarse en el entorno desplegado en Render o Cloud con datos reales o sanitizados.
2. **Manipulación de Toggles en vivo:** Se debe demostrar el comportamiento de la aplicación tanto con el toggle en ON como en OFF para verificar la degradación elegante.
3. **Datos de telemetría obligatorios:** Ningún feature con más de 48 horas en producción puede presentarse sin al menos una métrica de uso o rendimiento.
