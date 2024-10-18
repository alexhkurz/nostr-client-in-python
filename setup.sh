#!/bin/bash

# Create and activate a new virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip and install the required packages
pip install --upgrade pip
pip install nostr websockets asyncio colorama
pip install flask
pip install ecdsa
