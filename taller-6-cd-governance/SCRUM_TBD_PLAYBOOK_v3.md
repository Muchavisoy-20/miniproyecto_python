# Scrum + Trunk-Based Development (TBD) Playbook

**Versión:** 3.0 (Edición Oficial para Continuous Deployment)  
**Estado:** Vigente y Aprobado por el Equipo de Ingeniería y Producto  
**Ámbito de Aplicación:** Todos los repositorios, microservicios y equipos de producto  
**Fecha de Publicación:** 2026-10-24  

---

## 1. Manifiesto y Visión de Entrega Continua

En nuestra organización, el software no se acumula en ramas de larga duración esperando un "día de despliegue". **Adoptamos Trunk-Based Development y Continuous Deployment como disciplina de ingeniería fundamental:**

1. **`main` es siempre desplegable a producción:** Todo commit en la rama principal debe pasar las pruebas automatizadas y considerarse apto para producción.
2. **Despliegues frecuentes y pequeños (Small Batches):** Preferimos 10 despliegues diarios de 20 líneas a 1 despliegue mensual de 2,000 líneas.
3. **Desacoplar Despliegue de Liberación (Deploy != Release):**
   * **Deploy:** Proceso técnico automatizado mediante el cual el código compilado se transfiere a los servidores de producción (Render / AWS).
   * **Release:** Decisión de negocio mediante la cual una funcionalidad se hace visible a los usuarios finales utilizando **Feature Toggles (ConfigCat)**.
4. **La observabilidad es parte del código:** No existe código listo sin telemetría, logs estructurados y métricas de negocio.

---

## 2. Reglas Operativas de Trunk-Based Development (TBD)

```text
               +--------------------------------------------+
               |  RAMA 'main' (Protegida, CI verde, Deploy) |
               +--------------------------------------------+
                 ^             ^               ^
                 | Merge < 24h | Merge < 24h   | Merge < 24h
                 |             |               |
           [feat/slice-1] [feat/slice-2] [fix/quick-bug]
```

### Reglas de Oro para Desarrolladores:
1. **Longevidad Máxima de Rama:** Ninguna rama de feature puede vivir más de **24 horas**. Si una historia requiere más tiempo, debe dividirse en cortes verticales (*vertical slicing*) e integrarse detrás de un Feature Toggle.
2. **Integración Diaria Obligatoria:** Todo desarrollador debe integrar código a `main` al menos **1 o 2 veces al día**.
3. **No Pull Requests Gigantes:** El tamaño máximo recomendado para un PR es de **200 a 300 líneas de código**. Los PRs pequeños se revisan en menos de 30 minutos y tienen un riesgo de regresión cercano a cero.
4. **Tolerancia Cero a Tests Flaky:** Si un test falla aleatoriamente en el pipeline de CI, se traslada de inmediato a cuarentena y se abre una tarea técnica prioritaria de corrección. Ningún PR se aprueba con CI en rojo.

---

## 3. Política de Feature Toggles y Gobernanza de Deuda Técnica

Para evitar que los Feature Toggles se conviertan en laberintos de código muerto, se establece la siguiente política institucional con **ConfigCat**:

### Tipos de Banderas y Límites de Vida (TTL):

| Tipo de Toggle | Propósito | Tiempo de Vida Máximo (TTL) | Responsable |
| :--- | :--- | :--- | :--- |
| **Release Toggle** (ej. `pagos_express_v1`) | Proteger código en desarrollo y habilitar Canary Rollouts graduales. | **14 días** tras alcanzar el 100% de despliegue. | Equipo de Desarrollo |
| **Experiment Toggle** (A/B Test) | Comparar hipótesis de negocio o conversión entre dos grupos. | **30 días** (hasta finalizar experimento). | Product Owner |
| **Operational Toggle** (Kill-Switch) | Degradar servicios o apagar integraciones ante emergencias externas. | **Permanente / Indefinido** (requiere revisión semestral). | Tech Lead / DevOps |

### Ciclo de Vida Obligatorio:
1. **Creación:** Al crear la clave en ConfigCat, se debe vincular al ticket de la funcionalidad en GitHub Projects.
2. **Defensa por Defecto:** Todo toggle debe evaluar a `false` (inactivo) si la conexión con ConfigCat falla.
3. **Ticket de Retiro Automático:** Al encender el toggle al 100% para todos los usuarios, se agenda en el sprint siguiente la tarea de refactorización para remover el condicional `if/else` y las claves en ConfigCat.
4. **Regla de Bloqueo:** El equipo no puede iniciar nuevas historias de negocio si tiene más de 2 *Release Toggles* con más de 30 días de antigüedad sin limpiar.

---

## 4. Nuevo Formato Oficial de Sprint Review (CD)

