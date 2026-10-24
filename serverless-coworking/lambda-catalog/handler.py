import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

EVENT_BUS_NAME = os.getenv("EVENT_BUS_NAME", "CoworkingEventBus")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# Inicialización diferida del cliente EventBridge
events_client = None


def get_events_client():
    global events_client
    if events_client is None:
        events_client = boto3.client("events", region_name=AWS_REGION)
    return events_client


# Base de datos simulada de espacios de coworking
SPACES_DB = {
    1: {
        "id": 1,
        "name": "Sala Creativa Alpha",
        "capacity": 6,
        "price_per_hour": 25.0,
        "available": True,
        "location": "Piso 2 - Coworking Central",
    },
    2: {
        "id": 2,
        "name": "Oficina Privada Executive",
        "capacity": 4,
        "price_per_hour": 40.0,
        "available": True,
        "location": "Piso 4 - Zona Silenciosa",
    },
    3: {
        "id": 3,
        "name": "Hot Desk Flexible",
        "capacity": 1,
        "price_per_hour": 8.0,
        "available": True,
        "location": "Piso 1 - Open Space",
    },
    4: {
        "id": 4,
        "name": "Auditorio Meetups & Workshops",
        "capacity": 30,
        "price_per_hour": 90.0,
        "available": False,
        "location": "Sótano 1 - Event Hall",
    },
}


def build_response(status_code: int, body: Any) -> Dict[str, Any]:
    """Genera una respuesta compatible con API Gateway HTTP Proxy integration."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PATCH, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        },
        "body": json.dumps(body, ensure_ascii=False),
    }


def publish_space_changed_event(space: dict, previous_availability: bool) -> dict:
    """
    Publica un evento en AWS EventBridge indicando que la disponibilidad de un espacio ha cambiado.
    Permite que los suscriptores (orders-service, notificaciones) reaccionen asíncronamente.
    """
    client = get_events_client()
    event_payload = {
        "space_id": space["id"],
        "space_name": space["name"],
        "previous_availability": previous_availability,
        "current_availability": space["available"],
        "price_per_hour": space["price_per_hour"],
        "capacity": space["capacity"],
        "updated_at": datetime.now(timezone.utc).isoformat() + "Z",
        "triggered_by": "lambda-catalog-fn",
    }

    entry = {
        "Source": "coworking.catalog",
        "DetailType": "SpaceChanged",
        "Detail": json.dumps(event_payload),
        "EventBusName": EVENT_BUS_NAME,
        "Time": datetime.now(timezone.utc),
    }

    logger.info("Publicando evento a EventBridge Bus '%s': %s", EVENT_BUS_NAME, entry)
    response = client.put_events(Entries=[entry])
    logger.info("Respuesta de EventBridge: %s", response)
    return response


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Manejador principal de la función Lambda catalog-service.
    Enruta las peticiones HTTP provenientes de API Gateway.
    """
    logger.info("Evento entrante en catalog Lambda: %s", json.dumps(event))

    # Detección del método HTTP (compatible con Payload v1 y v2 de API Gateway)
    http_method = (
        event.get("httpMethod")
        or event.get("requestContext", {}).get("http", {}).get("method")
        or "GET"
    ).upper()

    # Detección del path
    raw_path = (
        event.get("path")
        or event.get("rawPath")
        or event.get("requestContext", {}).get("http", {}).get("path")
        or "/"
    )

    # Manejo de pre-flight CORS
    if http_method == "OPTIONS":
        return build_response(200, {"message": "OK"})

    # Rutas soportadas
    # 1. Health check
    if raw_path.endswith("/health"):
        return build_response(200, {
            "status": "ok",
            "service": "lambda-catalog-service",
            "event_bus": EVENT_BUS_NAME,
            "timestamp": datetime.now(timezone.utc).isoformat() + "Z",
        })

    # 2. Listar espacios (GET /spaces o GET /catalog o GET /catalog/spaces)
    if http_method == "GET" and (raw_path.endswith("/spaces") or raw_path.endswith("/catalog")):
        query_params = event.get("queryStringParameters") or {}
        available_only = query_params.get("available_only", "").lower() == "true"
        spaces = list(SPACES_DB.values())
        if available_only:
            spaces = [s for s in spaces if s["available"]]
        return build_response(200, spaces)

    # 3. Detalle de espacio por ID (GET /spaces/{id})
    path_parameters = event.get("pathParameters") or {}
    space_id_str = path_parameters.get("id") or path_parameters.get("space_id")

    # Extraer de URL si no viene en pathParameters
    if not space_id_str:
        parts = [p for p in raw_path.strip("/").split("/") if p]
        if parts and parts[-1].isdigit():
            space_id_str = parts[-1]
        elif len(parts) >= 2 and parts[-2] == "spaces" and parts[-1].isdigit():
            space_id_str = parts[-1]

    if space_id_str and space_id_str.isdigit():
        space_id = int(space_id_str)
        space = SPACES_DB.get(space_id)

        if not space:
            return build_response(404, {"detail": f"Espacio #{space_id} no encontrado en el catálogo"})

        # GET /spaces/{id}
        if http_method == "GET":
            return build_response(200, space)

        # PATCH /spaces/{id}/availability o POST con cambio de disponibilidad
        if http_method in ["PATCH", "POST", "PUT"]:
            try:
                body = json.loads(event.get("body", "{}") or "{}")
            except Exception as e:
                return build_response(400, {"detail": f"JSON inválido en el cuerpo de la petición: {str(e)}"})

            if "available" not in body:
                return build_response(400, {"detail": "El campo booleano 'available' es obligatorio"})

            previous_avail = space["available"]
            new_avail = bool(body["available"])
            space["available"] = new_avail

            # Publicar evento en EventBridge
            publish_result = {}
            try:
                publish_result = publish_space_changed_event(space, previous_avail)
            except Exception as exc:
                logger.error("Error al publicar evento en EventBridge: %s", exc)
                # En entornos locales o sin credenciales AWS reales, registramos la excepción
                publish_result = {"warning": f"No se pudo emitir a EventBridge: {str(exc)}"}

            return build_response(200, {
                "message": "Disponibilidad actualizada y evento publicado en EventBridge",
                "space": space,
                "event_published": publish_result.get("FailedEntryCount", 0) == 0,
            })

    # Ruta por defecto si no coincide
    return build_response(404, {
        "detail": f"Ruta no encontrada: {http_method} {raw_path}",
        "available_endpoints": [
            "GET /health",
            "GET /spaces",
            "GET /spaces/{id}",
            "PATCH /spaces/{id}/availability",
        ],
    })
