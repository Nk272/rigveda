#!/bin/bash

echo "=========================================="
echo "Starting Rigveda Web App"
echo "=========================================="
echo ""

echo "Starting Django backend..."
cd rigveda_backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!

sleep 3

echo ""
echo "Starting React frontend..."
cd ../rigveda-frontend
npm start &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "Both servers started!"
echo "=========================================="
echo ""
echo "Backend:  http://localhost:8000/api/"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

trap "kill $BACKEND_PID $FRONTEND_PID; exit" INT

wait
