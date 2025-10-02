import json
import re
import sqlite3
from pathlib import Path

file_path = "rigveda_data.json"

with open(file_path, "r") as file:
    data = json.load(file)

print(f"Total hymns: {data['total_hymns']}")
title_map={}
skipList=set(["variousdeities", "unknown", "etc", "the", "gods", "various", "press", "post", "go", "some", "others", "new", "others-", "fathers"])

def NormalizeWord(word: str) -> str:
    """Normalize word by removing possessive and punctuation"""
    word = word.lower().strip()
    word = re.sub(r"['']s$", '', word)
    word = re.sub(r'[.,;:!?"]', '', word)
    return word

def insertintoTitleMap(deity, ref):
    if deity in skipList:
        return
    if deity not in title_map:
        title_map[deity]=[ref]
    else:
        title_map[deity].append(ref)

def get_title_map():
    for i,book in data['books'].items():
        for j,hymn in book['hymns'].items():
            title=hymn['title'].split()
            deity="UNKNOWN"

            if len(title)>2:
                deity="".join(title[2:])

            ref=f"Book {book['book_number']}, Hymn {hymn['hymn_number']}"
            deity=NormalizeWord(deity)
            if deity in skipList:
                continue
            elif deity == "brahmaṇaspati":
                deity="bṛhaspati"
                insertintoTitleMap(deity, ref)
            elif len(title)==3:
                if "-" in deity:
                    deity1=NormalizeWord(deity.split("-")[0])
                    deity2=NormalizeWord(deity.split("-")[1])
                    insertintoTitleMap(deity1, ref)
                    insertintoTitleMap(deity2, ref)
                else:
                    insertintoTitleMap(deity, ref)
            elif len(title)==4:
                deity1=NormalizeWord(title[2])
                deity2=NormalizeWord(title[3])
                insertintoTitleMap(deity1, ref)
                insertintoTitleMap(deity2, ref)
            elif len(title)==5 and NormalizeWord(title[3]) == "and":
                deity1=NormalizeWord(title[2])
                deity2=NormalizeWord(title[4])
                insertintoTitleMap(deity1, ref)
                insertintoTitleMap(deity2, ref)
            else:
                pass

    sorted_title_map=dict(sorted(title_map.items(), key=lambda x: len(x[1]), reverse=True))
    with open("title_map.json", "w", encoding='utf-8') as file:
        json.dump(sorted_title_map, file, indent=4, ensure_ascii=False)
    for k in sorted_title_map.keys():
        print(k,len(sorted_title_map[k]))

    print(f"Total deities: {len(sorted_title_map)}")

def CreateDatabaseSchema(db_path):
    """Create database schema for hymn vectors"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("DROP TABLE IF EXISTS hymn_vectors")
    cursor.execute("DROP TABLE IF EXISTS deity_index")
    
    cursor.execute('''
        CREATE TABLE hymn_vectors (
            hymn_id TEXT PRIMARY KEY,
            book_number INTEGER,
            hymn_number INTEGER,
            title TEXT,
            deity_vector TEXT,
            deity_names TEXT,
            deity_count INTEGER,
            hymn_score REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE deity_index (
            deity_id INTEGER PRIMARY KEY,
            deity_name TEXT UNIQUE,
            vector_position INTEGER,
            deity_frequency INTEGER
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"✓ Database schema created at {db_path}")

def PopulateDeityIndex(db_path, deity_to_index, title_map):
    """Populate deity index table with deity names, positions, and frequencies"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    for deity, idx in deity_to_index.items():
        frequency = len(title_map[deity])
        cursor.execute(
            'INSERT OR REPLACE INTO deity_index (deity_id, deity_name, vector_position, deity_frequency) VALUES (?, ?, ?, ?)',
            (idx, deity, idx, frequency)
        )
    
    conn.commit()
    conn.close()
    print(f"✓ Populated deity index with {len(deity_to_index)} deities")

