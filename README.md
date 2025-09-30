# Rig-Veda Scraper & Analysis Tools

## Tools Available

### 1. Word Analysis Dashboard
Fast and interactive dashboard for analyzing word frequencies from Rigveda hymns.
- All words displayed by default with frequencies
- Lightning-fast Remove operation (async DB writes)
- Intelligent Merge with similarity matching
- Search and filter capabilities
- Beautiful modern UI with real-time stats
- Persistent SQLite storage

**Run:** `./run_word_dashboard.sh` or `python word_dashboard.py`
**Access:** http://localhost:5001

See `WORD_DASHBOARD_README.md` for detailed documentation.

### 2. Full Web Application
Complete Rigveda exploration platform with entity relationships.

**Run:** `./start_all.sh`

See `QUICKSTART.md` for setup instructions.

## Data Structure

### JSON Format
Books
    Book_no -> Book_no
                Name [Title]
                URL
                COunt of Hymns
                Hymns
                    Hymn_no
                    Text
                    Title
                    URL

### Entites
Deities, RIshis, Mandalas [10]

Edges (links) show the relationships—for example:
    "This Rishi composed hymns to this Deity."
    "This Deity is praised in these Mandalas."

When you click on a Deity node, the interface:

highlights all connected Rishis/Mandalas,

lists the relevant mantras in a side panel,

and lets you play audio of those mantras while a visualizer animates with the sound.
