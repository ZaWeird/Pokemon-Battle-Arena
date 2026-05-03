# Pokemon-Battle-Arena

A full‑stack Pokémon battle simulator with a Gen‑3 inspired pixel UI, real‑time Socket.IO battles, stage selection, gacha, inventory, shop, and leaderboard.

---
## Prerequisites

- Python 3.10+
- Node.js 18+
- npm

## Setup steps
```bash
### 1. Backend Setup

cd 02_backend
# Create & activate virtual environment 
# (Windows PowerShell) 
python -m venv .venv
.venv\Scripts\Activate.ps1

# (Linux / macOS)
python3 -m venv .venv
ource .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
python main.py

### 2. Frontend Setup

cd 03_frontend

# Install dependencies
npm install

# Start the development server
npm run dev

### 3. Guide
    
    - Register a new account or log in.

    - Visit the Lobby to start a PvE battle – choose a stage (levels 5‑50).

    - Earn coins and EXP by winning battles. Defeating higher‑level opponents gives better rewards.

    - Use coins in the Shop to buy EXP candies, and feed them to your Pokémon in the Inventory.

    - Summon new Pokémon in the Gacha section.

    - Build your team in the Team Builder (up to 3 Pokémon).

    - Check the Leaderboard to see how you rank.

### 4. Tech Stack

    - Backend: Python, Flask, Flask‑SocketIO, SQLAlchemy, SQLite

    - Frontend: React, Vite, Axios, Socket.IO‑client

    - Data: PokéAPI (seeded automatically)

### 5. Database

    - The SQLite database is located at 01_database/pokemon_battle.db.

    - It is automatically created and seeded when the backend starts for the first time.
    
    - To force a full reseed, run: python 02_backend/zSeedingz/seedings.py
```

### License

This project is for educational purposes. Redistribution, commercial use, or any form of monetary gain from this project is strictly prohibited without explicit permission from the author.