# 02_backend/services/battle_service.py
import random
from sqlalchemy import func
from flask_socketio import emit
from models import User, UserPokemon, Pokemon, Move, PokemonMove
from services.damage_service import calculate_damage
from services.experience_service import (
    calculate_stats_on_level_up,
    award_battle_end_total
)
from services.move_accuracy_service import calculate_move_accuracy
from services.turn_order import can_move, get_effective_speed
from services.pokeapi_service import init_user_pokemon_stats
from dependencies import get_db

active_battles = {}
pending_levels = {}

def handle_join_battle(data, socketio, active_battles, db):
    user_id = data['user_id']
    room = data['room']
    print(f"JOIN BATTLE: User {user_id} joining room {room}")
    battle_level = data.get('level')
    if battle_level is None:
        battle_level = pending_levels.pop(room, 50)
    else:
        pending_levels.pop(room, None)

    print(f"Battle level set to {battle_level} for room {room}")
    try:
        user_pokemons = db.query(UserPokemon).filter_by(user_id=user_id).all()
        for up in user_pokemons:
            if up.max_hp == 0 or up.attack == 0:
                print(f"Recalculating stats for {up.pokemon.name} (level {up.level})")
                init_user_pokemon_stats(up, db)
        db.commit()

        player_team_all = db.query(UserPokemon).filter_by(user_id=user_id).all()
        player_team_all = [up for up in player_team_all if up.pokemon is not None]

        if not player_team_all:
            socketio.emit('error', {'message': 'You have no Pokémon to battle with! Please summon some first.'}, room=room)
            return

        player_team = [up for up in player_team_all if up.is_in_team]
        if not player_team:
            player_team = player_team_all[:3]
        else:
            player_team = player_team[:3]

        ai_pokemon = db.query(Pokemon).order_by(func.random()).limit(3).all()
        if not ai_pokemon:
            socketio.emit('error', {'message': 'No Pokémon available in the database. Please contact the administrator.'}, room=room)
            return

        player_pokemon_data = []
        for up in player_team:
            pokemon_moves = db.query(PokemonMove).filter(
                PokemonMove.pokemon_id == up.pokemon_id,
                PokemonMove.learn_level <= up.level
            ).order_by(PokemonMove.learn_level).limit(4).all()

            moves = []
            for pm in pokemon_moves:
                move = db.query(Move).filter(Move.id == pm.move_id).first()
                if move:
                    moves.append({
                        'id': move.id,
                        'name': move.name,
                        'power': move.power or 0,
                        'type': move.type,
                        'accuracy': move.accuracy or 100,
                        'pp': move.pp,
                        'damage_class': move.damage_class,
                    })
            if not moves:
                moves = [
                    {'name': 'Tackle', 'power': 40, 'type': 'normal', 'accuracy': 100, 'pp': 35, 'damage_class': 'physical'},
                    {'name': 'Growl', 'power': 0, 'type': 'normal', 'accuracy': 100, 'pp': 40, 'damage_class': 'status'}
                ]

            poke = up.pokemon
            if not poke:
                continue
            player_pokemon_data.append({
                'id': up.pokemon_id,
                'user_pokemon_id': up.id,          # needed for EXP lookup
                'name': up.pokemon.name,
                'hp': up.max_hp,
                'max_hp': up.max_hp,
                'attack': up.attack,
                'defense': up.defense,
                'special': up.special,
                'speed': up.speed,
                'image_url': up.pokemon.image_url,
                'level': up.level,
                'types': [up.pokemon.type],
                'moves': moves,
                'current_exp': up.xp or 0
            })
            print(f"Loaded {len(moves)} moves for {up.pokemon.name}")

        ai_pokemon_data = []
        for p in ai_pokemon:
            ai_moves_query = db.query(PokemonMove).filter(
                PokemonMove.pokemon_id == p.id,
                PokemonMove.learn_level <= 50
            ).order_by(PokemonMove.learn_level).limit(4).all()

            ai_moves = []
            for pm in ai_moves_query:
                move = db.query(Move).filter(Move.id == pm.move_id).first()
                if move:
                    ai_moves.append({
                        'id': move.id,
                        'name': move.name,
                        'power': move.power or 0,
                        'type': move.type,
                        'accuracy': move.accuracy or 100,
                        'pp': move.pp,
                        'damage_class': move.damage_class,
                    })
            if not ai_moves:
                ai_moves = [
                    {'name': 'Tackle', 'power': 40, 'type': 'normal', 'accuracy': 100, 'pp': 35, 'damage_class': 'physical'},
                    {'name': 'Scratch', 'power': 40, 'type': 'normal', 'accuracy': 100, 'pp': 35, 'damage_class': 'physical'}
                ]

            stats = calculate_stats_on_level_up(p.hp, p.attack, p.defense, p.special_attack, p.speed, battle_level)
            ai_pokemon_data.append({
                'id': p.id,
                'name': p.name,
                'hp': stats['hp'],
                'max_hp': stats['hp'],
                'attack': stats['attack'],
                'defense': stats['defense'],
                'special': stats['special'],
                'speed': stats['speed'],
                'image_url': p.image_url,
                'level': battle_level,
                'types': [p.type],
                'moves': ai_moves,
                'base_experience': p.base_experience,
                'rarity': p.rarity                   # needed for EXP formula
            })
            print(f"Loaded {len(ai_moves)} moves for AI {p.name}")

        # Determine first turn
        player_first = player_pokemon_data[0]
        ai_first = ai_pokemon_data[0]
        player_speed = get_effective_speed(player_first)
        ai_speed = get_effective_speed(ai_first)
        first_turn = user_id if player_speed >= ai_speed else 'ai'

        active_battles[room] = {
            'players': {
                user_id: {
                    'hp': [p['hp'] for p in player_pokemon_data],
                    'max_hp': [p['max_hp'] for p in player_pokemon_data],
                    'pokemon': player_pokemon_data,
                    'current_pokemon': 0,
                    'exp': [p.get('current_exp', 0) for p in player_pokemon_data]
                },
                'ai': {
                    'hp': [p['hp'] for p in ai_pokemon_data],
                    'max_hp': [p['max_hp'] for p in ai_pokemon_data],
                    'pokemon': ai_pokemon_data,
                    'current_pokemon': 0
                }
            },
            'turn': first_turn,
            'battle_log': ['Battle started!'],
            'defeated_opponents': []                 # track defeated AI Pokémon for EXP
        }

        socketio.emit('battle_started', {
            'room': room,
            'opponent': 'AI',
            'player_pokemon': player_pokemon_data,
            'opponent_pokemon': ai_pokemon_data,
            'turn': first_turn
        }, room=room)
        print(f"Battle started event sent for room {room}")
    except Exception as e:
        print(f"Error in handle_join_battle: {e}")
        try:
            socketio.emit('error', {'message': 'An error occurred while starting the battle. Please try again.'}, room=room)
        except:
            pass

