# services/chat_service.py
"""Tazuna88 Chat Service — Gemini-powered Pokemon Battle Arena guide
with rule-based fallback and RAG for accurate game info."""

import random
import os

from config import Config

# ---------- Gemini client (lazy, graceful) ----------
_gemini_client = None
_gemini_available = True   # becomes False after first fatal error (rate limit)

def _get_gemini_client():
    global _gemini_client, _gemini_available
    if _gemini_client is not None:
        return _gemini_client
    try:
        from google import genai
        key = Config.GEMINI_API_KEY
        if not key:
            print("[Tazuna88] No GEMINI_API_KEY set — running in fallback mode.")
            _gemini_available = False
            return None
        _gemini_client = genai.Client(api_key=key)
        return _gemini_client
    except Exception as e:
        print(f"[Tazuna88] Could not initialise Gemini client: {e}")
        _gemini_available = False
        return None

# ---------- In-memory conversation storage ----------
_conversations = {}

# ---------- System prompt ----------
SYSTEM_PROMPT = (
    "You are Tazuna88, a concise Pokémon Battle Arena guide. "
    "ONLY answer game questions (battles, gacha, team, shop, PvE/PvP). "
    "Decline off-topic questions politely. "
    "Game: Gacha summons (Common/Rare/Epic/Legendary), team of 3, turn-based battles, "
    "Type matchups (2x/0.5x/0x), STAB 1.5x, 10 PvE stages, PvP in Lobby, "
    "Exp Candies from Shop to level up. "
    "Use ★ and ▶ occasionally."
)

# ---------- Game-related keywords ----------
_GAME_KEYWORDS = [
    'gacha', 'summon', 'battle', 'fight', 'team', 'shop', 'candy',
    'exp', 'level', 'coin', 'type', 'effective', 'stab', 'damage',
    'speed', 'pve', 'pvp', 'stage', 'inventory', 'leaderboard',
    'lobby', 'move', 'stat', 'rarity', 'pokemon', 'pokémon',
    'dragon', 'ice', 'fire', 'water', 'grass', 'electric',   # common type names
    'weak', 'strong', 'element', 'super effective', 'not very effective'
]

def _is_game_related(message: str) -> bool:
    lowered = message.lower()
    return any(kw in lowered for kw in _GAME_KEYWORDS)

# ---------- RAG retrieval ----------
import chromadb
from google import genai as genai_module

def _get_rag_context(query: str) -> str:
    """Try to get relevant game rule chunks from Chroma. Returns empty string on any failure."""
    try:
        chroma_path = os.path.join(
            os.path.dirname(__file__), '..', 'chat_data', 'chroma_store'
        )
        client = chromadb.PersistentClient(path=chroma_path)
        collection = client.get_collection("game_rules")

        key = Config.GEMINI_API_KEY
        if not key:
            return ""
        gemini_client = genai_module.Client(api_key=key)
        embed_result = gemini_client.models.embed_content(
            model='models/gemini-embedding-001',
            contents=[query],
        )
        if not embed_result.embeddings or len(embed_result.embeddings) == 0:
            return ""
        query_embedding = embed_result.embeddings[0].values

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=3
        )
        if results['documents'] and results['documents'][0]:
            return "\n\n".join(results['documents'][0])
    except Exception as e:
        print(f"[Tazuna88] RAG retrieval error: {e}")
    return ""

# =====================================================================
#  RULE-BASED FALLBACK CHAT  (activates when Gemini is unreachable)
# =====================================================================

