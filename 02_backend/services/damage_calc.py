import random
import math

TYPE_EFFECTIVENESS = {
    'normal': {'rock': 0.5, 'ghost': 0, 'steel': 0.5},
    'fire': {'fire': 0.5, 'water': 0.5, 'grass': 2.0, 'ice': 2.0, 'bug': 2.0, 'rock': 0.5, 'dragon': 0.5, 'steel': 0.5},
    'water': {'fire': 2.0, 'water': 0.5, 'grass': 0.5, 'ground': 2.0, 'rock': 2.0, 'dragon': 0.5},
    'electric': {'water': 2.0, 'electric': 0.5, 'grass': 0.5, 'ground': 0, 'flying': 2.0},
    'grass': {'fire': 0.5, 'water': 2.0, 'grass': 0.5, 'poison': 0.5, 'ground': 2.0, 'flying': 0.5, 'bug': 0.5, 'rock': 2.0, 'dragon': 0.5},
    'ice': {'fire': 0.5, 'water': 0.5, 'grass': 2.0, 'ice': 0.5, 'ground': 2.0, 'flying': 2.0, 'dragon': 2.0, 'steel': 0.5},
    'fighting': {'normal': 2.0, 'ice': 2.0, 'rock': 2.0, 'dark': 2.0, 'steel': 2.0, 'poison': 0.5, 'flying': 0.5, 'psychic': 0.5, 'bug': 0.5, 'ghost': 0},
    'poison': {'grass': 2.0, 'poison': 0.5, 'ground': 0.5, 'rock': 0.5, 'ghost': 0.5, 'steel': 0},
    'ground': {'fire': 2.0, 'electric': 2.0, 'poison': 2.0, 'rock': 2.0, 'steel': 2.0, 'grass': 0.5, 'bug': 0.5, 'flying': 0},
    'flying': {'grass': 2.0, 'fighting': 2.0, 'bug': 2.0, 'electric': 0.5, 'rock': 0.5, 'steel': 0.5},
    'psychic': {'fighting': 2.0, 'poison': 2.0, 'psychic': 0.5, 'steel': 0.5},
    'bug': {'grass': 2.0, 'psychic': 2.0, 'dark': 2.0, 'fire': 0.5, 'fighting': 0.5, 'poison': 0.5, 'flying': 0.5, 'ghost': 0.5, 'steel': 0.5},
    'rock': {'fire': 2.0, 'ice': 2.0, 'flying': 2.0, 'bug': 2.0, 'fighting': 0.5, 'ground': 0.5, 'steel': 0.5},
    'ghost': {'ghost': 2.0, 'normal': 0, 'psychic': 0},
    'dragon': {'dragon': 2.0, 'steel': 0.5}
}

def get_type_effectiveness(move_type, target_types):
    if not target_types:
        return 1.0
    multiplier = 1.0
    for t in target_types:
        eff = TYPE_EFFECTIVENESS.get(move_type, {}).get(t, 1.0)
        multiplier *= eff
        if multiplier == 0:
            return 0
    return multiplier

def calculate_damage(attacker, target, move, is_reflect_up=False, is_light_screen_up=False, random_value=None):
    # Fixed 6.25% critical chance
    is_critical = random.randint(1, 16) == 1

    # Determine A and D based on move class
    if move.get('damage_class') == 'physical':
        A = attacker.get('attack', 50)
        D = target.get('defense', 50)
        if is_reflect_up and not is_critical:
            D *= 2
    else:
        A = attacker.get('special', 50)
        D = target.get('special', 50)
        if is_light_screen_up and not is_critical:
            D *= 2

    # Explosion / Selfdestruct
    if move.get('name', '').lower() in ['explosion', 'selfdestruct']:
        D = max(1, D // 2)

    if A > 255 or D > 255:
        A = math.floor(A / 4)
        D = math.floor(D / 4)

    if D == 0:
        raise ZeroDivisionError("Gen 1 crash: D cannot be zero")

    level = attacker.get('level', 5)
    power = move.get('power', 40)
    critical = 2 if is_critical else 1

    step1 = math.floor((2 * level * critical) / 5 + 2)
    step2 = math.floor(step1 * power * A / D)
    step3 = math.floor(step2 / 50)
    damage = step3 + 2
    pre_random = damage

    if move.get('type') in attacker.get('types', []):
        damage += math.floor(damage / 2)

    effectiveness = get_type_effectiveness(move.get('type'), target.get('types', []))
    if effectiveness == 0:
        return 0, effectiveness, is_critical

    damage = math.floor(damage * effectiveness)

    if random_value is None:
        random_mult = 1 if pre_random == 1 else random.randint(217, 255)
    else:
        random_mult = random_value

    damage = math.floor(damage * random_mult / 255)

    if damage < 1 and effectiveness > 0:
        damage = 1

    return damage, effectiveness, is_critical