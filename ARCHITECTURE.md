# Rigveda Interactive Web App - Architecture Documentation

## System Overview

The Rigveda Interactive Web App is a full-stack application that visualizes relationships between named entities (deities, rishis, attributes) found in the Rigveda texts using an interactive bubble-based interface.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    USER BROWSER                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │           React Frontend (Port 3000)              │  │
│  │  ┌─────────────┐  ┌──────────────┐               │  │
│  │  │ Bubble      │  │  Info Panel  │               │  │
│  │  │ Visualiza-  │  │              │               │  │
│  │  │ tion (D3)   │  │  Zustand     │               │  │
│  │  └─────────────┘  │  Store       │               │  │
│  │         │          └──────────────┘               │  │
│  │         │                 │                       │  │
│  │         └────────┬────────┘                       │  │
│  │                  │                                │  │
│  │           ┌──────▼──────┐                         │  │
│  │           │  API Client │                         │  │
│  │           │   (Axios)   │                         │  │
│  │           └──────┬──────┘                         │  │
│  └──────────────────┼────────────────────────────────┘  │
└────────────────────┼─────────────────────────────────────┘
                     │ HTTP/JSON
                     │
┌────────────────────▼─────────────────────────────────────┐
│         Django REST Framework (Port 8000)                │
│  ┌─────────────────────────────────────────────────┐    │
│  │              API Layer                          │    │
│  │  ┌────────────┐  ┌─────────────┐               │    │
│  │  │ Entity     │  │Relationship │               │    │
│  │  │ ViewSet    │  │  ViewSet    │               │    │
│  │  └──────┬─────┘  └──────┬──────┘               │    │
│  │         │                │                      │    │
│  │  ┌──────▼────────────────▼──────┐               │    │
│  │  │      Serializers              │               │    │
│  │  └──────┬────────────────────────┘               │    │
│  │         │                                        │    │
│  │  ┌──────▼────────────────────────┐               │    │
│  │  │         Models                │               │    │
│  │  │  - Entity                     │               │    │
│  │  │  - Relationship               │               │    │
│  │  └──────┬────────────────────────┘               │    │
│  └─────────┼──────────────────────────────────────┘    │
│            │                                           │
│  ┌─────────▼────────────────┐                          │
│  │   SQLite Database        │                          │
│  │  - entity table          │                          │
│  │  - relationship table    │                          │
│  │  - indexes               │                          │
│  └──────────────────────────┘                          │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│            Data Processing Layer (Offline)               │
│  ┌────────────────────────────────────────────────┐      │
│  │      relationship_builder.py                   │      │
│  │                                                │      │
│  │  Input: rigveda_data.json                     │      │
│  │                                                │      │
│  │  Processes:                                    │      │
│  │  1. Named Entity Extraction                   │      │
│  │  2. Attribute Clustering (WordNet)            │      │
│  │  3. Conjunction Analysis                      │      │
│  │  4. Hymn Co-occurrence Analysis               │      │
│  │  5. Indirect Association (Graph)              │      │
│  │  6. Score Normalization                       │      │
│  │                                                │      │
│  │  Output:                                       │      │
│  │  - entities.json                              │      │
│  │  - entity_relationships_optimized.json        │      │
│  │  - relationship_matrix.json                   │      │
│  └────────────────────────────────────────────────┘      │
└──────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. Data Processing Layer

**Purpose**: Offline processing of Rigveda texts to extract entities and calculate relationships.

**Key Components:**

#### `relationship_builder.py`
- **Input**: `rigveda_data.json` (structured hymns data)
- **Processing Steps**:
  1. Extract deity names from hymn titles
  2. Extract high-frequency named words as attributes
  3. Cluster similar attributes using WordNet semantic similarity
  4. Build entity-hymn index
  5. Calculate conjunction scores (words appearing with "and", "with", "or")
  6. Calculate hymn co-occurrence scores
  7. Calculate indirect association scores using graph analysis
  8. Normalize all scores to [0, 1] range
  9. Combine with weighted formula

**Relationship Scoring Algorithm:**
```
finalScore = (conjunctionScore × 0.5) + 
             (hymnCooccurrenceScore × 0.3) + 
             (indirectScore × 0.2)
```

**Output Files:**
- `entities.json` - Entity metadata
- `entity_relationships_optimized.json` - Relationships for API
- `relationship_matrix.json` - Full NxN matrix
- `attribute_clusters.json` - Semantic clusters
- `relationship_metadata.json` - Statistics

---

### 2. Backend Layer (Django)

**Purpose**: RESTful API for serving entity and relationship data.

#### **Models** (`api/models.py`)

**Entity Model:**
```python
- id: Primary key
- name: Entity name (unique, indexed)
- entityType: 'deity' | 'attribute' | 'rishi'
- frequency: Occurrence count
- description: Optional text
- metadata: JSON field for extensibility
```

**Relationship Model:**
```python
- id: Primary key
- entity1: Foreign key to Entity
- entity2: Foreign key to Entity
- finalScore: Normalized score [0, 1]
- conjunctionScore: Conjunction component
- hymnCooccurrenceScore: Co-occurrence component
- indirectScore: Indirect association component
- hymnReferences: JSON array of hymn refs
- conjunctionContexts: JSON array of examples
```

**Indexes:**
- entity.name (for search)
- entity.entityType (for filtering)
- entity.frequency (for sorting)
- relationship.entity1 + finalScore (for queries)
- relationship.entity2 + finalScore (for queries)

#### **API Endpoints** (`api/views.py`)

