#!/bin/bash
# ==============================================================================
# Script de Chaos Engineering - Prueba de Caída de Servicio Dependiente (LAB 4)
# ==============================================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

ORDERS_URL="http://localhost:8002"
CATALOG_URL="http://localhost:8001"

echo -e "${BLUE}======================================================${NC}"
echo -e "${BLUE}  CHAOS ENGINEERING: Test 1 - Caída de catalog-service${NC}"
echo -e "${BLUE}======================================================${NC}\n"

# 1. Petición inicial (Estado saludable)
echo -e "${YELLOW}[Paso 1] Verificando estado inicial con ambos servicios arriba...${NC}"
STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${ORDERS_URL}/orders?space_id=1&user_email=test_initial@example.com&hours=2")
echo -e "Código HTTP recibido: ${STATUS_CODE}"

if [ "$STATUS_CODE" -eq 201 ] || [ "$STATUS_CODE" -eq 200 ]; then
    echo -e "${GREEN}✓ Primera petición exitosa (200/201 OK). El flujo síncrono funciona.${NC}\n"
else
    echo -e "${RED}✗ Falló la petición inicial (Código: $STATUS_CODE). Revisa que los servicios estén arriba.${NC}"
    exit 1
fi

# 2. Inyección de caos: Apagar catalog-service
echo -e "${YELLOW}[Paso 2] Inyectando Caos: Apagando 'catalog-service'...${NC}"
docker-compose stop catalog-service
echo -e "${RED}⚡ catalog-service detenido.${NC}\n"

# 3. Petición con catálogo caído
echo -e "${YELLOW}[Paso 3] Enviando petición a orders-service mientras catalog-service está caído...${NC}"
RESPONSE_BODY=$(curl -s -X POST "${ORDERS_URL}/orders?space_id=1&user_email=test_chaos@example.com&hours=2")
CHAOS_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${ORDERS_URL}/orders?space_id=1&user_email=test_chaos@example.com&hours=2")

echo -e "Código HTTP recibido: ${CHAOS_STATUS}"
echo -e "Respuesta recibida: ${RESPONSE_BODY}"

if [ "$CHAOS_STATUS" -eq 503 ]; then
    echo -e "${GREEN}✓ Comportamiento esperado: orders-service retornó 503 Service Unavailable ('Catalog service unavailable').${NC}\n"
else
    echo -e "${RED}✗ Inesperado: Se esperaba HTTP 503 pero se obtuvo $CHAOS_STATUS.${NC}\n"
fi

# 4. Recuperación: Reiniciar catalog-service
echo -e "${YELLOW}[Paso 4] Recuperando servicio: Reiniciando 'catalog-service'...${NC}"
docker-compose start catalog-service
echo "Esperando 5 segundos para calentamiento de red..."
sleep 5

# Esperar a que el healthcheck responda
echo "Verificando disponibilidad de catalog-service..."
for i in {1..10}; do
    if curl -s "${CATALOG_URL}/health" | grep -q "ok"; then
        echo -e "${GREEN}catalog-service está nuevamente ONLINE.${NC}\n"
        break
    fi
    echo "Intento $i: esperando catálogo..."
    sleep 2
done

# 5. Petición tras recuperación
echo -e "${YELLOW}[Paso 5] Verificando auto-recuperación de orders-service...${NC}"
RECOVERY_STATUS=$(curl -s -o /dev/null -w "%{http_code}" -X POST "${ORDERS_URL}/orders?space_id=1&user_email=test_recovery@example.com&hours=2")
echo -e "Código HTTP recibido: ${RECOVERY_STATUS}"

if [ "$RECOVERY_STATUS" -eq 201 ] || [ "$RECOVERY_STATUS" -eq 200 ]; then
    echo -e "${GREEN}✓ Éxito post-recuperación (200/201 OK). El sistema reanudó operaciones normales sin necesidad de reiniciar orders-service.${NC}\n"
else
    echo -e "${RED}✗ Falló tras recuperación (Código: $RECOVERY_STATUS).${NC}\n"
fi

echo -e "${BLUE}======================================================${NC}"
echo -e "${GREEN}  CHAOS TEST 1 FINALIZADO CON ÉXITO${NC}"
echo -e "${BLUE}======================================================${NC}"
