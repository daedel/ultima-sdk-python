Param(
    [string]$VenvPath = ".\.venv"
)

$ActivatePath = Join-Path $VenvPath "Scripts\Activate.ps1"

if (-Not (Test-Path $ActivatePath)) {
    Write-Host "Virtual environment not found at $VenvPath — creating..."
    python -m venv $VenvPath
}

Write-Host "Activating virtual environment: $ActivatePath"
& $ActivatePath

Write-Host "Upgrading pip and installing package in editable mode..."
python -m pip install --upgrade pip
python -m pip install -e .

$env:UO_ROOT = 'F:\Program Files (x86)\Electronic Arts\Ultima Online Classic' 

pytest -q
