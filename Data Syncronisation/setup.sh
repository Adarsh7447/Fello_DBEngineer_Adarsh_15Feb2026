#!/bin/bash
# Quick setup script for production database deployment

set -e

echo "=========================================="
echo "Database Deployment Setup"
echo "=========================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 is not installed. Please install pip."
    exit 1
fi

echo "✓ pip3 found"
echo ""

# Install dependencies
echo "Installing Python dependencies..."
pip3 install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found"
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "✓ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your database credentials"
    echo "   Run: nano .env"
    echo ""
    read -p "Press Enter to edit .env now, or Ctrl+C to exit and edit later..."
    ${EDITOR:-nano} .env
else
    echo "✓ .env file exists"
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Verify your .env file has correct DATABASE_URL"
echo "2. Run deployment:"
echo "   python3 deploy.py --full"
echo ""
echo "For more options, see:"
echo "   python3 deploy.py --help"
echo ""
