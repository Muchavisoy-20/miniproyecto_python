import os

import uvicorn
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


class Calculator:
    def suma(self, a: int, b: int) -> int:
        return a + b

    def resta(self, a: int, b: int) -> int:
        return a - b


app = FastAPI(
    title="Miniproyecto Python - Diplomado",
    description="API de Producción para despliegue continuo en Render",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

calc = Calculator()


@app.get("/")
def root():
    return {
        "message": "Bienvenido al Miniproyecto Python - Diplomado",
        "status": "online",
        "docs_url": "/docs",
        "health_check": "/health",
        "modules": {
            "parte_1_microservicios": "coworking-workshop (Puertos 8001 / 8002)",
            "parte_2_serverless": "serverless-coworking (AWS SAM & EventBridge)",
            "taller_6_governance": "taller-6-cd-governance (Continuous Deployment & Toggles)",
        },
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "miniproyecto-python"}


@app.get("/calculator/suma")
def api_suma(a: int = Query(..., description="Primer número"), b: int = Query(..., description="Segundo número")):
    return {"a": a, "b": b, "resultado": calc.suma(a, b)}


@app.get("/calculator/resta")
def api_resta(a: int = Query(..., description="Primer número"), b: int = Query(..., description="Segundo número")):
    return {"a": a, "b": b, "resultado": calc.resta(a, b)}


if __name__ == "__main__":
    # Render asigna dinámicamente el puerto en la variable de entorno PORT (por defecto 10000)
    port = int(os.environ.get("PORT", "10000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
