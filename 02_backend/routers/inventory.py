from flask import Blueprint, jsonify, request
import jwt
import traceback
from config import Config
from dependencies import get_db  
from models import UserPokemon, User

router = Blueprint('inventory', __name__, url_prefix='/api')

@router.route('/inventory', methods=['GET'])
def get_inventory():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
    except Exception as e:
        print(f"Token decode error: {e}")
        return jsonify({'message': 'Invalid token'}), 401

    db = next(get_db())
    try:
        user_pokemons = db.query(UserPokemon).filter_by(user_id=user_id).all()
        inventory = []
        for up in user_pokemons:
            if not up.pokemon:
                continue
            inventory.append({
                'id': up.id,
                'pokemon_id': up.pokemon_id,
                'name': up.pokemon.name,
                'level': up.level,
                'xp': up.xp,
                'hp': up.max_hp,
                'attack': up.attack,
                'defense': up.defense,
                'speed': up.speed,
                'special': up.special,
                'rarity': up.pokemon.rarity,
                'type': up.pokemon.type,
                'image_url': up.pokemon.image_url,
                'is_in_team': up.is_in_team,
                'team_position': up.team_position
            })
        return jsonify(inventory)
    except Exception as e:
        print(f"Inventory error: {e}")
        traceback.print_exc()
        return jsonify({'message': 'Failed to load inventory'}), 500
    finally:
        db.close()

# 02_backend/routers/inventory.py (add this after the existing routes)

@router.route('/release/batch', methods=['POST'])
def release_pokemon_batch():
    print("Batch release endpoint called")
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
        print(f"User ID from token: {user_id}")
    except Exception as e:
        print(f"Token decode error: {e}")
        return jsonify({'message': 'Invalid token'}), 401

    req = request.json
    pokemon_ids = req.get('pokemon_ids', [])
    print(f"Received pokemon_ids: {pokemon_ids}")

    if not pokemon_ids:
        return jsonify({'message': 'No Pokémon selected'}), 400

    db = next(get_db())
    # Fetch the user's Pokémon that are in the list
    user_pokemons = db.query(UserPokemon).filter(
        UserPokemon.id.in_(pokemon_ids),
        UserPokemon.user_id == user_id
    ).all()

    if not user_pokemons:
        db.close()
        return jsonify({'message': 'No valid Pokémon found'}), 404

    total_coins = 0
    released_names = []
    for up in user_pokemons:
        rarity = up.pokemon.rarity
        sell_values = {'Common': 10, 'Rare': 20, 'Epic': 50, 'Legendary': 100}
        coins = sell_values.get(rarity, 10)
        total_coins += coins
        released_names.append(up.pokemon.name)
        db.delete(up)

    # Update user's coin balance
    user = db.query(User).filter_by(id=user_id).first()
    if user:
        user.coins += total_coins
    db.commit()
    db.close()

    print(f"Released {len(released_names)} Pokémon, total coins {total_coins}")
    return jsonify({
        'message': f'Released {len(released_names)} Pokémon for {total_coins} coins',
        'coins_gained': total_coins,
        'new_balance': user.coins if user else 0,
        'released_count': len(released_names)
    })

@router.route('/release', methods=['POST'])
def release_pokemon():
    print("Release endpoint called")
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
        print(f"User ID from token: {user_id}")
    except Exception as e:
        print(f"Token decode error: {e}")
        return jsonify({'message': 'Invalid token'}), 401

    req = request.json
    user_pokemon_id = req.get('user_pokemon_id')
    print(f"Received user_pokemon_id: {user_pokemon_id}")

    db = next(get_db())
    user_pokemon = db.query(UserPokemon).filter_by(id=user_pokemon_id, user_id=user_id).first()
    if not user_pokemon:
        db.close()
        print("Pokémon not found")
        return jsonify({'message': 'Pokémon not found'}), 404

    rarity = user_pokemon.pokemon.rarity
    sell_values = {'Common': 10, 'Rare': 20, 'Epic': 50, 'Legendary': 100}
    coins_earned = sell_values.get(rarity, 10)
    pokemon_name = user_pokemon.pokemon.name

    # Delete the Pokémon
    db.delete(user_pokemon)

    # Update user coins
    user = db.query(User).filter_by(id=user_id).first()
    if not user:
        db.close()
        return jsonify({'message': 'User not found'}), 404
    user.coins += coins_earned
    db.commit()
    db.close()

    print(f"Released {pokemon_name}, earned {coins_earned}, new balance {user.coins}")
    return jsonify({
        'message': f'Released {pokemon_name} for {coins_earned} coins',
        'coins_gained': coins_earned,
        'new_balance': user.coins
    })