#!/bin/bash

echo "=========================================="
echo "Rigveda Backend Setup Script"
echo "=========================================="
echo ""

cd rigveda_backend

echo "Step 1: Creating virtual environment..."
python3 -m venv venv

echo ""
echo "Step 2: Activating virtual environment..."
source venv/bin/activate

echo ""
echo "Step 3: Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Step 4: Running migrations..."
python manage.py makemigrations
python manage.py migrate

echo ""
echo "Step 5: Loading data from JSON files..."
python manage.py load_data --data-dir=../

echo ""
echo "=========================================="
echo "Backend setup complete!"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  1. cd rigveda_backend"
echo "  2. source venv/bin/activate"
echo "  3. python manage.py runserver"
echo ""
echo "Optional: Create superuser for admin access"
echo "  python manage.py createsuperuser"
echo ""
