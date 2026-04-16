# Construction Site Safety PPE Detection - Windows Start Script
Write-Host "====================================================" -ForegroundColor Cyan
Write-Host "   REPORT-AI: CONSTRUCTION SITE SAFETY SYSTEM       " -ForegroundColor Cyan
Write-Host "====================================================" -ForegroundColor Cyan

$ROOT_DIR = Get-Location

# 1. AI Service (Python FastAPI)
Write-Host "`n[1/2] Starting AI Service (FastAPI)..." -ForegroundColor Yellow
$AI_DIR = Join-Path $ROOT_DIR "ai-service"
$VENV_PYTHON = Join-Path $AI_DIR "venv\Scripts\python.exe"

if (Test-Path $VENV_PYTHON) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$AI_DIR'; & '$VENV_PYTHON' -m uvicorn main:app --reload --host 127.0.0.1 --port 8000"
    Write-Host "AI Service is starting at http://localhost:8000/docs" -ForegroundColor Green
} else {
    Write-Host "Error: AI Service virtual environment not found at $VENV_PYTHON" -ForegroundColor Red
}

# 2. Frontend (Angular)
Write-Host "`n[2/2] Starting Frontend (Angular)..." -ForegroundColor Yellow
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"

if (Test-Path (Join-Path $FRONTEND_DIR "package.json")) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$FRONTEND_DIR'; npm start"
    Write-Host "Frontend is starting at http://localhost:4200" -ForegroundColor Green
} else {
    Write-Host "Error: Frontend directory or package.json not found." -ForegroundColor Red
}

# 3. .NET Backend API
Write-Host "`n[3/3] Starting Backend API (.NET)..." -ForegroundColor Yellow
$BACKEND_DIR = Join-Path $ROOT_DIR "backend\ReportAi.Orchestrator.Api"
if (Test-Path $BACKEND_DIR) {
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:DOTNET_ROLL_FORWARD='Major'; cd '$BACKEND_DIR'; dotnet run"
    Write-Host "Backend API is starting at http://localhost:8080" -ForegroundColor Green
} else {
    Write-Host "Error: Backend directory not found." -ForegroundColor Red
}

Write-Host "`n----------------------------------------------------"
Write-Host "Processes are running in separate windows. Close them to stop services."
Write-Host "----------------------------------------------------"
