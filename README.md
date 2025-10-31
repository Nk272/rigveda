# Rigveda Hymn Similarity Map

An interactive web visualization exploring similarities between Rigveda hymns based on deity co-occurrence patterns. Browse 1,028 hymns from 10 books as an explorable network graph.

## Features

- **Interactive Network Graph**: Explore all 1,028 hymns using a D3.js force-directed layout
- **Dynamic Exploration**: Click any hymn to reveal its 8 most similar neighbors
- **Smart Search**: Find hymns by title, deity name, or book.hymn number
- **Visual Encoding**: Node size indicates hymn importance, color shows deity count
- **Zoom & Pan**: Full navigation controls for detailed exploration
- **Detailed Info**: Hover tooltips and click-to-expand details for each hymn

## Quick Start

### Prerequisites
- Python 3.11 or higher
- `uv` package manager (or pip)

### Installation

```bash
# Clone repository
git clone <repository-url>
cd rigveda

# Install dependencies
uv sync
```

### Run Application

```bash
# Start server and open browser
uv run python demo.py
```

The application will be available at http://localhost:8000

### Alternative Start

```bash
# Start server manually
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Technology Stack

**Backend**: FastAPI, SQLAlchemy, SQLite, Uvicorn
**Frontend**: D3.js v7, Vanilla JavaScript
**Data Processing**: NumPy, Matplotlib, spaCy

## Project Structure

```
rigveda/
├── backend/app/          # FastAPI application
│   ├── main.py          # Entry point
│   ├── models.py        # Database models
│   ├── crud.py          # Database queries
│   └── routes/          # API endpoints
├── frontend/            # Web interface
│   ├── index.html      # Main page
│   └── app.js          # D3.js visualization
├── Data/               # Data processing scripts
│   ├── Explore.py      # Generate hymn vectors
│   ├── hymn_similarity.py  # Calculate similarities
│   └── JSONMaps/       # Source data
├── hymn_vectors.db     # SQLite database
└── demo.py             # Quick start script
```

## Usage

1. Open the application in your browser
2. View all 1,028 hymns in the initial graph
3. Click any node to reveal its similar hymns
4. Search for specific hymns or deities
5. Zoom and pan to navigate the network

## API Documentation

Interactive API documentation available at http://localhost:8000/docs

**Main Endpoints:**
- `GET /api/nodes` - Get all hymns
- `GET /api/node/{hymnId}?limit=8` - Get hymn with neighbors
- `GET /health` - Health check

## Data

- **10 Books**: Complete Rigveda collection
- **1,028 Hymns**: All hymns with deity metadata
- **221,957 Similarities**: Pairwise relationships (threshold ≥ 0.3)
- **15,175 Words**: Total word count across all hymns

## License

Proprietary
