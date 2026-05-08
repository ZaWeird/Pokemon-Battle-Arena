# 02_backend/routers/user.py
from flask import Blueprint, request, jsonify
import jwt
from config import Config
from dependencies import get_db
from models import UserItem

router = Blueprint('user', __name__, url_prefix='/api')

@router.route('/user/items', methods=['GET'])
def get_user_items():
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

    db = next(get_db())
    try:
        user_items = db.query(UserItem).filter_by(user_id=user_id).all()

        result = []
        for ui in user_items:
            result.append({
                'item_id': ui.item_id,
                'name': ui.item.name,
                'quantity': ui.quantity,
                'exp_value': ui.item.exp_value
            })
        return jsonify(result)
    finally:
        db.close()