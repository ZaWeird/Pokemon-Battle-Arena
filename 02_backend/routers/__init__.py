# 02_backend/routers/__init__.py
from . import auth
from . import gacha
from . import inventory
from . import team
from . import leaderboard
from . import battle
from . import shop
from . import user
from . import chat

__all__ = ['auth', 'gacha', 'inventory', 'team', 'leaderboard', 'battle', 'shop', 'user', 'chat']