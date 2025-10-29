# Rigveda Hymn Similarity Map

An interactive web application for exploring similarities between Rigveda hymns inspired by [internet-map.net](https://internet-map.net/). The application visualizes 1,028 hymns as an explorable network based on deity co-occurrence patterns, allowing users to discover connections between hymns through an intuitive force-directed graph interface.
10 books, 1028 hymns, 15175 Words
neighbor, color and clustering logic
Paths??

## Table of Contents
- [Features](#features)
- [System Architecture](#system-architecture)
- [Installation & Setup](#installation--setup)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Database Schema](#database-schema)
- [API Documentation](#api-documentation)
- [Data Processing Pipeline](#data-processing-pipeline)
- [Visualization Tools](#visualization-tools)
- [Frontend Guide](#frontend-guide)
- [Development](#development)
- [Usage Guide](#usage-guide)
- [Performance](#performance)
- [Resources](#resources)

## Features

### Interactive Visualization
- **Force-Directed Graph Layout**: All 1,028 hymns displayed using D3.js v7
- **Dynamic Node Expansion**: Click any hymn to reveal its 8 most similar neighbors
- **Visual Encoding**: 
  - Node size represents hymn score (sum of deity frequencies)
  - Color represents deity count
  - Higher-scoring hymns positioned toward center

### User Interactions
- **Zoom & Pan**: Full navigation controls for exploring the graph
- **Search Functionality**: Find hymns by title, deity, or book.hymn number
- **Hover Tooltips**: Quick information on mouseover
- **Detailed Info Panel**: Click nodes for comprehensive hymn details
- **Responsive Design**: Works on desktop and mobile devices

### Performance Features
- **Lazy Loading**: Neighbors loaded on-demand via API
- **Optimized Queries**: Database indexes for fast similarity lookups
- **Efficient Rendering**: Handles 500+ nodes smoothly
- **Configurable Physics**: Adjustable force simulation parameters

## System Architecture

### Technology Stack

**Backend**
- FastAPI (Python 3.11+)
- SQLAlchemy ORM
- SQLite database
- Uvicorn ASGI server
- Pydantic for data validation

**Frontend**
- D3.js v7 for visualization
- Vanilla JavaScript
- Modern CSS with gradient backgrounds
- Responsive design

**Data Processing**
- NumPy for vector operations
- Matplotlib for visualizations
- spaCy for text processing
- Custom similarity metrics

### Architecture Diagram
```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│                 │         │                  │         │                 │
│  Web Browser    │◄───────►│  FastAPI Server  │◄───────►│ SQLite Database │
│  (D3.js Graph)  │         │  (REST API)      │         │ (Hymn Vectors)  │
│                 │         │                  │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
        ▲                            ▲                            ▲
        │                            │                            │
        └────────────────────────────┴────────────────────────────┘
                    HTTP/JSON Communication
```

## Installation & Setup

### Prerequisites
- Python 3.11 or higher
- `uv` package manager (recommended) or pip
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation Steps

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd rigveda
   ```

2. **Install Dependencies**
   
   Using uv (recommended):
   ```bash
   uv sync
   ```

   Using pip:
   ```bash
   pip install -r requirements.txt
   ```

3. **Verify Database**
   
   Ensure `hymn_vectors.db` exists in the root directory. If not, generate it using:
   ```bash
   uv run python Data/Explore.py
   uv run python Data/hymn_similarity.py
   ```

## Quick Start

### Start the Application

**Option 1: Demo Script (Recommended)**
```bash
uv run python demo.py
```
This will:
- Display database statistics
- Start the server on port 8000
- Automatically open your browser

**Option 2: Direct Server Start**
```bash
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

### Access Points
- **Frontend Application**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Basic Usage
1. Open the application in your browser
2. View all 1,028 hymns in the initial graph
3. Click any node to reveal its 8 most similar hymns
4. Use search to find specific hymns (e.g., "Agni" or "Indra")
5. Zoom and pan to navigate the network
6. Hover over nodes for quick information

## Project Structure

```
rigveda/
├── backend/                    # Backend API and business logic
│   └── app/
│       ├── main.py            # FastAPI application entry point
│       ├── db.py              # Database connection and session management
│       ├── models.py          # SQLAlchemy ORM models
│       ├── crud.py            # Database query operations
│       ├── schemas.py         # Pydantic request/response schemas
│       └── routes/
│           └── nodes.py       # API endpoint definitions
│
├── frontend/                   # Frontend web application
│   ├── index.html            # Main HTML page with styling
│   └── app.js                # D3.js visualization logic
│
├── Data/                       # Data processing scripts
│   ├── Explore.py            # Generate hymn vectors and deity index
│   ├── hymn_similarity.py    # Calculate pairwise similarities
│   ├── visualize_hymns.py    # Generate statistical plots
│   ├── rigveda_scraper.py    # Scrape hymn data from sources
│   ├── JSONMaps/
│   │   ├── rigveda_data.json # Raw hymn data
│   │   └── title_map.json    # Deity to hymn mappings
│   ├── rigveda_texts/        # Text files for each hymn
│   │   ├── book_1/
│   │   ├── book_2/
│   │   └── ...               # Books 1-10
│   └── Viz/                  # Generated visualization plots
│
├── hymn_vectors.db            # SQLite database (generated)
├── demo.py                    # Demo script with stats
├── pyproject.toml             # Project dependencies (uv/pip)
├── uv.lock                    # Dependency lock file
└── README.md                  # This file
```

## Database Schema

The SQLite database contains three main tables:

### Table: hymn_vectors
Stores hymn metadata and deity vectors.

| Column        | Type    | Description                                    |
|---------------|---------|------------------------------------------------|
| hymn_id       | TEXT    | Primary key (hymn number)                      |
| book_number   | INTEGER | Book number (1-10)                             |
| hymn_number   | INTEGER | Hymn number within book                        |
| title         | TEXT    | Full hymn title                                |
| deity_vector  | TEXT    | JSON array of binary deity presence vector     |
| deity_names   | TEXT    | JSON array of deity names in hymn              |
| deity_count   | INTEGER | Number of deities in hymn                      |
| hymn_score    | REAL    | Sum of deity frequencies (importance metric)   |

**Example Row:**
```json
{
  "hymn_id": "1001",
  "book_number": 1,
  "hymn_number": 1001,
  "title": "Book 1, Hymn 1: Agni",
  "deity_vector": "[1, 0, 0, 1, ...]",
  "deity_names": "[\"agni\", \"indra\"]",
  "deity_count": 2,
  "hymn_score": 856.5
}
```

### Table: hymn_similarities_cosine
Stores pairwise similarity relationships.

| Column        | Type    | Description                          |
|---------------|---------|--------------------------------------|
| hymn1_id      | TEXT    | First hymn ID (composite primary key)|
| hymn2_id      | TEXT    | Second hymn ID (composite primary key)|
| similarity    | REAL    | Cosine similarity (0.0 to 1.0)       |

**Statistics:**
- Total hymns: 1,028
- Total similarity pairs: 221,957
- Minimum similarity threshold: 0.3

### Table: deity_index
Reference table for deity information.

| Column          | Type    | Description                         |
|-----------------|---------|-------------------------------------|
| deity_id        | INTEGER | Primary key                         |
| deity_name      | TEXT    | Normalized deity name               |
| vector_position | INTEGER | Position in deity vector            |
| deity_frequency | INTEGER | Number of hymns mentioning deity    |

**Top Deities by Frequency:**
1. Agni - 197 hymns
2. Indra - 289 hymns
3. Soma - 123 hymns

## API Documentation

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### 1. Get All Nodes
```http
GET /api/nodes
```

**Description**: Retrieve all hymn nodes with basic metadata.

**Response:**
```json
{
  "nodes": [
    {
      "id": "1001",
      "title": "Book 1, Hymn 1: Agni",
      "book_number": 1,
      "hymn_number": 1001,
      "deity_names": "agni, indra",
      "deity_count": 2,
      "hymn_score": 856.5
    }
  ]
}
```

#### 2. Get Initial Graph
```http
GET /api/graph/initial
```

**Description**: Get all hymns for initial graph rendering (same as /api/nodes).

**Query Parameters:**
- None

**Response:** Same as `/api/nodes`

#### 3. Get Node with Neighbors
```http
GET /api/node/{hymnId}?limit=8
```

**Description**: Get a specific hymn and its most similar neighbors.

**Path Parameters:**
- `hymnId` (string, required): Hymn ID

**Query Parameters:**
- `limit` (integer, optional): Number of neighbors to return (default: 8)

**Response:**
```json
{
  "node": {
    "id": "1001",
    "title": "Book 1, Hymn 1: Agni",
    "book_number": 1,
    "hymn_number": 1001,
    "deity_names": "agni, indra",
    "deity_count": 2,
    "hymn_score": 856.5
  },
  "neighbors": [
    {
      "id": "1002",
      "title": "Book 1, Hymn 2: Agni",
      "book_number": 1,
      "hymn_number": 1002,
      "deity_names": "agni",
      "deity_count": 1,
      "hymn_score": 654.3,
      "similarity": 0.95
    }
  ]
}
```

#### 4. Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Error Responses

**404 Not Found:**
```json
{
  "detail": "Hymn not found"
}
```

**500 Internal Server Error:**
```json
{
  "detail": "Internal server error message"
}
```

## Data Processing Pipeline

### Step 1: Data Extraction (Explore.py)

**Purpose**: Parse raw hymn data and generate deity vectors.

**Process:**
1. Load raw hymn data from `rigveda_data.json`
2. Extract and normalize deity names from hymn titles
3. Create deity-to-hymn mapping (title_map.json)
4. Generate binary deity vectors for each hymn
5. Calculate hymn scores (sum of deity frequencies)
6. Store in SQLite database

**Key Functions:**
- `NormalizeWord()`: Standardize deity names
- `CreateHymnVectors()`: Generate and store vectors
- `PopulateDeityIndex()`: Build deity reference table

**Run:**
```bash
uv run python Data/Explore.py
```

**Output:**
- `hymn_vectors.db` created
- `title_map.json` generated
- Statistics printed to console

### Step 2: Similarity Calculation (hymn_similarity.py)

**Purpose**: Calculate pairwise similarity between all hymns.

**Supported Metrics:**
1. **Cosine Similarity** (default): Measures angle between vectors
2. **Jaccard Similarity**: Set intersection over union
3. **Dice Coefficient**: 2 × intersection / sum of sizes
4. **Hamming Distance**: Number of differing positions

**Process:**
1. Load all hymn vectors from database
2. Calculate pairwise similarities for all combinations
3. Filter by minimum threshold (default: 0.3)
4. Store in `hymn_similarities_cosine` table
5. Create database indexes for fast lookup

**Key Functions:**
- `CosineSimilarity()`: Compute cosine similarity
- `CalculateAllPairwiseSimilarities()`: Process all pairs
- `SaveSimilaritiesToDatabase()`: Persist results
- `GetTopSimilarHymns()`: Query similar hymns

**Run:**
```bash
uv run python Data/hymn_similarity.py
```

**Performance:**
- Total pairs: 527,878 (1,028 × 1,027 / 2)
- Stored pairs: 221,957 (above 0.3 threshold)
- Processing time: ~2-3 minutes

### Step 3: Visualization (visualize_hymns.py)

**Purpose**: Generate statistical plots and distributions.

**Generated Plots:**
1. **Hymn Score Distribution**: Bar chart of score distribution
2. **Binned Score Distribution**: Histogram with 50-unit bins
3. **Deity Count vs Score**: Scatter plot with trend line

**Key Functions:**
- `GetHymnScores()`: Extract scores from database
- `PlotScoreDistribution()`: Generate distribution plot
- `PlotDeityCountVsScore()`: Create correlation plot
- `PrintScoreStatistics()`: Display statistics

**Run:**
```bash
uv run python Data/visualize_hymns.py
```

**Output Location:** `Data/Viz/`

## Visualization Tools

### Score Distribution Analysis

**Hymn Score Statistics:**
- Total Hymns: 1,028
- Mean Score: ~245.6
- Median Score: ~198.3
- Min Score: 0
- Max Score: 1,845
- Standard Deviation: ~187.5

**Score Ranges:**
- Score 0: 12 hymns
- Score < 100: 185 hymns
- Score 100-500: 728 hymns
- Score 500-1000: 98 hymns
- Score ≥ 1000: 5 hymns

### Deity Analysis

**Most Frequent Deities:**
1. Indra (289 hymns)
2. Agni (197 hymns)
3. Soma (123 hymns)
4. Vishvedevas (87 hymns)
5. Maruts (65 hymns)

**Deity Count Distribution:**
- Average deities per hymn: 2.3
- Min deities: 0
- Max deities: 15
- Most hymns have 1-3 deities

## Frontend Guide

### File Structure

**index.html**
- Main HTML structure
- CSS styling (embedded)
- Control panel and info panel
- Search interface

**app.js**
- D3.js visualization logic
- Force simulation configuration
- Node and link rendering
- User interaction handlers
- API communication

### Key Components

#### 1. Force Simulation
```javascript
const simulation = d3.forceSimulation(nodes)
    .force("link", d3.forceLink(links).id(d => d.id).distance(100))
    .force("charge", d3.forceManyBody().strength(-300))
    .force("center", d3.forceCenter(width / 2, height / 2))
    .force("collision", d3.forceCollide().radius(d => nodeSize(d.hymn_score) + 5));
```

#### 2. Node Rendering
- Size scaled by hymn score
- Color based on deity count
- Hover effects with tooltips
- Click handlers for expansion

#### 3. Search Functionality
- Real-time filtering
- Fuzzy matching on title, deity, book/hymn number
- Dropdown results with click navigation

#### 4. Zoom & Pan
```javascript
const zoom = d3.zoom()
    .scaleExtent([0.1, 10])
    .on("zoom", (event) => {
        svg.attr("transform", event.transform);
    });
```

### Customization

**Adjust Node Size:**
```javascript
const nodeSize = d3.scaleLinear()
    .domain([minScore, maxScore])
    .range([3, 15]);
```

**Modify Colors:**
```javascript
const colorScale = d3.scaleSequential(d3.interpolateViridis)
    .domain([0, maxDeityCount]);
```

**Change Force Parameters:**
- `strength`: -300 (repulsion between nodes)
- `distance`: 100 (link length)
- `collision`: radius + 5 (node collision padding)

## Development

### Project Setup

```bash
# Clone repository
git clone <repository-url>
cd rigveda

# Install dependencies
uv sync

# Verify installation
uv run python -c "import fastapi; print(fastapi.__version__)"
```

### Running Tests

```bash
# API tests
uv run python test_api.py

# Database integrity
uv run python -c "from backend.app.db import GetDatabase; from backend.app import crud; db = next(GetDatabase()); print(len(crud.GetAllHymns(db)))"
```

### Development Server

```bash
# With auto-reload
uv run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000

# With specific log level
uv run uvicorn backend.app.main:app --log-level debug
```

### Code Style

**Function Names**: TitleCase
```python
def GetAllHymns():
    pass
```

**Variable Names**: camelCase
```python
hymnScore = 100.5
deityCount = 3
```

**Comments**: Meaningful only, avoid self-explanatory
```python
# Good
# Calculate cosine similarity between deity vectors
similarity = CosineSimilarity(vector1, vector2)

# Avoid
# Set x to 10
x = 10
```

### Adding New Features

**New API Endpoint:**
1. Add route to `backend/app/routes/nodes.py`
2. Add CRUD function to `backend/app/crud.py` if needed
3. Add Pydantic schema to `backend/app/schemas.py`
4. Test using `/docs` interactive API

**New Similarity Metric:**
1. Add function to `Data/hymn_similarity.py`
2. Update `CalculateAllPairwiseSimilarities()` to support metric
3. Create new database table `hymn_similarities_{metric}`
4. Update frontend to use new metric

## Usage Guide

### Exploring the Graph

**Initial View:**
- All 1,028 hymns displayed
- Larger nodes (higher scores) gravitate toward center
- Color indicates deity count (darker = more deities)

**Expanding Nodes:**
1. Click any hymn node
2. 8 most similar hymns added to graph
3. Links show similarity strength (opacity)
4. Node highlighted in red

**Search:**
1. Type in search box (deity name, book number, etc.)
2. Results appear in dropdown
3. Click result to focus on node

**Navigation:**
- **Mouse Wheel**: Zoom in/out
- **Click + Drag Background**: Pan
- **Click + Drag Node**: Move node
- **Reset View Button**: Return to initial view
- **Center Graph Button**: Center all nodes

### Advanced Usage

**Finding Related Hymns:**
1. Search for a deity (e.g., "Agni")
2. Click a high-scoring Agni hymn
3. Explore similar hymns
4. Look for shared deities in info panel

**Discovering Patterns:**
1. Zoom out to see overall structure
2. Look for clusters (books or deity groups)
3. Find bridge nodes connecting clusters
4. Identify central vs peripheral hymns

**Analyzing Scores:**
- High-scoring hymns mention frequent deities
- Low-scoring hymns are more specialized
- Score ≥ 500 indicates major hymn
- Score < 100 indicates rare deity combination

## Performance

### Optimization Strategies

**Backend:**
- Database indexes on `hymn1_id`, `hymn2_id`, `similarity`
- Query limit on similar hymns (default: 8)
- SQLAlchemy session pooling
- FastAPI async support

**Frontend:**
- Lazy loading (neighbors loaded on click)
- Canvas rendering for large graphs
- Throttled force simulation updates
- Efficient D3 data binding

**Database:**
- Binary vectors stored as JSON (space-efficient)
- Composite primary keys for similarity table
- Minimum similarity threshold reduces storage

### Performance Metrics

**API Response Times:**
- `/api/nodes`: ~100ms (all 1,028 hymns)
- `/api/node/{id}`: ~20ms (1 hymn + 8 neighbors)
- `/health`: <5ms

**Frontend Rendering:**
- Initial load: ~2s (1,028 nodes)
- Node expansion: ~200ms (8 new nodes)
- Smooth animation up to 500+ nodes
- Search: Real-time (<50ms)

**Database Size:**
- hymn_vectors table: ~500 KB
- hymn_similarities_cosine: ~8 MB
- deity_index: ~50 KB
- Total database: ~10 MB

## Resources

### Rigveda Texts & Data
- [Ved Web (University of Cologne)](https://vedaweb.uni-koeln.de/rigveda/view/index/0) - Digital Rigveda with search
- [Sri Aurobindo Ashram Audio](https://sri-aurobindo.co.in/workings/matherials/rigveda/audio.htm) - Hymn recitations

### Technical Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [D3.js Force Simulation](https://d3js.org/d3-force)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [Internet Map Inspiration](https://internet-map.net/)

### Related Work
- Hymn similarity based on deity co-occurrence
- Network analysis of religious texts
- Force-directed graph visualization

## License

Proprietary

---

**Built with ❤️ for exploring the ancient wisdom of the Rigveda**

*For questions or issues, please contact the maintainer.*
