# 02_backend/services/stat_utils.py
import math

def calculate_stats_on_level_up(base_hp, base_attack, base_defense, base_special, base_speed, level):
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