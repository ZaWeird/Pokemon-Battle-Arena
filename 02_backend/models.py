# 02_backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import bcrypt

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    coins = Column(Integer, default=500)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    rank = Column(String(20), default='Bronze')
    rating = Column(Integer, default=1000)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to UserPokemon
    user_pokemons = relationship('UserPokemon', back_populates='user', cascade='all, delete-orphan')
    items = relationship('UserItem', back_populates='user', cascade='all, delete-orphan')

    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Pokemon(Base):
    __tablename__ = 'pokemons'
    
    id = Column(Integer, primary_key=True)
    pokeapi_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    type = Column(String(50), nullable=False)
    hp = Column(Integer, nullable=False)
    attack = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    special_attack = Column(Integer, nullable=False, default=50)
    special_defense = Column(Integer, nullable=False, default=50)
    speed = Column(Integer, nullable=False)
    base_experience = Column(Integer, nullable=False, default=100)
    image_url = Column(String(200))
    rarity = Column(String(20), nullable=False)

class UserPokemon(Base):
    __tablename__ = 'user_pokemons'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    pokemon_id = Column(Integer, ForeignKey('pokemons.id'), nullable=False)
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    max_hp = Column(Integer, nullable=False, default=0)
    attack = Column(Integer, nullable=False, default=0)
    defense = Column(Integer, nullable=False, default=0)
    special = Column(Integer, nullable=False, default=0)
    speed = Column(Integer, nullable=False, default=0)
    is_in_team = Column(Boolean, default=False)
    team_position = Column(Integer, nullable=True)
    acquired_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship('User', back_populates='user_pokemons')
    pokemon = relationship('Pokemon')

class Move(Base):
    __tablename__ = 'moves'
    
    id = Column(Integer, primary_key=True)
    pokeapi_id = Column(Integer, unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    accuracy = Column(Integer, nullable=True)
    power = Column(Integer, nullable=True)
    damage_class = Column(String(20), nullable=False)
    type = Column(String(20), nullable=False)
    pp = Column(Integer, nullable=False, default=35)
    stat_changes = Column(Text, nullable=True)
    ailment = Column(String(50), nullable=True)
    ailment_chance = Column(Integer, default=0)
    flinch_chance = Column(Integer, default=0)
    healing = Column(Integer, default=0)
    drain = Column(Integer, default=0)
    min_hits = Column(Integer, default=1)
    max_hits = Column(Integer, default=1)
    crit_rate = Column(Integer, default=0)

pokemon = relationship('Pokemon', backref='pokemon_moves')
move = relationship('Move', backref='pokemon_moves')

class PokemonMove(Base):
    __tablename__ = 'pokemon_moves'
    
    id = Column(Integer, primary_key=True)
    pokemon_id = Column(Integer, ForeignKey('pokemons.id'), nullable=False)
    move_id = Column(Integer, ForeignKey('moves.id'), nullable=False)
    learn_level = Column(Integer, nullable=False)

class Battle(Base):
    __tablename__ = 'battles'
    
    id = Column(Integer, primary_key=True)
    player_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    opponent_type = Column(String(20), nullable=False, default='ai')
    result = Column(String(10), nullable=False)
    coins_earned = Column(Integer, default=0)
    xp_earned = Column(Integer, default=0)
    battle_log = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class GachaHistory(Base):
    __tablename__ = 'gacha_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    pokemon_id = Column(Integer, ForeignKey('pokemons.id'), nullable=False)
    coins_spent = Column(Integer, nullable=False)
    summon_type = Column(String(10), default='single')
    summoned_at = Column(DateTime, default=datetime.utcnow)

# ========== NEW MODELS for Shop & Items ==========

class Item(Base):
    __tablename__ = 'items'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False)
    description = Column(String(200))
    item_type = Column(String(20), nullable=False)   # 'exp_candy'
    exp_value = Column(Integer, default=0)          # EXP gained when used
    price = Column(Integer, nullable=False)

class UserItem(Base):
    __tablename__ = 'user_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    quantity = Column(Integer, default=0)
    
    user = relationship('User', back_populates='items')
    item = relationship('Item')