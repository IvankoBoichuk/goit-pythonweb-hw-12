#!/bin/bash
# Script to build Sphinx documentation using Docker

set -e

echo "Building Sphinx documentation..."

# Ensure Docker container is running with docs dependencies
docker compose exec app pip install -e .[docs] || {
    echo "Installing documentation dependencies..."
    docker compose up --build app -d
    sleep 5
    docker compose exec app pip install -e .[docs]
}

# Build the documentation
docker compose exec app bash -c "cd /app/docs && sphinx-build -b html . _build/html"

echo "Documentation built successfully!"
echo "Open docs/_build/html/index.html in your browser to view the documentation."