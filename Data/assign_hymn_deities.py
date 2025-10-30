import json
import sqlite3
from collections import Counter

# Connect to database
db_path = '/Users/nikunjgoyal/Codes/rigveda/hymn_vectors.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get top 25 deities, excluding the 5 specified
cursor.execute("""
    SELECT deity_id, deity_name, deity_frequency
    FROM deity_index
    WHERE deity_id < 25
    AND deity_name NOT IN ('viśvedevas', 'dawn', 'heaven', 'earth', 'waters')
    ORDER BY deity_id
""")
deities = cursor.fetchall()

print(f"Working with {len(deities)} deities:")
for deity_id, deity_name, freq in deities:
    print(f"  {deity_id}: {deity_name} (freq: {freq})")

# Create deity lookup
deity_lookup = {d[1].lower(): d[0] for d in deities}
deity_names = [d[1].lower() for d in deities]

# Add primary_deity_id column if it doesn't exist
cursor.execute("PRAGMA table_info(hymn_vectors)")
columns = [col[1] for col in cursor.fetchall()]
if 'primary_deity_id' not in columns:
    print("\nAdding primary_deity_id column to hymn_vectors table...")
    cursor.execute("ALTER TABLE hymn_vectors ADD COLUMN primary_deity_id INTEGER")
    conn.commit()

# Read rigveda data for hymn texts
print("\nReading rigveda_data.json...")
with open('/Users/nikunjgoyal/Codes/rigveda/Data/JSONMaps/rigveda_data.json', 'r') as f:
    rigveda_data = json.load(f)

# Get all hymns
cursor.execute("SELECT hymn_id, title, book_number, hymn_number FROM hymn_vectors")
hymns = cursor.fetchall()

print(f"\nProcessing {len(hymns)} hymns...")

assigned_count = 0
unassigned_hymns = []

for hymn_id, title, book_num, hymn_num in hymns:
    primary_deity_id = None

    # Strategy 1: Check title for deity name
    title_lower = title.lower()
    for deity_name in deity_names:
        if deity_name in title_lower:
            primary_deity_id = deity_lookup[deity_name]
            break

    # Strategy 2: If not in title, check hymn text
    if primary_deity_id is None:
        book_key = str(book_num)
        hymn_key = str(hymn_id)

        if book_key in rigveda_data['books']:
            book = rigveda_data['books'][book_key]
            if 'hymns' in book and hymn_key in book['hymns']:
                hymn_text = book['hymns'][hymn_key].get('text', '').lower()

                # Count mentions of each deity in text
                deity_counts = {}
                for deity_name in deity_names:
                    count = hymn_text.count(deity_name)
                    if count > 0:
                        deity_counts[deity_name] = count

                # Assign to deity with most mentions
                if deity_counts:
                    most_mentioned = max(deity_counts, key=deity_counts.get)
                    primary_deity_id = deity_lookup[most_mentioned]

    # Update database
    if primary_deity_id is not None:
        cursor.execute(
            "UPDATE hymn_vectors SET primary_deity_id = ? WHERE hymn_id = ?",
            (primary_deity_id, hymn_id)
        )
        assigned_count += 1
    else:
        unassigned_hymns.append((hymn_id, title))

conn.commit()

print(f"\n✓ Assigned {assigned_count} hymns to deities")
print(f"✗ {len(unassigned_hymns)} hymns could not be assigned")

if unassigned_hymns:
    print("\nUnassigned hymns (first 20):")
    for hymn_id, title in unassigned_hymns[:20]:
        print(f"  {hymn_id}: {title}")

    # Assign remaining hymns to most common deity (indra)
    print(f"\nAssigning remaining {len(unassigned_hymns)} hymns to 'indra' (most common deity)...")
    indra_id = deity_lookup['indra']
    for hymn_id, _ in unassigned_hymns:
        cursor.execute(
            "UPDATE hymn_vectors SET primary_deity_id = ? WHERE hymn_id = ?",
            (indra_id, hymn_id)
        )
    conn.commit()
    print("✓ All hymns assigned")

# Show distribution
print("\nDeity distribution:")
cursor.execute("""
    SELECT d.deity_name, COUNT(h.hymn_id) as hymn_count, d.deity_frequency
    FROM deity_index d
    LEFT JOIN hymn_vectors h ON d.deity_id = h.primary_deity_id
    WHERE d.deity_id IN (SELECT deity_id FROM deity_index WHERE deity_id < 25
                         AND deity_name NOT IN ('viśvedevas', 'dawn', 'heaven', 'earth', 'waters'))
    GROUP BY d.deity_id, d.deity_name, d.deity_frequency
    ORDER BY hymn_count DESC
""")

for deity_name, hymn_count, freq in cursor.fetchall():
    print(f"  {deity_name}: {hymn_count} hymns (text mentions: {freq})")

conn.close()
print("\n✓ Database updated successfully!")
