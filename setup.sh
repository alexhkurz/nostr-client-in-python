#!/bin/bash

# Exit on error
set -e

# Choose a specific Python version (adjust as needed)
PYTHON="python3.12"  # or python3.13

echo "Creating virtual environment with $PYTHON..."

# Check if Python version exists
if ! command -v $PYTHON &> /dev/null; then
    echo "Error: $PYTHON not found. Please install it first."
    exit 1
fi

# Remove existing venv if it exists
if [ -d "venv" ]; then
    echo "Removing existing virtual environment..."
    rm -rf venv
fi

# Create and activate virtual environment
$PYTHON -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
# Upgrade pip
pip install --upgrade pip
# Install from requirements.txt
pip install -r requirements.txt

echo "Setup complete! Virtual environment is activated."
