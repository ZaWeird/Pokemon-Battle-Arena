# 02_backend/services/pokeapi_service.py
import requests
import json
import time
from models import Pokemon, Move, PokemonMove
from .experience_service import calculate_stats_on_level_up
from database import db

POKEAPI_BASE = "https://pokeapi.co/api/v2"

def get_type_string(types):
    return ','.join([t['type']['name'] for t in types])

def calculate_rarity(stat_total):
    if stat_total >= 600:
        return 'Legendary'
    elif stat_total >= 500:
        return 'Epic'
    elif stat_total >= 400:
        return 'Rare'
    else:
        return 'Common'

def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(url)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                return None
        except Exception as e:
            print(f"Attempt {attempt+1} failed: {e}")
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    return None

def fetch_pokemon_data(pokemon_name_or_id):
    url = f"{POKEAPI_BASE}/pokemon/{pokemon_name_or_id}"
    data = fetch_with_retry(url)
    if not data:
        return None

    stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
    stat_total = sum(s['base_stat'] for s in data['stats'])

    # Level-up moves
    level_up_moves = []
    for move_data in data['moves']:
        for detail in move_data['version_group_details']:
            if detail['move_learn_method']['name'] == 'level-up':
                level_up_moves.append({
                    'name': move_data['move']['name'],
                    'learned_at': detail['level_learned_at']
                })
                break

    unique_moves = {}
    for move in level_up_moves:
        if move['name'] not in unique_moves or move['learned_at'] < unique_moves[move['name']]:
            unique_moves[move['name']] = move['learned_at']

    return {
        'pokeapi_id': data['id'],
        'name': data['name'],
        'type': get_type_string(data['types']),
        'hp': stats.get('hp', 50),
        'attack': stats.get('attack', 50),
        'defense': stats.get('defense', 50),
        'special_attack': stats.get('special-attack', 50),
        'special_defense': stats.get('special-defense', 50),
        'speed': stats.get('speed', 50),
        'base_experience': data.get('base_experience', 100),
        'image_url': data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default'],
        'rarity': calculate_rarity(stat_total),
        'level_up_moves': unique_moves
    }

def fetch_move_data(move_name):
    data = fetch_with_retry(f"{POKEAPI_BASE}/move/{move_name}")
    if not data:
        return None
    meta = data.get('meta', {})
    return {
        'pokeapi_id': data['id'],
        'name': data['name'],
        'accuracy': data.get('accuracy'),
        'power': data.get('power'),
        'damage_class': data['damage_class']['name'],
        'type': data['type']['name'],
        'pp': data.get('pp', 35),
        'stat_changes': json.dumps([{'stat': c['stat']['name'], 'change': c['change']} for c in data.get('stat_changes', [])]),
        'ailment': meta.get('ailment', {}).get('name') if meta.get('ailment') else None,
        'ailment_chance': meta.get('ailment_chance', 0),
        'flinch_chance': meta.get('flinch_chance', 0),
        'healing': meta.get('healing', 0),
        'drain': meta.get('drain', 0),
        'min_hits': meta.get('min_hits', 1),
        'max_hits': meta.get('max_hits', 1),
        'crit_rate': meta.get('crit_rate', 0)
    }

def add_pokemon_to_database(pokemon_data):
    """Add a Pokemon and its level‑up moves to the database."""
    existing = db.session.query(Pokemon).filter_by(pokeapi_id=pokemon_data['pokeapi_id']).first()
    if existing:
        print(f"Pokemon {pokemon_data['name']} already exists")
        return existing

    new_pokemon = Pokemon(
        pokeapi_id=pokemon_data['pokeapi_id'],
        name=pokemon_data['name'],
        type=pokemon_data['type'],
        hp=pokemon_data['hp'],
        attack=pokemon_data['attack'],
        defense=pokemon_data['defense'],
        special_attack=pokemon_data['special_attack'],
        special_defense=pokemon_data['special_defense'],
        speed=pokemon_data['speed'],
        base_experience=pokemon_data['base_experience'],
        image_url=pokemon_data['image_url'],
        rarity=pokemon_data['rarity']
    )
    db.session.add(new_pokemon)
    db.session.flush()

    for move_name, learn_level in pokemon_data['level_up_moves'].items():
        move = db.session.query(Move).filter_by(name=move_name).first()
        if not move:
            move_data = fetch_move_data(move_name)
            if move_data:
                move = Move(
                    pokeapi_id=move_data['pokeapi_id'],
                    name=move_data['name'],
                    accuracy=move_data['accuracy'],
                    power=move_data['power'],
                    damage_class=move_data['damage_class'],
                    type=move_data['type'],
                    pp=move_data['pp'],
                    stat_changes=move_data['stat_changes'],
                    ailment=move_data['ailment'],
                    ailment_chance=move_data['ailment_chance'],
                    flinch_chance=move_data['flinch_chance'],
                    healing=move_data['healing'],
                    drain=move_data['drain'],
                    min_hits=move_data['min_hits'],
                    max_hits=move_data['max_hits'],
                    crit_rate=move_data['crit_rate']
                )
                db.session.add(move)
                db.session.flush()

        if move:
            pokemon_move = PokemonMove(
                pokemon_id=new_pokemon.id,
                move_id=move.id,
                learn_level=learn_level
            )
            db.session.add(pokemon_move)

    db.session.commit()
    print(f"Added {pokemon_data['name']} with {len(pokemon_data['level_up_moves'])} moves")
    return new_pokemon

def fetch_and_seed_gen1():
    """Fetch and seed all Gen 1 Pokemon (1-151) with their level‑up moves."""
    added = []
    failed = []
    for poke_id in range(1, 152):
        print(f"Fetching Pokemon #{poke_id}...")
        pokemon_data = fetch_pokemon_data(poke_id)
        if pokemon_data:
            pokemon = add_pokemon_to_database(pokemon_data)
            added.append(pokemon)
        else:
            failed.append(poke_id)
        time.sleep(0.1)
    return added, failed

def init_user_pokemon_stats(user_pokemon, db):
    base = user_pokemon.pokemon
    level = user_pokemon.level
    stats = calculate_stats_on_level_up(
        base.hp, base.attack, base.defense,
        base.special_attack, base.speed, level
    )
    user_pokemon.max_hp = stats['hp']
    user_pokemon.attack = stats['attack']
    user_pokemon.defense = stats['defense']
    user_pokemon.special = stats['special']
    user_pokemon.speed = stats['speed']
    db.flush()