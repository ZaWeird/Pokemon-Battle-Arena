# 02_backend/main.py
from flask import Flask, request
from flask_cors import CORS
from flask_socketio import SocketIO, join_room, emit
from config import Config
from database import db, socketio
from dependencies import engine, get_db
from models import Base
from routers import auth, gacha, inventory, team, leaderboard, battle, shop, user
import jwt
import time

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

# Import battle service functions
from services.battle_service import handle_join_battle as join_handler, make_ai_move
from services.damage_service import calculate_damage
from services.move_effects_service import calculate_move_accuracy
from services.turn_order import can_move

# Socket.IO Events
@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client disconnected: {request.sid}')

@socketio.on('join_battle')
def handle_join_battle(data):
    user_id = data.get('user_id')
    room = data.get('room')
    
    print(f"JOIN BATTLE: User {user_id} joining room {room}")
    join_room(room)
    
    db = next(get_db())
    
    try:
        # Create battle state and emit battle_started
        join_handler(data, socketio, active_battles, db)
        # After battle is set up, if first turn is AI, trigger AI move
        if room in active_battles and active_battles[room]['turn'] == 'ai':
            print("AI goes first, triggering AI move...")
            socketio.start_background_task(make_ai_move, room, socketio, active_battles)
    except Exception as e:
        print(f"Error in join_battle: {e}")
        import traceback
        traceback.print_exc()
        emit('error', {'message': str(e)}, room=room)
    finally:
        db.close()

@socketio.on('battle_action')
def handle_battle_action(data):
    room = data.get('room')
    user_id = data.get('user_id')
    action = data.get('action')
    
    print(f"BATTLE ACTION: {action} in room {room} by user {user_id}")
    
    if room not in active_battles:
        emit('error', {'message': 'Battle room not found'}, room=room)
        return
    
    battle = active_battles[room]
    
    # Verify it's the player's turn
    if battle['turn'] != user_id:
        emit('error', {'message': 'Not your turn!'}, room=room)
        return
    
    player = battle['players'][user_id]
    opponent = battle['players']['ai']
    
    if action == 'attack':
        move_index = data.get('move_index', 0)
        current_pokemon = player['pokemon'][player['current_pokemon']]
        target_pokemon = opponent['pokemon'][opponent['current_pokemon']]
        
        # Check if player can move (status effects)
        can_act, status_msg = can_move(current_pokemon)
        if not can_act:
            battle['battle_log'].append(status_msg)
            emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': status_msg,
                'next_turn': 'ai',
                'current_pokemon': {
                    user_id: player['current_pokemon'],
                    'ai': opponent['current_pokemon']
                }
            }, room=room)
            battle['turn'] = 'ai'
            socketio.start_background_task(make_ai_move, room, socketio, active_battles)
            return
        
        # Get selected move
        moves = current_pokemon.get('moves', [])
        if moves and move_index < len(moves):
            move = moves[move_index]
        else:
            move = {'name': 'Tackle', 'power': 40, 'type': 'normal', 'damage_class': 'physical'}
        
        # Accuracy check
        if not calculate_move_accuracy(move):
            log_entry = f"{current_pokemon['name']}'s attack missed!"
            battle['battle_log'].append(log_entry)
            emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': log_entry,
                'next_turn': 'ai',
                'current_pokemon': {
                    user_id: player['current_pokemon'],
                    'ai': opponent['current_pokemon']
                }
            }, room=room)
            battle['turn'] = 'ai'
            socketio.start_background_task(make_ai_move, room, socketio, active_battles)
            return
        
        # Calculate damage
        damage, effectiveness, is_critical = calculate_damage(current_pokemon, target_pokemon, move)
        
        # Apply damage
        opponent['hp'][opponent['current_pokemon']] -= damage
        if opponent['hp'][opponent['current_pokemon']] < 0:
            opponent['hp'][opponent['current_pokemon']] = 0
        
        # Build log message
        log_entry = f"{current_pokemon['name']} used {move['name']}! "
        if effectiveness == 0:
            log_entry += f"It had no effect on {target_pokemon['name']}!"
        elif effectiveness > 1:
            log_entry += f"It's super effective! ({damage} damage)"
        elif effectiveness < 1:
            log_entry += f"It's not very effective... ({damage} damage)"
        else:
            log_entry += f"It dealt {damage} damage!"
        if is_critical:
            log_entry += " Critical hit!"
        
        battle['battle_log'].append(log_entry)
        
        # Check if AI Pokemon fainted
        if opponent['hp'][opponent['current_pokemon']] <= 0:
            battle['battle_log'].append(f"{target_pokemon['name']} fainted!")
            remaining = [hp for hp in opponent['hp'] if hp > 0]
            if remaining:
                for i, hp in enumerate(opponent['hp']):
                    if hp > 0:
                        opponent['current_pokemon'] = i
                        battle['battle_log'].append(f"AI sent out {opponent['pokemon'][i]['name']}!")
                        break
            else:
                # Player wins - award EXP
                from services.experience_service import award_battle_exp
                exp_gained, level_up_msgs = award_battle_exp(user_id, player, target_pokemon, battle['battle_log'])
                battle['battle_log'].extend(level_up_msgs)
                
                db = next(get_db())
                from models import User
                user = db.query(User).filter_by(id=user_id).first()
                user.wins += 1
                user.coins += 50
                db.commit()
                db.close()
                
                emit('battle_ended', {
                    'winner': user_id,
                    'log': battle['battle_log'],
                    'exp_gained': exp_gained,
                    'coins_gained': 50,
                    'level_ups': level_up_msgs
                }, room=room)
                del active_battles[room]
                return
        
        # Switch turn to AI
        battle['turn'] = 'ai'
        emit('battle_update', {
            'hp_updates': [
                {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
            ],
            'log': log_entry,
            'next_turn': battle['turn'],
            'current_pokemon': {
                user_id: player['current_pokemon'],
                'ai': opponent['current_pokemon']
            }
        }, room=room)
        
        socketio.start_background_task(make_ai_move, room, socketio, active_battles)
    
    elif action == 'switch':
        pokemon_index = data.get('pokemon_index', 0)
        current_pokemon = player['pokemon'][player['current_pokemon']]
        
        can_act, status_msg = can_move(current_pokemon)
        if not can_act:
            battle['battle_log'].append(status_msg)
            emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': status_msg,
                'next_turn': 'ai',
                'current_pokemon': {
                    user_id: player['current_pokemon'],
                    'ai': opponent['current_pokemon']
                }
            }, room=room)
            battle['turn'] = 'ai'
            socketio.start_background_task(make_ai_move, room, socketio, active_battles)
            return
        
        if pokemon_index != player['current_pokemon'] and player['hp'][pokemon_index] > 0:
            player['current_pokemon'] = pokemon_index
            new_pokemon = player['pokemon'][pokemon_index]
            log_entry = f"You switched to {new_pokemon['name']}"
            battle['battle_log'].append(log_entry)
            battle['turn'] = 'ai'
            emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': log_entry,
                'next_turn': battle['turn'],
                'current_pokemon': {
                    user_id: player['current_pokemon'],
                    'ai': opponent['current_pokemon']
                }
            }, room=room)
            socketio.start_background_task(make_ai_move, room, socketio, active_battles)
        else:
            emit('error', {'message': 'Cannot switch to that Pokemon!'}, room=room)

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