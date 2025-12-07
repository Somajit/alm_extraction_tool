# Deploy script for ALM Extraction Tool
# This script rebuilds and deploys all services

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ALM Extraction Tool - Full Deployment" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Update backend/.env for Docker deployment
Write-Host "[1/6] Updating backend/.env for Docker..." -ForegroundColor Yellow
$envContent = @"
MONGO_URI=mongodb://mongodb:27017/releasecraftdb
CORS_ORIGINS=http://localhost:5173
ALM_URL=http://mock-alm:8001
MOCK_ALM_URL=http://mock-alm:8001
USE_MOCK_ALM=true
SECRET_KEY=your-secret-key-change-in-production
"@
Set-Content -Path "backend\.env" -Value $envContent
Write-Host "✓ Environment configured for Docker`n" -ForegroundColor Green

# Stop all containers
Write-Host "[2/6] Stopping all containers..." -ForegroundColor Yellow
# Stop all containers
Write-Host "[2/6] Stopping all containers..." -ForegroundColor Yellow
docker-compose down
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to stop containers" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Containers stopped`n" -ForegroundColor Green

# Build frontend locally first (faster and better error reporting)
Write-Host "[3/6] Building frontend assets..." -ForegroundColor Yellow
Set-Location frontend
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Frontend build failed" -ForegroundColor Red
    Set-Location ..
    exit 1
}
Set-Location ..
Write-Host "✓ Frontend built successfully`n" -ForegroundColor Green

# Build all Docker images
Write-Host "[4/6] Building Docker images..." -ForegroundColor Yellow
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Docker build failed" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker images built`n" -ForegroundColor Green

# Start all services
Write-Host "[5/6] Starting all services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to start services" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Services started`n" -ForegroundColor Green

# Wait for services to be ready
Write-Host "[6/6] Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check service status
Write-Host "`nService Status:" -ForegroundColor Cyan
docker-compose ps

# Test endpoints
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Services" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

Write-Host "Testing Frontend (http://localhost:5173)..." -ForegroundColor Yellow
try {
    $frontendTest = Invoke-WebRequest -Uri "http://localhost:5173" -UseBasicParsing -TimeoutSec 5
    if ($frontendTest.StatusCode -eq 200) {
        Write-Host "✓ Frontend is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Frontend is not responding" -ForegroundColor Red
}

Write-Host "Testing Backend (http://localhost:8000/docs)..." -ForegroundColor Yellow
try {
    $backendTest = Invoke-WebRequest -Uri "http://localhost:8000/docs" -UseBasicParsing -TimeoutSec 5
    if ($backendTest.StatusCode -eq 200) {
        Write-Host "✓ Backend is accessible" -ForegroundColor Green
    }
} catch {
    Write-Host "✗ Backend is not responding" -ForegroundColor Red
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "`nAccess the application at: http://localhost:5173" -ForegroundColor White
Write-Host "API documentation at: http://localhost:8000/docs`n" -ForegroundColor White
