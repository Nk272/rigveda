#!/usr/bin/env python3
"""
Demo script to showcase the Rigveda Hymn Similarity Map
"""

import sys
from pathlib import Path
import webbrowser
import time

# Add the backend directory to Python path
backend_path = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_path))

def main():
    print("🕉️  Rigveda Hymn Similarity Map")
    print("=" * 50)
    print()
    print("This interactive web application visualizes 1,028 Rigveda hymns")
    print("as an explorable network based on deity co-occurrence patterns.")

    try:
        from app.db import GetDatabase
        from app import crud

        print("Getting database")
        
        db = next(GetDatabase())
        hymnCount = len(crud.GetAllHymns(db))
        topHymn = crud.GetTopHymnsByScore(db, 1)[0]
        db.close()
        
        print("📊 Database Status:")
        print(f"  • {hymnCount:,} hymns loaded")
        print(f"  • Top hymn: {topHymn.title} (Score: {topHymn.hymn_score})")
        print()
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return
    
    print("🚀 Starting server...")
    print("   Frontend: http://localhost:8000")
    print("   API Docs: http://localhost:8000/docs")
    print()
    print("💡 Try these interactions:")
    print("  1. Click any node to explore similar hymns")
    print("  2. Use search to find specific hymns (try 'Agni' or 'Indra')")
    print("  3. Zoom and pan to navigate the network")
    print("  4. Hover over nodes for quick information")
    print()
    print("Press Ctrl+C to stop the server")
    print("-" * 50)
    
    # Start server
    try:
        import uvicorn
        
        # Open browser after a short delay
        def open_browser():
            time.sleep(2)
            webbrowser.open("http://localhost:8000")
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Server stopped. Thanks for exploring the Rigveda!")
    except Exception as e:
        print(f"❌ Server error: {e}")

if __name__ == "__main__":
    main()
