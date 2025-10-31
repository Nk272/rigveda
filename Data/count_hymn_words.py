"""
Script to count words in each hymn and update the database
"""
import sqlite3
import os
import re

# Path to database
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'hymn_vectors.db')
TEXT_DIR = os.path.join(os.path.dirname(__file__), 'rigveda_texts')

def count_words_in_file(file_path):
    """Count words in a hymn text file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by the separator to get just the hymn text
        parts = content.split('==================================================')
        if len(parts) > 1:
            text = parts[1]
        else:
            text = content

        # Count words (split by whitespace)
        words = re.findall(r'\b\w+\b', text)
        return len(words)
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return 0

def add_word_count_column():
    """Add word_count column to the database if it doesn't exist"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("ALTER TABLE hymn_vectors ADD COLUMN word_count INTEGER DEFAULT 0")
        conn.commit()
        print("Added word_count column to database")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("word_count column already exists")
        else:
            raise
    finally:
        conn.close()

def update_word_counts():
    """Update word counts for all hymns in the database"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all hymns
    cursor.execute("SELECT hymn_id, book_number FROM hymn_vectors")
    hymns = cursor.fetchall()

    print(f"Processing {len(hymns)} hymns...")

    updated = 0
    for hymn_id, book_number in hymns:
        # Construct file path
        file_path = os.path.join(TEXT_DIR, f'book_{book_number}', f'hymn_{hymn_id}.txt')

        if os.path.exists(file_path):
            word_count = count_words_in_file(file_path)

            # Update database
            cursor.execute(
                "UPDATE hymn_vectors SET word_count = ? WHERE hymn_id = ?",
                (word_count, hymn_id)
            )
            updated += 1

            if updated % 100 == 0:
                print(f"Updated {updated}/{len(hymns)} hymns...")
        else:
            print(f"File not found: {file_path}")

    conn.commit()
    conn.close()

    print(f"Successfully updated word counts for {updated} hymns")

if __name__ == "__main__":
    print("Adding word_count column to database...")
    add_word_count_column()

    print("\nUpdating word counts for all hymns...")
    update_word_counts()

    print("\nDone!")
