# 02_backend/reseed.py
import sqlite3
import os
import requests
import time
import json

# Database path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')
POKEAPI_BASE = "https://pokeapi.co/api/v2"

# ------------------------------------------------------------
# Helper functions
# ------------------------------------------------------------
def fetch_with_retry(url, max_retries=3):
    for attempt in range(max_retries):
        try:
            r = requests.get(url)
            if r.status_code == 200:
                return r.json()
            elif r.status_code == 404:
                return None
        except:
            pass
        if attempt < max_retries - 1:
            time.sleep(2 ** attempt)
    return None

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

def fetch_pokemon_data(poke_id):
    url = f"{POKEAPI_BASE}/pokemon/{poke_id}"
    data = fetch_with_retry(url)
    if not data:
        return None

    stats = {s['stat']['name']: s['base_stat'] for s in data['stats']}
    stat_total = sum(stats.values())
    types = get_type_string(data['types'])
    image_url = data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default']

    # Get level‑up moves
    level_up_moves = {}
    for move_data in data['moves']:
        for detail in move_data['version_group_details']:
            if detail['move_learn_method']['name'] == 'level-up':
                name = move_data['move']['name']
                level = detail['level_learned_at']
                if name not in level_up_moves or level < level_up_moves[name]:
                    level_up_moves[name] = level
                break

    return {
        'pokeapi_id': data['id'],
        'name': data['name'],
        'type': types,
        'hp': stats.get('hp', 50),
        'attack': stats.get('attack', 50),
        'defense': stats.get('defense', 50),
        'special_attack': stats.get('special-attack', 50),
        'special_defense': stats.get('special-defense', 50),
        'speed': stats.get('speed', 50),
        'base_experience': data.get('base_experience', 100),
        'image_url': image_url,
        'rarity': calculate_rarity(stat_total),
        'level_up_moves': level_up_moves
    }

def fetch_move_data(move_name):
    url = f"{POKEAPI_BASE}/move/{move_name}"
    data = fetch_with_retry(url)
    if not data:
        return None

    # Parse stat changes
    stat_changes = json.dumps([{'stat': c['stat']['name'], 'change': c['change']} for c in data.get('stat_changes', [])])

    # Meta object (may be None for some moves like Struggle)
    meta = data.get('meta')
    if meta is None:
        meta = {}

    return {
        'pokeapi_id': data['id'],
        'name': data['name'],
        'accuracy': data.get('accuracy'),
        'power': data.get('power'),
        'damage_class': data['damage_class']['name'],
        'type': data['type']['name'],
        'pp': data.get('pp', 35),
        'stat_changes': stat_changes,
        'ailment': meta.get('ailment', {}).get('name') if meta.get('ailment') else None,
        'ailment_chance': meta.get('ailment_chance', 0),
        'flinch_chance': meta.get('flinch_chance', 0),
        'healing': meta.get('healing', 0),
        'drain': meta.get('drain', 0),
        'min_hits': meta.get('min_hits', 1),
        'max_hits': meta.get('max_hits', 1),
        'crit_rate': meta.get('crit_rate', 0)
    }

def seed_all():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Clear tables
    cursor.execute("DELETE FROM pokemon_moves")
    cursor.execute("DELETE FROM moves")
    cursor.execute("DELETE FROM pokemons")
    conn.commit()
    print("Cleared existing data.")

    for poke_id in range(1, 152):
        print(f"Processing #{poke_id}...", end=" ")
        pokemon = fetch_pokemon_data(poke_id)
        if not pokemon:
            print("FAILED (no data)")
            continue

        # Insert Pokemon
        cursor.execute("""
            INSERT INTO pokemons (
                pokeapi_id, name, type, hp, attack, defense,
                special_attack, special_defense, speed,
                base_experience, image_url, rarity
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pokemon['pokeapi_id'], pokemon['name'], pokemon['type'],
            pokemon['hp'], pokemon['attack'], pokemon['defense'],
            pokemon['special_attack'], pokemon['special_defense'],
            pokemon['speed'], pokemon['base_experience'],
            pokemon['image_url'], pokemon['rarity']
        ))
        pokemon_db_id = cursor.lastrowid

        # Insert moves and links
        move_count = 0
        for move_name, learn_level in pokemon['level_up_moves'].items():
            # Check if move already exists
            cursor.execute("SELECT id FROM moves WHERE name = ?", (move_name,))
            row = cursor.fetchone()
            if row:
                move_id = row[0]
            else:
                move_data = fetch_move_data(move_name)
                if not move_data:
                    print(f"  WARNING: Could not fetch move {move_name}")
                    continue
                cursor.execute("""
                    INSERT INTO moves (
                        pokeapi_id, name, accuracy, power, damage_class, type, pp,
                        stat_changes, ailment, ailment_chance, flinch_chance,
                        healing, drain, min_hits, max_hits, crit_rate
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    move_data['pokeapi_id'], move_data['name'],
                    move_data['accuracy'], move_data['power'],
                    move_data['damage_class'], move_data['type'], move_data['pp'],
                    move_data['stat_changes'], move_data['ailment'],
                    move_data['ailment_chance'], move_data['flinch_chance'],
                    move_data['healing'], move_data['drain'],
                    move_data['min_hits'], move_data['max_hits'],
                    move_data['crit_rate']
                ))
                move_id = cursor.lastrowid
                move_count += 1

            # Insert Pokémon‑Move link
            cursor.execute("""
                INSERT INTO pokemon_moves (pokemon_id, move_id, learn_level)
                VALUES (?, ?, ?)
            """, (pokemon_db_id, move_id, learn_level))

        conn.commit()
        print(f"OK (moves: {len(pokemon['level_up_moves'])})")
        time.sleep(0.1)  # be nice to the API

    conn.close()
    print("\nSeeding complete!")

if __name__ == '__main__':
    seed_all()