El Sprint Review se formaliza con los siguientes parámetros:
* **Frecuencia:** Fin de sprint (ej. quincenal) o bajo demanda ante hitos mayores.
* **Duración:** 45 a 60 minutos máximo.
* **Audiencia Obligatoria:** Product Owner, Desarrolladores, Tech Lead, Stakeholders y Clientes Piloto.
* **Prohibición Expresa:** Queda terminantemente prohibido hacer demostraciones en entornos locales (`localhost`). Todo se demuestra en el entorno de producción (Render).
* **Estructura Estándar de Demostración (4-5 min por ítem):**
  1. *Problema de Usuario* y valor de negocio esperado.
  2. *Estado de Liberación* (Producción general vs Detrás de Toggle en ConfigCat).
  3. *Demostración en Vivo en Render* mostrando el comportamiento con Toggle OFF y Toggle ON.
  4. *Evidencia y Telemetría* (datos reales de latencia, conversión o volumen de transacciones).
  5. *Pregunta de Cierre al Stakeholder:* "¿Esto resuelve el dolor del cliente?"

---

## 5. Nuevo Formato Oficial de Sprint Retrospective

La Retrospectiva se orienta a la inspección del sistema sociotécnico de entrega:
* **Duración:** 60 minutos.
* **Insumo Inicial Obligatorio:** Panel de métricas del sprint:
  * Número de integraciones diarias a `main`.
  * Tasa de fallo del CI y tiempo promedio de build.
  * Tiempo de despliegue promedio a Render y registro de incidentes de rollback.
  * Inventario y antigüedad de Feature Toggles activos.
* **Estructura del Tablero Miro:**
  * 🟢 **Lo que funcionó bien:** Prácticas a celebrar y mantener.
  * 🟡 **Lo que generó fricción:** Retrasos, esperas innecesarias o ambigüedades.
  * 🔴 **Lo que rompió el flujo:** Tests flaky, caídas en producción o deuda crítica.
  * 🚀 **Acciones de Mejora (Máximo 3):** Solamente se seleccionan hasta 3 compromisos de mejora, cada uno con un único responsable y una métrica de verificación medible.

---

## 6. Definition of Done (DoD) Versión 3.0

Una historia de usuario o incremento solo se considera **DONE** cuando cumple el 100% de la siguiente lista de verificación:

- [x] **Código y Calidad:**
  - [x] Código formateado y analizado sin advertencias con `ruff` o linters oficiales.
  - [x] Principios SOLID y Clean Architecture aplicados; sin duplicación de lógica.
- [x] **Pruebas Automatizadas:**
  - [x] Pruebas unitarias completas con cobertura >= 80%.
  - [x] Pruebas de integración para endpoints y servicios dependientes.
  - [x] Suite de CI ejecutada en verde en GitHub Actions sin reintentos manuales.
- [x] **Despliegue Continuo e Integración:**
  - [x] Rama integrada a `main` y eliminada en menos de 24 horas.
  - [x] Auto-deploy exitoso al entorno de producción en Render.
  - [x] Health check del servicio respondiendo `HTTP 200` de forma estable.
- [x] **Feature Toggles y Seguridad:**
  - [x] Si la funcionalidad es riesgosa o de negocio crítico, está protegida por un Feature Toggle en ConfigCat con fallback seguro a `false`.
  - [x] Creado el ticket de retiro del Feature Toggle en el backlog técnico.
- [x] **Observabilidad y Telemetría (Nuevo Requisito v3.0):**
  - [x] Logs estructurados con contexto y `correlation_id`.
  - [x] Métricas de éxito/error instrumentadas y visibles en dashboard antes de abrir el tráfico al público general.

---

## 7. Checklist de Cierre: Fase 1 (100% Completada)

| Hito / Entregable de Fase 1 | Estado | Evidencia |
| :--- | :---: | :--- |
| **Repositorio estructurado con Trunk-Based Development** | ✅ 100% | Ramas efímeras, commits semánticos y sincronización diaria con `main`. |
| **Pipeline de CI/CD automatizado** | ✅ 100% | GitHub Actions ejecutando pruebas unitarias, análisis estático y auto-deploy a Render. |
| **Integración de Feature Toggles con ConfigCat** | ✅ 100% | SDK integrado con soporte para segmentación de usuarios, canary rollouts y kill-switch. |
| **Definición de Terminado (DoD v3.0) adoptada** | ✅ 100% | Criterios estrictos incluyendo telemetría de observabilidad y pruebas automáticas. |
| **Ceremonias ágiles adaptadas a CD** | ✅ 100% | Sprint Review enfocado en valor en producción y Sprint Retrospective basada en métricas de pipeline. |
| **Playbook v3.0 publicado y oficializado** | ✅ 100% | Documento rector aprobado y distribuido a todo el equipo. |

---

## 8. Ronda Final de Cierre (Compromiso del Equipo)

> **Pregunta de Cierre:** *“En una frase: ¿Qué cambia en nuestro próximo Review y Retro después de este taller?”*
>
> * **Tech Lead:** *"Dejamos de temer a los despliegues de los viernes porque aprendimos a controlar el riesgo con toggles graduales y métricas en vivo en lugar de con burocracia."*
> * **Product Owner:** *"Nuestras revisiones ahora evalúan valor real de negocio y comportamiento de usuarios en producción, en vez de discutir qué porcentaje de una rama quedó pendiente."*
> * **Developer:** *"El CI vuelve a ser nuestro mejor aliado: no toleraremos un solo test inestable y nuestras ramas volverán a cerrarse el mismo día en que se abren."*
