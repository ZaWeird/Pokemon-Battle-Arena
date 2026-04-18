# 04_scripts/make_admin.py
import sqlite3
import bcrypt
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

password_hash = bcrypt.hashpw(b'admin123', bcrypt.gensalt()).decode('utf-8')

cursor.execute("""
    INSERT OR REPLACE INTO users (id, username, email, password_hash, coins, wins, losses, rank, rating)
    VALUES ((SELECT id FROM users WHERE username = 'admin'), 'admin', 'admin@pokemon.com', ?, 9999999999, 0, 0, 'Admin', 9999)
""", (password_hash,))

conn.commit()
print("=" * 40)
print("Admin Account Ready!")
print("=" * 40)
print("  Username: admin")
print("  Password: admin123")
print("  Coins: 9,999,999,999")
print("  Rank: Admin")
print("=" * 40)
conn.close()