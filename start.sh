#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# A2 Intelligence Risk Analytics Platform — Startup Script
# Usage: ./start.sh
# ──────────────────────────────────────────────────────────────────────────────
set -e

PROJECT_ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
BACKEND_PORT=8001
FRONTEND_PORT=3000

echo ""
echo "  ============================================"
echo "   A2 Intelligence Risk Analytics Platform"
echo "   by AA Impact Inc."
echo "  ============================================"
echo ""

# ── Pre-flight checks ────────────────────────────────────────────────────────
echo "[1/4] Checking prerequisites..."
command -v python3 >/dev/null 2>&1 || { echo "ERROR: python3 not found"; exit 1; }
command -v node >/dev/null 2>&1    || { echo "ERROR: node not found"; exit 1; }

if [ ! -f "$BACKEND_DIR/.env" ]; then
  echo "ERROR: backend/.env not found. Configure DATABASE_URL."
  exit 1
fi

# ── Frontend dependencies ─────────────────────────────────────────────────────
echo "[2/4] Checking frontend dependencies..."
if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
  echo "  Installing frontend dependencies (first run only)..."
  cd "$FRONTEND_DIR" && npm install --legacy-peer-deps
fi

# ── Start backend ─────────────────────────────────────────────────────────────
echo "[3/4] Starting backend on port $BACKEND_PORT..."
cd "$BACKEND_DIR"
python3 -m uvicorn server:app --host 0.0.0.0 --port "$BACKEND_PORT" &
BACKEND_PID=$!

# Wait for backend
echo "  Waiting for backend..."
for i in $(seq 1 30); do
  if curl -s -o /dev/null http://127.0.0.1:$BACKEND_PORT/api/health 2>/dev/null; then
    echo "  Backend is live at http://localhost:$BACKEND_PORT"
    break
  fi
  sleep 1
done

# ── Start frontend ────────────────────────────────────────────────────────────
echo "[4/4] Starting frontend on port $FRONTEND_PORT..."
cd "$FRONTEND_DIR"
BROWSER=none npm start &
FRONTEND_PID=$!

echo ""
echo "  ============================================"
echo "   Platform is running!"
echo ""
echo "   Frontend:  http://localhost:$FRONTEND_PORT"
echo "   Backend:   http://localhost:$BACKEND_PORT"
echo "   API Docs:  http://localhost:$BACKEND_PORT/docs"
echo ""
echo "   Press Ctrl+C to stop both servers."
echo "  ============================================"
echo ""

# ── Graceful shutdown ─────────────────────────────────────────────────────────
cleanup() {
  echo ""
  echo "Shutting down..."
  kill $BACKEND_PID 2>/dev/null
  kill $FRONTEND_PID 2>/dev/null
  wait
  echo "Done."
}
trap cleanup INT TERM
wait
