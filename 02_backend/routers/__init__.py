# 02_backend/routers/__init__.py
from . import auth
from . import gacha
from . import inventory
from . import team
from . import leaderboard
from . import battle

__all__ = ['auth', 'gacha', 'inventory', 'team', 'leaderboard', 'battle']