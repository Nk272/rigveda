# Rigveda Interactive Web App - Setup Guide

## Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

---

## Phase 1: Data Processing

### Step 1: Generate Relationship Matrix

```bash
# Make sure you're in the project root
cd /Users/nikunjgoyal/Codes/rigveda

# Run the relationship builder script
python relationship_builder.py
```

This will generate the following files:
- `entities.json` - All extracted entities with metadata
- `attribute_clusters.json` - Grouped similar attributes
- `relationship_matrix.json` - Full NxN relationship matrix
- `entity_relationships_optimized.json` - Optimized relationships for API
- `relationship_metadata.json` - Statistics and metadata

**Expected Output:**
- ~200-300 entities (deities + attributes)
- ~2000-5000 relationships
- Processing time: 5-15 minutes depending on your machine

---

## Phase 2: Backend Setup (Django)

### Step 1: Create Virtual Environment

```bash
cd rigveda_backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 4: Load Data into Database

```bash
# Load entities and relationships from JSON files
python manage.py load_data --data-dir=../

# This command will:
# - Clear existing data
# - Load all entities
# - Load all relationships
# - Create database indexes
```

### Step 5: Create Admin User (Optional)

```bash
python manage.py createsuperuser
```

### Step 6: Run Django Server

```bash
python manage.py runserver
```

The API will be available at: `http://localhost:8000/api/`

**API Endpoints:**
- `GET /api/entities/` - List all entities
- `GET /api/entities/{id}/` - Entity details
- `GET /api/entities/{id}/relationships/` - Entity relationships
- `POST /api/entities/search/` - Search entities
- `GET /api/relationships/` - List relationships
- `GET /api/stats/` - Global statistics

---

## Phase 3: Frontend Setup (React)

### Step 1: Install Dependencies

```bash
cd rigveda-frontend

npm install
```

### Step 2: Start Development Server

```bash
npm start
```

The app will open at: `http://localhost:3000`

---

## Using the Application

### 1. Landing Page
- You'll see animated bubbles representing entities
- Bubble size indicates frequency
- Colors represent entity types:
  - **Gold** - Deities
  - **Green** - Attributes
  - **Blue** - Rishis

### 2. Exploring Relationships
1. **Click on any bubble** to select it
2. The bubble moves to center
3. Related entities appear around it
4. Lines show relationship strength (thickness = score)
5. Side panel shows detailed information

### 3. Viewing Relationship Details
1. Click on a related entity bubble
2. See detailed score breakdown:
   - Conjunction score
   - Hymn co-occurrence score
   - Indirect association score
3. View hymn references where they co-occur
4. See conjunction examples

### 4. Navigation
- Click the center bubble again to deselect
- Use the **X** button in side panel to close
- Click **Back** button to return to relationships list

---

## Project Structure

```
rigveda/
├── PROJECT_PLAN.md                    # Comprehensive project plan
├── SETUP_GUIDE.md                     # This file
├── relationship_builder.py            # Data processing script
├── rigveda_data.json                  # Source data
│
├── rigveda_backend/                   # Django Backend
│   ├── manage.py
│   ├── requirements.txt
│   ├── rigveda_backend/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── api/
│       ├── models.py                  # Entity & Relationship models
│       ├── serializers.py             # DRF serializers
│       ├── views.py                   # API views
│       ├── urls.py                    # API routes
│       └── management/
│           └── commands/
│               └── load_data.py       # Data loading command
│
└── rigveda-frontend/                  # React Frontend
    ├── package.json
    ├── public/
    │   └── index.html
    └── src/
        ├── App.js                     # Main app component
        ├── components/
        │   ├── BubbleVisualization.jsx  # D3 bubble visualization
        │   └── InfoPanel.jsx            # Side information panel
        ├── services/
        │   └── api.js                   # API client
        └── store/
            └── entityStore.js           # Zustand state management
```

---

## Troubleshooting

### Backend Issues

**Issue:** ModuleNotFoundError
```bash
# Make sure virtual environment is activated
source venv/bin/activate
pip install -r requirements.txt
```

**Issue:** Database errors
```bash
# Delete and recreate database
rm db.sqlite3
python manage.py migrate
python manage.py load_data --data-dir=../
```

**Issue:** CORS errors
- Make sure Django server is running on port 8000
- Check `CORS_ALLOWED_ORIGINS` in settings.py

### Frontend Issues

**Issue:** API connection errors
- Ensure Django backend is running
- Check `proxy` setting in package.json
- Verify API_BASE_URL in src/services/api.js

**Issue:** npm install errors
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue:** Bubbles not rendering
- Check browser console for errors
- Ensure entities are loaded (check Network tab)
- Verify D3.js is properly installed

---

## Performance Optimization

### Backend
- Database indexes are created automatically
- Caching is enabled for frequently accessed data
- Pagination limits large datasets

### Frontend
- Uses React.memo for expensive components
- D3 force simulation optimized for 100+ bubbles
- Relationship data is lazy-loaded

---

## Development Tips

### Backend Development
```bash
# Access Django admin panel
http://localhost:8000/admin/

# Run tests (when implemented)
python manage.py test

# View API documentation
http://localhost:8000/api/
```

### Frontend Development
```bash
# Build for production
npm run build

# Run tests (when implemented)
npm test
```

---

## Next Steps

### Enhancements
1. Add search functionality
2. Implement filtering by entity type
3. Add export features
4. Include audio playback of hymns
5. Multi-language support

### Deployment
1. Set up PostgreSQL database
2. Configure production Django settings
3. Build React app for production
4. Deploy to cloud platform (AWS, Heroku, etc.)

---

## Contact & Support

For issues or questions:
1. Check this guide
2. Review PROJECT_PLAN.md
3. Check browser/server console logs
4. Review Django admin panel for data issues
