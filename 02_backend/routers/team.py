# 02_backend/routers/team.py
from flask import Blueprint, request, jsonify
import sqlite3
import os
from services.auth_utils import verify_token

router = Blueprint('team', __name__, url_prefix='/api')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '01_database', 'pokemon_battle.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.route('/team/save', methods=['POST'])
def save_team():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid token'}), 401
    
    data = request.get_json()
    team = data.get('team', [])
    
    if len(team) > 3:
        return jsonify({'message': 'Team cannot have more than 3 Pokemon'}), 400
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Clear current team
    cursor.execute("UPDATE user_pokemons SET is_in_team = 0, team_position = NULL WHERE user_id = ?", (user_id,))
    
    # Set new team
    for i, pokemon_id in enumerate(team):
        cursor.execute("""
            UPDATE user_pokemons SET is_in_team = 1, team_position = ?
            WHERE id = ? AND user_id = ?
        """, (i, pokemon_id, user_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Team saved successfully'})