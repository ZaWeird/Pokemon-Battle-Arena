from .damage_calc import calculate_damage as gen1_calculate_damage

def calculate_damage(attacker, target, move):
    damage, effectiveness, crit = gen1_calculate_damage(attacker, target, move)
    return damage, effectiveness, crit