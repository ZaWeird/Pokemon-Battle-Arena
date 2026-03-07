from flask import Flask, request, jsonify, session
from flask_cors import CORS
from flask_socketio import join_room, leave_room, emit, send
from database import db, socketio
from config import Config
from models import User, Pokemon, UserPokemon, Battle, GachaHistory
import requests
import random
from functools import wraps
import jwt
from datetime import datetime, timedelta
import time

app = Flask(__name__)
app.config.from_object(Config)
CORS(app, supports_credentials=True)
db.init_app(app)
socketio.init_app(app, cors_allowed_origins="*")

# Authentication decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            data = jwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.filter_by(id=data['user_id']).first()
        except:
            return jsonify({'message': 'Token is invalid'}), 401
            
        return f(current_user, *args, **kwargs)
    
    return decorated

# Create tables
with app.app_context():
    db.create_all()
    
    # Populate some Pokemon if database is empty
    if Pokemon.query.count() == 0:
        # Add some initial Pokemon
        initial_pokemon = [
            {'id': 1, 'name': 'Bulbasaur', 'type': 'Grass', 'hp': 45, 'attack': 49, 'defense': 49, 'speed': 45, 'rarity': 'Common'},
            {'id': 4, 'name': 'Charmander', 'type': 'Fire', 'hp': 39, 'attack': 52, 'defense': 43, 'speed': 65, 'rarity': 'Common'},
            {'id': 7, 'name': 'Squirtle', 'type': 'Water', 'hp': 44, 'attack': 48, 'defense': 65, 'speed': 43, 'rarity': 'Common'},
            {'id': 25, 'name': 'Pikachu', 'type': 'Electric', 'hp': 35, 'attack': 55, 'defense': 40, 'speed': 90, 'rarity': 'Rare'},
            {'id': 150, 'name': 'Mewtwo', 'type': 'Psychic', 'hp': 106, 'attack': 110, 'defense': 90, 'speed': 130, 'rarity': 'Legendary'},
        ]
        
        for p in initial_pokemon:
            pokemon = Pokemon(
                pokeapi_id=p['id'],
                name=p['name'],
                type=p['type'],
                hp=p['hp'],
                attack=p['attack'],
                defense=p['defense'],
                speed=p['speed'],
                image_url=f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p['id']}.png",
                rarity=p['rarity']
            )
            db.session.add(pokemon)
        
        db.session.commit()

# Routes
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    # Give starter Pokemon
    db.session.add(user)
    db.session.commit()
    
    # Give starter Pokemon to new users
    starter_pokemon = Pokemon.query.filter_by(rarity='Common').limit(3).all()
    for pokemon in starter_pokemon:
        user_pokemon = UserPokemon(
            user_id=user.id,
            pokemon_id=pokemon.id,
            level=5
        )
        db.session.add(user_pokemon)
    
    db.session.commit()
    
    # Generate token
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, app.config['JWT_SECRET_KEY'])
    
    return jsonify({
        'message': 'User created successfully',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'coins': user.coins,
            'wins': user.wins,
            'losses': user.losses,
            'rank': user.rank,
            'rating': user.rating
        }
    })

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401
    
    token = jwt.encode({
        'user_id': user.id,
        'exp': datetime.utcnow() + timedelta(days=7)
    }, app.config['JWT_SECRET_KEY'])
    
    return jsonify({
        'message': 'Login successful',
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'coins': user.coins,
            'wins': user.wins,
            'losses': user.losses,
            'rank': user.rank,
            'rating': user.rating
        }
    })

@app.route('/api/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'coins': current_user.coins,
        'wins': current_user.wins,
        'losses': current_user.losses,
        'rank': current_user.rank,
        'rating': current_user.rating,
        'pokemon_count': len(current_user.pokemons)
    })

