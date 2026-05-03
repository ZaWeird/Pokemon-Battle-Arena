-- Users table
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    coins INTEGER DEFAULT 500,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    rank TEXT DEFAULT 'Bronze',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pokemon base data (from PokeAPI)
CREATE TABLE IF NOT EXISTS pokemons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokeapi_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    hp INTEGER NOT NULL,
    attack INTEGER NOT NULL,
    defense INTEGER NOT NULL,
    special_attack INTEGER NOT NULL DEFAULT 50,
    special_defense INTEGER NOT NULL DEFAULT 50,
    speed INTEGER NOT NULL,
    base_experience INTEGER NOT NULL DEFAULT 100,
    image_url TEXT,
    rarity TEXT NOT NULL
);

-- User's Pokemon collection
CREATE TABLE IF NOT EXISTS user_pokemons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pokemon_id INTEGER NOT NULL,
    level INTEGER DEFAULT 1,
    xp INTEGER DEFAULT 0,
    max_hp INTEGER NOT NULL DEFAULT 0,
    attack INTEGER NOT NULL DEFAULT 0,
    defense INTEGER NOT NULL DEFAULT 0,
    special INTEGER NOT NULL DEFAULT 0,
    speed INTEGER NOT NULL DEFAULT 0,
    is_in_team BOOLEAN DEFAULT 0,
    team_position INTEGER,
    acquired_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemons(id) ON DELETE CASCADE
);

-- Moves data
CREATE TABLE IF NOT EXISTS moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokeapi_id INTEGER UNIQUE NOT NULL,
    name TEXT NOT NULL,
    accuracy INTEGER,
    power INTEGER,
    damage_class TEXT NOT NULL,
    type TEXT NOT NULL,
    pp INTEGER NOT NULL DEFAULT 35,
    stat_changes TEXT,
    ailment TEXT,
    ailment_chance INTEGER DEFAULT 0,
    flinch_chance INTEGER DEFAULT 0,
    healing INTEGER DEFAULT 0,
    drain INTEGER DEFAULT 0,
    min_hits INTEGER DEFAULT 1,
    max_hits INTEGER DEFAULT 1,
    crit_rate INTEGER DEFAULT 0
);

-- Pokemon-Move junction table
CREATE TABLE IF NOT EXISTS pokemon_moves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pokemon_id INTEGER NOT NULL,
    move_id INTEGER NOT NULL,
    learn_level INTEGER NOT NULL,
    FOREIGN KEY (pokemon_id) REFERENCES pokemons(id) ON DELETE CASCADE,
    FOREIGN KEY (move_id) REFERENCES moves(id) ON DELETE CASCADE,
    UNIQUE(pokemon_id, move_id)
);

-- Battle history
CREATE TABLE IF NOT EXISTS battles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    opponent_type TEXT NOT NULL DEFAULT 'ai',
    result TEXT NOT NULL,
    coins_earned INTEGER DEFAULT 0,
    xp_earned INTEGER DEFAULT 0,
    battle_log TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (player_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Gacha summon history
CREATE TABLE IF NOT EXISTS gacha_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pokemon_id INTEGER NOT NULL,
    coins_spent INTEGER NOT NULL,
    summon_type TEXT DEFAULT 'single',
    summoned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (pokemon_id) REFERENCES pokemons(id) ON DELETE CASCADE
);

-- Shop items
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE,
    description TEXT,
    item_type TEXT,
    exp_value INTEGER,
    price INTEGER
);

-- User's purchased items
CREATE TABLE IF NOT EXISTS user_items (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    item_id INTEGER,
    quantity INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(item_id) REFERENCES items(id)
);