"""
Utility functions to query semantic similarity scores from the database.
These complement the existing hymn_similarity.py functions.
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Optional

DB_PATH = Path(__file__).parent.parent / "hymn_vectors.db"

def GetSemanticSimilarity(hymnId1: str, hymnId2: str) -> Optional[float]:
    """Get semantic similarity score between two specific hymns"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check both directions since table stores hymn1_id < hymn2_id
    cursor.execute('''
        SELECT similarity
        FROM hymn_similarities_semantic
        WHERE (hymn1_id = ? AND hymn2_id = ?)
           OR (hymn1_id = ? AND hymn2_id = ?)
        LIMIT 1
    ''', (hymnId1, hymnId2, hymnId2, hymnId1))

    result = cursor.fetchone()
    conn.close()

    return result[0] if result else None

def GetTopSemanticNeighbors(hymnId: str, topN: int = 10) -> List[Tuple[str, float]]:
    """Get top N most semantically similar hymns for a given hymn"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT hymn2_id, similarity
        FROM hymn_similarities_semantic
        WHERE hymn1_id = ?
        UNION
        SELECT hymn1_id, similarity
        FROM hymn_similarities_semantic
        WHERE hymn2_id = ?
        ORDER BY similarity DESC
        LIMIT ?
    ''', (hymnId, hymnId, topN))

    results = cursor.fetchall()
    conn.close()

    return results

def GetSemanticNeighborsAboveThreshold(hymnId: str, minSimilarity: float = 0.5) -> List[Tuple[str, float]]:
    """Get all hymns above a similarity threshold for a given hymn"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT hymn2_id, similarity
        FROM hymn_similarities_semantic
        WHERE hymn1_id = ? AND similarity >= ?
        UNION
        SELECT hymn1_id, similarity
        FROM hymn_similarities_semantic
        WHERE hymn2_id = ? AND similarity >= ?
        ORDER BY similarity DESC
    ''', (hymnId, minSimilarity, hymnId, minSimilarity))

    results = cursor.fetchall()
    conn.close()

    return results

def GetAllSemanticPairs(minSimilarity: float = 0.0, maxResults: Optional[int] = None) -> List[Tuple[str, str, float]]:
    """Get all hymn pairs with their semantic similarity scores"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    query = '''
        SELECT hymn1_id, hymn2_id, similarity
        FROM hymn_similarities_semantic
        WHERE similarity >= ?
        ORDER BY similarity DESC
    '''

    if maxResults:
        query += f' LIMIT {maxResults}'

    cursor.execute(query, (minSimilarity,))
    results = cursor.fetchall()
    conn.close()

    return results

def CompareWithDeitysimilarity(hymnId: str, topN: int = 10) -> None:
    """Compare semantic similarity vs deity-based similarity for a hymn"""
    from hymn_similarity import GetTopSimilarHymns

    print(f"\nComparison for Hymn {hymnId}")
    print("=" * 60)

    print(f"\nTop {topN} by SEMANTIC similarity (summary-based):")
    semanticNeighbors = GetTopSemanticNeighbors(hymnId, topN)
    for i, (neighborId, similarity) in enumerate(semanticNeighbors, 1):
        print(f"  {i:2d}. Hymn {neighborId}: {similarity:.4f}")

    print(f"\nTop {topN} by DEITY similarity (co-occurrence):")
    deityNeighbors = GetTopSimilarHymns(hymnId, metric="cosine", topN=topN)
    for i, (neighborId, similarity) in enumerate(deityNeighbors, 1):
        print(f"  {i:2d}. Hymn {neighborId}: {similarity:.4f}")

def GetStatistics() -> None:
    """Print statistics about semantic similarities in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*), MIN(similarity), MAX(similarity), AVG(similarity) FROM hymn_similarities_semantic')
    count, minSim, maxSim, avgSim = cursor.fetchone()

    print("\n" + "=" * 60)
    print("SEMANTIC SIMILARITY DATABASE STATISTICS")
    print("=" * 60)
    print(f"Total pairs stored:  {count:,}")
    print(f"Similarity range:    [{minSim:.4f}, {maxSim:.4f}]")
    print(f"Average similarity:  {avgSim:.4f}")

    # Distribution
    ranges = [(0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 1.0)]
    print("\nDistribution:")
    for minVal, maxVal in ranges:
        cursor.execute('SELECT COUNT(*) FROM hymn_similarities_semantic WHERE similarity >= ? AND similarity < ?', (minVal, maxVal))
        rangeCount = cursor.fetchone()[0]
        percentage = (rangeCount / count) * 100
        print(f"  [{minVal:.1f} - {maxVal:.1f}]: {rangeCount:7,} ({percentage:5.2f}%)")

    conn.close()

# Example usage
if __name__ == "__main__":
    print("Semantic Similarity Query Examples")
    print("=" * 60)

    # Example 1: Get specific pair similarity
    print("\nExample 1: Similarity between Hymn 1001 and 1002")
    similarity = GetSemanticSimilarity("1001", "1002")
    print(f"Similarity: {similarity:.4f}")

    # Example 2: Top neighbors
    print("\nExample 2: Top 5 most similar hymns to Hymn 1001")
    neighbors = GetTopSemanticNeighbors("1001", topN=5)
    for i, (hymnId, sim) in enumerate(neighbors, 1):
        print(f"  {i}. Hymn {hymnId}: {sim:.4f}")

    # Example 3: Neighbors above threshold
    print("\nExample 3: All hymns with similarity >= 0.8 to Hymn 1001")
    highSimilarities = GetSemanticNeighborsAboveThreshold("1001", minSimilarity=0.8)
    print(f"Found {len(highSimilarities)} hymns with similarity >= 0.8")
    for hymnId, sim in highSimilarities[:5]:
        print(f"  - Hymn {hymnId}: {sim:.4f}")

    # Example 4: Statistics
    GetStatistics()

    # Example 5: Comparison
    CompareWithDeitysimilarity("1001", topN=5)