**EntityViewSet:**
- `GET /api/entities/` - List all entities (paginated)
- `GET /api/entities/{id}/` - Entity details with top relationships
- `GET /api/entities/{id}/relationships/` - All relationships for entity
- `POST /api/entities/search/` - Search by name

**RelationshipViewSet:**
- `GET /api/relationships/` - List relationships (paginated)
- `GET /api/relationships/?min_score=0.5` - Filter by score
- `GET /api/relationships/?entity_id=1` - Filter by entity

**StatsViewSet:**
- `GET /api/stats/` - Global statistics

#### **Caching Strategy**
- Entity list cached for 1 hour
- Entity relationships cached per entity
- Stats cached for 1 hour
- Cache invalidated on data reload

#### **Management Commands**
- `python manage.py load_data` - Load JSON data into database

---

### 3. Frontend Layer (React)

**Purpose**: Interactive visualization and user interface.

#### **State Management** (`store/entityStore.js`)

Using Zustand for lightweight state management:
```javascript
{
  entities: [],              // All entities
  selectedEntity: null,      // Currently selected entity
  hoveredEntity: null,       // Hovered entity (for tooltip)
  relationships: [],         // Relationships of selected entity
  selectedRelationship: null,// Selected relationship detail
  loading: boolean,
  error: string | null
}
```

#### **Key Components**

**BubbleVisualization** (`components/BubbleVisualization.jsx`)
- **Technology**: D3.js force simulation
- **Features**:
  - Initial state: All entities as floating bubbles
  - Bubble size: Proportional to frequency
  - Color coding by entity type
  - Click to select and center
  - Shows relationships as lines with thickness = score
  - Smooth animations with Framer Motion

**D3 Force Simulation:**
```javascript
forceSimulation(entities)
  .force('charge', forceManyBody().strength(-100))
  .force('center', forceCenter(centerX, centerY))
  .force('collision', forceCollide().radius(r => radius + 5))
```

**InfoPanel** (`components/InfoPanel.jsx`)
- **Features**:
  - Slides in from right on entity selection
  - Shows entity metadata
  - Lists top relationships with score bars
  - Detailed relationship breakdown
  - Hymn references and conjunction examples
  - Smooth animations with Framer Motion

**API Client** (`services/api.js`)
- Axios-based HTTP client
- Centralized error handling
- Base URL configuration
- Request/response interceptors

---

## Data Flow

### 1. Initial Load
```
User opens app
  → React App.js useEffect
  → fetchEntities() API call
  → Django EntityViewSet.list()
  → Check cache
  → Query database (if cache miss)
  → Serialize and return JSON
  → Update Zustand store
  → Render bubbles with D3
```

### 2. Entity Selection
```
User clicks bubble
  → HandleEntityClick(entity)
  → setSelectedEntity(entity)
  → fetchEntityRelationships(entity.id)
  → Django EntityViewSet.relationships()
  → Query relationships (entity1=id OR entity2=id)
  → Join with related entities
  → Order by finalScore DESC
  → Return top 50
  → setRelationships(data)
  → Re-render: center bubble + relationship bubbles
  → Slide in InfoPanel
```

### 3. Relationship Detail
```
User clicks related bubble
  → HandleRelatedEntityClick(relatedEntity)
  → Find relationship in current data
  → setSelectedRelationship(relationship)
  → InfoPanel shows detailed breakdown
  → Display score components
  → Show hymn references
  → Show conjunction examples
```

---

## Performance Considerations

### Backend
1. **Database Indexing**: Multi-column indexes for common queries
2. **Query Optimization**: select_related() for joins
3. **Caching**: In-memory cache for frequent requests
4. **Pagination**: Limit response sizes
5. **Serializer Optimization**: Separate serializers for list/detail views

### Frontend
1. **D3 Optimization**: Limited force simulation iterations
2. **React Optimization**: React.memo for expensive components
3. **Lazy Loading**: Relationships loaded on demand
4. **Efficient Rendering**: SVG instead of Canvas for better DOM control
5. **State Management**: Zustand for minimal re-renders

---

## Security Considerations

### Backend
1. **CSRF Protection**: Enabled for state-changing requests
2. **CORS**: Restricted to localhost:3000 in development
3. **Rate Limiting**: API throttling (100/hour anonymous)
4. **SQL Injection**: Django ORM prevents SQL injection
5. **Input Validation**: Serializer validation

### Frontend
1. **XSS Prevention**: React escapes content by default
2. **HTTPS**: Required for production
3. **API Authentication**: Ready for token-based auth

---

## Scalability

### Current Limitations
- SQLite (single-file database)
- In-memory caching
- Single-threaded development server

### Production Recommendations
1. **Database**: PostgreSQL with connection pooling
2. **Caching**: Redis for distributed caching
3. **Web Server**: Gunicorn + Nginx
4. **Frontend**: CDN for static assets
5. **Load Balancing**: Multiple backend instances

---

## Testing Strategy

### Backend Testing
```python
# Unit tests for models
# Integration tests for API endpoints
# Test fixtures for sample data
```

### Frontend Testing
```javascript
// Unit tests for utility functions
// Component tests with React Testing Library
// E2E tests for user flows
```

---

## Monitoring & Logging

### Backend
- Django logging configured
- Request/response logging
- Error tracking (ready for Sentry)

### Frontend
- Console error logging
- API error handling
- User interaction tracking (ready for analytics)

---

## Future Enhancements

### Technical
1. WebSocket for real-time updates
2. GraphQL for flexible queries
3. Server-side rendering for SEO
4. Progressive Web App features
5. Offline support with Service Workers

### Features
1. Advanced search and filtering
2. Custom relationship scoring
3. Historical analysis views
4. Export to various formats
5. Audio integration for hymns
6. Multi-language support
