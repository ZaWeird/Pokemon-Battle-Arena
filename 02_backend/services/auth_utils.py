import jwt
from config import Config
from functools import wraps
from flask import request, jsonify

def verify_token(token):
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=['HS256'])
        return payload.get('user_id')
    except:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token missing'}), 401
        if token.startswith('Bearer '):
            token = token[7:]
        user_id = verify_token(token)
        if not user_id:
            return jsonify({'message': 'Invalid token'}), 401
        return f(user_id, *args, **kwargs)
    return decorated