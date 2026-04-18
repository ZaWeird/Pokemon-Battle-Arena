import sqlite3
import os
import math

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

def calculate_stats_on_level_up(base_hp, base_attack, base_defense, base_special, base_speed, level):
    hp = math.floor(((base_hp * 2) * level) / 100) + level + 10
    attack = math.floor(((base_attack * 2) * level) / 100) + 5
    defense = math.floor(((base_defense * 2) * level) / 100) + 5
    special = math.floor(((base_special * 2) * level) / 100) + 5
    speed = math.floor(((base_speed * 2) * level) / 100) + 5
    return hp, attack, defense, special, speed

def fix_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all user_pokemons with their base stats
    cursor.execute("""
        SELECT up.id, up.level, p.hp, p.attack, p.defense, p.special_attack, p.speed
        FROM user_pokemons up
        JOIN pokemons p ON up.pokemon_id = p.id
    """)
    rows = cursor.fetchall()

    updated = 0
    for up_id, level, base_hp, base_atk, base_def, base_spa, base_spd in rows:
        hp, atk, df, spa, spd = calculate_stats_on_level_up(
            base_hp, base_atk, base_def, base_spa, base_spd, level
        )
        cursor.execute("""
            UPDATE user_pokemons
            SET max_hp = ?, attack = ?, defense = ?, special = ?, speed = ?
            WHERE id = ?
        """, (hp, atk, df, spa, spd, up_id))
        updated += 1

    conn.commit()
    conn.close()
    print(f"Fixed stats for {updated} user Pokemon.")

if __name__ == '__main__':
    fix_stats()