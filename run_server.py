#!/usr/bin/env python3
"""
Rigveda Hymn Similarity Map Server
Run this script to start the FastAPI server
"""

import uvicorn
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

if __name__ == "__main__":
    print("🕉️  Starting Rigveda Hymn Similarity Map Server...")
    print("📊 Database: hymn_vectors.db")
    print("🌐 Frontend: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    print("\nPress Ctrl+C to stop the server\n")
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=["backend", "frontend"]
    )
