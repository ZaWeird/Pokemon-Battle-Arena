# 02_backend/routers/gacha.py
from flask import Blueprint, request, jsonify
import sqlite3
import random
import os
from services.auth_utils import verify_token
from dependencies import get_db
router = Blueprint('gacha', __name__, url_prefix='/api')

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '01_database', 'pokemon_battle.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.route('/gacha/summon', methods=['POST'])
def summon_pokemon():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid token'}), 401
    
    data = request.get_json()
    summon_type = data.get('type', 'single')
    cost = 100 if summon_type == 'single' else 900
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Check user coins
    cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    if not user or user['coins'] < cost:
        conn.close()
        return jsonify({'message': 'Insufficient coins'}), 400
    
    # Rarity probabilities
    rarities = [('Common', 0.60), ('Rare', 0.25), ('Epic', 0.10), ('Legendary', 0.05)]
    summon_count = 1 if summon_type == 'single' else 10
    results = []
    
    for _ in range(summon_count):
        rand = random.random()
        cumulative = 0
        selected_rarity = 'Common'
        for rarity, prob in rarities:
            cumulative += prob
            if rand < cumulative:
                selected_rarity = rarity
                break
        
        # Get random Pokemon of that rarity
        cursor.execute("SELECT id, name, rarity, image_url FROM pokemons WHERE rarity = ? ORDER BY RANDOM() LIMIT 1", (selected_rarity,))
        pokemon = cursor.fetchone()
        if not pokemon:
            cursor.execute("SELECT id, name, rarity, image_url FROM pokemons ORDER BY RANDOM() LIMIT 1")
            pokemon = cursor.fetchone()
        
        # Add to user_pokemons
        cursor.execute("""
            INSERT INTO user_pokemons (user_id, pokemon_id, level, xp, max_hp, attack, defense, special, speed)
            VALUES (?, ?, 1, 0, 0, 0, 0, 0, 0)
        """, (user_id, pokemon['id']))
        
        # Record gacha history
        cursor.execute("""
            INSERT INTO gacha_history (user_id, pokemon_id, coins_spent, summon_type)
            VALUES (?, ?, ?, ?)
        """, (user_id, pokemon['id'], cost // summon_count, summon_type))
        
        results.append({
            'id': pokemon['id'],
            'name': pokemon['name'],
            'rarity': pokemon['rarity'],
            'image_url': pokemon['image_url'],
            'level': 1
        })
    
    # Deduct coins
    cursor.execute("UPDATE users SET coins = coins - ? WHERE id = ?", (cost, user_id))
    conn.commit()
    
    # Get new coin balance
    cursor.execute("SELECT coins FROM users WHERE id = ?", (user_id,))
    new_balance = cursor.fetchone()['coins']
    conn.close()
    
    return jsonify({
        'message': f'Summoned {len(results)} Pokemon',
        'results': results,
        'remaining_coins': new_balance
    })