def handle_battle_action(data, socketio, active_battles, make_ai_move_func):
    room = data['room']
    user_id = data['user_id']
    action = data['action']
    move_index = data.get('move_index', 0)

    if room not in active_battles:
        socketio.emit('error', {'message': 'Battle room not found'}, room=room)
        return

    battle = active_battles[room]
    if battle['turn'] != user_id:
        socketio.emit('error', {'message': 'Not your turn!'}, room=room)
        return

    player = battle['players'][user_id]
    opponent = battle['players']['ai']

    if action == 'attack':
        current_pokemon = player['pokemon'][player['current_pokemon']]
        target_pokemon = opponent['pokemon'][opponent['current_pokemon']]

        can_act, status_msg = can_move(current_pokemon)
        if not can_act:
            battle['battle_log'].append(status_msg)
            socketio.emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': status_msg,
                'next_turn': 'ai',
                'current_pokemon': {user_id: player['current_pokemon'], 'ai': opponent['current_pokemon']}
            }, room=room)
            battle['turn'] = 'ai'
            make_ai_move_func(room, socketio, active_battles)
            return

        moves = current_pokemon.get('moves', [])
        move = moves[move_index] if move_index < len(moves) else {'name': 'Tackle', 'power': 40, 'type': 'normal', 'damage_class': 'physical'}

        if not calculate_move_accuracy(move):
            log_entry = f"{current_pokemon['name']}'s attack missed!"
            battle['battle_log'].append(log_entry)
            socketio.emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': log_entry,
                'next_turn': 'ai',
                'current_pokemon': {user_id: player['current_pokemon'], 'ai': opponent['current_pokemon']}
            }, room=room)
            battle['turn'] = 'ai'
            make_ai_move_func(room, socketio, active_battles)
            return

        damage, effectiveness, is_critical = calculate_damage(current_pokemon, target_pokemon, move)

        opponent['hp'][opponent['current_pokemon']] -= damage
        if opponent['hp'][opponent['current_pokemon']] < 0:
            opponent['hp'][opponent['current_pokemon']] = 0

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

        # Faint handling for AI Pokémon
        if opponent['hp'][opponent['current_pokemon']] <= 0:
            faint_msg = f"{target_pokemon['name']} fainted!"
            battle['battle_log'].append(faint_msg)

            # Record the defeated opponent for later EXP calculation
            battle.setdefault('defeated_opponents', []).append({
                'level': target_pokemon['level'],
                'rarity': target_pokemon.get('rarity', 'Common')
            })

            remaining = [hp for hp in opponent['hp'] if hp > 0]
            if remaining:
                for i, hp in enumerate(opponent['hp']):
                    if hp > 0:
                        opponent['current_pokemon'] = i
                        sendout_msg = f"AI sent out {opponent['pokemon'][i]['name']}!"
                        battle['battle_log'].append(sendout_msg)
                        break
                log_entry = f"{log_entry}\n{faint_msg}\n{sendout_msg}"
            else:
                # Player wins – all opponents fainted
                db = next(get_db())
                try:
                    # Award EXP at battle end (win)
                    exp_gained, level_up_msgs = award_battle_end_total(
                        user_id, player, battle['defeated_opponents'], True, db
                    )
                    battle['battle_log'].extend(level_up_msgs)
                finally:
                    db.close()

                # Update user stats
                db = next(get_db())
                try:
                    user = db.query(User).filter_by(id=user_id).first()
                    if user:
                        user.wins += 1
                        user.coins += 50
                        db.commit()
                finally:
                    db.close()

                socketio.emit('battle_ended', {
                    'winner': user_id,
                    'log': battle['battle_log'],
                    'exp_gained': exp_gained,
                    'coins_gained': 50,
                    'level_ups': level_up_msgs
                }, room=room)
                del active_battles[room]
                return

        battle['turn'] = 'ai'
        socketio.emit('battle_update', {
            'hp_updates': [
                {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
            ],
            'log': log_entry,
            'next_turn': battle['turn'],
            'current_pokemon': {user_id: player['current_pokemon'], 'ai': opponent['current_pokemon']}
        }, room=room)

        make_ai_move_func(room, socketio, active_battles)

    elif action == 'switch':
        pokemon_index = data.get('pokemon_index', 0)
        current_pokemon = player['pokemon'][player['current_pokemon']]

        can_act, status_msg = can_move(current_pokemon)
        if not can_act:
            battle['battle_log'].append(status_msg)
            socketio.emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': status_msg,
                'next_turn': 'ai',
                'current_pokemon': {user_id: player['current_pokemon'], 'ai': opponent['current_pokemon']}
            }, room=room)
            battle['turn'] = 'ai'
            make_ai_move_func(room, socketio, active_battles)
            return

        if pokemon_index != player['current_pokemon'] and player['hp'][pokemon_index] > 0:
            player['current_pokemon'] = pokemon_index
            new_pokemon = player['pokemon'][pokemon_index]
            log_entry = f"You switched to {new_pokemon['name']}"
            battle['battle_log'].append(log_entry)
            battle['turn'] = 'ai'

            socketio.emit('battle_update', {
                'hp_updates': [
                    {'player': user_id, 'hp': player['hp'], 'max_hp': player['max_hp']},
                    {'player': 'ai', 'hp': opponent['hp'], 'max_hp': opponent['max_hp']}
                ],
                'log': log_entry,
                'next_turn': battle['turn'],
                'current_pokemon': {user_id: player['current_pokemon'], 'ai': opponent['current_pokemon']}
            }, room=room)

            make_ai_move_func(room, socketio, active_battles)
        else:
            socketio.emit('error', {'message': 'Cannot switch to that Pokemon!'}, room=room)

