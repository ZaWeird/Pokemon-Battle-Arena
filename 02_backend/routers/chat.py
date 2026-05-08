# routers/chat.py
"""Chat router for Tazuna88 AI guide."""

from flask import Blueprint, request, jsonify
from services.chat_service import get_chat_response, _gemini_available

router = Blueprint('chat', __name__, url_prefix='/api')


@router.route('/chat', methods=['POST'])
def chat():
    """Handle chat messages from the Tazuna88 widget."""
    data = request.get_json()

    if not data or 'message' not in data:
        return jsonify({'error': 'Message is required'}), 400

    message = data['message'].strip()
    if not message:
        return jsonify({'error': 'Message cannot be empty'}), 400

    # Limit message length
    if len(message) > 500:
        return jsonify({'error': 'Message too long (max 500 characters)'}), 400

    session_id = data.get('session_id', 'default')

    response_text = get_chat_response(message, session_id)

    return jsonify({
        'response': response_text,
        'mode': 'ai' if _gemini_available else 'offline',
    })
