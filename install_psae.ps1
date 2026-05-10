# PSAE Windows Installer
# Run with: powershell -ExecutionPolicy Bypass -File install_psae.ps1

$ErrorActionPreference = "Stop"
Write-Host "=== PSAE Windows Installer ===" -ForegroundColor Cyan

# 1. Check Python
try {
    $pyver = python --version 2>&1
    Write-Host "✓ Found $pyver" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Installing via winget..." -ForegroundColor Yellow
    winget install -e --id Python.Python.3.11 --silent
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine")
}

# 2. Upgrade pip
python -m pip install --upgrade pip --quiet

# 3. Install CPU torch first (avoids downloading 2GB CUDA build)
Write-Host "Installing PyTorch (CPU)..." -ForegroundColor Cyan
pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet

# 4. Install all PSAE packages from GitHub
Write-Host "Installing PSAE packages..." -ForegroundColor Cyan
$packages = @(
    "psae-core",
    "psae-signal",
    "psae-ingest",
    "psae-factor",
    "psae-backtest",
    "psae-folio"
)
foreach ($pkg in $packages) {
    Write-Host "  Installing $pkg..." -NoNewline
    pip install "git+https://github.com/psae-project/$pkg.git" --quiet
    Write-Host " ✓" -ForegroundColor Green
}

# 5. Install spaCy model
Write-Host "Downloading spaCy model..." -ForegroundColor Cyan
python -m spacy download en_core_web_sm --quiet

# 6. Set up environment variables prompt
Write-Host ""
Write-Host "=== Configuration ===" -ForegroundColor Cyan
$openai = Read-Host "Enter your OpenAI API key (press Enter to skip)"
if ($openai) {
    [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", $openai, "User")
    Write-Host "  ✓ OPENAI_API_KEY saved to user environment" -ForegroundColor Green
}

# 7. Verify install
Write-Host ""
Write-Host "=== Verifying install ===" -ForegroundColor Cyan
python -c "import psae; import psae_signal; import psae_backtest; print('All PSAE packages imported OK')"

Write-Host ""
Write-Host "=== Done! ===" -ForegroundColor Green
Write-Host "Run: psae-backtest --help"
Write-Host "Run: psae-signal-serve"
