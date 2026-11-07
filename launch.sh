#!/usr/bin/env bash
# ==============================================================================
# Job Hunter Studio — 1-Click Native Launcher
# Concurrently boots FastAPI backend (:8000) and Next.js 16 frontend (:3000)
# ==============================================================================

set -e

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"

echo "=========================================================="
echo "  🚀 Starting Job Hunter Studio"
echo "  Autonomous Headhunter & Multi-Channel Pitch Engine"
echo "=========================================================="

# 1. Sense Python (prefer Python 3.11 if present, else python3)
PYTHON_BIN=""
if command -v python3.11 >/dev/null 2>&1; then
    PYTHON_BIN="python3.11"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "❌ Error: Python 3 is not installed or not in PATH."
    exit 1
fi

echo "✓ Using Python: $($PYTHON_BIN --version)"

# 2. Sense Node.js & npm
if ! command -v node >/dev/null 2>&1; then
    echo "❌ Error: Node.js is not installed."
    exit 1
fi
if ! command -v npm >/dev/null 2>&1; then
    echo "❌ Error: npm is not installed."
    exit 1
fi
echo "✓ Using Node.js: $(node -v) / npm: $(npm -v)"

# 3. Setup Backend Virtual Environment
VENV_DIR="$BACKEND_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating backend virtual environment..."
    if command -v uv >/dev/null 2>&1; then
        uv venv "$VENV_DIR" --python "$PYTHON_BIN"
    else
        "$PYTHON_BIN" -m venv "$VENV_DIR"
    fi
fi

# 4. Install backend dependencies
echo "🔍 Checking backend dependencies..."
if command -v uv >/dev/null 2>&1; then
    uv pip install -r "$BACKEND_DIR/requirements.txt" --python "$VENV_DIR/bin/python" -q
else
    "$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt" -q
fi

# 5. Install frontend dependencies if missing
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "📦 Installing frontend dependencies (npm install)..."
    (cd "$FRONTEND_DIR" && npm install)
fi

# 6. Trap SIGINT and SIGTERM to kill both servers cleanly
cleanup() {
    echo ""
    echo "🛑 Shutting down Job Hunter Studio processes..."
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null || true
    fi
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null || true
    fi
    wait "$BACKEND_PID" 2>/dev/null || true
    wait "$FRONTEND_PID" 2>/dev/null || true
    echo "✓ Graceful shutdown complete. See you next hunt!"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 7. Start FastAPI Backend on Port 8000
echo "⚡ Starting FastAPI Backend on http://localhost:8000 ..."
(cd "$BACKEND_DIR" && "$VENV_DIR/bin/uvicorn" app.main:app --host 0.0.0.0 --port 8000 --reload) &
BACKEND_PID=$!

# Wait briefly for backend to initialize
sleep 2

# 8. Start Next.js Frontend on Port 3000
echo "💻 Starting Next.js Frontend on http://localhost:3000 ..."
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "=========================================================="
echo "  🎉 Job Hunter Studio is Live!"
echo "  👉 Command Center UI:     http://localhost:3000"
echo "  👉 Interactive API Docs:  http://localhost:8000/docs"
echo "  Press Ctrl+C to stop all servers."
echo "=========================================================="
echo ""

# Keep launcher process running to supervise child processes
wait
