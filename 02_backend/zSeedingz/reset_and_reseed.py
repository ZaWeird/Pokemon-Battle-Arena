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

    from seedings import seed_all
    seed_all()