# 02_backend/routers/leaderboard.py
from flask import Blueprint, jsonify
import sqlite3
import os

router = Blueprint('leaderboard', __name__, url_prefix='/api')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '01_database', 'pokemon_battle.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.route('/leaderboard', methods=['GET'])
def get_leaderboard():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            u.username, 
            u.wins, 
            u.losses,
            ROUND(CAST(u.wins AS FLOAT) / NULLIF(u.wins + u.losses, 0) * 100, 1) as win_rate,
            COUNT(up.id) as pokemon_count
        FROM users u
        LEFT JOIN user_pokemons up ON u.id = up.user_id
        GROUP BY u.id
        ORDER BY u.wins DESC, u.losses ASC
        LIMIT 50
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    leaderboard = []
    for i, row in enumerate(rows, 1):
        leaderboard.append({
            'rank': i,
            'username': row['username'],
            'wins': row['wins'],
            'losses': row['losses'],
            'win_rate': row['win_rate'] if row['win_rate'] else 0,
            'pokemon_count': row['pokemon_count']
        })
    
    return jsonify(leaderboard)