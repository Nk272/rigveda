# Hymn Similarity Map — Technical Implementation Plan

This document describes the architecture, backend, frontend, and interaction flow to build an interactive hymn similarity map web app (inspired by [internet-map.net](https://internet-map.net/)).

1. High Level Milestones

1. Setup project skeleton (backend + frontend).  
2. Implement core API endpoints (`/nodes`, `/graph/initial`, `/node/{id}`).  
3. Render initial graph using D3.js.  
4. Enable interactive node expansion (click to reveal similar hymns).  
5. Add UX polish (zoom, pan, tooltips, node sizing, edge styling).  
6. Add optional features: search, filters, clustering, bookmarks.

---

2. Database [hymn_vectors.db]

Tables
- **`hymn_vectors`** → Hymn metadata (node table).  
- **`hymn_similarities_cosine`** → Pairwise hymn similarities (edge table).  
- **`deity_index`** → Deity metadata (not essential for graph but useful for node info).

Indexes
```sql
CREATE INDEX IF NOT EXISTS idx_sim_hymn1_similarity 
ON hymn_similarities_cosine (hymn1_id, similarity DESC);

CREATE INDEX IF NOT EXISTS idx_hymn_vectors_hymn_id 
ON hymn_vectors (hymn_id);
3. Backend (FastAPI + SQLite)
Tech Stack
FastAPI (Python) for REST APIs.

SQLAlchemy ORM for DB access.

SQLite for storage (1k nodes → sufficient).

Project Structure
bash
Copy code
backend/
├─ app/
│  ├─ main.py          # FastAPI app & routes
│  ├─ db.py            # DB session
│  ├─ models.py        # SQLAlchemy models
│  ├─ crud.py          # DB queries
│  ├─ schemas.py       # Pydantic schemas
│  ├─ routes/
│  │  ├─ nodes.py
Core API Endpoints
1. Get all nodes

http
Copy code
GET /nodes
Returns all hymns with basic metadata.

2. Get initial graph subset

http
Copy code
GET /graph/initial?limit=20
Returns top-N hymns by score for landing view.

3. Get top-N similar hymns for a given node

http
Copy code
GET /node/{id}?limit=8
Returns selected hymn and its most similar neighbors.

Example JSON Response
json
Copy code
{
  "node": {"id": 101, "title": "Agni Hymn", "score": 12.4, "deity_count": 3},
  "neighbors": [
    {"id": 102, "title": "Indra Hymn", "score": 9.1, "deity_count": 2, "similarity": 0.91},
    {"id": 103, "title": "Soma Hymn", "score": 7.3, "deity_count": 1, "similarity": 0.89}
  ]
}
4. Frontend (D3.js)
Tech Stack
D3.js for visualization (force-directed graph).

Vanilla JS (quick prototype) or React + D3 (modular, scalable).

Data Model
Nodes: from hymn_vectors.

Edges: from hymn_similarities_cosine.

Node size: mapped to hymn_score (or deity_count).

Edge weight: mapped to similarity.

Core Features
Force simulation: d3.forceSimulation() with link + charge + center forces.

Zoom/Pan: d3.zoom().

Node size scale: d3.scaleSqrt() for radius.

Edge styling: thickness or opacity based on similarity.

Tooltip: show title, book:hymn, deity_names.

Click expansion: fetch /node/{id}, add neighbors dynamically.

Interaction Flow
Load initial graph from /graph/initial.

Render with force-directed layout.

On node click → fetch neighbors → add new nodes & edges → restart simulation.

Keep track of visited nodes to avoid duplicates.

Optional: replace graph with local ego network (alternative UX).

Example Pseudocode
js
Copy code
async function onNodeClick(nodeId) {
  if (pendingRequests.has(nodeId)) return;
  pendingRequests.add(nodeId);
  const res = await api.get(`/node/${nodeId}?limit=8`);
  res.neighbors.forEach(nb => {
    if (!nodesById.has(nb.id)) addNode(nb);
    addLink({source: nodeId, target: nb.id, similarity: nb.similarity});
  });
  simulation.alpha(0.5).restart();
  pendingRequests.delete(nodeId);
}
5. Testing
Backend
Unit tests: for crud.py DB queries with pytest + SQLite test fixtures.

API tests: using httpx + pytest for endpoints.

Frontend
Interaction tests: ensure clicking node expands correctly (Playwright/Cypress).

Visual regression tests: check layout stability.

6. Performance Notes
Lazy loading: only fetch neighbors on demand.

Cap visible nodes: limit to ~500 nodes for clarity.

Index DB: ensure similarity queries are efficient.

Optional clustering: precompute clusters and use color-coding.

7. Optional Enhancements
Search bar / autocomplete (via /nodes).

Filters: deity count, hymn score, book number.

Bookmarks: save graph state locally.

Permalinks: encode expanded node IDs in URL.

Pin/unpin nodes: allow manual graph shaping.

Cluster visualization: community detection offline → color nodes by cluster.