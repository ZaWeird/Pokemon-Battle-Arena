# backend/pokeapi_service.py
import requests
import random
from models import db, Pokemon
from sqlalchemy import func

POKEAPI_BASE = "https://pokeapi.co/api/v2"

def get_type_string(types):
    """Convert types list to comma-separated string"""
    type_names = [t['type']['name'] for t in types]
    return ','.join(type_names)

def get_pokemon_from_api(pokemon_name_or_id):
    """Fetch a single Pokemon from PokeAPI"""
    try:
        url = f"{POKEAPI_BASE}/pokemon/{pokemon_name_or_id}"
        response = requests.get(url)
        
        if response.status_code != 200:
            print(f"Failed to fetch {pokemon_name_or_id}: {response.status_code}")
            return None
        
        data = response.json()
        
        # Get stats
        hp = data['stats'][0]['base_stat']
        attack = data['stats'][1]['base_stat']
        defense = data['stats'][2]['base_stat']
        special = data['stats'][3]['base_stat']
        speed = data['stats'][5]['base_stat']
        
        # Determine rarity based on base stat total
        stat_total = hp + attack + defense + special + speed
        
        if stat_total >= 600:
            rarity = 'Legendary'
        elif stat_total >= 500:
            rarity = 'Epic'
        elif stat_total >= 400:
            rarity = 'Rare'
        else:
            rarity = 'Common'
        
        pokemon_data = {
            'pokeapi_id': data['id'],
            'name': data['name'],
            'type': get_type_string(data['types']),
            'hp': hp,
            'attack': attack,
            'defense': defense,
            'speed': speed,
            'image_url': data['sprites']['other']['official-artwork']['front_default'] or data['sprites']['front_default'],
            'rarity': rarity
        }
        
        return pokemon_data
        
    except Exception as e:
        print(f"Error fetching {pokemon_name_or_id}: {e}")
        return None

def add_pokemon_to_database(pokemon_data):
    """Add a single Pokemon to database if it doesn't exist"""
    existing = Pokemon.query.filter_by(pokeapi_id=pokemon_data['pokeapi_id']).first()
    
    if existing:
        print(f"Pokemon {pokemon_data['name']} already exists in database")
        return existing
    
    new_pokemon = Pokemon(
        pokeapi_id=pokemon_data['pokeapi_id'],
        name=pokemon_data['name'],
        type=pokemon_data['type'],
        hp=pokemon_data['hp'],
        attack=pokemon_data['attack'],
        defense=pokemon_data['defense'],
        speed=pokemon_data['speed'],
        image_url=pokemon_data['image_url'],
        rarity=pokemon_data['rarity']
    )
    
    db.session.add(new_pokemon)
    db.session.commit()
    print(f"Added {pokemon_data['name']} to database with rarity {pokemon_data['rarity']}")
    
    return new_pokemon

def fetch_and_add_pokemon_batch(pokemon_names):
    """Fetch multiple Pokemon and add to database"""
    added = []
    failed = []
    
    for name in pokemon_names:
        print(f"Fetching {name}...")
        pokemon_data = get_pokemon_from_api(name)
        
        if pokemon_data:
            pokemon = add_pokemon_to_database(pokemon_data)
            added.append(pokemon)
        else:
            failed.append(name)
    
    return added, failed

def fetch_pokemon_by_generation(gen_start, gen_end):
    """Fetch Pokemon by ID range (generations)"""
    added = []
    
    for poke_id in range(gen_start, gen_end + 1):
        print(f"Fetching Pokemon #{poke_id}...")
        pokemon_data = get_pokemon_from_api(poke_id)
        
        if pokemon_data:
            pokemon = add_pokemon_to_database(pokemon_data)
            added.append(pokemon)
    
    return added

def get_random_pokemon_from_db():
    """Get a random Pokemon from database for gacha"""
    count = Pokemon.query.count()
    if count == 0:
        return None
    
    random_offset = random.randint(0, count - 1)
    return Pokemon.query.offset(random_offset).first()

def get_pokemon_by_rarity(rarity):
    """Get a random Pokemon of specific rarity"""
    pokemon_list = Pokemon.query.filter_by(rarity=rarity).all()
    if not pokemon_list:
        return None
    return random.choice(pokemon_list)

def get_all_pokemon_count():
    """Get total number of Pokemon in database"""
    return Pokemon.query.count()