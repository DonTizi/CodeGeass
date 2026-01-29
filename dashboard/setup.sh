#!/bin/bash
# Setup script for CodeGeass Dashboard

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Setting up CodeGeass Dashboard..."

# Backend setup
echo ""
echo "Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

cd ..

# Frontend setup
echo ""
echo "Setting up frontend..."
cd frontend

if command -v npm &> /dev/null; then
    npm install
else
    echo "Warning: npm not found. Please install Node.js and run 'npm install' in the frontend directory."
fi

cd ..

echo ""
echo "Setup complete!"
echo ""
echo "To run the dashboard:"
echo "  ./run.sh"
echo ""
echo "Or run separately:"
echo "  Backend:  cd backend && source venv/bin/activate && uvicorn main:app --port 8001 --reload"
echo "  Frontend: cd frontend && npm run dev"
