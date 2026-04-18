# 04_scripts/clear_pokemon.py
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), '01_database', 'pokemon_battle.db')

def clear_all_pokemon():
    """Delete all Pokemon from database"""
    
    if not os.path.exists(DB_PATH):
        print("Database not found.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get counts before deletion
    cursor.execute("SELECT COUNT(*) FROM pokemons")
    pokemon_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM moves")
    move_count = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM pokemon_moves")
    link_count = cursor.fetchone()[0]
    
    print(f"\nRecords to delete:")
    print(f"  Pokemon: {pokemon_count}")
    print(f"  Moves: {move_count}")
    print(f"  Pokemon-Move links: {link_count}")
    
    confirm = input("\nDelete ALL Pokemon data? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    cursor.execute("DELETE FROM pokemon_moves")
    cursor.execute("DELETE FROM moves")
    cursor.execute("DELETE FROM pokemons")
    conn.commit()
    
    print(f"\nDeleted {pokemon_count} Pokemon")
    print("Database cleared!")
    
    conn.close()

def clear_by_rarity(rarity):
    """Delete Pokemon by rarity"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM pokemons WHERE rarity = ?", (rarity,))
    count = cursor.fetchone()[0]
    
    if count == 0:
        print(f"No Pokemon found with rarity: {rarity}")
        return
    
    confirm = input(f"Delete {count} Pokemon with rarity '{rarity}'? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    cursor.execute("DELETE FROM pokemon_moves WHERE pokemon_id IN (SELECT id FROM pokemons WHERE rarity = ?)", (rarity,))
    cursor.execute("DELETE FROM pokemons WHERE rarity = ?", (rarity,))
    conn.commit()
    
    print(f"Deleted {count} Pokemon with rarity '{rarity}'")
    conn.close()

if __name__ == '__main__':
    print("=" * 40)
    print("Pokemon Database Cleaner")
    print("=" * 40)
    print("1. Delete ALL Pokemon")
    print("2. Delete by rarity")
    print("3. Exit")
    
    choice = input("\nChoose option (1-3): ")
    
    if choice == '1':
        clear_all_pokemon()
    elif choice == '2':
        rarity = input("Enter rarity (Common, Rare, Epic, Legendary): ")
        clear_by_rarity(rarity)
    else:
        print("Exiting...")