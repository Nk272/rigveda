from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .routes import nodes

app = FastAPI(title="Rigveda Hymn Similarity API", version="1.0.0")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
def HealthCheck():
    return {"status": "healthy"}

# Include API routes
app.include_router(nodes.router, prefix="/api")

# Serve Data directory for JSON files
app.mount("/Data", StaticFiles(directory="Data"), name="data")

# Serve static files (frontend) - must be last as catch-all
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")
