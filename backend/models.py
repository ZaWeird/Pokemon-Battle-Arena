from database import db
from datetime import datetime
import bcrypt

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    coins = db.Column(db.Integer, default=500)  # Starting coins
    wins = db.Column(db.Integer, default=0)
    losses = db.Column(db.Integer, default=0)
    rank = db.Column(db.String(20), default='Bronze')
    rating = db.Column(db.Integer, default=1000)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pokemons = db.relationship('UserPokemon', backref='owner', lazy=True, cascade='all, delete-orphan')
    battles = db.relationship('Battle', foreign_keys='Battle.player1_id', backref='player1', lazy=True)
    battles_as_player2 = db.relationship('Battle', foreign_keys='Battle.player2_id', backref='player2', lazy=True)
    
    def set_password(self, password):
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))

class Pokemon(db.Model):
    __tablename__ = 'pokemons'
    
    id = db.Column(db.Integer, primary_key=True)
    pokeapi_id = db.Column(db.Integer, unique=True, nullable=False)
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    hp = db.Column(db.Integer, nullable=False)
    attack = db.Column(db.Integer, nullable=False)
    defense = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(200))
    rarity = db.Column(db.String(20), nullable=False)  # Common, Rare, Epic, Legendary

class UserPokemon(db.Model):
    __tablename__ = 'user_pokemons'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    is_in_team = db.Column(db.Boolean, default=False)
    team_position = db.Column(db.Integer, nullable=True)
    acquired_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    pokemon = db.relationship('Pokemon')

class Battle(db.Model):
    __tablename__ = 'battles'
    
    id = db.Column(db.Integer, primary_key=True)
    player1_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    player2_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    winner_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    battle_type = db.Column(db.String(20), nullable=False)  # PvE or PvP
    battle_log = db.Column(db.Text)
    coins_reward = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
class GachaHistory(db.Model):
    __tablename__ = 'gacha_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    pokemon_id = db.Column(db.Integer, db.ForeignKey('pokemons.id'), nullable=False)
    coins_spent = db.Column(db.Integer, nullable=False)
    summon_date = db.Column(db.DateTime, default=datetime.utcnow)