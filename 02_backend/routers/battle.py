# 02_backend/routers/battle.py
from flask import Blueprint, request, jsonify
import time
from services.auth_utils import verify_token

router = Blueprint('battle', __name__, url_prefix='/api')

@router.route('/battle/pve', methods=['POST'])
def start_pve_battle():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid token'}), 401
    
    room_id = f"pve_{user_id}_{int(time.time())}"
    return jsonify({'roomId': room_id, 'message': 'PvE battle created'})