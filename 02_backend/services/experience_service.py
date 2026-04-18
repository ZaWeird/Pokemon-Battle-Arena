# 02_backend/services/experience_service.py
import math

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

def get_level_from_exp(total_exp):
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

def award_battle_exp(user_id, player_state, defeated_pokemon, battle_log):
    """Award EXP to participating Pokémon (simplified – expand as needed)"""
    # For now, give 20 EXP; you can implement full EXP distribution later.
    exp_gained = 20
    level_up_messages = []
    # Here you would update the database and check for level-ups.
    return exp_gained, level_up_messages