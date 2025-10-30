#!/bin/bash
# Start the Rigveda Hymn Similarity API server

cd "$(dirname "$0")"

echo "Starting Rigveda Hymn Similarity API..."
echo "Server will be available at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
