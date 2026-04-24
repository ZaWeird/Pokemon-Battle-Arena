# 02_backend/routers/auth.py
from flask import Blueprint, request, jsonify
import jwt
import sqlite3
import bcrypt
from datetime import datetime, timedelta
import os
from config import Config

router = Blueprint('auth', __name__, url_prefix='/api')

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '01_database', 'pokemon_battle.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@router.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    if not username or not email or not password:
        return jsonify({'message': 'Missing fields'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute("SELECT id FROM users WHERE username = ? OR email = ?", (username, email))
    if cursor.fetchone():
        conn.close()
        return jsonify({'message': 'Username or email already exists'}), 400
    
    # Hash password
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    # Insert user
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, coins, wins, losses, rank)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (username, email, password_hash, 500, 0, 0, 'Bronze', 1000))
    
    user_id = cursor.lastrowid
    conn.commit()
    
    # Generate token
    token = jwt.encode(
        {'user_id': user_id, 'exp': datetime.utcnow() + timedelta(days=7)},
        Config.JWT_SECRET_KEY,
        algorithm='HS256'
    )
    
    conn.close()
    
    return jsonify({
        'message': 'User created',
        'token': token,
        'user': {
            'id': user_id,
            'username': username,
            'coins': 500,
            'wins': 0,
            'losses': 0,
            'rank': 'Bronze',
        }
    }), 201

@router.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, username, password_hash, coins, wins, losses, rank FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401
    
    if not bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8')):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode(
        {'user_id': user['id'], 'exp': datetime.utcnow() + timedelta(days=7)},
        Config.JWT_SECRET_KEY,
        algorithm='HS256'
    )
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user['id'],
            'username': user['username'],
            'coins': user['coins'],
            'wins': user['wins'],
            'losses': user['losses'],
            'rank': user['rank'],
        }
    })

@router.route('/profile', methods=['GET'])
def get_profile():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    
    if token.startswith('Bearer '):
        token = token[7:]
    
    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
    except:
        return jsonify({'message': 'Invalid token'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, coins, wins, losses, rank FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if not user:
        return jsonify({'message': 'User not found'}), 401
    
    # Count pokemon
    conn2 = get_db_connection()
    cursor2 = conn2.cursor()
    cursor2.execute("SELECT COUNT(*) FROM user_pokemons WHERE user_id = ?", (user_id,))
    pokemon_count = cursor2.fetchone()[0]
    conn2.close()
    
    return jsonify({
        'id': user['id'],
        'username': user['username'],
        'coins': user['coins'],
        'wins': user['wins'],
        'losses': user['losses'],
        'rank': user['rank'],
        'pokemon_count': pokemon_count
    })