_FALLBACK_RULES = [
    # --- Broader type/effectiveness catch-all (NEW) ---
    (["type", "effect"], [
        "★ Type effectiveness: attacks can be super effective (2x), not very effective (0.5x), or immune (0x). Match your moves to your opponent's weakness!",
        "▶ Types matter! Check your opponent's type and use moves that are super effective against it. Your Pokémon's own type may also give STAB bonus!",
    ]),
    (["super", "effective"], [
        "★ Super effective moves deal double damage! Use type matchups to find the right counter. For example, Water beats Fire, Fire beats Grass, Grass beats Water. ♦",
    ]),
    (["element", "damage"], [
        "★ The element (type) of your move determines how much damage it deals. Look for type weaknesses - e.g., Electric is strong against Water but weak to Ground.",
    ]),

    # --- Type matchups (original) ---
    (
        ["type", "matchup"],
        [
            "★ Type matchups follow classic Pokémon rules! Fire beats Grass, Grass beats Water, Water beats Fire. Super effective = 2x damage, not very effective = 0.5x, immune = 0x. Build your team with good type coverage, Trainer!",
            "▶ Here's a quick tip: always check your opponent's types before battle! Super effective moves deal 2x damage. STAB (Same Type Attack Bonus) adds another 1.5x if the move matches your Pokémon's type. ★",
        ],
    ),
    (
        ["type", "effective"],
        [
            "★ Type effectiveness is key! Fire > Grass > Water > Fire is the basic triangle. Don't forget Electric is super effective against Water, Ground beats Electric, and Ghost & Normal are immune to each other!",
        ],
    ),
    # --- Gacha / Summon ---
    (
        ["gacha"],
        [
            "★ The Gacha system lets you summon new Pokémon using coins! You can do a single summon or a multi-summon for better value. Pokémon come in four rarities: Common, Rare, Epic, and Legendary. Good luck on your pulls, Trainer!",
            "▶ Head to the Gacha page to summon Pokémon! Multi-summons give you more chances at Epic and Legendary pulls. Save up those coins! ♦",
        ],
    ),
    (
        ["summon"],
        [
            "★ To summon Pokémon, visit the Gacha page! Spend coins for a chance to get Common, Rare, Epic, or Legendary Pokémon. Multi-summons are a great way to build your collection quickly!",
        ],
    ),
    # --- Team Building ---
    (
        ["team", "build"],
        [
            "★ You can build a team of up to 3 Pokémon in the Team Builder! Consider type coverage — try to cover each other's weaknesses. A balanced team with different types will carry you further in battles!",
            "▶ Team building tips: Pick Pokémon that cover each other's weaknesses, level them up with Exp Candies, and make sure you have a mix of physical and special attackers. ★ Head to the Team Builder to get started!",
        ],
    ),
    (
        ["team"],
        [
            "★ Your battle team holds up to 3 Pokémon! Visit the Team Builder page to assemble your squad. Make sure to level them up before taking on harder PvE stages, Trainer!",
        ],
    ),
    # --- Battle strategy ---
    (
        ["battle", "strateg"],
        [
            "★ Here are my top battle tips: 1) Build a team with good type coverage. 2) Level up your Pokémon with Exp Candies. 3) Pay attention to Speed — the faster Pokémon attacks first. 4) Use STAB moves for 1.5x bonus damage!",
            "▶ Strategy time! Speed determines turn order, so fast Pokémon get a big advantage. Pair that with super effective STAB moves and you'll be crushing stages in no time! ★",
        ],
    ),
    (
        ["strateg"],
        [
            "★ Key strategies: balance your team's types, level up evenly, and always exploit type weaknesses! Check the type chart and pick moves that hit your opponents super effectively. You've got this, Trainer!",
        ],
    ),
    # --- Battle general ---
    (
        ["battle"],
        [
            "★ Battles are turn-based! Each Pokémon has 4 moves. The one with higher Speed goes first. Damage depends on ATK/SPA, DEF/SPD, move power, type effectiveness, and STAB. Head to the Lobby to start a battle!",
            "▶ Ready to battle? You can take on PvE stages for rewards or challenge other Trainers in PvP! Make sure your team is set in the Team Builder first. ★",
        ],
    ),
    # --- PvE ---
    (
        ["pve", "stage"],
        [
            "★ PvE has 20 stages of increasing difficulty! Each stage features specific Pokémon at set levels. Make sure to level up your team before tackling harder stages. Rewards get better as you progress!",
            "▶ Stuck on a PvE stage? Try leveling up your Pokémon with Exp Candies from the Shop, and make sure your team has type advantages against that stage's opponents! ★",
        ],
    ),
    (
        ["pve"],
        [
            "★ PvE mode lets you fight AI opponents across 20 stages! Start from Stage 1 and work your way up. Each stage gets tougher, so keep leveling your team. You can start PvE from the Lobby!",
        ],
    ),
    # --- PvP ---
    (
        ["pvp"],
        [
            "★ PvP lets you challenge other Trainers in real-time battles! Head to the Lobby and look for available opponents. Make sure your team of 3 is set in the Team Builder before jumping in!",
            "▶ PvP battles are the ultimate test! Outsmart your opponent with smart type coverage and higher-level Pokémon. Check the Leaderboard to see how you rank! ★",
        ],
    ),
    # --- Shop ---
    (
        ["shop"],
        [
            "★ The Shop sells useful items like Exp Candies! Use them to level up your Pokémon and boost their stats. Visit the Shop page from the navigation menu. Stronger Pokémon = easier battles!",
            "▶ Head to the Shop to stock up on Exp Candies! Leveling up your Pokémon is the fastest way to get stronger for PvE stages and PvP battles. ★",
        ],
    ),
    # --- Leveling / EXP / Candy ---
    (
        ["level"],
        [
            "★ Level up your Pokémon by feeding them Exp Candies! You can buy candies in the Shop. Higher-level Pokémon have better stats and deal more damage in battle. Keep grinding, Trainer!",
            "▶ To help you level up: buy Exp Candies from the Shop → go to your Inventory → feed them to your Pokémon! Each level boosts HP, ATK, DEF, SPA, SPD, and SPE. ★",
        ],
    ),
    (
        ["exp", "cand"],
        [
            "★ Exp Candies are available in the Shop! Feed them to your Pokémon in the Inventory to gain levels. More levels = higher stats = more battle power! ♦",
        ],
    ),
    (
        ["candy"],
        [
            "★ Exp Candies level up your Pokémon! Buy them from the Shop, then use them in your Inventory. Each candy gives your Pokémon a stat boost across the board!",
        ],
    ),
    # --- Inventory ---
    (
        ["inventory"],
        [
            "★ Your Inventory shows all the Pokémon you've collected! Check their stats (HP, ATK, DEF, SPA, SPD, SPE), types, and levels. You can also feed them Exp Candies here to level up!",
        ],
    ),
    # --- Leaderboard ---
    (
        ["leaderboard", "rank"],
        [
            "★ The Leaderboard ranks Trainers by wins and battle performance! Keep battling in PvP and PvE to climb the ranks. Check it out from the navigation menu!",
        ],
    ),
    (
        ["leaderboard"],
        [
            "★ Visit the Leaderboard to see the top Trainers! Rankings are based on wins and performance. Keep winning battles to climb higher! ♦",
        ],
    ),
    # --- Lobby ---
    (
        ["lobby"],
        [
            "★ The Lobby is your hub! From here you can start PvE stages or join PvP battles against other Trainers. Make sure your team is ready in the Team Builder first!",
        ],
    ),
    # --- Navigation / help ---
    (
        ["how", "play"],
        [
            "★ Here's how to get started, Trainer! 1) Summon Pokémon in the Gacha. 2) Check your Inventory. 3) Build a team of 3 in the Team Builder. 4) Head to the Lobby to battle! Buy Exp Candies from the Shop to level up. ▶",
        ],
    ),
    (
        ["help"],
        [
            "★ I'm here to help, Trainer! You can ask me about: type matchups, battle strategy, gacha/summoning, team building, the shop, leveling up, PvE stages, PvP battles, or how to navigate the game!",
            "▶ Need help? Here's what I can guide you on: ★ Battle mechanics ★ Type effectiveness ★ Gacha summoning ★ Team building ★ Shop & leveling ★ PvE/PvP tips. Just ask!",
        ],
    ),
    # --- Greetings ---
    (
        ["hello"],
        [
            "Hey there, Trainer! ★ I'm Tazuna88, your Pokémon Battle Arena guide! What would you like to know? I can help with battles, team building, gacha, and more!",
        ],
    ),
    (
        ["hi"],
        [
            "Hi, Trainer! ★ Welcome! Ask me anything about Pokémon Battle Arena — battles, gacha, type matchups, leveling up, you name it!",
        ],
    ),
    (
        ["hey"],
        [
            "Hey! ★ Ready to become the ultimate Trainer? Ask me about battles, team building, the shop, or anything about Pokémon Battle Arena!",
        ],
    ),
    # --- Damage / STAB ---
    (
        ["damage"],
        [
            "★ Damage is calculated using the attacker's ATK (or SPA for special moves), defender's DEF (or SPD), move power, type effectiveness, STAB (1.5x if the move matches the Pokémon's type), and level. Stack those bonuses for maximum impact!",
        ],
    ),
    (
        ["stab"],
        [
            "★ STAB stands for Same Type Attack Bonus! If a Fire-type Pokémon uses a Fire-type move, it gets a 1.5x damage boost. Always try to use moves that match your Pokémon's type for extra power!",
        ],
    ),
    # --- Speed ---
    (
        ["speed"],
        [
            "★ Speed determines who attacks first in battle! The Pokémon with higher SPE goes first each turn. This can be a huge advantage — striking first might knock out the opponent before they can act!",
        ],
    ),
    # --- Coins ---
    (
        ["coin"],
        [
            "★ Coins are the main currency! Earn them by winning battles and completing PvE stages. Spend them on Gacha summons or Shop items like Exp Candies. Keep battling to stack those coins, Trainer!",
        ],
    ),
    # --- Rarity ---
    (
        ["rarity"],
        [
            "★ Pokémon come in four rarities: Common, Rare, Epic, and Legendary! Higher rarity Pokémon tend to have better base stats. Try multi-summons in the Gacha for better chances at Epic and Legendary pulls!",
        ],
    ),
    (
        ["legendary"],
        [
            "★ Legendary Pokémon are the rarest and most powerful! They have the highest base stats. Keep summoning in the Gacha and you might just pull one. Good luck, Trainer! ♦",
        ],
    ),
    # --- Stats ---
    (
        ["stat"],
        [
            "★ Each Pokémon has 6 stats: HP (health), ATK (physical attack), DEF (physical defense), SPA (special attack), SPD (special defense), and SPE (speed). Level up with Exp Candies to boost all stats!",
        ],
    ),
    # --- Moves ---
    (
        ["move"],
        [
            "★ Each Pokémon has 4 moves to use in battle! Moves have a type, power, and can be physical or special. Pick moves with good type coverage and STAB for maximum effectiveness!",
        ],
    ),
]

