# PrintOscar Backend - One-Click Setup (PowerShell)
# Run: .\scripts\setup.ps1

Write-Host "🏆 PrintOscar Backend Setup Starting..." -ForegroundColor Green

# Check prerequisites
if (-NOT (Get-Command pip -ErrorAction SilentlyContinue)) {
    Write-Error "Python/pip not found. Install Python 3.11+"
    exit 1
}

# Activate venv if exists, else create
if (Test-Path .venv) {
    .\.venv\Scripts\Activate.ps1
} else {
    python -m venv .venv
    .\.venv\Scripts\Activate.ps1
    Write-Host "✅ Virtual env created & activated"
}

# Install dependencies
pip install -r requirements.txt
Write-Host "✅ Dependencies installed"

# Copy .env if not exists
if (-NOT (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "✅ .env.example copied to .env (EDIT YOUR VALUES!)"
} else {
    Write-Host "ℹ️  .env exists - skipping copy"
}

# Database migrations (requires psql in PATH)
$env:DATABASE_URL = "postgresql://postgres:root@localhost:5432/trophy_store"
Write-Host "ℹ️  Run manual migrations first:"
Write-Host "   psql trophy_store -f migrations/001_extend_schema.sql"
Write-Host "   psql trophy_store -f migrations/002_full_feature_extensions.sql"
Write-Host "   psql trophy_store -f migrations/003_dynamic_customization.sql"
Write-Host "   alembic upgrade head"

# Admin & seed
Write-Host "`n🚀 Ready to run:"
Write-Host "   .\scripts\run_dev.ps1"
Write-Host "   Or: uvicorn app.main:app --reload"
Write-Host "`n📖 Full guide: docs/QUICKSTART.md"
Write-Host "🌐 API Docs: http://localhost:8000/docs" -ForegroundColor Cyan

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
