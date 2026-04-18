# 04_scripts/diagnose.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

def diagnose():
    print("=" * 50)
    print("DATABASE DIAGNOSIS")
    print("=" * 50)
    
    if not os.path.exists(DB_PATH):
        print("ERROR: Database file not found!")
        print(f"Path: {DB_PATH}")
        return
    
    print(f"Database found at: {DB_PATH}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nTables found: {[t[0] for t in tables]}")
    
    # Check users table structure
    if ('users',) in tables:
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nUsers table columns:")
        for col in columns:
            print(f"  {col[1]} ({col[2]})")
        
        # Check users
        cursor.execute("SELECT id, username, email, coins, rank FROM users")
        users = cursor.fetchall()
        print(f"\nUsers in database: {len(users)}")
        for user in users:
            print(f"  ID: {user[0]}, Username: {user[1]}, Email: {user[2]}, Coins: {user[3]}, Rank: {user[4]}")
    else:
        print("\nERROR: users table does not exist!")
    
    conn.close()

if __name__ == '__main__':
    diagnose()