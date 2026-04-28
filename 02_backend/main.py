# 02_backend/main.py
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, emit
from config import Config
from database import socketio
from dependencies import engine, get_db
from models import Base
from routers import auth, gacha, inventory, team, leaderboard, battle, shop, user
from services.battle_service import handle_join_battle as join_handler, make_ai_move
from services.battle_service import handle_battle_action

app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY
CORS(app, supports_credentials=True)
socketio = SocketIO(app, cors_allowed_origins="*")

# Create database tables
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
    print("=" * 50)
    print("Pokemon Battle Arena - Backend Server")
    print("=" * 50)
    print(f"Server running on http://localhost:5000")
    print(f"Socket.IO enabled for real-time battles")
    print("=" * 50)
    socketio.run(app, debug=True, port=5000)