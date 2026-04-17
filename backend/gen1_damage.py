# backend/gen1_damage.py
import random
import math

# Type effectiveness chart for Gen 1
TYPE_EFFECTIVENESS = {
    # Attacking Type: {Defending Type: multiplier}
    'normal': {
        'rock': 0.5,
        'ghost': 0,  # Immune
        'steel': 0.5
    },
    'fire': {
        'fire': 0.5,
        'water': 0.5,
        'grass': 2.0,
        'ice': 2.0,
        'bug': 2.0,
        'rock': 0.5,
        'dragon': 0.5,
        'steel': 0.5
    },
    'water': {
        'fire': 2.0,
        'water': 0.5,
        'grass': 0.5,
        'ground': 2.0,
        'rock': 2.0,
        'dragon': 0.5
    },
    'electric': {
        'water': 2.0,
        'electric': 0.5,
        'grass': 0.5,
        'ground': 0,  # Immune
        'flying': 2.0
    },
    'grass': {
        'fire': 0.5,
        'water': 2.0,
        'grass': 0.5,
        'poison': 0.5,
        'ground': 2.0,
        'flying': 0.5,
        'bug': 0.5,
        'rock': 2.0,
        'dragon': 0.5
    },
    'ice': {
        'fire': 0.5,
        'water': 0.5,
        'grass': 2.0,
        'ice': 0.5,
        'ground': 2.0,
        'flying': 2.0,
        'dragon': 2.0,
        'steel': 0.5
    },
    'fighting': {
        'normal': 2.0,
        'ice': 2.0,
        'rock': 2.0,
        'dark': 2.0,
        'steel': 2.0,
        'poison': 0.5,
        'flying': 0.5,
        'psychic': 0.5,
        'bug': 0.5,
        'ghost': 0  # Immune
    },
    'poison': {
        'grass': 2.0,
        'poison': 0.5,
        'ground': 0.5,
        'rock': 0.5,
        'ghost': 0.5,
        'steel': 0  # Immune
    },
    'ground': {
        'fire': 2.0,
        'electric': 2.0,
        'poison': 2.0,
        'rock': 2.0,
        'steel': 2.0,
        'grass': 0.5,
        'bug': 0.5,
        'flying': 0  # Immune
    },
    'flying': {
        'grass': 2.0,
        'fighting': 2.0,
        'bug': 2.0,
        'electric': 0.5,
        'rock': 0.5,
        'steel': 0.5
    },
    'psychic': {
        'fighting': 2.0,
        'poison': 2.0,
        'psychic': 0.5,
        'steel': 0.5,
        'dark': 0  # Immune in later gens, but in Gen 1 it's neutral
    },
    'bug': {
        'grass': 2.0,
        'psychic': 2.0,
        'dark': 2.0,
        'fire': 0.5,
        'fighting': 0.5,
        'poison': 0.5,
        'flying': 0.5,
        'ghost': 0.5,
        'steel': 0.5
    },
    'rock': {
        'fire': 2.0,
        'ice': 2.0,
        'flying': 2.0,
        'bug': 2.0,
        'fighting': 0.5,
        'ground': 0.5,
        'steel': 0.5
    },
    'ghost': {
        'ghost': 2.0,
        'psychic': 0,  # Immune in Gen 1? Actually Ghost doesn't affect Psychic in Gen 1
        'normal': 0  # Immune
    },
    'dragon': {
        'dragon': 2.0,
        'steel': 0.5
    }
}

# Base stats for Pokemon (these will come from your database)
# This is just for reference

def get_type_effectiveness(move_type, target_types):
    """
    Calculate type effectiveness multiplier for Gen 1
    Returns the combined multiplier (0, 0.25, 0.5, 1, 2, or 4)
    """
    if not target_types:
        return 1.0
    
    multiplier = 1.0
    for target_type in target_types:
        effectiveness = TYPE_EFFECTIVENESS.get(move_type, {}).get(target_type, 1.0)
        multiplier *= effectiveness
    
    # If any type gives immunity (0), overall is 0
    if multiplier == 0:
        return 0
    
    return multiplier

def get_random_damage_multiplier(pre_random_damage):
    """
    Get random multiplier for damage calculation
    If pre_random_damage is 1, multiplier is 1 (fixed damage)
    Otherwise, random between 217 and 255
    """
    if pre_random_damage == 1:
        return 1
    return random.randint(217, 255)

def is_critical_hit():
    """
    Gen 1 critical hit chance: base 6.25% (1/16)
    """
    return random.randint(1, 16) == 1