@app.route('/api/gacha/summon', methods=['POST'])
@token_required
def summon_pokemon(current_user):
    data = request.json
    summon_type = data.get('type', 'single')  # 'single' or 'ten'
    
    cost = 100 if summon_type == 'single' else 900  # 10x summon discount
    
    if current_user.coins < cost:
        return jsonify({'message': 'Insufficient coins'}), 400
    
    # Rarity probabilities
    rarities = {
        'Common': 0.60,
        'Rare': 0.25,
        'Epic': 0.10,
        'Legendary': 0.05
    }
    
    results = []
    summon_count = 1 if summon_type == 'single' else 10
    
    for _ in range(summon_count):
        # Determine rarity
        rand = random.random()
        cumulative = 0
        selected_rarity = 'Common'
        
        for rarity, prob in rarities.items():
            cumulative += prob
            if rand < cumulative:
                selected_rarity = rarity
                break
        
        # Get random Pokemon of selected rarity
        pokemon = Pokemon.query.filter_by(rarity=selected_rarity).order_by(db.func.random()).first()
        
        # Add to user's collection
        user_pokemon = UserPokemon(
            user_id=current_user.id,
            pokemon_id=pokemon.id
        )
        db.session.add(user_pokemon)
        
        # Record in history
        history = GachaHistory(
            user_id=current_user.id,
            pokemon_id=pokemon.id,
            coins_spent=cost // summon_count
        )
        db.session.add(history)
        
        results.append({
            'id': pokemon.id,
            'name': pokemon.name,
            'rarity': pokemon.rarity,
            'image_url': pokemon.image_url,
            'level': 1
        })
    
    # Deduct coins
    current_user.coins -= cost
    db.session.commit()
    
    return jsonify({
        'message': f'Summoned {len(results)} Pokemon',
        'results': results,
        'remaining_coins': current_user.coins
    })

@app.route('/api/inventory', methods=['GET'])
@token_required
def get_inventory(current_user):
    user_pokemons = UserPokemon.query.filter_by(user_id=current_user.id).all()
    
    inventory = []
    for up in user_pokemons:
        inventory.append({
            'id': up.id,
            'pokemon_id': up.pokemon_id,
            'name': up.pokemon.name,
            'level': up.level,
            'xp': up.xp,
            'rarity': up.pokemon.rarity,
            'type': up.pokemon.type,
            'hp': up.pokemon.hp,
            'attack': up.pokemon.attack,
            'defense': up.pokemon.defense,
            'speed': up.pokemon.speed,
            'image_url': up.pokemon.image_url,
            'is_in_team': up.is_in_team,
            'team_position': up.team_position
        })
    
    return jsonify(inventory)

@app.route('/api/team/save', methods=['POST'])
@token_required
def save_team(current_user):
    data = request.json
    team = data.get('team', [])
    
    if len(team) > 3:
        return jsonify({'message': 'Team cannot have more than 3 Pokemon'}), 400
    
    # Clear current team
    UserPokemon.query.filter_by(user_id=current_user.id).update({'is_in_team': False, 'team_position': None})
    
    # Set new team
    for i, pokemon_id in enumerate(team):
        user_pokemon = UserPokemon.query.filter_by(id=pokemon_id, user_id=current_user.id).first()
        if user_pokemon:
            user_pokemon.is_in_team = True
            user_pokemon.team_position = i
    
    db.session.commit()
    
    return jsonify({'message': 'Team saved successfully'})

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    top_players = User.query.order_by(User.rating.desc()).limit(50).all()
    
    leaderboard = []
    for i, player in enumerate(top_players, 1):
        leaderboard.append({
            'rank': i,
            'username': player.username,
            'rating': player.rating,
            'wins': player.wins,
            'losses': player.losses,
            'win_rate': round(player.wins / (player.wins + player.losses) * 100, 1) if (player.wins + player.losses) > 0 else 0
        })
    
    return jsonify(leaderboard)

# NEW: PvE Battle endpoint
@app.route('/api/battle/pve', methods=['POST'])
@token_required
def start_pve_battle(current_user):
    # Create a unique room ID
    room_id = f"pve_{current_user.id}_{int(time.time())}"
    
    return jsonify({
        'roomId': room_id,
        'message': 'PvE battle created'
    })

