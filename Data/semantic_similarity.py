import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Dict, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# Paths
DATA_DIR = Path(__file__).parent
DB_PATH = DATA_DIR.parent / "hymn_vectors.db"
SUMMARIES_PATH = DATA_DIR / "JSONMaps" / "rigveda_summaries.json"

def LoadHymnSummaries() -> Dict[str, str]:
    """Load hymn summaries from JSON file"""
    print("Loading hymn summaries...")
    with open(SUMMARIES_PATH, 'r', encoding='utf-8') as f:
        summaries = json.load(f)
    print(f"✓ Loaded {len(summaries)} hymn summaries")
    return summaries

def GenerateEmbeddings(summaries: Dict[str, str], modelName: str = 'all‑mpnet‑base‑v2') -> Tuple[List[str], np.ndarray]:
    """Generate embeddings for all hymn summaries using SentenceTransformers"""
    print(f"\nLoading SentenceTransformer model: {modelName}...")
    model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

    # Sort by hymn ID to ensure consistent ordering
    hymnIds = sorted(summaries.keys())
    summaryTexts = [summaries[hymnId] for hymnId in hymnIds]

    print(f"Generating embeddings for {len(summaryTexts)} hymns...")
    embeddings = model.encode(summaryTexts, show_progress_bar=True, batch_size=32)

    print(f"✓ Generated embeddings with shape: {embeddings.shape}")
    return hymnIds, embeddings

def ComputeAllPairwiseSimilarities(hymnIds: List[str], embeddings: np.ndarray) -> List[Dict]:
    """Compute cosine similarity for all hymn pairs"""
    numHymns = len(hymnIds)
    totalPairs = numHymns * (numHymns - 1) // 2

    print(f"\nComputing pairwise cosine similarities for {totalPairs:,} pairs...")

    # Compute full similarity matrix at once (much faster than loop)
    similarityMatrix = cosine_similarity(embeddings)

    # Extract upper triangle (avoid duplicates and self-similarity)
    similarities = []
    for i in range(numHymns):
        for j in range(i + 1, numHymns):
            similarity = float(similarityMatrix[i, j])
            similarities.append({
                'hymn1_id': hymnIds[i],
                'hymn2_id': hymnIds[j],
                'similarity': similarity
            })

        # Progress update every 100 hymns
        if (i + 1) % 100 == 0:
            processed = (i + 1) * (numHymns - i - 1) // 2 + (i + 1) * i // 2
            print(f"  Processed {i + 1}/{numHymns} hymns ({processed:,}/{totalPairs:,} pairs)...")

    print(f"✓ Computed {len(similarities):,} pairwise similarities")
    return similarities

