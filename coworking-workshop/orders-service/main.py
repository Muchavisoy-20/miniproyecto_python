import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel, Field

app = FastAPI(
    title="Coworking Orders Service",
    description="Microservicio de gestión de reservas y órdenes de coworking que depende de catalog-service",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# URL del catalog-service configurable por variable de entorno
CATALOG_SERVICE_URL = os.getenv("CATALOG_SERVICE_URL", "http://localhost:8001").rstrip("/")
HTTP_TIMEOUT_SECONDS = float(os.getenv("HTTP_TIMEOUT_SECONDS", "3.0"))


class OrderCreateRequest(BaseModel):
    space_id: int = Field(..., example=1)
    user_email: str = Field(..., example="usuario@ejemplo.com")
    hours: int = Field(..., ge=1, le=24, example=2)


class OrderResponse(BaseModel):
    id: int
    space_id: int
    space_name: str
    user_email: str
    hours: int
    hourly_rate_charged: float
    total_price: float
    status: str
    created_at: str


# Base de datos en memoria para las órdenes
ORDERS_DB: Dict[int, dict] = {}
ORDER_COUNTER = 0


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint del servicio de órdenes."""
    return {
        "status": "ok",
        "service": "orders-service",
        "catalog_service_url": CATALOG_SERVICE_URL,
    }


@app.get("/orders", tags=["Orders"])
def list_orders():
    """Retorna todas las órdenes de reserva creadas."""
    return list(ORDERS_DB.values())


@app.get("/orders/{order_id}", tags=["Orders"])
def get_order(order_id: int):
    """Retorna los detalles de una orden por su ID."""
    order = ORDERS_DB.get(order_id)
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Orden con ID {order_id} no encontrada",
        )
    return order


@app.post("/orders", status_code=status.HTTP_201_CREATED, tags=["Orders"])
async def create_order(
    space_id: int = Query(..., description="ID del espacio a reservar"),
    user_email: str = Query(..., description="Correo del usuario que reserva"),
    hours: int = Query(..., ge=1, le=24, description="Cantidad de horas de reserva"),
):
    """
    Crea una nueva orden de reserva.
    Consulta de forma sincrónica HTTP al catalog-service para verificar existencia,
    disponibilidad y precio por hora.
    """
    global ORDER_COUNTER

    catalog_url = f"{CATALOG_SERVICE_URL}/spaces/{space_id}"

    # 1. Comunicación HTTP con el servicio dependiente (catalog-service)
    try:
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(catalog_url)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.RequestError) as exc:
        # LAB 4: Chaos Engineering - El catálogo está caído o no responde
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog service unavailable",
        ) from exc

    # 2. Manejo de códigos de estado del catálogo
    if response.status_code == status.HTTP_404_NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El espacio con ID {space_id} no existe en el catálogo",
        )
    elif response.status_code != status.HTTP_200_OK:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Error inesperado al consultar el catálogo (HTTP {response.status_code})",
        )

    space_data = response.json()

    # 3. Validación de disponibilidad del espacio
    if not space_data.get("available", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El espacio '{space_data.get('name', space_id)}' no está disponible para reserva",
        )

    # 4. Cálculo de precio usando el contrato esperado: space["price_per_hour"]
    # LAB 5: Chaos Engineering - Si el catálogo cambió el contrato a 'hourly_rate'
    # sin avisar, se producirá un KeyError o un fallo de integración.
    try:
        # Se asume explícitamente el contrato acordado con 'price_per_hour'
        price_per_hour = space_data["price_per_hour"]
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Contract Violation Error: El servicio de órdenes esperaba el campo "
                "'price_per_hour' en la respuesta del catálogo, pero no fue encontrado. "
                f"Campos recibidos: {list(space_data.keys())}"
            ),
        ) from exc

    total_price = round(price_per_hour * hours, 2)

    # 5. Registro de la orden
    ORDER_COUNTER += 1
    new_order = {
        "id": ORDER_COUNTER,
        "space_id": space_id,
        "space_name": space_data.get("name", f"Espacio #{space_id}"),
        "user_email": user_email,
        "hours": hours,
        "hourly_rate_charged": price_per_hour,
        "total_price": total_price,
        "status": "CONFIRMED",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    ORDERS_DB[ORDER_COUNTER] = new_order

    return new_order


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