# Catch-all response when no rule matches
_FALLBACK_DEFAULT = [
    "★ Great question, Trainer! I'm currently in offline mode, so my answers are limited. Try asking about: type matchups, battle strategy, gacha, team building, the shop, leveling, PvE, or PvP!",
    "▶ I'm running in backup mode right now! I can help with common questions about battles, team building, gacha summoning, type effectiveness, and game navigation. What do you need? ★",
    "♦ I'm in offline guide mode! Ask me about specific topics like 'type matchups', 'team building tips', 'how does gacha work', or 'battle strategy' and I'll do my best! ★",
]

def _fallback_response(message: str, is_game: bool = False) -> str:
    """Return a rule-based response. If is_game is True and no rule matches,
    give a game-specific fallback instead of the generic default."""
    lowered = message.lower()
    for keywords, responses in _FALLBACK_RULES:
        if all(kw in lowered for kw in keywords):
            return random.choice(responses)
    if is_game:
        return random.choice([
            "★ That's a great battle question! My AI brain is a bit slow right now. Try asking about type matchups, damage, or PvE stages!",
            "▶ I know the answer, but I'm having trouble accessing my full knowledge. Ask me about something like 'how does damage work?' and I'll explain!",
            "♦ I can help with that! Please rephrase your question about types, battles, or team building and I'll give you a detailed answer.",
        ])
    return random.choice(_FALLBACK_DEFAULT)

