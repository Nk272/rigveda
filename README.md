# Rigveda Hymn Similarity Map

An interactive web application for exploring similarities between Rigveda hymns, inspired by [internet-map.net](https://internet-map.net/). The application visualizes hymns as nodes in a force-directed graph where users can click to explore similar hymns.

## Features

- **Interactive Graph Visualization**: Force-directed layout using D3.js
- **Node Expansion**: Click any hymn to reveal its most similar neighbors
- **Visual Encoding**: Node size represents hymn score, color represents deity count
- **Zoom & Pan**: Full navigation controls for exploring the graph
- **Detailed Information**: Hover tooltips and detailed info panel
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Start the Server**:
   ```bash
   uv run python run_server.py
   ```

3. **Open the Application**:
   - Frontend: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

## Architecture

### Backend (FastAPI + SQLite)
- **FastAPI** for REST API endpoints
- **SQLAlchemy** ORM for database access
- **SQLite** database with 1,028 hymns and 221,957 similarity relationships

### Frontend (D3.js)
- **D3.js v7** for interactive graph visualization
- **Force-directed layout** with customizable forces
- **Responsive design** with modern UI

### Database Structure
- `hymn_vectors`: Hymn metadata and deity information
- `hymn_similarities_cosine`: Pairwise cosine similarities
- `deity_index`: Deity reference data

## API Endpoints

- `GET /api/nodes` - Get all hymn nodes
- `GET /api/graph/initial?limit=20` - Get initial graph subset
- `GET /api/node/{id}?limit=8` - Get hymn and its similar neighbors
- `GET /health` - Health check endpoint

## Data

The project includes:
- **1,028 Rigveda hymns** with metadata
- **221,957 similarity relationships** based on deity co-occurrence
- **Deity vectors** for each hymn
- **Hymn scores** based on deity richness

## Development

### Testing
```bash
uv run python test_api.py
```

### Project Structure
```
rigveda/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI application
│       ├── db.py            # Database connection
│       ├── models.py        # SQLAlchemy models
│       ├── crud.py          # Database queries
│       ├── schemas.py       # Pydantic schemas
│       └── routes/
│           └── nodes.py     # API endpoints
├── frontend/
│   ├── index.html          # Main HTML page
│   └── app.js              # D3.js visualization
├── hymn_vectors.db         # SQLite database
└── run_server.py           # Server startup script
```

## Usage

1. **Initial View**: The map loads all 1,028 hymns with larger nodes (higher scores) positioned toward the center
2. **Explore**: Click any node to reveal its 8 most similar hymns
3. **Navigate**: Use mouse to zoom and pan around the graph
4. **Information**: Hover over nodes for quick info, click for detailed panel
5. **Search**: Use the search bar to find specific hymns by title, deity, or book.hymn number
6. **Controls**: Use the control panel to reset view or center the graph

## Performance

- **Lazy Loading**: Neighbors loaded on-demand
- **Optimized Queries**: Database indexes for fast similarity lookups
- **Efficient Rendering**: D3.js handles up to 500+ nodes smoothly
- **Force Simulation**: Configurable physics for optimal layout


https://sri-aurobindo.co.in/workings/matherials/rigveda/audio.htm
Audios
https://vedaweb.uni-koeln.de/rigveda/view/index/0


license
proritary