# NEW: PvP Queue endpoint
@app.route('/api/battle/pvp/queue', methods=['POST'])
@token_required
def join_pvp_queue(current_user):
    # Create a unique room ID
    room_id = f"pvp_{current_user.id}_{int(time.time())}"
    
    return jsonify({
        'roomId': room_id,
        'message': 'Joined PvP queue'
    })

# Socket.IO events for battle system
active_battles = {}

@socketio.on('join_battle')
def handle_join_battle(data):
    user_id = data['user_id']
    room = data['room']
    
    print(f"User {user_id} joining battle room: {room}")
    join_room(room)
    
    # Check if it's a PvE battle (room starts with "pve_")
    if room.startswith('pve_'):
        # Get player's team
        player_team = UserPokemon.query.filter_by(
            user_id=user_id, 
            is_in_team=True
        ).order_by(UserPokemon.team_position).all()
        
        # If no team selected, get any 3 pokemon
        if not player_team or len(player_team) == 0:
            player_team = UserPokemon.query.filter_by(user_id=user_id).limit(3).all()
        
        # If still no pokemon, create some for testing
        if not player_team or len(player_team) == 0:
            # Get some default pokemon
            default_pokemon = Pokemon.query.limit(3).all()
            player_team = []
            for p in default_pokemon:
                up = UserPokemon(
                    user_id=user_id,
                    pokemon_id=p.id,
                    level=5
                )
                # Add to session but don't commit yet
                db.session.add(up)
                player_team.append(up)
            db.session.commit()
        
        # Create AI opponent (random Pokemon)
        ai_pokemon = Pokemon.query.order_by(db.func.random()).limit(3).all()
        
        # Prepare player Pokemon data
        player_pokemon_data = []
        for p in player_team:
            pokemon_data = {
                'id': p.pokemon.id,
                'name': p.pokemon.name,
                'hp': p.pokemon.hp,
                'max_hp': p.pokemon.hp,
                'attack': p.pokemon.attack,
                'defense': p.pokemon.defense,
                'speed': p.pokemon.speed,
                'image_url': p.pokemon.image_url,
                'level': p.level
            }
            player_pokemon_data.append(pokemon_data)
            print(f"Player Pokemon: {pokemon_data['name']} - HP: {pokemon_data['hp']}")
        
        # Prepare AI Pokemon data
        ai_pokemon_data = []
        for p in ai_pokemon:
            pokemon_data = {
                'id': p.id,
                'name': p.name,
                'hp': p.hp,
                'max_hp': p.hp,
                'attack': p.attack,
                'defense': p.defense,
                'speed': p.speed,
                'image_url': p.image_url
            }
            ai_pokemon_data.append(pokemon_data)
            print(f"AI Pokemon: {pokemon_data['name']} - HP: {pokemon_data['hp']}")
        
        # Store battle state
        active_battles[room] = {
            'players': {
                user_id: {
                    'hp': [p.pokemon.hp for p in player_team],
                    'max_hp': [p.pokemon.hp for p in player_team],
                    'pokemon': player_pokemon_data,
                    'current_pokemon': 0
                },
                'ai': {
                    'hp': [p.hp for p in ai_pokemon],
                    'max_hp': [p.hp for p in ai_pokemon],
                    'pokemon': ai_pokemon_data,
                    'current_pokemon': 0
                }
            },
            'turn': user_id,  # Player goes first
            'battle_log': ['Battle started!']
        }
        
        print(f"PvE Battle started in room {room}")
        print(f"Player team: {[p['name'] for p in active_battles[room]['players'][user_id]['pokemon']]}")
        print(f"AI team: {[p['name'] for p in active_battles[room]['players']['ai']['pokemon']]}")
        
        # Send battle start event with BOTH player's and opponent's Pokemon
        emit('battle_started', {
            'room': room,
            'opponent': 'AI',
            'player_pokemon': player_pokemon_data,  # Send player's own Pokemon
            'opponent_pokemon': ai_pokemon_data,    # Send opponent's Pokemon
            'turn': user_id
        }, room=room)

