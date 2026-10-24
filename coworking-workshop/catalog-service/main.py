import os
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(
    title="Coworking Catalog Service",
    description="Microservicio de gestión de catálogo de espacios de coworking",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variable de entorno para simular el fallo de contrato del LAB 5
# Si BREAK_CONTRACT es "true", se reemplaza 'price_per_hour' por 'hourly_rate'
BREAK_CONTRACT = os.getenv("BREAK_CONTRACT", "false").lower() == "true"


class SpaceBase(BaseModel):
    name: str = Field(..., example="Sala Innovación")
    capacity: int = Field(..., example=8)
    price_per_hour: float = Field(..., example=25.0)
    available: bool = Field(default=True, example=True)
    location: str = Field(default="Piso 3 - Torre Norte", example="Piso 3 - Torre Norte")
    amenities: List[str] = Field(
        default_factory=lambda: ["WiFi 6", "Proyector 4K", "Pizarra", "Café premium"]
    )


class SpaceResponse(SpaceBase):
    id: int = Field(..., example=1)


class SpaceBrokenResponse(BaseModel):
    id: int
    name: str
    capacity: int
    hourly_rate: float  # ¡Rompe el contrato esperado por orders-service!
    available: bool
    location: str
    amenities: List[str]


class AvailabilityUpdateRequest(BaseModel):
    available: bool


# Base de datos en memoria para el catálogo
CATALOG_DB: Dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Sala Creativa Alpha",
        "capacity": 6,
        "price_per_hour": 25.0,
        "available": True,
        "location": "Piso 2 - Coworking Central",
        "amenities": ["WiFi 6", "Pizarra magnética", "Pantalla 55 pulg", "Cafetería libre"],
    },
    2: {
        "id": 2,
        "name": "Oficina Privada Executive",
        "capacity": 4,
        "price_per_hour": 40.0,
        "available": True,
        "location": "Piso 4 - Zona Silenciosa",
        "amenities": ["WiFi 6", "Monitor dual", "Llamadas ilimitadas", "Aire acondicionado"],
    },
    3: {
        "id": 3,
        "name": "Hot Desk Flexible",
        "capacity": 1,
        "price_per_hour": 8.0,
        "available": True,
        "location": "Piso 1 - Open Space",
        "amenities": ["WiFi 6", "Enchufe individual", "Lockers"],
    },
    4: {
        "id": 4,
        "name": "Auditorio Meetups & Workshops",
        "capacity": 30,
        "price_per_hour": 90.0,
        "available": False,  # Espacio reservado para pruebas
        "location": "Sótano 1 - Event Hall",
        "amenities": ["Sistema de audio", "2 Proyectores", "Micrófonos inalámbricos"],
    },
}


def _format_space_response(space: dict, break_contract: bool = False) -> dict:
    """Devuelve la representación del espacio según el contrato acordado o simulando el rompimiento."""
    if break_contract or BREAK_CONTRACT:
        # LAB 5: Romper el contrato cambiando price_per_hour -> hourly_rate
        broken = dict(space)
        broken["hourly_rate"] = broken.pop("price_per_hour")
        return broken
    return space


@app.get("/health", tags=["Health"])
def health_check():
    """Endpoint de verificación de estado y liveness probe."""
    return {
        "status": "ok",
        "service": "catalog-service",
        "contract_broken": BREAK_CONTRACT,
    }


@app.get("/spaces", tags=["Spaces"])
def get_spaces(
    available_only: bool = Query(default=False, description="Filtrar solo espacios disponibles"),
    break_contract: bool = Query(default=False, description="Simular rompimiento de contrato para pruebas"),
):
    """Retorna la lista de espacios de coworking."""
    spaces = list(CATALOG_DB.values())
    if available_only:
        spaces = [s for s in spaces if s["available"]]
    return [_format_space_response(s, break_contract) for s in spaces]


@app.get("/spaces/{space_id}", tags=["Spaces"])
def get_space(
    space_id: int,
    break_contract: bool = Query(default=False, description="Simular rompimiento de contrato para pruebas"),
):
    """Retorna los detalles de un espacio específico por su ID."""
    space = CATALOG_DB.get(space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Espacio con id {space_id} no encontrado en el catálogo",
        )
    return _format_space_response(space, break_contract)


@app.patch("/spaces/{space_id}/availability", tags=["Spaces"])
def update_availability(space_id: int, update: AvailabilityUpdateRequest):
    """Actualiza la disponibilidad de un espacio de coworking."""
    space = CATALOG_DB.get(space_id)
    if not space:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Espacio con id {space_id} no encontrado",
        )
    space["available"] = update.available
    return {
        "message": "Disponibilidad actualizada exitosamente",
        "space_id": space_id,
        "available": space["available"],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
