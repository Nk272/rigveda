# 🚀 Quick Start Guide

Get the Rigveda Interactive Web App running in 3 simple steps!

---

## Prerequisites Check

Before starting, ensure you have:
- ✅ Python 3.8+ installed (`python3 --version`)
- ✅ Node.js 16+ installed (`node --version`)
- ✅ npm installed (`npm --version`)

---

## 🎯 Three-Step Setup

### Step 1: Process the Data (5-15 minutes)

```bash
./run_data_processing.sh
```

This will analyze the Rigveda texts and generate relationship data.

**Output Files:**
- `entities.json` - All entities (deities, attributes)
- `entity_relationships_optimized.json` - Relationship data
- `relationship_matrix.json` - Full relationship matrix

---

### Step 2: Set Up Backend (2-3 minutes)

```bash
./setup_backend.sh
```

This will:
- Create Python virtual environment
- Install Django and dependencies
- Set up database
- Load the processed data

---

### Step 3: Set Up Frontend (1-2 minutes)

```bash
./setup_frontend.sh
```

This will install all React dependencies.

---

## ▶️ Running the App

### Start Both Servers
```bash
./start_all.sh
```

OR start them separately:

### Terminal 1: Backend
```bash
cd rigveda_backend
source venv/bin/activate
python manage.py runserver
```

### Terminal 2: Frontend
```bash
cd rigveda-frontend
npm start
```

---

## 🌐 Access the Application

Open your browser to:
- **Web App**: http://localhost:3000
- **API**: http://localhost:8000/api/
- **Admin Panel**: http://localhost:8000/admin/

---

## 🎮 Using the App

1. **Landing Page**: See all entities as floating bubbles
2. **Click a Bubble**: Explore its relationships
3. **Click Related Bubble**: See detailed connection info
4. **Side Panel**: View scores, hymn references, and examples
5. **Click X or center**: Return to overview

---

## 🐛 Troubleshooting

### Backend won't start
```bash
cd rigveda_backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
```

### Frontend won't start
```bash
cd rigveda-frontend
rm -rf node_modules package-lock.json
npm install
```

### Data not loading
```bash
cd rigveda_backend
python manage.py load_data --data-dir=../
```

---

## 📚 Next Steps

- Read [README_WEBAPP.md](README_WEBAPP.md) for full documentation
- Check [SETUP_GUIDE.md](SETUP_GUIDE.md) for detailed instructions
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for technical details

---

**Happy Exploring! 🕉️**
