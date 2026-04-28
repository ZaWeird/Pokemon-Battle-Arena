# 02_backend/services/experience_service.py
import math
from sqlalchemy.orm import Session
from models import UserPokemon, Pokemon

# Gen 1 Level thresholds (EXP needed to reach each level)
LEVEL_THRESHOLDS = {
    1: 0, 2: 8, 3: 19, 4: 37, 5: 61, 6: 93, 7: 135, 8: 187, 9: 251, 10: 327,
    11: 417, 12: 521, 13: 641, 14: 777, 15: 931, 16: 1105, 17: 1300, 18: 1518,
    19: 1760, 20: 2028, 21: 2324, 22: 2650, 23: 3008, 24: 3400, 25: 3828,
    26: 4294, 27: 4800, 28: 5348, 29: 5940, 30: 6578, 31: 7264, 32: 8000,
    33: 8788, 34: 9630, 35: 10528, 36: 11484, 37: 12500, 38: 13578, 39: 14720,
    40: 15928, 41: 17204, 42: 18550, 43: 19968, 44: 21460, 45: 23028, 46: 24674,
    47: 26400, 48: 28208, 49: 30100, 50: 32078, 51: 34144, 52: 36300, 53: 38548,
    54: 40890, 55: 43328, 56: 45864, 57: 48500, 58: 51238, 59: 54080, 60: 57028,
    61: 60084, 62: 63250, 63: 66528, 64: 69920, 65: 73428, 66: 77054, 67: 80800,
    68: 84668, 69: 88660, 70: 92778, 71: 97024, 72: 101400, 73: 105908, 74: 110550,
    75: 115328, 76: 120244, 77: 125300, 78: 130498, 79: 135840, 80: 141328,
    81: 146964, 82: 152750, 83: 158688, 84: 164780, 85: 171028, 86: 177434,
    87: 184000, 88: 190728, 89: 197620, 90: 204678, 91: 211904, 92: 219300,
    93: 226868, 94: 234610, 95: 242528, 96: 250624, 97: 258900, 98: 267358,
    99: 276000, 100: 29701
}

RARITY_BASE_EXP = {
    'Common': 4,
    'Rare': 8,
    'Epic': 16,
    'Legendary': 24
}

def get_level_from_exp(total_exp):
    """Return the current level based on accumulated EXP."""
    for level, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if total_exp < threshold:
            return level - 1
    return 100

def calculate_exp_gain(defeated_base_exp, defeated_level, participants_count=1):
    total_exp = math.floor((defeated_base_exp * defeated_level) / 7)
    return max(1, math.floor(total_exp / participants_count))

def calculate_stats_on_level_up(base_hp, base_attack, base_defense, base_special, base_speed, level):
    """
    Gen 1 stat formulas:
    HP = floor(((baseHP * 2) * level) / 100) + level + 10
    Other = floor(((baseStat * 2) * level) / 100) + 5
    """
    hp = math.floor(((base_hp * 2) * level) / 100) + level + 10
    attack = math.floor(((base_attack * 2) * level) / 100) + 5
    defense = math.floor(((base_defense * 2) * level) / 100) + 5
    special = math.floor(((base_special * 2) * level) / 100) + 5
    speed = math.floor(((base_speed * 2) * level) / 100) + 5
    return {
        'hp': max(1, hp),
        'attack': max(1, attack),
        'defense': max(1, defense),
        'special': max(1, special),
        'speed': max(1, speed)
    }

def award_battle_end_total(user_id, player_state, defeated_opponents, won, db):
    """
    Award EXP to each of the player's Pokémon after a battle ends.
    - For each defeated opponent: state * opponent_level * rarity_base_exp
    - Flat bonus: 64 if won, 32 if lost
    state = 2 if the player's Pokémon is alive, 1 if fainted.
    """
    bonus = 64 if won else 32
    total_exp_gained = 0
    level_up_messages = []

    player_pokemon_list = player_state['pokemon']
    hp_list = player_state['hp']

    for i, pokemon in enumerate(player_pokemon_list):
        state = 2 if hp_list[i] > 0 else 1

        exp_from_opponents = 0
        for opp in defeated_opponents:
            opp_level = opp.get('level', 1)
            opp_rarity = opp.get('rarity', 'Common')
            base = RARITY_BASE_EXP.get(opp_rarity, 16)
            exp_from_opponents += state * opp_level * base

        total_pokemon_exp = exp_from_opponents + bonus
        if total_pokemon_exp <= 0:
            continue

        total_exp_gained += total_pokemon_exp

        # Find the UserPokemon record (prefer user_pokemon_id stored in pokemon dict)
        up_id = pokemon.get('user_pokemon_id')
        if up_id is None:
            up = db.query(UserPokemon).filter_by(
                user_id=user_id, pokemon_id=pokemon['id']
            ).first()
        else:
            up = db.query(UserPokemon).filter_by(id=up_id).first()
        if not up:
            continue

        up.xp = (up.xp or 0) + total_pokemon_exp
        old_level = up.level
        new_level = get_level_from_exp(up.xp)
        if new_level > old_level:
            up.level = new_level
            base_pokemon = up.pokemon
            if base_pokemon:
                new_stats = calculate_stats_on_level_up(
                    base_pokemon.hp, base_pokemon.attack, base_pokemon.defense,
                    base_pokemon.special_attack, base_pokemon.speed, new_level
                )
                up.max_hp = new_stats['hp']
                up.attack = new_stats['attack']
                up.defense = new_stats['defense']
                up.special = new_stats['special']
                up.speed = new_stats['speed']
                # Update the in‑memory Pokémon data (won't affect battle, but good for consistency)
                pokemon['hp'] = up.max_hp
                pokemon['max_hp'] = up.max_hp
                pokemon['attack'] = up.attack
                pokemon['defense'] = up.defense
                pokemon['special'] = up.special
                pokemon['speed'] = up.speed
                pokemon['level'] = new_level

                level_up_messages.append(
                    f"{base_pokemon.name} grew to level {new_level}!"
                )
        db.add(up)

    db.commit()
    return total_exp_gained, level_up_messages