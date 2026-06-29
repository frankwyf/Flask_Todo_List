param(
    [string]$PythonExe = "python"
)

$ErrorActionPreference = "Stop"

Write-Host "[1/4] Install project dependencies" -ForegroundColor Cyan
& $PythonExe -m pip install -r requirements.txt
& $PythonExe -m pip install -r tests/requirements.txt
& $PythonExe -m pip install -r requirements-dev.txt

Write-Host "[2/4] Lint with Ruff" -ForegroundColor Cyan
& $PythonExe -m ruff check app tests run.py db_create.py

Write-Host "[3/4] Run test suite with coverage" -ForegroundColor Cyan
& $PythonExe -m pytest --cov=app --cov-report=term --cov-report=xml

Write-Host "[4/4] Security dependency scan" -ForegroundColor Cyan
& $PythonExe -m pip_audit -r requirements.txt

Write-Host "Quality gate completed successfully." -ForegroundColor Green
