# Rigveda Interactive Word Relationship Web App

## Project Overview
An interactive web application that visualizes relationships between named entities and important words in the Rigveda, using animated bubble graphics with relationship scoring based on co-occurrence patterns.

## Tech Stack
- **Frontend**: React.js with D3.js/Three.js for visualization
- **Backend**: Django REST Framework
- **Database**: SQLite (for development) / PostgreSQL (for production)
- **Data Processing**: Python (NLTK, NetworkX)

---

## Phase 1: Data Processing & Relationship Matrix
**Goal**: Build a comprehensive relationship matrix with normalized scores (0-1)

### 1.1 Named Entity Extraction & Attribute Clustering
- **Input**: rigveda_data.json
- **Process**:
  - Extract named entities (deities, rishis, places)
  - Identify attribute words (strength, might, power, glory, etc.)
  - Use NLTK WordNet to cluster similar attributes
  - Merge semantically similar words using existing analyzer
- **Output**: 
  - `entities.json`: List of all entities with metadata
  - `attributes_clusters.json`: Grouped attributes by semantic similarity

### 1.2 Relationship Scoring Algorithm
**Three-tier scoring system** (weights in descending order):

#### Tier 1: Conjunction Co-occurrence (Weight: 0.5)
- Words appearing together with conjunctions: "and", "with", "or"
- Pattern: "word1 and word2" in same sentence
- Example: "Indra and Agni" → highest correlation

#### Tier 2: Hymn Co-occurrence (Weight: 0.3)
- Words appearing in the same hymn
- Frequency-based: more co-occurrences = higher score
- Normalized by hymn count

#### Tier 3: Indirect Association (Weight: 0.2)
- Words sharing common associated terms
- Second-degree relationships
- Network analysis using graph theory

**Formula**:
```
final_score = (conjunction_score * 0.5) + 
              (hymn_cooccurrence_score * 0.3) + 
              (indirect_association_score * 0.2)

Normalized to [0, 1] range
```

### 1.3 Output Files
- `relationship_matrix.json`: Full NxN matrix
- `entity_relationships.json`: Optimized relationships above threshold (0.1)
- `relationship_metadata.json`: Statistics and analysis

---

## Phase 2: Backend Development (Django)
**Goal**: RESTful API for serving relationship data

### 2.1 Django Project Setup
```
rigveda_backend/
├── manage.py
├── rigveda_backend/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── utils.py
└── requirements.txt
```

### 2.2 Data Models
```python
class Entity:
    - id
    - name
    - type (deity/rishi/attribute)
    - frequency
    - description
    - metadata

class Relationship:
    - id
    - entity1_id (FK)
    - entity2_id (FK)
    - score (0-1)
    - conjunction_score
    - hymn_cooccurrence_score
    - indirect_score
    - hymn_references []
```

### 2.3 API Endpoints
```
GET  /api/entities/                    # List all entities
GET  /api/entities/{id}/               # Entity detail
GET  /api/entities/{id}/relationships/ # Entity relationships
GET  /api/relationships/               # All relationships (paginated)
POST /api/search/                      # Search entities
GET  /api/stats/                       # Global statistics
```

### 2.4 Features
- Pagination for large datasets
- Caching with Django cache framework
- CORS enabled for React frontend
- API documentation with DRF browsable API

---

## Phase 3: Frontend Development (React)
**Goal**: Interactive bubble visualization with relationship exploration

### 3.1 Project Structure
```
rigveda-frontend/
├── public/
├── src/
│   ├── components/
│   │   ├── BubbleVisualization.jsx
│   │   ├── EntityBubble.jsx
│   │   ├── RelationshipLine.jsx
│   │   └── InfoPanel.jsx
│   ├── services/
│   │   └── api.js
│   ├── hooks/
│   │   └── useEntityData.js
│   ├── utils/
│   │   └── visualization.js
│   ├── App.jsx
│   └── index.js
└── package.json
```

### 3.2 Landing Page Features
**Visual Design**:
- White dotted background (grid pattern)
- Animated floating bubbles
- Bubble size proportional to entity frequency
- Color-coded by entity type:
  - Deities: Gold (#FFD700)
  - Rishis: Blue (#4169E1)
  - Attributes: Green (#32CD32)

**Animations**:
- Gentle floating motion (CSS/Framer Motion)
- Hover effects: scale up, glow
- Click effects: smooth center transition

### 3.3 Interaction Flow
1. **Initial State**: All entities as floating bubbles
2. **Click Bubble 1**: 
   - Move to center
   - Show relationship lines to connected entities
   - Line thickness = relationship score
   - Connected bubbles highlighted
3. **Click Bubble 2** (connected):
   - Both bubbles prominent
   - Show their specific relationship score
   - Display context: hymns where they co-occur
4. **Navigation**:
   - Click outside to reset
   - Breadcrumb trail of selected entities
   - Back button to previous state

### 3.4 Side Panel
- Entity name and type
- Frequency statistics
- Related hymn excerpts
- Top relationships list
- Relationship score breakdown

### 3.5 Technology Choices
- **Visualization**: D3.js force simulation or Three.js
- **Animation**: Framer Motion
- **State Management**: React Context / Zustand
- **HTTP Client**: Axios
- **UI Components**: Custom + Tailwind CSS

---

## Phase 4: Integration & Deployment

### 4.1 Development Environment
- Django backend: `http://localhost:8000`
- React frontend: `http://localhost:3000`
- Django CORS settings for local development

### 4.2 Data Loading
- Django management command to load JSON data into database
- Indexing for performance optimization

### 4.3 Testing Strategy
- Backend: Django test cases for API endpoints
- Frontend: React Testing Library for components
- Integration: E2E tests for user flows

### 4.4 Performance Optimization
- Backend: Database indexing, query optimization
- Frontend: React.memo, useMemo for expensive calculations
- Lazy loading for large datasets
- WebGL for smooth animations with many bubbles

---

## Implementation Timeline

### Week 1: Data Processing
- Day 1-2: Named entity extraction and clustering
- Day 3-4: Relationship scoring algorithm
- Day 5: Testing and validation

### Week 2: Backend Development
- Day 1-2: Django project setup and models
- Day 3-4: API endpoints and serializers
- Day 5: Data loading and testing

### Week 3: Frontend Development
- Day 1-2: React setup and bubble visualization
- Day 3-4: Interaction logic and animations
- Day 5: Side panel and information display

### Week 4: Integration & Polish
- Day 1-2: Backend-frontend integration
- Day 3-4: UI/UX refinement
- Day 5: Testing and documentation

---

## Success Metrics
- All entities extracted and scored
- Relationship scores validated against manual inspection
- Smooth animation with 100+ bubbles (60 FPS)
- API response time < 200ms
- Intuitive user interaction flow

---

## Future Enhancements
- Search and filter functionality
- Export relationship data
- Audio playback of hymns
- Multi-language support (Sanskrit)
- Advanced analytics dashboard
- Share specific relationship views
