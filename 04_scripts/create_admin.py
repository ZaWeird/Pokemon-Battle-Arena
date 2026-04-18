# 04_scripts/create_admin.py
import sqlite3
import bcrypt
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

def create_admin():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    password = "admin123"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Delete existing admin if exists
    cursor.execute("DELETE FROM users WHERE username = 'admin'")
    
    # Create new admin
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, coins, wins, losses, rank, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('admin', 'admin@pokemon.com', password_hash, 9999999999, 0, 0, 'Admin', 9999))
    
    conn.commit()
    conn.close()
    
    print("=" * 40)
    print("ADMIN ACCOUNT CREATED")
    print("=" * 40)
    print("Username: admin")
    print("Password: admin123")
    print("Coins: 9,999,999,999")
    print("Rank: Admin")
    print("=" * 40)

if __name__ == '__main__':
    create_admin()