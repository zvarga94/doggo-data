#!/bin/bash

set -e

echo "Setting up the project..."

if ! command -v python3 &>/dev/null; then
    echo "Python3 is not installed. Please install Python3 and try again."
    exit 1
fi

if ! command -v poetry &>/dev/null; then
    echo "Poetry is not installed. Please install Poetry and try again."
    exit 1
fi

VENV_DIR="venv"
rm -rf "$VENV_DIR"
echo "Creating virtual environment..."
python3 -m venv "$VENV_DIR"

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing dependencies..."
poetry install
pre-commit install

echo "Project setup complete!"