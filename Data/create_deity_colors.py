import sqlite3
import json

# Connect to database
db_path = '/Users/nikunjgoyal/Codes/rigveda/hymn_vectors.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get the 20 deities ordered by hymn count (which should correlate with importance)
cursor.execute("""
    SELECT d.deity_id, d.deity_name, COUNT(h.hymn_id) as hymn_count, d.deity_frequency
    FROM deity_index d
    LEFT JOIN hymn_vectors h ON d.deity_id = h.primary_deity_id
    WHERE d.deity_id IN (
        SELECT deity_id FROM deity_index WHERE deity_id < 25
        AND deity_name NOT IN ('viśvedevas', 'dawn', 'heaven', 'earth', 'waters')
    )
    GROUP BY d.deity_id, d.deity_name, d.deity_frequency
    ORDER BY hymn_count DESC
""")

deities = cursor.fetchall()

# Create 20 distinct, visually appealing colors
# More prominent colors for deities with more hymns
colors = [
    "#E74C3C",  # Red - Indra (most hymns)
    "#F39C12",  # Orange - Agni
    "#9B59B6",  # Purple - Soma
    "#3498DB",  # Blue - Aśvins
    "#1ABC9C",  # Teal - Varuṇa
    "#2ECC71",  # Green - Maruts
    "#E67E22",  # Dark Orange - Savitar
    "#95A5A6",  # Gray - Ṛbhus
    "#34495E",  # Dark Blue - Bṛhaspati
    "#16A085",  # Dark Teal - Vāyu
    "#27AE60",  # Dark Green - Pūṣan
    "#F1C40F",  # Yellow - Sūrya
    "#8E44AD",  # Dark Purple - Āprīs
    "#C0392B",  # Dark Red - Ādityas
    "#D35400",  # Burnt Orange - Rudra
    "#2980B9",  # Medium Blue - Viṣṇu
    "#7F8C8D",  # Medium Gray - Mitra
    "#BDC3C7",  # Light Gray - Pavamana
    "#E8DAEF",  # Light Purple - Vaikuntha
    "#AED6F1",  # Light Blue - Indra-vāyu
]

# Create deity color mapping
deity_colors = {}
for i, (deity_id, deity_name, hymn_count, freq) in enumerate(deities):
    color = colors[i] if i < len(colors) else "#95A5A6"
    deity_colors[deity_id] = {
        "deity_id": deity_id,
        "deity_name": deity_name,
        "color": color,
        "hymn_count": hymn_count,
        "text_frequency": freq
    }
    print(f"{deity_name:15} (ID: {deity_id:2}) → {color}  [{hymn_count} hymns, {freq} mentions]")

# Add deity_color column if it doesn't exist
cursor.execute("PRAGMA table_info(deity_index)")
columns = [col[1] for col in cursor.fetchall()]
if 'deity_color' not in columns:
    print("\nAdding deity_color column to deity_index table...")
    cursor.execute("ALTER TABLE deity_index ADD COLUMN deity_color TEXT")
    conn.commit()

# Update deity colors in database
print("\nUpdating deity colors in database...")
for deity_id, data in deity_colors.items():
    cursor.execute(
        "UPDATE deity_index SET deity_color = ? WHERE deity_id = ?",
        (data['color'], deity_id)
    )

conn.commit()

# Save color mapping to JSON for reference
output_path = '/Users/nikunjgoyal/Codes/rigveda/Data/JSONMaps/deity_colors.json'
with open(output_path, 'w') as f:
    json.dump(deity_colors, f, indent=2)

print(f"\n✓ Deity colors saved to {output_path}")
print("✓ Database updated successfully!")

conn.close()
