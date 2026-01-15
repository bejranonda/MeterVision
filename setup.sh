#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting MeterVision application setup..."

# 1. Check for Prerequisites
echo "🔍 Checking for prerequisites..."
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 is not installed. Please install it and try again."
    exit 1
fi
echo "✅ Python 3 found."

if ! command -v tesseract &> /dev/null
then
    echo "⚠️ Tesseract OCR is not found. The OCR service may not work correctly."
    echo "   On Debian/Ubuntu, install it with: sudo apt update && sudo apt install tesseract-ocr"
    # Continue since it might not be a hard requirement for all parts of the app
fi
echo "✅ Tesseract OCR found (or warning issued)."


# 2. Create Python Virtual Environment
VENV_DIR="venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "🐍 Creating Python virtual environment in '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    echo "✅ Virtual environment created."
else
    echo "👍 Virtual environment already exists."
fi

# 3. Install Dependencies
echo "📦 Installing dependencies from requirements.txt..."
$VENV_DIR/bin/pip install -r requirements.txt
echo "✅ Dependencies installed."

# 4. Check for .env.local file
ENV_FILE=".env.local"
EXAMPLE_ENV_FILE=".env.example"
if [ ! -f "$ENV_FILE" ]; then
    echo "🔑 Configuration file '$ENV_FILE' not found."
    echo "📄 An example file has been created at '$EXAMPLE_ENV_FILE'."
    echo "👉 Please copy it to '$ENV_FILE' and fill in your details:"
    echo "   cp $EXAMPLE_ENV_FILE $ENV_FILE"
    echo "   nano $ENV_FILE"
    echo "   After editing, re-run this script."
    exit 1
else
    echo "👍 Configuration file '$ENV_FILE' found."
fi

echo "🎉 Setup complete!"
echo "-----------------"
echo "Next steps:"
echo "1. If you haven't already, deploy the app as a service by running:"
echo "   ./deploy.sh"
echo ""
