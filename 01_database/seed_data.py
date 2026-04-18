import sqlite3
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DB_PATH = os.path.join(os.path.dirname(__file__), 'pokemon_battle.db')

def seed_initial_pokemon():
    """Seed initial Gen 1 Pokemon into the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    initial_pokemon = [
        (1, 'Bulbasaur', 'Grass', 45, 49, 49, 45, 'Common'),
        (4, 'Charmander', 'Fire', 39, 52, 43, 65, 'Common'),
        (7, 'Squirtle', 'Water', 44, 48, 65, 43, 'Common'),
        (25, 'Pikachu', 'Electric', 35, 55, 40, 90, 'Rare'),
        (150, 'Mewtwo', 'Psychic', 106, 110, 90, 130, 'Legendary'),
    ]
    
    for p in initial_pokemon:
        cursor.execute('''
            INSERT OR IGNORE INTO pokemons 
            (pokeapi_id, name, type, hp, attack, defense, speed, image_url, rarity)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (p[0], p[1], p[2], p[3], p[4], p[5], p[6], f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{p[0]}.png", p[7]))
    
    conn.commit()
    conn.close()
    print("Initial Pokemon seeded!")

if __name__ == '__main__':
    seed_initial_pokemon()