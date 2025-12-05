# Full deployment script for ALM Extraction Tool
param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("local", "atlas")]
    [string]$MongoChoice = "local"
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$WorkspaceRoot = Split-Path -Parent $ScriptDir

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "ALM Extraction Tool - Full Deployment" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "MongoDB Mode: $MongoChoice" -ForegroundColor Yellow
Write-Host "`n" -ForegroundColor Cyan

Set-Location $WorkspaceRoot

# Step 1: Stop existing containers
Write-Host "[Step 1/6] Stopping existing containers..." -ForegroundColor Yellow
docker-compose down
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to stop containers" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Containers stopped`n" -ForegroundColor Green

# Step 2: Build frontend
Write-Host "[Step 2/6] Building frontend..." -ForegroundColor Yellow
Set-Location "$WorkspaceRoot\frontend"
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Frontend build failed" -ForegroundColor Red
    Set-Location $WorkspaceRoot
    exit 1
}
Set-Location $WorkspaceRoot
Write-Host "✓ Frontend built`n" -ForegroundColor Green

# Step 3: Build Docker images
Write-Host "[Step 3/6] Building Docker images..." -ForegroundColor Yellow
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker images built`n" -ForegroundColor Green

# Step 4: Start services
Write-Host "[Step 4/6] Starting services..." -ForegroundColor Yellow
if ($MongoChoice -eq "local") {
    docker-compose up -d
} else {
    # For Atlas, don't start mongo container
    docker-compose up -d backend frontend mock-alm
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start services" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Services started`n" -ForegroundColor Green

# Step 5: Wait for services
Write-Host "[Step 5/6] Waiting for services to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 8
Write-Host "✓ Services initialized`n" -ForegroundColor Green

# Step 6: Verify services
Write-Host "[Step 6/6] Verifying services..." -ForegroundColor Yellow

Write-Host "  Testing Frontend (http://localhost:5173)..." -ForegroundColor Gray
try {
    $frontend = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ Frontend: OK (Status $($frontend.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Frontend: FAILED" -ForegroundColor Red
}

Write-Host "  Testing Backend (http://localhost:8000/docs)..." -ForegroundColor Gray
try {
    $backend = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ Backend: OK (Status $($backend.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Backend: FAILED" -ForegroundColor Red
}

Write-Host "  Testing Mock ALM (http://localhost:8001/health)..." -ForegroundColor Gray
try {
    $mockAlm = Invoke-WebRequest -Uri "http://localhost:8001/health" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✓ Mock ALM: OK (Status $($mockAlm.StatusCode))" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Mock ALM: FAILED" -ForegroundColor Red
}

Write-Host "`n=============================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Cyan

Write-Host "`nService Status:" -ForegroundColor Yellow
docker-compose ps

Write-Host "`nAccess Points:" -ForegroundColor Yellow
Write-Host "  • Frontend:  http://localhost:5173" -ForegroundColor White
Write-Host "  • Backend:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Mock ALM:  http://localhost:8001" -ForegroundColor White
if ($MongoChoice -eq "local") {
    Write-Host "  • MongoDB:   localhost:27017" -ForegroundColor White
}

Write-Host "`nDefault Credentials:" -ForegroundColor Yellow
Write-Host "  • Username: admin" -ForegroundColor White
Write-Host "  • Password: admin123" -ForegroundColor White

Write-Host "`nUseful Commands:" -ForegroundColor Yellow
Write-Host "  • View logs: docker-compose logs -f [service]" -ForegroundColor Gray
Write-Host "  • Stop all:  docker-compose down" -ForegroundColor Gray
Write-Host "  • Restart:   docker-compose restart [service]" -ForegroundColor Gray

Write-Host ""
