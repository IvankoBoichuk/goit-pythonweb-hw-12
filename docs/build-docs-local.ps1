# PowerShell script to build Sphinx documentation locally
Write-Host "Building Sphinx documentation locally..."

# Check if Python is available
try {
    $pythonVersion = python --version 2>$null
    Write-Host "Found Python: $pythonVersion"
} catch {
    Write-Host "Python not found. Please install Python 3.8+ and try again." -ForegroundColor Red
    exit 1
}

# Install Sphinx and dependencies locally
Write-Host "Installing Sphinx and dependencies..."
try {
    python -m pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints myst-parser
    Write-Host "Dependencies installed successfully." -ForegroundColor Green
} catch {
    Write-Host "Failed to install dependencies. Error: $_" -ForegroundColor Red
    exit 1
}

# Build documentation
Write-Host "Building HTML documentation..."
try {
    sphinx-build -b html . _build/html
    Write-Host "Documentation built successfully!" -ForegroundColor Green
    Write-Host "Open _build/html/index.html in your browser to view the documentation."
} catch {
    Write-Host "Failed to build documentation. Error: $_" -ForegroundColor Red
    exit 1
}

pause