@socketio.on('battle_action')
def handle_battle_action(data):
    room = data['room']
    user_id = data['user_id']
    action = data['action']
    
    print(f"Battle action in {room}: {action} by {user_id}")
    
    if room not in active_battles:
        emit('error', {'message': 'Battle room not found'}, room=room)
        return
    
    battle = active_battles[room]
    
    # Check if it's this player's turn
    if battle['turn'] != user_id and 'ai' not in battle['players']:
        emit('error', {'message': 'Not your turn!'}, room=room)
        return
    
    # Determine opponent
    if 'ai' in battle['players']:
        opponent_id = 'ai'
    else:
        opponent_id = [p for p in battle['players'] if p != user_id][0]
    
    player = battle['players'][user_id]
    opponent = battle['players'][opponent_id]
    
    if action == 'attack':
        current_pokemon = player['pokemon'][player['current_pokemon']]
        target_pokemon = opponent['pokemon'][opponent['current_pokemon']]
        
        # Calculate damage
        attack = current_pokemon.get('attack', 50)
        defense = target_pokemon.get('defense', 50)
        level = current_pokemon.get('level', 5)
        
        # Basic damage formula
        damage = max(1, int(((2 * level / 5 + 2) * attack / defense / 50 + 2) * random.uniform(0.85, 1.0)))
        
        opponent['hp'][opponent['current_pokemon']] -= damage
        if opponent['hp'][opponent['current_pokemon']] < 0:
            opponent['hp'][opponent['current_pokemon']] = 0
        
        log_entry = f"{current_pokemon['name']} attacked for {damage} damage"
        battle['battle_log'].append(log_entry)
        print(log_entry)
        
        # Check if opponent's Pokemon fainted
        if opponent['hp'][opponent['current_pokemon']] <= 0:
            log_entry += f" - {target_pokemon['name']} fainted!"
            battle['battle_log'].append(f"{target_pokemon['name']} fainted!")
            print(f"{target_pokemon['name']} fainted!")
            
            # Switch to next Pokemon
            if opponent['current_pokemon'] < len(opponent['pokemon']) - 1:
                opponent['current_pokemon'] += 1
                new_pokemon = opponent['pokemon'][opponent['current_pokemon']]
                battle['battle_log'].append(f"{opponent_id if opponent_id != 'ai' else 'AI'} sent out {new_pokemon['name']}!")
                print(f"Switched to {new_pokemon['name']}")
            else:
                # Battle ended
                winner = user_id
                battle['battle_log'].append(f"{'AI' if opponent_id == 'ai' else 'Opponent'} has no Pokemon left! You win!")
                print(f"Battle ended, winner: {winner}")
                
                # Update user stats and coins
                user = User.query.get(user_id)
                if opponent_id != 'ai':
                    opponent_user = User.query.get(opponent_id)
                    user.wins += 1
                    opponent_user.losses += 1
                    user.rating += 25
                    opponent_user.rating -= 10
                    user.coins += 100
                    opponent_user.coins += 20
                else:
                    user.wins += 1
                    user.coins += 50
                
                db.session.commit()
                
                emit('battle_ended', {
                    'winner': winner,
                    'log': battle['battle_log']
                }, room=room)
                
                # Clean up
                del active_battles[room]
                return
        
        # Switch turn
        if opponent_id == 'ai':
            battle['turn'] = 'ai'
        else:
            battle['turn'] = opponent_id
        
        emit('battle_update', {
            'hp_updates': [
                {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                {'player': opponent_id, 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
            ],
            'log': log_entry,
            'next_turn': battle['turn'],
            'current_pokemon': {
                user_id: player['current_pokemon'],
                opponent_id: opponent['current_pokemon']
            }
        }, room=room)
        
        # If it's AI's turn, make AI move after a short delay
        if opponent_id == 'ai' and battle['turn'] == 'ai':
            socketio.sleep(1)
            make_ai_move(room)
    
    elif action == 'switch':
        pokemon_index = data.get('pokemon_index', 0)
        
        if pokemon_index != player['current_pokemon'] and player['hp'][pokemon_index] > 0:
            player['current_pokemon'] = pokemon_index
            current_pokemon = player['pokemon'][pokemon_index]
            
            log_entry = f"Player switched to {current_pokemon['name']}"
            battle['battle_log'].append(log_entry)
            print(log_entry)
            
            # Switch turn
            if opponent_id == 'ai':
                battle['turn'] = 'ai'
            else:
                battle['turn'] = opponent_id
            
            emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': opponent_id, 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': log_entry,
                'next_turn': battle['turn'],
                'current_pokemon': {
                    user_id: player['current_pokemon'],
                    opponent_id: opponent['current_pokemon']
                }
            }, room=room)
            
            # If it's AI's turn, make AI move
            if opponent_id == 'ai' and battle['turn'] == 'ai':
                socketio.sleep(1)
                make_ai_move(room)