def SaveSimilaritiesToDatabase(similarities: List[Dict], tableName: str = "hymn_similarities_semantic"):
    """Save all pairwise similarities to database"""
    print(f"\nSaving similarities to database table '{tableName}'...")

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Create table
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {tableName} (
            hymn1_id TEXT NOT NULL,
            hymn2_id TEXT NOT NULL,
            similarity REAL NOT NULL,
            PRIMARY KEY (hymn1_id, hymn2_id)
        )
    ''')

    # Drop existing data
    cursor.execute(f'DELETE FROM {tableName}')
    print(f"  Cleared existing data from '{tableName}'")

    # Batch insert for performance
    print(f"  Inserting {len(similarities):,} rows...")

    batchSize = 10000
    for i in range(0, len(similarities), batchSize):
        batch = similarities[i:i + batchSize]
        cursor.executemany(
            f'INSERT INTO {tableName} (hymn1_id, hymn2_id, similarity) VALUES (?, ?, ?)',
            [(s['hymn1_id'], s['hymn2_id'], s['similarity']) for s in batch]
        )
        conn.commit()
        print(f"    Inserted {min(i + batchSize, len(similarities)):,}/{len(similarities):,} rows...")

    # Create indexes for fast retrieval
    print("  Creating indexes...")
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{tableName}_hymn1 ON {tableName}(hymn1_id, similarity DESC)')
    cursor.execute(f'CREATE INDEX IF NOT EXISTS idx_{tableName}_hymn2 ON {tableName}(hymn2_id, similarity DESC)')

    conn.commit()
    conn.close()

    print(f"✓ Saved {len(similarities):,} similarities to database")
    print(f"✓ Created indexes for fast retrieval")

def GetStatistics(similarities: List[Dict]) -> None:
    """Print statistics about the similarity scores"""
    scores = [s['similarity'] for s in similarities]

    print("\n" + "=" * 60)
    print("SIMILARITY STATISTICS")
    print("=" * 60)
    print(f"Total pairs:        {len(scores):,}")
    print(f"Mean similarity:    {np.mean(scores):.4f}")
    print(f"Median similarity:  {np.median(scores):.4f}")
    print(f"Std deviation:      {np.std(scores):.4f}")
    print(f"Min similarity:     {np.min(scores):.4f}")
    print(f"Max similarity:     {np.max(scores):.4f}")

    # Distribution by ranges
    print("\nDistribution by similarity range:")
    ranges = [
        (0.0, 0.1, "Very low"),
        (0.1, 0.2, "Low"),
        (0.2, 0.3, "Low-Medium"),
        (0.3, 0.4, "Medium"),
        (0.4, 0.5, "Medium-High"),
        (0.5, 0.6, "High"),
        (0.6, 0.7, "Very High"),
        (0.7, 1.0, "Extremely High")
    ]

    for minVal, maxVal, label in ranges:
        count = sum(1 for s in scores if minVal <= s < maxVal)
        percentage = (count / len(scores)) * 100
        print(f"  [{minVal:.1f} - {maxVal:.1f}] {label:15s}: {count:6,} ({percentage:5.2f}%)")

    # Top 10 most similar pairs
    print("\nTop 10 most similar hymn pairs:")
    topPairs = sorted(similarities, key=lambda x: x['similarity'], reverse=True)[:10]
    for i, pair in enumerate(topPairs, 1):
        print(f"  {i:2d}. Hymn {pair['hymn1_id']} <-> Hymn {pair['hymn2_id']}: {pair['similarity']:.4f}")

def ValidateDatabase(tableName: str = "hymn_similarities_semantic") -> None:
    """Validate the database contents"""
    print("\n" + "=" * 60)
    print("DATABASE VALIDATION")
    print("=" * 60)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{tableName}'")
    if not cursor.fetchone():
        print(f"❌ Table '{tableName}' not found!")
        conn.close()
        return

    print(f"✓ Table '{tableName}' exists")

    # Check row count
    cursor.execute(f'SELECT COUNT(*) FROM {tableName}')
    rowCount = cursor.fetchone()[0]
    print(f"✓ Total rows: {rowCount:,}")

    # Check for any NULL values
    cursor.execute(f'SELECT COUNT(*) FROM {tableName} WHERE similarity IS NULL')
    nullCount = cursor.fetchone()[0]
    print(f"✓ NULL values: {nullCount}")

    # Check similarity range
    cursor.execute(f'SELECT MIN(similarity), MAX(similarity), AVG(similarity) FROM {tableName}')
    minSim, maxSim, avgSim = cursor.fetchone()
    print(f"✓ Similarity range: [{minSim:.4f}, {maxSim:.4f}], avg: {avgSim:.4f}")

    # Check indexes
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='{tableName}'")
    indexes = cursor.fetchall()
    print(f"✓ Indexes: {len(indexes)} indexes created")
    for idx in indexes:
        print(f"    - {idx[0]}")

    # Sample query performance test
    import time
    cursor.execute(f'SELECT hymn2_id, similarity FROM {tableName} WHERE hymn1_id = "1001" ORDER BY similarity DESC LIMIT 10')
    startTime = time.time()
    results = cursor.fetchall()
    queryTime = (time.time() - startTime) * 1000
    print(f"✓ Sample query (top 10 for hymn 1001): {queryTime:.2f}ms")
    print(f"  Top 3 similar to hymn 1001:")
    for i, (hymnId, sim) in enumerate(results[:3], 1):
        print(f"    {i}. Hymn {hymnId}: {sim:.4f}")

    conn.close()

def main():
    """Main execution pipeline"""
    print("=" * 60)
    print("SEMANTIC SIMILARITY COMPUTATION")
    print("Using SentenceTransformers: all-MiniLM-L6-v2")
    print("=" * 60)

    # Step 1: Load summaries
    summaries = LoadHymnSummaries()

    # Step 2: Generate embeddings
    hymnIds, embeddings = GenerateEmbeddings(summaries)

    # Step 3: Compute all pairwise similarities
    similarities = ComputeAllPairwiseSimilarities(hymnIds, embeddings)

    # Step 4: Display statistics
    GetStatistics(similarities)

    # Step 5: Save to database
    SaveSimilaritiesToDatabase(similarities)

    # Step 6: Validate database
    ValidateDatabase()

    print("\n" + "=" * 60)
    print("✓ SEMANTIC SIMILARITY COMPUTATION COMPLETE")
    print("=" * 60)
    print(f"Database: {DB_PATH}")
    print(f"Table: hymn_similarities_semantic")
    print(f"Total pairs: {len(similarities):,}")
    print("\nYou can now query similarities using:")
    print("  - GetTopSimilarHymns() in hymn_similarity.py")
    print("  - /api/node/{hymn_id} endpoint (after updating routes)")
    print("=" * 60)

if __name__ == "__main__":
    main()
