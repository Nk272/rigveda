#!/bin/bash

echo "=========================================="
echo "Rigveda Frontend Setup Script"
echo "=========================================="
echo ""

cd rigveda-frontend

echo "Step 1: Installing dependencies..."
npm install

echo ""
echo "=========================================="
echo "Frontend setup complete!"
echo "=========================================="
echo ""
echo "To start the development server:"
echo "  1. cd rigveda-frontend"
echo "  2. npm start"
echo ""
echo "The app will open at http://localhost:3000"
echo ""
echo "Note: Make sure the Django backend is running"
echo "      on http://localhost:8000 before starting"
echo ""