def make_ai_move(room, socketio, active_battles):
    if room not in active_battles:
        return

    battle = active_battles[room]
    if battle['turn'] != 'ai':
        return

    ai = battle['players']['ai']
    player_id = [p for p in battle['players'] if p != 'ai'][0]
    player = battle['players'][player_id]

    current_ai_pokemon = ai['pokemon'][ai['current_pokemon']]
    target_pokemon = player['pokemon'][player['current_pokemon']]

    can_act, status_msg = can_move(current_ai_pokemon)
    if not can_act:
        battle['battle_log'].append(status_msg)
        battle['turn'] = player_id
        socketio.emit('battle_update', {
            'hp_updates': [
                {'player': 'ai', 'hp': ai['hp'], 'max_hp': ai['max_hp']},
                {'player': player_id, 'hp': player['hp'], 'max_hp': player['max_hp']}
            ],
            'log': status_msg,
            'next_turn': battle['turn'],
            'current_pokemon': {'ai': ai['current_pokemon'], player_id: player['current_pokemon']}
        }, room=room)
        return

    ai_moves = current_ai_pokemon.get('moves', [])
    damaging_moves = [m for m in ai_moves if m.get('power', 0) > 0]
    if damaging_moves:
        move = random.choice(damaging_moves)
    else:
        move = {'name': 'Tackle', 'power': 40, 'type': 'normal', 'damage_class': 'physical'}

    damage, effectiveness, is_critical = calculate_damage(current_ai_pokemon, target_pokemon, move)

    player['hp'][player['current_pokemon']] -= damage
    if player['hp'][player['current_pokemon']] < 0:
        player['hp'][player['current_pokemon']] = 0

    log_entry = f"AI's {current_ai_pokemon['name']} used {move['name']}! "
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

    if player['hp'][player['current_pokemon']] <= 0:
        faint_msg = f"{target_pokemon['name']} fainted!"
        battle['battle_log'].append(faint_msg)
        remaining = [hp for hp in player['hp'] if hp > 0]
        if remaining:
            for i, hp in enumerate(player['hp']):
                if hp > 0:
                    player['current_pokemon'] = i
                    sendout_msg = f"You sent out {player['pokemon'][i]['name']}!"
                    battle['battle_log'].append(sendout_msg)
                    break
            log_entry = f"{log_entry}\n{faint_msg}\n{sendout_msg}"
        else:
            # Player loses – award EXP for defeated opponents (collected so far)
            db = next(get_db())
            try:
                exp_gained, level_up_msgs = award_battle_end_total(
                    player_id, player, battle.get('defeated_opponents', []), False, db
                )
                battle['battle_log'].extend(level_up_msgs)
            finally:
                db.close()

            db = next(get_db())
            try:
                user = db.query(User).filter_by(id=player_id).first()
                if user:
                    user.losses += 1
                    user.coins += 20
                    db.commit()
            finally:
                db.close()

            socketio.emit('battle_ended', {
                'winner': 'ai',
                'log': battle['battle_log'],
                'exp_gained': exp_gained,
                'coins_gained': 20,
                'level_ups': level_up_msgs
            }, room=room)
            del active_battles[room]
            return

    battle['turn'] = player_id

    socketio.emit('battle_update', {
        'hp_updates': [
            {'player': 'ai', 'hp': ai['hp'], 'max_hp': ai['max_hp']},
            {'player': player_id, 'hp': player['hp'], 'max_hp': player['max_hp']}
        ],
        'log': log_entry,
        'next_turn': battle['turn'],
        'current_pokemon': {'ai': ai['current_pokemon'], player_id: player['current_pokemon']}
    }, room=room)