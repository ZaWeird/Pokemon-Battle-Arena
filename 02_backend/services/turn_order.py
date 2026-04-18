# 02_backend/services/turn_order.py
import random
import math

def get_stat_stage_multiplier(stage):
    """Gen 1 stat stage multiplier (-6 to +6)."""
    if stage >= 0:
        return (2 + stage) / 2
    else:
        return 2 / (2 - stage)

def get_effective_speed(pokemon):
    """
    Calculate effective speed with paralysis and stat stage modifiers.
    pokemon dict must have 'speed', optionally 'status' and 'speed_stage'.
    """
    base_speed = pokemon.get('speed', 50)
    stage = pokemon.get('speed_stage', 0)
    speed = base_speed * get_stat_stage_multiplier(stage)
    if pokemon.get('status') == 'paralysis':
        speed *= 0.5
    return max(1, math.floor(speed))

def get_move_priority(move):
    """Return move priority (Quick Attack = +1, most moves = 0)."""
    priority_moves = {
        'quick attack': 1, 'extremespeed': 1, 'mach punch': 1,
        'vital throw': -1, 'focus punch': -1
    }
    return priority_moves.get(move.get('name', '').lower(), 0)

def determine_turn_order(pokemon1, pokemon2, move1, move2):
    """
    Determine which Pokémon moves first.
    Returns ('player', 'ai') or ('ai', 'player').
    """
    p1_prio = get_move_priority(move1)
    p2_prio = get_move_priority(move2)
    if p1_prio > p2_prio:
        return 'player', 'ai'
    if p2_prio > p1_prio:
        return 'ai', 'player'
    p1_speed = get_effective_speed(pokemon1)
    p2_speed = get_effective_speed(pokemon2)
    if p1_speed > p2_speed:
        return 'player', 'ai'
    if p2_speed > p1_speed:
        return 'ai', 'player'
    # Tie – random 50/50
    return ('player', 'ai') if random.randint(1, 2) == 1 else ('ai', 'player')

def can_move(pokemon):
    """
    Check if a Pokémon can move this turn based on status.
    Returns (can_move, message).
    Updates sleep_counter and clears temporary statuses.
    """
    status = pokemon.get('status')
    name = pokemon.get('name', 'Pokémon')
    if status == 'paralysis':
        if random.randint(1, 100) <= 25:
            return False, f"{name} is paralyzed and can't move!"
        return True, None
    if status == 'sleep':
        counter = pokemon.get('sleep_counter', 0)
        if counter > 0:
            pokemon['sleep_counter'] = counter - 1
            return False, f"{name} is fast asleep."
        else:
            pokemon['status'] = None
            return True, f"{name} woke up!"
    if status == 'freeze':
        if random.randint(1, 100) <= 20:
            pokemon['status'] = None
            return True, f"{name} thawed out!"
        else:
            return False, f"{name} is frozen solid!"
    if status == 'flinch':
        pokemon['status'] = None
        return False, f"{name} flinched and couldn't move!"
    return True, None