def calculate_damage(attacker, target, move, is_critical=False, is_reflect_up=False, is_light_screen_up=False, random_value=None):
    """
    Calculate damage using exact Gen 1 formula
    
    Parameters:
    - attacker: dict with 'attack', 'defense', 'special', 'types', 'level'
    - target: dict with 'defense', 'special', 'types', 'level'
    - move: dict with 'power', 'type', 'damage_class' (physical/special)
    - is_critical: boolean for critical hit
    - is_reflect_up: boolean for Reflect screen
    - is_light_screen_up: boolean for Light Screen
    - random_value: optional fixed random value (for testing)
    
    Returns:
    - damage: int (minimum 1)
    - effectiveness: float (type effectiveness multiplier)
    - is_critical: bool
    """
    
    # Determine A (Attack) and D (Defense) based on move type
    if move.get('damage_class') == 'physical':
        A = attacker.get('attack', 50)
        D = target.get('defense', 50)
        
        # Apply Reflect if active
        if is_reflect_up:
            D = D * 2
    else:  # special
        A = attacker.get('special', 50)
        D = target.get('special', 50)
        
        # Apply Light Screen if active
        if is_light_screen_up:
            D = D * 2
    
    # Special case for Explosion/Selfdestruct
    if move.get('name') in ['explosion', 'selfdestruct']:
        D = max(1, D // 2)
    
    # Handle D = 0 (Gen 1 crash prevention)
    if D == 0:
        raise ValueError("Gen 1 crash: Division by zero - D cannot be 0")
    
    # Overflow handling: If A > 255 or D > 255, divide by 4
    if A > 255 or D > 255:
        A = math.floor(A / 4)
        D = math.floor(D / 4)
        # Ensure minimum values
        A = max(1, A)
        D = max(1, D)
    
    # Critical hit modifier
    critical = 2 if is_critical else 1
    
    # Level
    level = attacker.get('level', 5)
    
    # Power
    power = move.get('power', 0)
    
    # Step 1: (2 * Level * Critical / 5 + 2)
    step1 = math.floor((2 * level * critical) / 5 + 2)
    
    # Step 2: Step1 * Power * A / D
    step2 = math.floor(step1 * power * A / D)
    
    # Step 3: Step2 / 50
    step3 = math.floor(step2 / 50)
    
    # Step 4: Step3 + 2
    step4 = step3 + 2
    
    # Store pre-random damage for fixed damage moves
    pre_random_damage = step4
    
    # Apply STAB (Same Type Attack Bonus) - Additive in Gen 1
    if move.get('type') in attacker.get('types', []):
        stab_bonus = math.floor(pre_random_damage / 2)
        step4 = step4 + stab_bonus
    
    # Apply type effectiveness
    effectiveness = get_type_effectiveness(move.get('type', 'normal'), target.get('types', []))
    
    if effectiveness == 0:
        # Immune - move misses
        return 0, effectiveness, is_critical
    
    step4 = step4 * effectiveness
    
    # Apply random multiplier
    if random_value is None:
        random_mult = get_random_damage_multiplier(pre_random_damage)
    else:
        random_mult = random_value
    
    damage = math.floor(step4 * random_mult / 255)
    
    # Minimum damage is always 1 if effectiveness > 0
    if damage < 1 and effectiveness > 0:
        damage = 1
    
    return damage, effectiveness, is_critical

def calculate_move_accuracy(move, target):
    """
    Calculate if a move hits in Gen 1
    Returns True if hit, False if miss
    """
    accuracy = move.get('accuracy', 100)
    
    # Gen 1 accuracy formula
    # Accuracy modifiers not implemented for simplicity
    hit_chance = accuracy
    
    # Special case: moves with 0 accuracy always hit (status moves)
    if accuracy == 0:
        return True
    
    return random.randint(1, 100) <= hit_chance

def get_move_damage_class(move_type, move_name=''):
    """
    Determine if move is physical or special in Gen 1
    Gen 1 rule: All moves of a type are either physical or special
    """
    # Physical types in Gen 1
    physical_types = ['normal', 'fighting', 'flying', 'poison', 'ground', 
                      'rock', 'bug', 'ghost', 'steel']
    
    # Special types in Gen 1
    special_types = ['fire', 'water', 'grass', 'electric', 'psychic', 
                     'ice', 'dragon', 'dark']
    
    # Special case: Counter and Mirror Coat
    if move_name.lower() == 'counter':
        return 'physical'
    if move_name.lower() == 'mirror coat':
        return 'special'
    
    if move_type in physical_types:
        return 'physical'
    else:
        return 'special'

# Helper function to prepare Pokemon data for damage calculation
def prepare_pokemon_for_damage(pokemon_data):
    """
    Convert your Pokemon data format to the format needed for damage calculation
    """
    return {
        'attack': pokemon_data.get('attack', 50),
        'defense': pokemon_data.get('defense', 50),
        'special': pokemon_data.get('special_attack', pokemon_data.get('special', 50)),
        'types': pokemon_data.get('types', ['normal']),
        'level': pokemon_data.get('level', 5)
    }

def prepare_move_for_damage(move_data):
    """
    Convert your move data format to the format needed for damage calculation
    """
    move_type = move_data.get('type', 'normal')
    move_name = move_data.get('name', '')
    
    return {
        'name': move_name,
        'power': move_data.get('power', 0),
        'type': move_type,
        'accuracy': move_data.get('accuracy', 100),
        'damage_class': get_move_damage_class(move_type, move_name)
    }