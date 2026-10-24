# Taller 6: Sprint Review, Retrospective y Liberación Segura en Continuous Deployment

Este módulo documenta y desarrolla de forma integral todas las directrices, ceremonias y decisiones de ingeniería requeridas en el **Taller 6** del diplomado, basado en el caso práctico de alta complejidad:

> *"La funcionalidad de ‘Pagos Express’ ya está en main, pero nadie se atreve a activarla"*

---

## 📚 Documentación Técnica y Entregables

| Documento | Descripción y Alcance |
| :--- | :--- |
| 📘 [`SCRUM_TBD_PLAYBOOK_v3.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/SCRUM_TBD_PLAYBOOK_v3.md) | **Playbook Oficial v3.0:** Reglas de Trunk-Based Development, ciclo de vida de Feature Toggles (TTL), DoD con observabilidad y cierre del checklist de Fase 1 al 100%. |
| 🎯 [`safe_release_pagos_express.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/safe_release_pagos_express.md) | **Estrategia de Liberación Segura:** Manejo de la presión del PO/Marketing, plan Canary Rollout (Interno -> 1% -> 10% -> 50% -> 100%), telemetría obligatoria y protocolo de Kill-Switch. |
| 🎤 [`sprint_review_simulation.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/sprint_review_simulation.md) | **Nuevo Sprint Review:** Diferencias vs review clásico, estructura obligatoria de demo (máx 5 min), guión en vivo con 3 incrementos y manipulación de toggles en Render y ConfigCat. |
| 🔄 [`sprint_retrospective_board.md`](file:///j:/ARCHIVOS%20MUCHAVISOY/DIPLOMADO/Clases%20Sabado/miniproyecto_python/taller-6-cd-governance/sprint_retrospective_board.md) | **Nueva Retrospectiva:** Inspección de salud del pipeline (CI flaky, deploy de 11 min), disciplina TBD (solo 4 integraciones), tablero Miro (🟢🟡🔴🚀) y las 3 acciones de mejora prioritarias. |

---

## 💻 Simulador Interactivo de Feature Toggles y Kill-Switch

Para validar empíricamente la estrategia de liberación, se incluye un servicio funcional en `simulator/`:

```text
taller-6-cd-governance/simulator/
├── feature_toggle_service.py   # Servicio FastAPI con motor ConfigCat y emulador determinista
├── requirements.txt            # Dependencias
└── test_toggle_flow.py         # Suite de pruebas automatizadas del flujo de toggles
```

### Ejecutar las Pruebas Automatizadas del Simulador:
```bash
python taller-6-cd-governance/simulator/test_toggle_flow.py
```

### Ejecutar el Servicio en Vivo:
```bash
python taller-6-cd-governance/simulator/feature_toggle_service.py
```
* **Swagger UI:** `http://localhost:8003/docs`
* **Endpoints Clave:**
  * `GET /toggle/status`: Consulta el estado del toggle `pagos_express_v1`.
  * `POST /toggle/configure`: Modifica el porcentaje del Canary Rollout (0% a 100%).
  * `POST /checkout`: Procesa compras evaluando dinámicamente si el cliente accede a 1-clic o al flujo clásico.
  * `GET /metrics/dashboard`: Métricas en vivo (tasa de error, latencia, solicitudes).
  * `POST /toggle/kill-switch`: Apagado inmediato de emergencia en caliente.