def make_ai_move(room):
    """Helper function for AI moves"""
    if room not in active_battles:
        return
    
    battle = active_battles[room]
    ai = battle['players']['ai']
    player_id = [p for p in battle['players'] if p != 'ai'][0]
    player = battle['players'][player_id]
    
    # Simple AI: always attack
    current_ai_pokemon = ai['pokemon'][ai['current_pokemon']]
    target_pokemon = player['pokemon'][player['current_pokemon']]
    
    # Calculate damage
    attack = current_ai_pokemon.get('attack', 50)
    defense = target_pokemon.get('defense', 50)
    damage = max(1, attack - defense // 2 + random.randint(-5, 5))
    
    player['hp'][player['current_pokemon']] -= damage
    if player['hp'][player['current_pokemon']] < 0:
        player['hp'][player['current_pokemon']] = 0
    
    log_entry = f"AI's {current_ai_pokemon['name']} attacked for {damage} damage"
    battle['battle_log'].append(log_entry)
    print(log_entry)
    
    # Check if player's Pokemon fainted
    if player['hp'][player['current_pokemon']] <= 0:
        log_entry += f" - {target_pokemon['name']} fainted!"
        battle['battle_log'].append(f"{target_pokemon['name']} fainted!")
        print(f"{target_pokemon['name']} fainted!")
        
        if player['current_pokemon'] < len(player['pokemon']) - 1:
            player['current_pokemon'] += 1
            new_pokemon = player['pokemon'][player['current_pokemon']]
            battle['battle_log'].append(f"Player sent out {new_pokemon['name']}!")
            print(f"Player switched to {new_pokemon['name']}")
        else:
            # Battle ended - AI wins
            battle['battle_log'].append("All your Pokemon fainted! You lose!")
            print("Battle ended, AI wins")
            
            # Update user stats
            user = User.query.get(player_id)
            user.losses += 1
            user.coins += 20  # Consolation prize
            db.session.commit()
            
            emit('battle_ended', {
                'winner': 'ai',
                'log': battle['battle_log']
            }, room=room)
            
            del active_battles[room]
            return
    
    # Switch turn back to player
    battle['turn'] = player_id
    
    emit('battle_update', {
        'hp_updates': [
            {'player': 'ai', 'hp': ai['hp'], 'max_hp': ai['max_hp']},
            {'player': player_id, 'hp': player['hp'], 'max_hp': player['max_hp']}
        ],
        'log': log_entry,
        'next_turn': battle['turn'],
        'current_pokemon': {
            'ai': ai['current_pokemon'],
            player_id: player['current_pokemon']
        }
    }, room=room)

@socketio.on('battle_chat')
def handle_battle_chat(data):
    room = data['room']
    message = data['message']
    username = data['username']
    
    emit('chat_message', {
        'username': username,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)

@socketio.on('leave_battle')
def handle_leave_battle(data):
    room = data['room']
    user_id = data['user_id']
    
    leave_room(room)
    
    if room in active_battles:
        # Notify other player
        emit('player_left', {'player_id': user_id}, room=room)
        
        # Clean up room if empty
        if len(active_battles[room]['players']) <= 1:
            del active_battles[room]

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)