@echo off
REM Script to build Sphinx documentation using Docker

echo Building Sphinx documentation...

REM Restart Docker containers to pick up new dependencies
echo Starting Docker containers...
docker compose down
docker compose up --build -d

REM Wait for containers to be ready
timeout /t 10

REM Install documentation dependencies
echo Installing documentation dependencies...
docker compose exec app pip install -e .[docs]

REM Build the documentation  
echo Building documentation...
docker compose exec app bash -c "cd /app/docs && sphinx-build -b html . _build/html"

echo.
echo Documentation built successfully!
echo Open docs\_build\html\index.html in your browser to view the documentation.
pause