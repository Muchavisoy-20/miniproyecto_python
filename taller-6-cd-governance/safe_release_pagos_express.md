# Estrategia de Liberación Segura de Valor: Caso "Pagos Express"

**Caso de Estudio:** *“La funcionalidad de ‘Pagos Express’ ya está en main, pero nadie se atreve a activarla”*  
**Rol:** Senior Software Engineer / Tech Lead  
**Taller:** Taller 6 - Continuous Deployment, Feature Toggles & Safe Release  
**Fecha:** 2026-10-24  

---

## 1. Diagnóstico de la Situación Actual y Análisis de Riesgos

El equipo se encuentra ante un dilema clásico en organizaciones en transición hacia Continuous Deployment: **el código está en `main` y desplegado en producción (Render), pero el riesgo percibido paraliza la entrega de valor.**

### Evaluación de los Hechos Problemáticos

| Hecho Reportado | Diagnóstico Técnico de Causa Raíz | Nivel de Riesgo | Impacto Inmediato |
| :--- | :--- | :--- | :--- |
| **PO exige activar al 20% el viernes por campaña de marketing** | Presión externa sin validación técnica previa. Lanzar en viernes (*Friday Deploy*) sin observabilidad es una violación de las mejores prácticas operativas. | 🔴 **CRÍTICO** | Alta probabilidad de degradación de ingresos durante el fin de semana sin soporte activo. |
| **Último deploy falló health check 11 min (rollback manual)** | Pipeline inmaduro: falta de *Automated Rollback* en Render y fallas de arranque o sondas mal configuradas. | 🔴 **CRÍTICO** | Desconfianza del equipo en el auto-deploy y estrés operacional. |
| **3 Feature Toggles llevan > 45 días activos sin limpiar** | Ausencia de gobernanza y ciclo de vida de banderas (*Toggle Debt*). El código acumula bifurcaciones obsoletas y complejidad cognitiva. | 🟡 **MEDIO** | Posibles efectos colaterales de interacción entre banderas (*toggle interaction bugs*). |
| **Solo 4 integraciones a main en el sprint (lejos de TBD)** | Los desarrolladores están acumulando trabajo localmente por miedo al CI en rojo o historias demasiado grandes. | 🔴 **ALTO** | Incrementos masivos (*big bangs*), mayor probabilidad de conflictos de integración. |
| **Rama viva 4 días por test flaky en CI** | Deuda técnica en la suite de pruebas automatizadas. Un test inestable destruye la confianza en el pipeline. | 🔴 **ALTO** | El equipo elude el flujo continuo y ralentiza el Lead Time de 1 día a casi una semana. |
| **Cero métricas de conversión o errores de pago** | Ceguera operativa. Activar el toggle es como "volar a ciegas en una tormenta". | 🔴 **CRÍTICO** | Si los pagos fallan silenciosamente, el negocio pierde dinero y usuarios sin darse cuenta. |
| **Stakeholder anunció "Pagos Express ya está listo"** | Desalineación de expectativas entre "desplegado a main" vs "liberado al usuario". | 🟡 **MEDIO** | Tensión política y presión innecesaria sobre el equipo técnico. |

---

## 2. Negociación y Respuesta Profesional al Product Owner y Marketing

Como Tech Lead, la postura ante la solicitud del PO de activar el 20% el viernes es: **"NO al 20% indiscriminado el viernes; SÍ a una liberación controlada por fases con observabilidad garantizada."**

### Mensaje Formal al PO y Stakeholders de Negocio:
> *"Entendemos el compromiso de marketing y la importancia estratégica de Pagos Express. Sin embargo, activar la pasarela de pagos al 20% sin telemetría de transacciones ni telemetría de errores tras un fallo reciente de despliegue pone en riesgo directo la facturación total de la compañía durante el fin de semana.  
>  
> Proponemos el siguiente plan de liberación segura que protege los ingresos y permite cumplir los objetivos comerciales:*  
> 1. *Viernes mañana:* Activación interna (100% empleados y cuentas de prueba del equipo).  
> 2. *Viernes tarde:* Activación tipo Canary al **1%** de usuarios reales, monitoreado en tiempo real durante 2 horas. Si la tasa de error es < 0.1%, se mantiene.  
> 3. *Lunes 09:00 AM:* Escalamiento al **10%** y luego al **25%** con todo el equipo de guardia activo.  
> 4. *Si algo falla en cualquier momento:* El Feature Toggle en ConfigCat cuenta con Kill-Switch instantáneo que desactiva la función en 5 segundos sin requerir despliegue de código."*

---

## 3. Plan Técnico de Liberación Gradual (Phased Canary Rollout)

### Segmentación en ConfigCat

Se define la clave del toggle: `pagos_express_v1` (tipo: Boolean).

