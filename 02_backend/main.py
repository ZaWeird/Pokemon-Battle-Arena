# 02_backend/main.py
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, emit
from config import Config
from dependencies import engine, get_db
from models import Base
from routers import auth, gacha, inventory, team, leaderboard, battle, shop, user, chat
from services.battle_service import handle_join_battle as join_handler, make_ai_move
from services.battle_service import handle_battle_action
import os
import sqlite3
from seedings import seed_all

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create database tables
def initialize_database():
    """Create database from schema and seed it if it's empty."""
    # Compute the absolute path to the same DB used everywhere
    db_path = os.path.join(os.path.dirname(__file__), '..', '01_database', 'pokemon_battle.db')
    db_path = os.path.abspath(db_path)

    need_seed = False
    if not os.path.exists(db_path):
        need_seed = True
    else:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pokemons'")
        table_exists = cursor.fetchone()
        if not table_exists:
            need_seed = True
        else:
            cursor.execute("SELECT COUNT(*) FROM pokemons")
            count = cursor.fetchone()[0]
            need_seed = (count == 0)
        conn.close()

    if need_seed:
        print("Database empty or missing – setting up for the first time...")
        # Run schema.sql
        schema_path = os.path.join(os.path.dirname(__file__), '..', '01_database', 'schema.sql')
        schema_path = os.path.abspath(schema_path)
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        conn = sqlite3.connect(db_path)
        conn.executescript(schema_sql)
        conn.close()

        # Seed Pokémon, moves, and items
        seed_all()
        print("Initial database setup complete.")

#Fallback in case of any issues with the above seeding logic
Base.metadata.create_all(bind=engine)

# Register blueprints
app.register_blueprint(auth.router)
app.register_blueprint(gacha.router)
app.register_blueprint(inventory.router)
app.register_blueprint(team.router)
app.register_blueprint(leaderboard.router)
app.register_blueprint(battle.router)
app.register_blueprint(shop.router)
app.register_blueprint(user.router)
app.register_blueprint(chat.router)

# Active battles storage
active_battles = {}

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_battle')
def handle_join_battle(data):
    room = data.get('room')
    join_room(room)

    db = next(get_db())
    try:
        join_handler(data, socketio, active_battles, db)
        # If AI goes first, kick off its move
        if room in active_battles and active_battles[room]['turn'] == 'ai':
            socketio.start_background_task(make_ai_move, room, socketio, active_battles)
    except Exception as e:
        print(f"Error in join_battle: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)}, room=room)
    finally:
        db.close()

@socketio.on('battle_action')
def handle_battle_action_event(data):
    print(f"BATTLE ACTION: {data.get('action')} in room {data.get('room')} by user {data.get('user_id')}")
    handle_battle_action(data, socketio, active_battles, make_ai_move)

@socketio.on('leave_battle')
def handle_leave_battle(data):
    room = data.get('room')
    if room in active_battles:
        del active_battles[room]
        print(f"Battle room {room} cleaned up")

# Error handler for socket events
@socketio.on_error_default
def default_error_handler(e):
    print(f"Socket error: {e}")

if __name__ == '__main__':
    initialize_database()
    print("=" * 50)
    print("Pokemon Battle Arena - Backend Server")
    print("=" * 50)
    print(f"Server running on http://localhost:5000")
    print(f"Socket.IO enabled for real-time battles")
    print("=" * 50)
    socketio.run(app, debug=True, port=5000)