import sqlite3
import os

# Path to database (adjust if needed)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

# Updated item definitions
items = [
    ('Small EXP Candy',   'Gives 150 EXP to a Pokémon',           'exp_candy', 150,   30),
    ('Medium EXP Candy',  'Gives 450 EXP to a Pokémon',           'exp_candy', 450,   80),
    ('Large EXP Candy',   'Gives 1200 EXP to a Pokémon',          'exp_candy', 1200, 200),
    ('Ultimate EXP Candy','The ultimate exp candy! Gives 3200 EXP to a Pokémon', 'exp_candy', 3200, 500),
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

print("=== Cleaning up duplicates & adding UNIQUE constraint ===")

# 1. Create tables if they don't exist (in case we run this on a fresh DB)
cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY,
        name TEXT UNIQUE,
        description TEXT,
        item_type TEXT,
        exp_value INTEGER,
        price INTEGER
    )
""")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_items (
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        item_id INTEGER,
        quantity INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(item_id) REFERENCES items(id)
    )
""")

# 3. Delete all items that are NOT the ones we want (old descriptions)
cursor.execute("""
    DELETE FROM items
    WHERE description LIKE '%Gives 150 EXP%'
       OR description LIKE '%Gives 450 EXP%'
       OR description LIKE '%Gives 1200 EXP%'
       OR description LIKE '%Gives 3200 EXP%'
       OR name NOT IN ('Small EXP Candy','Medium EXP Candy','Large EXP Candy','Ultimate EXP Candy')
""")

# 4. Delete duplicate names, keeping only the earliest row (safety measure)
cursor.execute("""
    DELETE FROM items
    WHERE rowid NOT IN (
        SELECT MIN(rowid) FROM items GROUP BY name
    )
""")

# 5. Now insert/update the correct items using REPLACE
for item in items:
    cursor.execute(
        "INSERT OR REPLACE INTO items (name, description, item_type, exp_value, price) VALUES (?,?,?,?,?)",
        item
    )

conn.commit()
conn.close()
print("=== Done! Items table now has exactly 4 items: Small, Medium, Large, Ultimate ===")