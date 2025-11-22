#!/usr/bin/env bash
# Quick start script for local FileCherry development testing

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}FileCherry Local Dev Setup${NC}"
echo "================================"
echo ""

# Check prerequisites
echo "Checking prerequisites..."

if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found"
    exit 1
fi

if ! command -v node &> /dev/null; then
    echo "❌ Node.js not found"
    exit 1
fi

if ! systemctl is-active --quiet ollama 2>/dev/null && ! pgrep -x ollama > /dev/null; then
    echo -e "${YELLOW}⚠️  Ollama doesn't appear to be running${NC}"
    echo "   Starting Ollama..."
    ollama serve > /dev/null 2>&1 &
    sleep 2
fi

echo "✅ Prerequisites OK"
echo ""

# Setup Python environment
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

echo "Activating Python environment..."
source .venv/bin/activate

# Install Python deps if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "Installing Python dependencies..."
    pip install -U pip -q
    pip install -r requirements.txt -q
fi

# Setup dev-data directory
echo "Setting up dev-data directory..."
mkdir -p dev-data/{inputs,outputs,config,logs,runtime}
export FILECHERRY_DATA_DIR="$PROJECT_ROOT/dev-data"

# Check if test file exists
if [ ! -f "dev-data/inputs/test.txt" ]; then
    echo "Creating test file..."
    echo "This is a test document for FileCherry." > dev-data/inputs/test.txt
fi

# Install UI deps if needed
if [ ! -d "apps/ui/node_modules" ]; then
    echo "Installing UI dependencies..."
    cd apps/ui
    npm install --silent
    cd "$PROJECT_ROOT"
fi

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To start FileCherry, open TWO terminals and run:"
echo ""
echo -e "${YELLOW}Terminal 1 - Orchestrator:${NC}"
echo "  cd $PROJECT_ROOT"
echo "  source .venv/bin/activate"
echo "  export FILECHERRY_DATA_DIR=\$PWD/dev-data"
echo "  python -m src.orchestrator.main"
echo ""
echo -e "${YELLOW}Terminal 2 - UI:${NC}"
echo "  cd $PROJECT_ROOT/apps/ui"
echo "  npm run dev"
echo ""
echo "Then open: ${GREEN}http://localhost:3000${NC}"
echo ""
echo "For full instructions, see: TESTING.md"

