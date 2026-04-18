import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

items = [
    ('Small EXP Candy', 'Gives 50 EXP to a Pokémon', 'exp_candy', 50, 300),
    ('Medium EXP Candy', 'Gives 150 EXP to a Pokémon', 'exp_candy', 150, 800),
    ('Large EXP Candy', 'Gives 400 EXP to a Pokémon', 'exp_candy', 400, 2000),
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS items (id INTEGER PRIMARY KEY, name TEXT, description TEXT, item_type TEXT, exp_value INTEGER, price INTEGER)")
cursor.execute("CREATE TABLE IF NOT EXISTS user_items (id INTEGER PRIMARY KEY, user_id INTEGER, item_id INTEGER, quantity INTEGER, FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(item_id) REFERENCES items(id))")

for item in items:
    cursor.execute("INSERT OR IGNORE INTO items (name, description, item_type, exp_value, price) VALUES (?,?,?,?,?)", item)

conn.commit()
conn.close()
print("Items seeded.")