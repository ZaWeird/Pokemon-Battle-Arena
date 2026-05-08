# 02_backend/routers/shop.py
from flask import Blueprint, request, jsonify
import jwt
from config import Config
from dependencies import get_db
from models import User, UserItem, Item, UserPokemon
from services.experience_service import get_level_from_exp, calculate_stats_on_level_up

router = Blueprint('shop', __name__, url_prefix='/api')

@router.route('/shop/items', methods=['GET'])
def get_shop_items():
    db = next(get_db())
    try:
        items = db.query(Item).all()
        return jsonify([{
            'id': i.id,
            'name': i.name,
            'description': i.description,
            'price': i.price,
            'exp_value': i.exp_value
        } for i in items])
    finally:
        db.close()

@router.route('/shop/buy', methods=['POST'])
def buy_item():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
    except:
        return jsonify({'message': 'Invalid token'}), 401

    req = request.json
    item_id = req.get('item_id')
    quantity = req.get('quantity', 1)

    db = next(get_db())
    try:
        user = db.query(User).filter_by(id=user_id).first()
        item = db.query(Item).filter_by(id=item_id).first()

        if not item:
            return jsonify({'message': 'Item not found'}), 404

        total_cost = item.price * quantity
        if user.coins < total_cost:
            return jsonify({'message': 'Not enough coins'}), 400

        user.coins -= total_cost

        user_item = db.query(UserItem).filter_by(user_id=user_id, item_id=item_id).first()
        if user_item:
            user_item.quantity += quantity
        else:
            user_item = UserItem(user_id=user_id, item_id=item_id, quantity=quantity)
            db.add(user_item)

        db.commit()
        return jsonify({'message': f'Bought {quantity}x {item.name}', 'new_balance': user.coins})
    finally:
        db.close()

@router.route('/feed', methods=['POST'])
def feed_pokemon():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    if token.startswith('Bearer '):
        token = token[7:]

    try:
        data = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        user_id = data['user_id']
    except:
        return jsonify({'message': 'Invalid token'}), 401

    req = request.json
    user_pokemon_id = req.get('user_pokemon_id')
    item_id = req.get('item_id')
    quantity = req.get('quantity', 1)

    if quantity <= 0:
        return jsonify({'message': 'Quantity must be at least 1'}), 400

    db = next(get_db())
    user_pokemon = db.query(UserPokemon).filter_by(id=user_pokemon_id, user_id=user_id).first()
    if not user_pokemon:
        return jsonify({'message': 'Pokémon not found'}), 404

    user_item = db.query(UserItem).filter_by(user_id=user_id, item_id=item_id).first()
    if not user_item or user_item.quantity < quantity:
        return jsonify({'message': f'You only have {user_item.quantity if user_item else 0} of this item'}), 400

    item = db.query(Item).filter_by(id=item_id).first()
    if not item or item.item_type != 'exp_candy':
        return jsonify({'message': 'Invalid item for feeding'}), 400

    # Total EXP gained
    total_exp_gain = item.exp_value * quantity
    old_exp = user_pokemon.xp or 0
    new_exp = old_exp + total_exp_gain
    old_level = user_pokemon.level
    new_level = get_level_from_exp(new_exp)

    level_up_messages = []
    # Recalculate stats if level increased
    if new_level > old_level:
        base = user_pokemon.pokemon
        for lvl in range(old_level + 1, new_level + 1):
            stats = calculate_stats_on_level_up(
                base.hp, base.attack, base.defense,
                base.special_attack, base.speed, lvl
            )
            user_pokemon.max_hp = stats['hp']
            user_pokemon.attack = stats['attack']
            user_pokemon.defense = stats['defense']
            user_pokemon.special = stats['special']
            user_pokemon.speed = stats['speed']
            user_pokemon.level = lvl
            level_up_messages.append(f"Level up to {lvl}!")
    # Update HP if current HP is zero? Not needed; stats updated.
    user_pokemon.xp = new_exp
    user_item.quantity -= quantity
    remaining_qty = user_item.quantity
    if remaining_qty <= 0:
        remaining_qty = 0
        db.delete(user_item)
    db.commit()

    return jsonify({
        'message': f'{user_pokemon.pokemon.name} gained {total_exp_gain} EXP!',
        'new_level': user_pokemon.level,
        'level_up_messages': level_up_messages,
        'new_exp': user_pokemon.xp,
        'remaining_quantity': remaining_qty
    })