import json
import sqlite3
import numpy as np
from pathlib import Path
from typing import List, Tuple, Dict

DB_PATH = Path(__file__).parent.parent / "hymn_vectors.db"

def GetHymnVector(hymnId: str) -> Tuple[List[int], str, int, int]:
    """Retrieve hymn vector and metadata from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT deity_vector, title, book_number, hymn_number 
        FROM hymn_vectors 
        WHERE hymn_id = ?
    ''', (hymnId,))
    
    result = cursor.fetchone()
    conn.close()
    
    if result:
        vector = json.loads(result[0])
        return vector, result[1], result[2], result[3]
    return None, None, None, None

def GetAllHymnVectors() -> Dict[str, Tuple[List[int], str, int, int]]:
    """Retrieve all hymn vectors from database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT hymn_id, deity_vector, title, book_number, hymn_number 
        FROM hymn_vectors
        ORDER BY book_number, hymn_number
    ''')
    
    hymns = {}
    for row in cursor.fetchall():
        hymnId = row[0]
        vector = json.loads(row[1])
        hymns[hymnId] = (vector, row[2], row[3], row[4])
    
    conn.close()
    return hymns

def CosineSimilarity(vector1: List[int], vector2: List[int]) -> float:
    """Calculate cosine similarity between two vectors"""
    v1 = np.array(vector1)
    v2 = np.array(vector2)
    
    dotProduct = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return float(dotProduct / (norm1 * norm2))

def JaccardSimilarity(vector1: List[int], vector2: List[int]) -> float:
    """Calculate Jaccard similarity for binary vectors"""
    v1 = set(i for i, val in enumerate(vector1) if val == 1)
    v2 = set(i for i, val in enumerate(vector2) if val == 1)
    
    if len(v1) == 0 and len(v2) == 0:
        return 1.0
    
    intersection = len(v1.intersection(v2))
    union = len(v1.union(v2))
    
    if union == 0:
        return 0.0
    
    return float(intersection / union)

def HammingDistance(vector1: List[int], vector2: List[int]) -> int:
    """Calculate Hamming distance between two binary vectors"""
    return sum(v1 != v2 for v1, v2 in zip(vector1, vector2))

def DiceSimilarity(vector1: List[int], vector2: List[int]) -> float:
    """Calculate Dice coefficient for binary vectors"""
    v1 = set(i for i, val in enumerate(vector1) if val == 1)
    v2 = set(i for i, val in enumerate(vector2) if val == 1)
    
    if len(v1) == 0 and len(v2) == 0:
        return 1.0
    
    intersection = len(v1.intersection(v2))
    
    if len(v1) + len(v2) == 0:
        return 0.0
    
    return float(2 * intersection / (len(v1) + len(v2)))

def CalculateSimilarity(hymnId1: str, hymnId2: str, metric: str = "cosine") -> float:
    """Calculate similarity between two hymns using specified metric"""
    vector1, _, _, _ = GetHymnVector(hymnId1)
    vector2, _, _, _ = GetHymnVector(hymnId2)
    
    if vector1 is None or vector2 is None:
        return 0.0
    
    if metric == "cosine":
        return CosineSimilarity(vector1, vector2)
    elif metric == "jaccard":
        return JaccardSimilarity(vector1, vector2)
    elif metric == "dice":
        return DiceSimilarity(vector1, vector2)
    elif metric == "hamming":
        return float(HammingDistance(vector1, vector2))
    else:
        raise ValueError(f"Unknown metric: {metric}")

def CalculateAllPairwiseSimilarities(metric: str = "cosine", minSimilarity: float = 0.0):
    """Calculate pairwise similarities for all hymns"""
    print("Loading all hymn vectors...")
    hymns = GetAllHymnVectors()
    hymnIds = list(hymns.keys())
    totalPairs = len(hymnIds) * (len(hymnIds) - 1) // 2
    
    print(f"Calculating {totalPairs} pairwise similarities using {metric} metric...")
    
    similarities = []
    processed = 0
    
    for i, hymnId1 in enumerate(hymnIds):
        vector1, title1, book1, hymn1 = hymns[hymnId1]
        
        for j in range(i + 1, len(hymnIds)):
            hymnId2 = hymnIds[j]
            vector2, title2, book2, hymn2 = hymns[hymnId2]
            
            if metric == "cosine":
                similarity = CosineSimilarity(vector1, vector2)
            elif metric == "jaccard":
                similarity = JaccardSimilarity(vector1, vector2)
            elif metric == "dice":
                similarity = DiceSimilarity(vector1, vector2)
            elif metric == "hamming":
                similarity = float(HammingDistance(vector1, vector2))
            else:
                raise ValueError(f"Unknown metric: {metric}")
            
            if similarity >= minSimilarity:
                similarities.append({
                    'hymn1_id': hymnId1,
                    'hymn2_id': hymnId2,
                    'hymn1_book': book1,
                    'hymn1_number': hymn1,
                    'hymn2_book': book2,
                    'hymn2_number': hymn2,
                    'similarity': similarity
                })
            
            processed += 1
            if processed % 10000 == 0:
                print(f"  Processed {processed}/{totalPairs} pairs...")
    
    print(f"✓ Calculated {len(similarities)} similarities above threshold {minSimilarity}")
    return similarities

def SaveSimilaritiesToDatabase(similarities: List[Dict], metric: str):
    """Save pairwise similarities to database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS hymn_similarities_{metric} (
            hymn1_id TEXT,
            hymn2_id TEXT,
            similarity REAL,
            PRIMARY KEY (hymn1_id, hymn2_id)
        )
    ''')
    
    cursor.execute(f'DELETE FROM hymn_similarities_{metric}')
    
    for sim in similarities:
        cursor.execute(f'''
            INSERT INTO hymn_similarities_{metric} (hymn1_id, hymn2_id, similarity)
            VALUES (?, ?, ?)
        ''', (sim['hymn1_id'], sim['hymn2_id'], sim['similarity']))
    
    conn.commit()
    conn.close()
    print(f"✓ Saved {len(similarities)} similarities to database table 'hymn_similarities_{metric}'")

def GetTopSimilarHymns(hymnId: str, metric: str = "cosine", topN: int = 10) -> List[Tuple]:
    """Get top N most similar hymns for a given hymn"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute(f'''
        SELECT hymn2_id, similarity 
        FROM hymn_similarities_{metric}
        WHERE hymn1_id = ?
        UNION
        SELECT hymn1_id, similarity 
        FROM hymn_similarities_{metric}
        WHERE hymn2_id = ?
        ORDER BY similarity DESC
        LIMIT ?
    ''', (hymnId, hymnId, topN))
    
    results = cursor.fetchall()
    conn.close()
    
    return results

def main():
    print("Hymn Similarity Calculator")
    print("=" * 50)
    
    metric = "cosine"
    minThreshold = 0.3
    
    similarities = CalculateAllPairwiseSimilarities(metric=metric, minSimilarity=minThreshold)
    
    similarities.sort(key=lambda x: x['similarity'], reverse=True)
    
    print(f"\nTop 10 most similar hymn pairs ({metric} similarity):")
    for i, sim in enumerate(similarities[:10], 1):
        print(f"{i}. Hymn {sim['hymn1_id']} (Book {sim['hymn1_book']}) <-> "
              f"Hymn {sim['hymn2_id']} (Book {sim['hymn2_book']}): {sim['similarity']:.4f}")
    
    SaveSimilaritiesToDatabase(similarities, metric)

if __name__ == "__main__":
    main()