```text
[Regla 1: Entorno Interno / Allowlist]
Condición: Email termina en "@tuempresa.com" OR UserID en [lista_beta_testers]
Resultado: TRUE (100%)

[Regla 2: Despliegue Porcentual (Canary)]
Condición: Percentage rollout por UserID hash
  - Fase 0 (Viernes 10:00 AM): 0% público general
  - Fase 1 (Viernes 02:00 PM): 1% usuarios reales
  - Fase 2 (Lunes 10:00 AM): 10% usuarios reales
  - Fase 3 (Martes 10:00 AM): 50% usuarios reales
  - Fase 4 (Miércoles 02:00 PM): 100% General Availability (GA)

[Regla por Defecto (Fallback)]:
Resultado: FALSE (0%)
```

---

## 4. Cuadro de Mando de Observabilidad y SLIs/SLOs

Antes de activar el toggle, se instrumentan obligatoriamente las siguientes métricas en tiempo real:

```text
+-----------------------------------------------------------------------------------+
|                        DASHBOARD EN VIVO: PAGOS EXPRESS                           |
+-----------------------------------------------------------------------------------+
| SLI / Métrica                 | Umbral Normal (SLO)    | Alerta / Criterio Rollback|
+-----------------------------------------------------------------------------------+
| Tasa de Éxito de Transacción  | >= 99.5%               | < 98.0% en ventana de 5m  |
| Tasa de Errores HTTP 5xx/4xx  | < 0.2%                 | > 1.0% en 3m consecutivas |
| Latencia p95 de Checkout      | < 800 ms               | > 2000 ms                 |
| Tasa de Abandono de Checkout  | Baseline +/- 3%        | Incremento > 15%          |
| Webhook de Pasarela de Pago   | Confirmación en < 2s   | Timeout / Reintentos > 5% |
+-----------------------------------------------------------------------------------+
```

---

## 5. Criterios de Rollback Inmediato (Kill-Switch Automatizado)

El equipo no realiza rollbacks redesplegando código ni revirtiendo commits de git durante una emergencia de negocio. **El rollback se realiza cambiando el estado del Feature Toggle en ConfigCat.**

### Protocolo de Kill-Switch:
1. **Condición de Disparo:**
   * Tasa de error de checkout > 1.5% durante más de 3 minutos.
   * Caída de transacciones bancarias exitosas en más del 10% frente a la hora anterior.
   * Detección de doble cobro a cualquier usuario.
2. **Acción de Ejecución:**
   * El Tech Lead o Ingeniero de Guardia cambia el toggle `pagos_express_v1` a **OFF (0%)** en la consola de ConfigCat.
   * Las instancias en Render refrescan la configuración en menos de 30 segundos vía webhook/polling de ConfigCat.
   * La interfaz de usuario degrada limpiamente al flujo de pago clásico de 3 pasos sin errores visuales para el cliente.
3. **Post-Mortem:**
   * Convocatoria inmediata a sesión sin culpas (*Blameless Post-Mortem*).
   * Diagnóstico sobre logs estructurados con `correlation_id` de las transacciones fallidas.

---

## 6. Plan de Observación de las Próximas 24 - 48 Horas

* **T+0 a T+2h:** Monitoreo activo en canal de Slack `#war-room-pagos-express`. Dos ingenieros validan logs de transacciones, latencias y eventos de pasarela de pago.
* **T+2h a T+24h:** Guardias rotativas con alertas en PagerDuty / Opsgenie conectadas al umbral de errores HTTP 500 y excepciones no controladas.
* **T+24h a T+48h:** Revisión conjunta con Product Owner de métricas de negocio:
  * Número total de transacciones completadas con 1-clic.
  * Tasa de conversión vs flujo tradicional.
  * Incidencias reportadas a servicio al cliente.

---

## 7. Política de Ciclo de Vida y Limpieza de Feature Toggles (*Toggle Retirement*)

Para solucionar el problema de los 3 toggles que llevan más de 45 días activos y evitar que `pagos_express_v1` se convierta en deuda técnica:

1. **Fecha de Caducidad Obligatoria (TTL):**
   * Todo *Release Toggle* tiene un TTL máximo de **14 días** desde que alcanza el 100% en producción.
2. **Creación del Ticket de Limpieza al Momento de Crear el Toggle:**
   * Al crear la historia de usuario para el toggle, se crea en GitHub Projects la tarea hermana: `[TECH-DEBT] Retirar Feature Toggle 'pagos_express_v1' y eliminar código muerto`.
3. **Higiene Semanal en la Retrospectiva:**
   * El equipo revisa el inventario de toggles activos en ConfigCat. Todo toggle con más de 30 días al 100% bloquea el inicio de nuevos features hasta ser removido.
