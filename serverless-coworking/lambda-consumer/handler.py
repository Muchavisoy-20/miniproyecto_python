import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List
import boto3
import urllib3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ORDERS_SERVICE_WEBHOOK_URL = os.getenv("ORDERS_SERVICE_WEBHOOK_URL", "")
NOTIFICATION_SNS_TOPIC_ARN = os.getenv("NOTIFICATION_SNS_TOPIC_ARN", "")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

http = urllib3.PoolManager()
PROCESSED_MESSAGE_IDS = set()


def process_single_event(event_detail: dict, message_id: str) -> None:
    """
    Procesa un evento individual deserializado de EventBridge.
    Aplica lógica de negocio: sincronización con orders-service, notificación o auditoría.
    """
    space_id = event_detail.get("space_id")
    space_name = event_detail.get("space_name")
    current_avail = event_detail.get("current_availability")
    price = event_detail.get("price_per_hour")
    updated_at = event_detail.get("updated_at")

    logger.info(
        "🔔 [EVENT CONSUMER] Evento recibido: Espacio #%s ('%s') cambió disponibilidad a: %s. Tarifa: $%s/h. Timestamp: %s",
        space_id,
        space_name,
        "DISPONIBLE" if current_avail else "NO DISPONIBLE",
        price,
        updated_at,
    )

    # 1. Si está configurada una URL hacia orders-service o webhook externo, notificar
    if ORDERS_SERVICE_WEBHOOK_URL:
        try:
            payload = json.dumps({
                "event": "SPACE_AVAILABILITY_CHANGED",
                "space_id": space_id,
                "available": current_avail,
                "timestamp": updated_at,
            })
            resp = http.request(
                "POST",
                ORDERS_SERVICE_WEBHOOK_URL,
                body=payload.encode("utf-8"),
                headers={"Content-Type": "application/json"},
                timeout=3.0,
            )
            logger.info("Notificación enviada a orders-service. Código HTTP: %s", resp.status)
        except Exception as exc:
            logger.warning("No se pudo notificar a orders-service webhook (%s): %s", ORDERS_SERVICE_WEBHOOK_URL, exc)

    # 2. Si el espacio pasa a NO DISPONIBLE, registrar alerta de inventario
    if not current_avail:
        logger.warning(
            "⚠️ ATENCIÓN: El espacio #%s ('%s') ya no está disponible para nuevas reservas. Órdenes en tránsito deben ser validadas.",
            space_id,
            space_name,
        )


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Manejador Lambda para procesar lotes de mensajes provenientes de AWS SQS
    (desencadenados por las reglas de AWS EventBridge).
    """
    logger.info("Recibido lote de eventos de SQS. Cantidad de registros: %d", len(event.get("Records", [])))

    batch_item_failures: List[Dict[str, str]] = []

    for record in event.get("Records", []):
        message_id = record.get("messageId", "unknown")
        body_raw = record.get("body", "{}")

        # Control de idempotencia en memoria (o con DynamoDB en producción)
        if message_id in PROCESSED_MESSAGE_IDS:
            logger.info("Mensaje %s ya fue procesado previamente. Omitiendo duplicado.", message_id)
            continue

        try:
            body = json.loads(body_raw)

            # Verificar si el mensaje viene envuelto en un envelope de EventBridge
            if "detail" in body and "detail-type" in body:
                detail = body.get("detail", {})
                detail_type = body.get("detail-type", "Unknown")
                source = body.get("source", "Unknown")
                logger.info("Mensaje de EventBridge detectado: Source='%s', Type='%s'", source, detail_type)
                process_single_event(detail, message_id)
            else:
                # Payload directo
                process_single_event(body, message_id)

            PROCESSED_MESSAGE_IDS.add(message_id)

        except Exception as exc:
            logger.error("Error al procesar el mensaje SQS ID %s: %s", message_id, exc, exc_info=True)
            # Enviar a batch_item_failures para que SQS mantenga solo este mensaje y lo envíe a la DLQ
            batch_item_failures.append({"itemIdentifier": message_id})

    return {
        "statusCode": 200,
        "processed_count": len(event.get("Records", [])) - len(batch_item_failures),
        "batchItemFailures": batch_item_failures,
    }
