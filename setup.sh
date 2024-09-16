#!/bin/bash

# Remove any existing virtual environment
if [ -d "venv" ]; then
    rm -rf venv
fi

# Create a new virtual environment named 'venv'
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Ensure the virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "Virtual environment not activated. Exiting."
    exit 1
fi

# Upgrade pip and install the required packages
pip install --upgrade pip
pip install nostr websockets colorama

# Debugging: Check if nostr is installed

echo "Virtual environment setup complete. 'nostr' module installed."

#pip show nostr
#pip show websockets

