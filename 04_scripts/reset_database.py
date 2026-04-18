# 04_scripts/reset_complete.py
import sqlite3
import os
import bcrypt
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'schema.sql')

def reset_database():
    print("=" * 50)
    print("COMPLETE DATABASE RESET")
    print("=" * 50)
    
    # Delete old database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Deleted old database")
    
    # Create new database with schema
    if os.path.exists(SCHEMA_PATH):
        conn = sqlite3.connect(DB_PATH)
        with open(SCHEMA_PATH, 'r') as f:
            schema = f.read()
            conn.executescript(schema)
        print("Created new database with schema")
        conn.close()
    else:
        print(f"ERROR: Schema file not found at {SCHEMA_PATH}")
        return False
    
    # Add admin user
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    password = "admin123"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, coins, wins, losses, rank, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('admin', 'admin@pokemon.com', password_hash, 9999999999, 0, 0, 'Admin', 9999))
    
    conn.commit()
    print("Added admin user")
    
    # Verify
    cursor.execute("SELECT id, username, coins, rank FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    if admin:
        print(f"\nAdmin user created successfully!")
        print(f"  ID: {admin[0]}")
        print(f"  Username: {admin[1]}")
        print(f"  Coins: {admin[2]:,}")
        print(f"  Rank: {admin[3]}")
    else:
        print("ERROR: Failed to create admin user")
    
    conn.close()
    return True

if __name__ == '__main__':
    reset_database()