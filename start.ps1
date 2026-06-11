Write-Host "=======================================" -ForegroundColor Cyan
Write-Host "  Brevet 2026 - Dashboard Controle Continu" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    Write-Host "Python introuvable. Installe Python 3.10+." -ForegroundColor Red
    exit 1
}

# Check dependencies
Write-Host "Verification des dependances..." -ForegroundColor Yellow
$missing = @()
$deps = @("fastapi", "uvicorn", "pronotepy")
foreach ($dep in $deps) {
    try {
        python -c "import $dep" 2>$null
    } catch {
        $missing += $dep
    }
}

if ($missing.Count -gt 0) {
    Write-Host "   Installation de : $($missing -join ', ')" -ForegroundColor Yellow
    python -m pip install $missing
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Echec. Essaie : python -m pip install -r requirements.txt" -ForegroundColor Red
        exit 1
    }
}

Write-Host "Dependances OK" -ForegroundColor Green
Write-Host ""

$port = 8000
Write-Host "Lancement du serveur sur http://localhost:$port" -ForegroundColor Green
Write-Host "   Appuie sur Ctrl+C pour arreter." -ForegroundColor DarkGray
Write-Host ""

python -m uvicorn api.index:app --reload --host 0.0.0.0 --port $port
