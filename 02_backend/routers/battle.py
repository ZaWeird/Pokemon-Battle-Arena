# 02_backend/routers/battle.py
from flask import Blueprint, request, jsonify
import time
import uuid
from services.auth_utils import verify_token
from services.battle_service import pending_levels

router = Blueprint('battle', __name__, url_prefix='/api')

@router.route('/battle/pve', methods=['POST'])
def start_pve_battle():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token missing'}), 401
    
    user_id = verify_token(token)
    if not user_id:
        return jsonify({'message': 'Invalid token'}), 401
    
    # Read level from frontend, default 50
    data = request.get_json(silent=True) or {}
    level = data.get('level')

    room_id = f"pve_{user_id}_{int(time.time())}_{uuid.uuid4().hex[:6]}"
    
    # Store the level temporarily; handle_join_battle will read it
    pending_levels[room_id] = level
    
    return jsonify({'roomId': room_id, 'message': 'PvE battle created'})