def NormalizeTextWords(text):
    """Split text into words and normalize each word"""
    words = re.split(r'\s+', text)
    normalized_words = set()
    for word in words:
        normalized = NormalizeWord(word)
        if normalized:
            normalized_words.add(normalized)
            if normalized == "brahmaṇaspati":
                normalized_words.add("bṛhaspati")
    return normalized_words

def CreateHymnVectors():
    """Generate hymn vectors based on deity presence in text and store in database"""
    
    with open("title_map.json", "r", encoding='utf-8') as file:
        title_map = json.load(file)
    
    deity_list = list(title_map.keys())
    deity_to_index = {deity: idx for idx, deity in enumerate(deity_list)}
    deity_frequency = {deity: len(refs) for deity, refs in title_map.items()}
    
    print(f"\nGenerating hymn vectors with {len(deity_list)} deities...")
    
    db_path = Path(__file__).parent.parent / "hymn_vectors.db"
    
    CreateDatabaseSchema(db_path)
    PopulateDeityIndex(db_path, deity_to_index, title_map)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM hymn_vectors')
    
    total_hymns = 0
    for book_key, book in data['books'].items():
        for hymn_key, hymn in book['hymns'].items():
            hymn_id = str(hymn['hymn_number'])
            book_num = book['book_number']
            hymn_num = hymn['hymn_number']
            title = hymn['title']
            
            title_words = NormalizeTextWords(title)
            text_words = NormalizeTextWords(hymn['text'])
            all_words = title_words.union(text_words)
            
            vector = [0] * len(deity_list)
            hymn_deities = []
            hymn_score = 0.0
            
            for deity, idx in deity_to_index.items():
                if deity in all_words:
                    vector[idx] = 1
                    hymn_deities.append(deity)
                    hymn_score += deity_frequency[deity]
            
            vector_json = json.dumps(vector)
            deities_json = json.dumps(hymn_deities)
            deity_count = sum(vector)
            
            cursor.execute('''
                INSERT INTO hymn_vectors 
                (hymn_id, book_number, hymn_number, title, deity_vector, deity_names, deity_count, hymn_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (hymn_id, book_num, hymn_num, title, vector_json, deities_json, deity_count, hymn_score))
            
            total_hymns += 1
    
    conn.commit()
    conn.close()
    
    print(f"✓ Stored {total_hymns} hymn vectors in database")
    
    PrintVectorStatistics(db_path)

def PrintVectorStatistics(db_path):
    """Print statistics about stored hymn vectors"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT AVG(deity_count), MIN(deity_count), MAX(deity_count) FROM hymn_vectors')
    avg, min_count, max_count = cursor.fetchone()
    print(f"\nDeity Count Statistics:")
    print(f"  Average deities per hymn: {avg:.2f}")
    print(f"  Min deities per hymn: {min_count}")
    print(f"  Max deities per hymn: {max_count}")
    
    cursor.execute('SELECT AVG(hymn_score), MIN(hymn_score), MAX(hymn_score) FROM hymn_vectors')
    avg_score, min_score, max_score = cursor.fetchone()
    print(f"\nHymn Score Statistics:")
    print(f"  Average hymn score: {avg_score:.2f}")
    print(f"  Min hymn score: {min_score:.2f}")
    print(f"  Max hymn score: {max_score:.2f}")
    
    cursor.execute('SELECT hymn_id, title, deity_names, deity_count, hymn_score FROM hymn_vectors ORDER BY hymn_score DESC LIMIT 5')
    print(f"\nTop 5 hymns by score (sum of deity frequencies):")
    for hymn_id, title, deity_names, count, score in cursor.fetchall():
        deities = json.loads(deity_names)
        print(f"  Hymn {hymn_id}: {title}")
        print(f"    Score: {score:.0f} | Deities: {count} | Names: {', '.join(deities[:5])}{'...' if len(deities) > 5 else ''}")
    
    conn.close()

def main():
    get_title_map()
    CreateHymnVectors()


if __name__ == "__main__":
    main()