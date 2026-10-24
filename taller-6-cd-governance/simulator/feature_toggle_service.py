import hashlib
import logging
import os
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Manejo tolerante de dependencias externas (FastAPI / Pydantic)
try:
    from fastapi import FastAPI, HTTPException, Query, status
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel, EmailStr, Field
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

    class FastAPI:
        def __init__(self, *args, **kwargs): pass
        def add_middleware(self, *args, **kwargs): pass
        def get(self, *args, **kwargs): return lambda f: f
        def post(self, *args, **kwargs): return lambda f: f
        def patch(self, *args, **kwargs): return lambda f: f

    class CORSMiddleware: pass

    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(f"HTTP {status_code}: {detail}")

    class status:
        HTTP_200_OK = 200
        HTTP_201_CREATED = 201
        HTTP_400_BAD_REQUEST = 400
        HTTP_404_NOT_FOUND = 404
        HTTP_500_INTERNAL_SERVER_ERROR = 500
        HTTP_503_SERVICE_UNAVAILABLE = 503

    def Query(*args, **kwargs): return None

    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        def dict(self):
            return self.__dict__

    EmailStr = str

    def Field(*args, **kwargs):
        if "default_factory" in kwargs:
            return kwargs["default_factory"]()
        return kwargs.get("default", None)

# Configuración de logging estructurado
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("toggle-simulator")

app = FastAPI(
    title="Feature Toggle & Safe Release Simulator",
    description="Servicio interactivo para simular el ciclo de vida seguro de 'Pagos Express' con ConfigCat y métricas en vivo",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CONFIGCAT_SDK_KEY = os.getenv("CONFIGCAT_SDK_KEY", "")
TOGGLE_KEY = "pagos_express_v1"

# Intento de cargar el cliente oficial de ConfigCat si está disponible
configcat_client = None
if CONFIGCAT_SDK_KEY:
    try:
        import configcatclient
        configcat_client = configcatclient.get(CONFIGCAT_SDK_KEY)
        logger.info("ConfigCat SDK inicializado con clave real.")
    except Exception as exc:
        logger.warning("No se pudo iniciar ConfigCat SDK: %s. Usando emulador en memoria.", exc)

# ------------------------------------------------------------------------------
# Configuración del Emulador de ConfigCat en Memoria
# ------------------------------------------------------------------------------
class ToggleConfig(BaseModel):
    is_active: bool = Field(default=False, description="Estado maestro del toggle")
    percentage_rollout: int = Field(default=0, ge=0, le=100, description="Porcentaje de usuarios canary")
    allowlist_emails: List[str] = Field(
        default_factory=lambda: ["admin@coworking.com", "qa@coworking.com", "dev@coworking.com"],
        description="Lista de correos autorizados al 100%",
    )
    allowlist_domains: List[str] = Field(
        default_factory=lambda: ["coworking.com"],
        description="Dominios corporativos con acceso total",
    )

    def __init__(self, is_active=False, percentage_rollout=0, allowlist_emails=None, allowlist_domains=None, **kwargs):
        super().__init__(**kwargs)
        self.is_active = is_active
        self.percentage_rollout = percentage_rollout
        self.allowlist_emails = allowlist_emails if allowlist_emails is not None else ["admin@coworking.com", "qa@coworking.com", "dev@coworking.com"]
        self.allowlist_domains = allowlist_domains if allowlist_domains is not None else ["coworking.com"]


SIMULATED_CONFIG = ToggleConfig()

# Métricas de telemetría en tiempo real
METRICS = {
    "total_requests": 0,
    "express_attempts": 0,
    "express_success": 0,
    "express_errors": 0,
    "classic_attempts": 0,
    "classic_success": 0,
    "latencies_ms": [],
}


def evaluate_feature_toggle(user_email: str) -> bool:
    """
    Evalúa si un usuario tiene acceso a la funcionalidad 'Pagos Express'.
    Utiliza el SDK de ConfigCat si existe o las reglas del emulador.
    """
    # 1. Si existe SDK real de ConfigCat
    if configcat_client:
        try:
            import configcatclient
            user = configcatclient.User(identifier=user_email, email=user_email)
            return configcat_client.get_value(TOGGLE_KEY, False, user)
        except Exception as e:
            logger.error("Error al consultar ConfigCat SDK: %s. Aplicando fallback defensivo a False.", e)
            return False

    # 2. Emulador en memoria de ConfigCat
    if not SIMULATED_CONFIG.is_active:
        return False

    # Regla 1: Permitir por dominio o lista blanca explícita
    domain = user_email.split("@")[-1].lower() if "@" in user_email else ""
    if domain in SIMULATED_CONFIG.allowlist_domains or user_email.lower() in [
        e.lower() for e in SIMULATED_CONFIG.allowlist_emails
    ]:
        return True

    # Regla 2: Despliegue porcentual determinista por hash del correo
    if SIMULATED_CONFIG.percentage_rollout <= 0:
        return False
    if SIMULATED_CONFIG.percentage_rollout >= 100:
        return True

    # Hash determinista (0 a 99)
    hash_val = int(hashlib.md5(user_email.encode("utf-8")).hexdigest(), 16) % 100
    return hash_val < SIMULATED_CONFIG.percentage_rollout


# ------------------------------------------------------------------------------
# Endpoints de la API
# ------------------------------------------------------------------------------
@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "feature-toggle-simulator",
        "engine": "ConfigCat Cloud" if configcat_client else "In-Memory Emulator",
    }


