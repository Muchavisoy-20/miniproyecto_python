# ==============================================================================
# Script PowerShell de Chaos Engineering - Prueba de Caída de Servicio (LAB 4)
# ==============================================================================
$ErrorActionPreference = "Continue"

$OrdersUrl = "http://localhost:8002"
$CatalogUrl = "http://localhost:8001"

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  CHAOS ENGINEERING: Test 1 - Caída de catalog-service" -ForegroundColor Cyan
Write-Host "======================================================`n" -ForegroundColor Cyan

# 1. Petición inicial
Write-Host "[Paso 1] Verificando estado inicial con ambos servicios arriba..." -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "$OrdersUrl/orders?space_id=1&user_email=test_initial@example.com&hours=2" -Method Post
    Write-Host "✓ Primera petición exitosa (200/201 OK). ID de Orden: $($res.id), Total: $($res.total_price)`n" -ForegroundColor Green
} catch {
    Write-Host "✗ Error en petición inicial: $_" -ForegroundColor Red
}

# 2. Inyección de caos: Apagar catalog-service
Write-Host "[Paso 2] Inyectando Caos: Apagando 'catalog-service' con docker-compose..." -ForegroundColor Yellow
docker-compose stop catalog-service
Write-Host "⚡ catalog-service detenido.`n" -ForegroundColor Red

# 3. Petición con catálogo caído
Write-Host "[Paso 3] Enviando petición a orders-service mientras catalog-service está caído..." -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "$OrdersUrl/orders?space_id=1&user_email=test_chaos@example.com&hours=2" -Method Post
    Write-Host "Inesperado: respondió con éxito" -ForegroundColor Red
} catch {
    $status = $_.Exception.Response.StatusCode.value__
    Write-Host "Código HTTP recibido: $status" -ForegroundColor Magenta
    if ($status -eq 503) {
        Write-Host "✓ Comportamiento esperado: orders-service retornó 503 ('Catalog service unavailable').`n" -ForegroundColor Green
    } else {
        Write-Host "Se recibió código $status: $($_.ErrorDetails.Message)`n" -ForegroundColor Yellow
    }
}

# 4. Recuperación
Write-Host "[Paso 4] Recuperando servicio: Reiniciando 'catalog-service'..." -ForegroundColor Yellow
docker-compose start catalog-service
Start-Sleep -Seconds 5

# 5. Petición tras recuperación
Write-Host "[Paso 5] Verificando auto-recuperación de orders-service..." -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "$OrdersUrl/orders?space_id=1&user_email=test_recovery@example.com&hours=2" -Method Post
    Write-Host "✓ Éxito post-recuperación (200/201 OK). ID de Orden: $($res.id)`n" -ForegroundColor Green
} catch {
    Write-Host "✗ Falló tras recuperación: $_" -ForegroundColor Red
}

Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "  CHAOS TEST 1 FINALIZADO" -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan
