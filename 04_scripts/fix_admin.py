# 04_scripts/fix_admin.py
import sqlite3
import bcrypt
import jwt
import os
import sys

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')
SECRET_KEY = "jwt-secret-key-change"  # Must match config.py

def fix_admin():
    """Fix admin account with proper setup"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # First, check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if not cursor.fetchone():
        print("Users table not found! Please initialize database first.")
        conn.close()
        return
    
    # Delete existing admin
    cursor.execute("DELETE FROM users WHERE username = 'admin'")
    
    # Create fresh admin
    password = "admin123"
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, coins, wins, losses, rank, rating)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, ('admin', 'admin@pokemon.com', password_hash, 9999999999, 0, 0, 'Admin', 9999))
    
    conn.commit()
    
    # Verify
    cursor.execute("SELECT id, username, coins, rank FROM users WHERE username = 'admin'")
    admin = cursor.fetchone()
    
    print("\n" + "=" * 50)
    print("Admin Account Fixed!")
    print("=" * 50)
    print(f"  ID: {admin[0]}")
    print(f"  Username: {admin[1]}")
    print(f"  Coins: {admin[2]:,}")
    print(f"  Rank: {admin[3]}")
    print(f"  Password: admin123")
    print("=" * 50)
    
    # Test token generation
    token = jwt.encode({'user_id': admin[0]}, SECRET_KEY, algorithm='HS256')
    print(f"\nTest Token (for debugging):")
    print(f"  {token}")
    
    conn.close()

if __name__ == '__main__':
    fix_admin()