@app.get("/toggle/status", tags=["Feature Toggle Governance"])
def get_toggle_status():
    """Consulta la configuración actual del Feature Toggle 'pagos_express_v1'."""
    return {
        "toggle_key": TOGGLE_KEY,
        "active": SIMULATED_CONFIG.is_active,
        "percentage_rollout": SIMULATED_CONFIG.percentage_rollout,
        "allowlist_emails": SIMULATED_CONFIG.allowlist_emails,
        "allowlist_domains": SIMULATED_CONFIG.allowlist_domains,
        "sdk_connected": configcat_client is not None,
    }


@app.post("/toggle/configure", tags=["Feature Toggle Governance"])
def update_toggle_configuration(config: ToggleConfig):
    """Actualiza en caliente las reglas de segmentación y porcentaje del toggle."""
    global SIMULATED_CONFIG
    SIMULATED_CONFIG = config
    logger.info(
        "Configuración del toggle '%s' actualizada: Activo=%s, Rollout=%d%%",
        TOGGLE_KEY,
        config.is_active,
        config.percentage_rollout,
    )
    return {
        "message": "Configuración de Feature Toggle actualizada exitosamente",
        "current_config": SIMULATED_CONFIG,
    }


@app.post("/toggle/kill-switch", tags=["Feature Toggle Governance"])
def activate_emergency_kill_switch():
    """Desactiva de emergencia el feature toggle (0% y desactivado)."""
    global SIMULATED_CONFIG
    SIMULATED_CONFIG.is_active = False
    SIMULATED_CONFIG.percentage_rollout = 0
    logger.critical("🚨 KILL-SWITCH ACTIVADO: 'pagos_express_v1' ha sido completamente apagado.")
    return {
        "message": "🚨 KILL-SWITCH ACTIVADO. La funcionalidad ha sido apagada para el 100% de los usuarios.",
        "toggle_key": TOGGLE_KEY,
        "active": False,
        "percentage_rollout": 0,
    }


class CheckoutRequest(BaseModel):
    user_email: str
    space_id: int
    amount: float
    simulate_failure: bool = False

    def __init__(self, user_email: str, space_id: int, amount: float, simulate_failure: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.user_email = user_email
        self.space_id = space_id
        self.amount = amount
        self.simulate_failure = simulate_failure


@app.post("/checkout", tags=["Checkout Transactions"])
def process_checkout(request: CheckoutRequest):
    """
    Procesa un pago evaluando dinámicamente si el usuario recibe 'Pagos Express' o el flujo clásico.
    """
    start_time = time.time()
    METRICS["total_requests"] += 1

    # Evaluar Feature Toggle
    has_express = evaluate_feature_toggle(request.user_email)

    if has_express:
        METRICS["express_attempts"] += 1
        elapsed_sim = 0.05
        time.sleep(elapsed_sim)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        METRICS["latencies_ms"].append(latency_ms)

        # Simular posible error si se solicita
        if request.simulate_failure:
            METRICS["express_errors"] += 1
            logger.error("Fallo transaccional en Pagos Express para usuario %s", request.user_email)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fallo en la pasarela de pagos express 1-clic.",
            )

        METRICS["express_success"] += 1
        return {
            "flow": "PAGOS_EXPRESS_1_CLICK",
            "status": "APPROVED",
            "user_email": request.user_email,
            "amount_paid": request.amount,
            "latency_ms": latency_ms,
            "transaction_id": f"TX-EXP-{random.randint(100000, 999999)}",
            "message": "¡Pago procesado instantáneamente con un solo clic!",
        }
    else:
        METRICS["classic_attempts"] += 1
        elapsed_sim = 0.10
        time.sleep(elapsed_sim)
        latency_ms = round((time.time() - start_time) * 1000, 2)
        METRICS["latencies_ms"].append(latency_ms)
        METRICS["classic_success"] += 1

        return {
            "flow": "PAGO_TRADICIONAL_3_PASOS",
            "status": "APPROVED",
            "user_email": request.user_email,
            "amount_paid": request.amount,
            "latency_ms": latency_ms,
            "transaction_id": f"TX-STD-{random.randint(100000, 999999)}",
            "message": "Pago procesado a través del flujo tradicional de confirmación.",
        }


@app.get("/metrics/dashboard", tags=["Observability Dashboard"])
def get_metrics_dashboard():
    """Retorna el cuadro de mando de observabilidad en vivo para evaluar la salud de la liberación."""
    total_express = METRICS["express_attempts"]
    error_rate_pct = round((METRICS["express_errors"] / total_express * 100), 2) if total_express > 0 else 0.0

    avg_latency = (
        round(sum(METRICS["latencies_ms"]) / len(METRICS["latencies_ms"]), 2)
        if METRICS["latencies_ms"]
        else 0.0
    )

    health_status = "HEALTHY"
    alert_triggered = False
    if error_rate_pct > 1.5:
        health_status = "CRITICAL_ALERT - DISPARAR KILL-SWITCH"
        alert_triggered = True
    elif error_rate_pct > 0.5:
        health_status = "WARNING"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_checkout_requests": METRICS["total_requests"],
        "express_payments": {
            "attempts": METRICS["express_attempts"],
            "successful": METRICS["express_success"],
            "errors": METRICS["express_errors"],
            "error_rate_percentage": error_rate_pct,
        },
        "classic_payments": {
            "attempts": METRICS["classic_attempts"],
            "successful": METRICS["classic_success"],
        },
        "performance": {
            "average_latency_ms": avg_latency,
            "p95_target_ms": "< 800 ms",
        },
        "system_health": health_status,
        "kill_switch_recommended": alert_triggered,
    }


if __name__ == "__main__":
    if FASTAPI_AVAILABLE:
        import uvicorn
        uvicorn.run("feature_toggle_service:app", host="0.0.0.0", port=8003, reload=True)
    else:
        print("FastAPI no está instalado en el entorno actual. Ejecuta los tests con test_toggle_flow.py.")
