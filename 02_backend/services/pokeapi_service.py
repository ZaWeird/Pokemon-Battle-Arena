# 02_backend/services/pokeapi_service.py
from services.experience_service import calculate_stats_on_level_up

def init_user_pokemon_stats(user_pokemon, db):
    """
    Recalculate and set a UserPokemon's battle stats based on its level
    and its base Pokémon's stats.
    """
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