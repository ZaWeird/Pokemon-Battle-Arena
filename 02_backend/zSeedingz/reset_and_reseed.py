# 02_backend/reset_and_reseed.py
from main import app
from database import db
from models import Pokemon, Move, PokemonMove

with app.app_context():
    print("Clearing existing Pokémon and move data...")
    db.session.query(PokemonMove).delete()
    db.session.query(Move).delete()
    db.session.query(Pokemon).delete()
    db.session.commit()
    print("Database cleared.")

    from services.pokeapi_service import fetch_and_seed_gen1
    print("Starting full Gen 1 seeding (including moves)...")
    print("This will take 5–10 minutes.")
    added, failed = fetch_and_seed_gen1()
    print(f"Seeding complete. Added {len(added)} Pokémon, failed: {len(failed)}")