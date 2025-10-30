import json
import sqlite3
from collections import Counter

# Connect to database
db_path = '/Users/nikunjgoyal/Codes/rigveda/hymn_vectors.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get top 25 deities
cursor.execute("SELECT deity_id, deity_name FROM deity_index ORDER BY deity_id LIMIT 25")
top_25_deities = cursor.fetchall()

print(f"Processing top 25 deities...")
for deity_id, deity_name in top_25_deities:
    print(f"  {deity_id}: {deity_name}")

# Read rigveda_data.json
print("\nReading rigveda_data.json...")
with open('/Users/nikunjgoyal/Codes/rigveda/Data/JSONMaps/rigveda_data.json', 'r') as f:
    rigveda_data = json.load(f)

# Count mentions for each deity across all books
deity_counts = {}

for deity_id, deity_name in top_25_deities:
    count = 0

    # Search through all 10 books
    for book_num in range(1, 11):
        book_key = str(book_num)
        if book_key in rigveda_data['books']:
            book = rigveda_data['books'][book_key]
            if 'hymns' in book:
                for hymn_id, hymn_data in book['hymns'].items():
                    # Count mentions in hymn text (case insensitive)
                    text = hymn_data.get('text', '').lower()
                    title = hymn_data.get('title', '').lower()

                    # Count occurrences in text and title
                    count += text.count(deity_name.lower())
                    count += title.count(deity_name.lower())

    deity_counts[deity_id] = count
    print(f"Deity '{deity_name}' (ID: {deity_id}) mentioned {count} times")

# Update database
print("\nUpdating database...")
for deity_id, count in deity_counts.items():
    cursor.execute(
        "UPDATE deity_index SET deity_frequency = ? WHERE deity_id = ?",
        (count, deity_id)
    )

conn.commit()
print("Database updated successfully!")

# Show updated values
print("\nUpdated deity frequencies:")
cursor.execute("SELECT deity_id, deity_name, deity_frequency FROM deity_index ORDER BY deity_id LIMIT 25")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} = {row[2]}")

conn.close()
