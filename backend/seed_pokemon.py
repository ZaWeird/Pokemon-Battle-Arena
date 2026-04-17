# backend/seed_pokemon.py
from app import app, db
from models import Pokemon
from pokeapi_service import fetch_pokemon_by_generation

with app.app_context():
    print("Fetching Gen 1 Pokemon...")
    added = fetch_pokemon_by_generation(1, 151)
    print(f"Added {len(added)} Pokemon to database")
    
    # Count total
    count = Pokemon.query.count()
    print(f"Total Pokemon in database: {count}")