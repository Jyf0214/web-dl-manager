#!/bin/bash
set -e

echo "Building gallery-dl-web application..."

# Install dependencies
pip install pyinstaller

# Run the build script
python build.py

echo "Build process completed! Check the dist/ folder for the binary."