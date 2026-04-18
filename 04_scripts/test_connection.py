# 04_scripts/test_connection.py
import requests
import socketio
import time

def test_backend():
    """Test backend API connection"""
    print("\n" + "=" * 40)
    print("Testing Backend API...")
    print("=" * 40)
    
    try:
        response = requests.get('http://localhost:5000/api/leaderboard', timeout=5)
        print(f"  API Status: {response.status_code}")
        if response.status_code == 200:
            print("  Backend is running!")
            return True
    except requests.exceptions.ConnectionError:
        print("  Backend is NOT running!")
        print("  Start backend with: cd 02_backend && python main.py")
    except Exception as e:
        print(f"  Error: {e}")
    
    return False

def test_database():
    """Test database connection"""
    print("\n" + "=" * 40)
    print("Testing Database...")
    print("=" * 40)
    
    import sqlite3
    import os
    
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')
    
    if os.path.exists(DB_PATH):
        print(f"  Database found at: {DB_PATH}")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        table_count = cursor.fetchone()[0]
        print(f"  Tables: {table_count}")
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"  Users: {user_count}")
        
        cursor.execute("SELECT COUNT(*) FROM pokemons")
        pokemon_count = cursor.fetchone()[0]
        print(f"  Pokemon: {pokemon_count}")
        
        conn.close()
        return True
    else:
        print(f"  Database NOT found at: {DB_PATH}")
        print("  Run: cd 01_database && python db.py")
        return False

def test_frontend():
    """Test frontend connection"""
    print("\n" + "=" * 40)
    print("Testing Frontend...")
    print("=" * 40)
    
    try:
        response = requests.get('http://localhost:3000', timeout=5)
        print(f"  Frontend Status: {response.status_code}")
        if response.status_code == 200:
            print("  Frontend is running!")
            return True
    except requests.exceptions.ConnectionError:
        print("  Frontend is NOT running!")
        print("  Start frontend with: cd 03_frontend && npm run dev")
    except Exception as e:
        print(f"  Error: {e}")
    
    return False

if __name__ == '__main__':
    print("=" * 50)
    print("Pokemon Battle Arena - Connection Test")
    print("=" * 50)
    
    backend_ok = test_backend()
    database_ok = test_database()
    frontend_ok = test_frontend()
    
    print("\n" + "=" * 40)
    print("Summary")
    print("=" * 40)
    print(f"  Backend:  {'✓' if backend_ok else '✗'}")
    print(f"  Database: {'✓' if database_ok else '✗'}")
    print(f"  Frontend: {'✓' if frontend_ok else '✗'}")
    
    if not backend_ok:
        print("\nTo start backend:")
        print("  cd 02_backend")
        print("  python main.py")
    
    if not frontend_ok:
        print("\nTo start frontend:")
        print("  cd 03_frontend")
        print("  npm run dev")