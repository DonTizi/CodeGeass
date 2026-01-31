#!/bin/bash
# Build the dashboard frontend and copy to the package static directory
#
# This script should be run before every release to ensure the bundled
# dashboard is up-to-date with the frontend source code.

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

FRONTEND_DIR="$PROJECT_ROOT/dashboard/frontend"
STATIC_DIR="$PROJECT_ROOT/src/codegeass/dashboard/static"

echo "=== Building CodeGeass Dashboard ==="
echo ""

# Check if frontend directory exists
if [ ! -d "$FRONTEND_DIR" ]; then
    echo "Error: Frontend directory not found: $FRONTEND_DIR"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed"
    exit 1
fi

# Step 1: Install dependencies
echo "[1/4] Installing dependencies..."
cd "$FRONTEND_DIR"
npm install --silent

# Step 2: Build the frontend
echo "[2/4] Building frontend (this may take a moment)..."
npm run build

# Step 3: Clear old static files
echo "[3/4] Clearing old static files..."
rm -rf "$STATIC_DIR/assets"
rm -f "$STATIC_DIR/index.html"

# Step 4: Copy new build
echo "[4/4] Copying new build..."
cp -r "$FRONTEND_DIR/dist/"* "$STATIC_DIR/"

echo ""
echo "=== Dashboard build complete ==="
echo "Static files: $STATIC_DIR"
echo ""

# Verify the build contains expected features
if grep -q "Code Source" "$STATIC_DIR/assets/"*.js 2>/dev/null; then
    echo "Verified: Code Source field present"
else
    echo "Warning: Code Source field not found in build"
fi

if grep -q "code_source" "$STATIC_DIR/assets/"*.js 2>/dev/null; then
    echo "Verified: code_source API field present"
else
    echo "Warning: code_source API field not found in build"
fi

echo ""
echo "Don't forget to commit the changes:"
echo "  git add src/codegeass/dashboard/static/"
echo "  git commit -m 'build: update dashboard static files'"