# ---------- Public API ----------
def get_chat_response(message: str, session_id: str) -> str:
    global _gemini_available

    # 0. Always use fallback for common greetings (no API call)
    lowered = message.lower().strip()
    if any(kw in lowered for kw in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
        return _fallback_response(message)

    # 1. Determine if the question is game‑related (used even if we fall back)
    is_game_q = _is_game_related(message)

    # 2. If Gemini is unavailable, use fallback for everything
    if not _gemini_available:
        return _fallback_response(message, is_game_q)

    client = _get_gemini_client()
    if client is None:
        return _fallback_response(message, is_game_q)

    # 3. Gemini is available - try to use it for ALL messages
    try:
        from google import genai

        # Retrieve or create conversation history
        if session_id not in _conversations:
            _conversations[session_id] = []
        history = _conversations[session_id]

        formatted_history = []
        for msg in history[-6:]:
            role = "user" if msg["role"] == "user" else "model"
            formatted_history.append({"role": role, "parts": [{"text": msg["content"]}]})

        # 4. Build system prompt
        if is_game_q:
            # Attempt RAG - if it fails, we still continue with just the system prompt
            rag_context = _get_rag_context(message)
            if rag_context:
                final_prompt = (
                    SYSTEM_PROMPT +
                    "\n\nUse the following verified game information when answering:\n" +
                    rag_context
                )
            else:
                final_prompt = SYSTEM_PROMPT
        else:
            # General question - no RAG, but tag it as off‑topic
            final_prompt = (
                SYSTEM_PROMPT +
                "\n\nIf the user asks a question that is not related to Pokémon Battle Arena, "
                "politely remind them that you can only answer game questions, and add "
                "'★ This question is outside the game scope!' at the end of your reply."
            )
        chat = client.chats.create(
            model='gemini-2.5-flash',
            config=genai.types.GenerateContentConfig(
                system_instruction=final_prompt,
                temperature=0.7,
                max_output_tokens=1000,
            ),
            history=formatted_history
        )

        response = chat.send_message(message)
        reply = response.text

        # Update history
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": reply})
        _conversations[session_id] = history

        # Limit stored conversations
        if len(_conversations[session_id]) > 6:
            _conversations[session_id] = _conversations[session_id][-6:]
        if len(_conversations) > 200:
            oldest_key = next(iter(_conversations))
            del _conversations[oldest_key]

        return reply

    except Exception as e:
        print(f"[Tazuna88] Gemini API error: {e}")
        if '429' in str(e) or 'rate' in str(e).lower():
            _gemini_available = False
            print("[Tazuna88] Rate limit reached - switching to fallback mode.")
        import traceback
        traceback.print_exc()
        # Fall back to rule-based response, using is_game flag for better messages
        return _fallback_response(message, is_game_q)
    