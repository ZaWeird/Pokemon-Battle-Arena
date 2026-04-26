// frontend/src/components/Battle.jsx
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import io from 'socket.io-client';
import toast from 'react-hot-toast';
import axios from 'axios';

// Type icon mapping (from the GitHub repo)
const TYPE_ICON_BASE = 'https://raw.githubusercontent.com/partywhale/pokemon-type-icons/main/icons';
const TYPE_ICONS = {
  normal: `${TYPE_ICON_BASE}/normal.svg`,
  fire: `${TYPE_ICON_BASE}/fire.svg`,
  water: `${TYPE_ICON_BASE}/water.svg`,
  electric: `${TYPE_ICON_BASE}/electric.svg`,
  grass: `${TYPE_ICON_BASE}/grass.svg`,
  ice: `${TYPE_ICON_BASE}/ice.svg`,
  fighting: `${TYPE_ICON_BASE}/fighting.svg`,
  poison: `${TYPE_ICON_BASE}/poison.svg`,
  ground: `${TYPE_ICON_BASE}/ground.svg`,
  flying: `${TYPE_ICON_BASE}/flying.svg`,
  psychic: `${TYPE_ICON_BASE}/psychic.svg`,
  bug: `${TYPE_ICON_BASE}/bug.svg`,
  rock: `${TYPE_ICON_BASE}/rock.svg`,
  ghost: `${TYPE_ICON_BASE}/ghost.svg`,
  dragon: `${TYPE_ICON_BASE}/dragon.svg`,
  dark: `${TYPE_ICON_BASE}/dark.svg`,
  steel: `${TYPE_ICON_BASE}/steel.svg`,
  fairy: `${TYPE_ICON_BASE}/fairy.svg`,
};

function Battle({ user, setUser }) {
  const { roomId } = useParams();
  const navigate = useNavigate();
  const [socket, setSocket] = useState(null);
  const [showQuitConfirm, setShowQuitConfirm] = useState(false);
  const [showResult, setShowResult] = useState(false);
  const [selectedMoveIndex, setSelectedMoveIndex] = useState(null);
  const [showMoveInfo, setShowMoveInfo] = useState(false);
  const [battleResult, setBattleResult] = useState({
    result: '', resultText: '', coinsGained: 0, xpGained: 0, items: []
  });
  const [battle, setBattle] = useState({
    player: { hp: [], max_hp: [], pokemon: [], exp: [] },
    opponent: { hp: [], max_hp: [], pokemon: [] },
    currentPokemon: 0,
    opponentCurrentPokemon: 0,
    turn: null,
    battleLog: [],
    playerMoves: []
  });
  const [loading, setLoading] = useState(true);
  const [animating, setAnimating] = useState(false);
  const [playerDamage, setPlayerDamage] = useState(null);
  const [opponentDamage, setOpponentDamage] = useState(null);
  const [battlePhase, setBattlePhase] = useState('command');

  useEffect(() => {
    if (battle.turn === user.id) {
      setBattlePhase('command');
    }
  }, [battle.turn, user.id]);
  const getHpBarColor = (percentage) => {
    if (percentage > 50) return '#10b981';
    if (percentage > 20) return '#f59e0b';
    return '#ef4444';
  };

  const getStatusIcon = (status) => {
    if (!status) return null;
    const icons = {
      'paralysis': '⚡', 'sleep': '💤', 'freeze': '❄️',
      'burn': '🔥', 'poison': '☠️', 'flinch': '😵'
    };
    return icons[status] || '⚠️';
  };

  const getStatusText = (status) => {
    if (!status) return '';
    const texts = {
      'paralysis': 'PAR', 'sleep': 'SLP', 'freeze': 'FRZ',
      'burn': 'BRN', 'poison': 'PSN', 'flinch': 'FLN'
    };
    return texts[status] || status;
  };

  const renderTypeIconsWithText = (typeString) => {
    if (!typeString) return null;
    const types = typeString.split(',');
    return (
      <div className="battle-type-group">
        {types.map(t => {
          const type = t.trim();
          const iconUrl = TYPE_ICONS[type];
          if (!iconUrl) return null;
          return (
            <div key={type} className="battle-type-item">
              <img src={iconUrl} alt={type} className="battle-type-icon" />
              <span className="battle-type-name">{type}</span>
            </div>
          );
        })}
      </div>
    );
  };

  const refreshUserData = async () => {
    try {
      const response = await axios.get('/api/profile', {
        headers: { Authorization: localStorage.getItem('token') }
      });
      if (setUser) {
        setUser(response.data);
        localStorage.setItem('user', JSON.stringify(response.data));
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  };

  const showDamageNumber = (damage, isPlayer) => {
    if (isPlayer) {
      setPlayerDamage(damage);
      setTimeout(() => setPlayerDamage(null), 3000);
    } else {
      setOpponentDamage(damage);
      setTimeout(() => setOpponentDamage(null), 3000);
    }
  };

  useEffect(() => {
    console.log('Battle component mounted for room:', roomId);
    const newSocket = io('http://localhost:5000', { transports: ['websocket', 'polling'] });

    newSocket.on('connect', () => {
      console.log('Socket connected!');
      newSocket.emit('join_battle', { user_id: user.id, room: roomId });
    });

    newSocket.on('battle_started', (data) => {
      console.log('Battle started data:', data);
      const playerPokemon = data.player_pokemon || [];
      const opponentPokemon = data.opponent_pokemon || [];
      const firstPokemon = playerPokemon[0];
      const playerMoves = firstPokemon?.moves || [
        { name: 'Tackle', power: 40, type: 'normal', accuracy: 100, pp: 35, damage_class: 'physical' }
      ];

      setBattle({
        player: {
          pokemon: playerPokemon,
          hp: playerPokemon.map(p => p.hp),
          max_hp: playerPokemon.map(p => p.max_hp || p.hp),
          exp: playerPokemon.map(p => p.current_exp || 0)
        },
        opponent: {
          pokemon: opponentPokemon,
          hp: opponentPokemon.map(p => p.hp),
          max_hp: opponentPokemon.map(p => p.max_hp || p.hp)
        },
        currentPokemon: 0,
        opponentCurrentPokemon: 0,
        turn: data.turn || user.id,
        battleLog: ['Battle started!'],
        playerMoves: playerMoves
      });
      setLoading(false);
      toast.success('Battle started!');
    });

    newSocket.on('battle_update', (data) => {
      setBattle(prev => {
        const newBattle = { ...prev };
        data.hp_updates.forEach(update => {
          if (update.player === user.id) {
            const oldHp = newBattle.player.hp[newBattle.currentPokemon];
            newBattle.player.hp = update.hp;
            newBattle.player.max_hp = update.max_hp;
            if (oldHp && update.hp[newBattle.currentPokemon] < oldHp) {
              showDamageNumber(oldHp - update.hp[newBattle.currentPokemon], true);
            }
          } else if (update.player === 'ai') {
            const oldHp = newBattle.opponent.hp[newBattle.opponentCurrentPokemon];
            newBattle.opponent.hp = update.hp;
            newBattle.opponent.max_hp = update.max_hp;
            if (oldHp && update.hp[newBattle.opponentCurrentPokemon] < oldHp) {
              showDamageNumber(oldHp - update.hp[newBattle.opponentCurrentPokemon], false);
            }
          }
        });

        if (data.current_pokemon) {
          if (data.current_pokemon[user.id] !== undefined) {
            const newIndex = data.current_pokemon[user.id];
            newBattle.currentPokemon = newIndex;
            const switchedPokemon = newBattle.player.pokemon[newIndex];
            if (switchedPokemon && switchedPokemon.moves) {
              newBattle.playerMoves = switchedPokemon.moves;
            }
          }
          if (data.current_pokemon.ai !== undefined) {
            newBattle.opponentCurrentPokemon = data.current_pokemon.ai;
          }
        }

        newBattle.turn = data.next_turn;
        newBattle.battleLog = [...newBattle.battleLog, data.log];
        setAnimating(true);
        setTimeout(() => setAnimating(false), 300);
        return newBattle;
      });
    });

    newSocket.on('battle_ended', async (data) => {
      const isWinner = data.winner === user.id;
      const coinsGained = data.coins_gained || (isWinner ? 50 : 20);
      const xpGained = data.exp_gained || (isWinner ? 20 : 10);
      const resultText = isWinner ? 'Victory!' : 'Defeat!';
      if (isWinner) toast.success('Victory! You won the battle!');
      else toast.error('Defeat! Better luck next time!');
      await refreshUserData();
      setBattleResult({ result: isWinner ? 'win' : 'lose', resultText, coinsGained, xpGained, items: [] });
      setBattle(prev => ({ ...prev, battleLog: [...prev.battleLog, ...(data.log || [])] }));
      setShowResult(true);
    });

    newSocket.on('error', (data) => {
      console.error('Socket error:', data);
      toast.error(data.message);
    });

    newSocket.on('connect_error', (err) => {
      console.error('Connection error:', err);
      toast.error('Failed to connect to battle server');
    });

    setSocket(newSocket);
    return () => { if (newSocket) newSocket.disconnect(); };
  }, [roomId, user.id]);

  const handleMoveSelect = (move, index) => {
    if (socket && battle.turn === user.id) {
      setSelectedMoveIndex(index);
      setShowMoveInfo(true);
    }
  };

  const confirmMove = () => {
    if (selectedMoveIndex !== null && socket) {
      setAnimating(true);
      socket.emit('battle_action', {
        room: roomId,
        user_id: user.id,
        action: 'attack',
        move_index: selectedMoveIndex
      });
      setTimeout(() => {
        setAnimating(false);
        setSelectedMoveIndex(null);
        setShowMoveInfo(false);
      }, 500);
    }
  };

  const cancelMove = () => {
    setSelectedMoveIndex(null);
    setShowMoveInfo(false);
  };

  const handleSwitch = (pokemonIndex) => {
    if (socket && battle.turn === user.id) {
      if (battle.player.hp[pokemonIndex] > 0) {
        socket.emit('battle_action', {
          room: roomId,
          user_id: user.id,
          action: 'switch',
          pokemon_index: pokemonIndex
        });
      } else {
        toast.error("This Pokemon has fainted and cannot be switched in!");
      }
    } else {
      toast.error("It's not your turn!");
    }
  };

  const handleQuit = async () => {
    if (socket) socket.disconnect();
    await refreshUserData();
    navigate('/lobby');
    toast.success('Left battle');
  };

  const closeResultModal = async () => {
    await refreshUserData();
    setShowResult(false);
    navigate('/lobby');
  };

  const currentPlayerPokemon = battle.player.pokemon?.[battle.currentPokemon] || null;
  const currentOpponentPokemon = battle.opponent.pokemon?.[battle.opponentCurrentPokemon] || null;

  const playerHpPercent = currentPlayerPokemon && battle.player.hp[battle.currentPokemon] !== undefined
    ? (battle.player.hp[battle.currentPokemon] / (battle.player.max_hp[battle.currentPokemon] || currentPlayerPokemon.hp)) * 100 : 0;

  const opponentHpPercent = currentOpponentPokemon && battle.opponent.hp[battle.opponentCurrentPokemon] !== undefined
    ? (battle.opponent.hp[battle.opponentCurrentPokemon] / (battle.opponent.max_hp[battle.opponentCurrentPokemon] || currentOpponentPokemon.hp)) * 100 : 0;

  if (loading) {
    return (
      <div className="battle-arena loading-screen">
        <div className="loading-content">
          <h2>Loading Battle...</h2>
          <div className="loading-spinner"></div>
          <button className="pixel-btn cancel-loading-btn" onClick={() => navigate('/lobby')}>Cancel</button>
        </div>
      </div>
    );
  }

  return (
    <div className="battle-arena">
      {showQuitConfirm && (
        <div className="modal-overlay">
          <div className="modal-content confirm-modal">
            <h3>Confirm Quit</h3>
            <p>Are you sure you want to quit this battle?</p>
            <p>You will not receive any rewards!</p>
            <div className="modal-buttons">
              <button className="btn-confirm" onClick={handleQuit}>Yes, Quit</button>
              <button className="btn-cancel" onClick={() => setShowQuitConfirm(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {showResult && (
        <div className="modal-overlay">
          <div className="modal-content result-modal">
            <h2 className={`result-title ${battleResult.result}`}>{battleResult.resultText}</h2>
            <div className="result-details">
              <div className="result-item"><span className="result-label">Coins Gained:</span><span className="result-value">+{battleResult.coinsGained}</span></div>
              <div className="result-item"><span className="result-label">Experience Gained:</span><span className="result-value">+{battleResult.xpGained} XP</span></div>
            </div>
            <button className="btn-continue" onClick={closeResultModal}>Continue</button>
          </div>
        </div>
      )}

      {showMoveInfo && battle.playerMoves[selectedMoveIndex] && (
        <div className="modal-overlay" onClick={cancelMove}>
          <div className="move-info-modal" onClick={(e) => e.stopPropagation()}>
            <h3>{battle.playerMoves[selectedMoveIndex].name}</h3>
            <div className="move-stats">
              <p>Type: {battle.playerMoves[selectedMoveIndex].type}</p>
              <p>Power: {battle.playerMoves[selectedMoveIndex].power || '—'}</p>
              <p>Accuracy: {battle.playerMoves[selectedMoveIndex].accuracy}%</p>
              <p>PP: {battle.playerMoves[selectedMoveIndex].pp}</p>
            </div>
            <div className="modal-buttons">
              <button className="confirm-btn" onClick={confirmMove}>Use Move</button>
              <button className="cancel-btn" onClick={cancelMove}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {/* RSE-style battle field layout */}
      <div className="battle-field-rse">
        {/* Opponent side */}
        <div className="battle-opponent-rse">
          <div className="opponent-row">
            {/* Left: Info box */}
            <div className="opponent-info-box pixel-box">
              {currentOpponentPokemon ? (
                <>
                  <div className="name-row">
                    <span className="pokemon-name">{currentOpponentPokemon.name}</span>
                    <span className="pokemon-level">Lv.{currentOpponentPokemon.level || 50}</span>
                    {currentOpponentPokemon.status && (
                      <span className="status-icon" title={currentOpponentPokemon.status}>
                        {getStatusIcon(currentOpponentPokemon.status)}
                        <span className="status-text">{getStatusText(currentOpponentPokemon.status)}</span>
                      </span>
                    )}
                  </div>
                  {renderTypeIconsWithText(currentOpponentPokemon.type)}
                  <div className="hp-bar-container">
                    <div className="hp-bar">
                      <div className="hp-fill" style={{ width: `${Math.max(0, opponentHpPercent)}%`, backgroundColor: getHpBarColor(opponentHpPercent) }} />
                    </div>
                    <div className="hp-numbers">{battle.opponent.hp[battle.opponentCurrentPokemon] || 0} / {battle.opponent.max_hp[battle.opponentCurrentPokemon] || currentOpponentPokemon.hp || 0}</div>
                  </div>
                  <div className="speed-display">Speed: {currentOpponentPokemon.speed || 0}</div>
                </>
              ) : <p>Loading Opponent...</p>}
            </div>

            {/* Right: Team list and sprite stacked */}
            <div className="opponent-right-group">
              <div className="opponent-team-list pixel-box">
                <p>Opponent Pokemon's Team:</p>
                <div className="team-mini-list">
                  {battle.opponent.pokemon.map((p, idx) => (
                    <div key={idx} className={`team-mini-item ${idx === battle.opponentCurrentPokemon ? 'active' : ''} ${battle.opponent.hp[idx] <= 0 ? 'fainted' : ''}`}>
                      <img src={p.image_url} alt={p.name} />
                      <div className="mini-hp-bar">
                        <div
                          className="mini-hp-fill"
                          style={{
                            width: `${(battle.opponent.hp[idx] / p.hp) * 100}%`,
                            backgroundColor: getHpBarColor((battle.opponent.hp[idx] / p.hp) * 100)
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              <div className="opponent-sprite-container">
                {currentOpponentPokemon ? (
                  <>
                    <img src={currentOpponentPokemon.image_url || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'} alt={currentOpponentPokemon.name} className={animating ? 'shake' : ''} />
                    {opponentDamage !== null && (
                      <div className="damage-number">-{opponentDamage}</div>
                    )}
                  </>
                ) : <p>Loading...</p>}
              </div>
            </div>
          </div>
        </div>

        {/* VS and turn indicator */}
        <div className="battle-vs-rse">
          <h2>VS</h2>
          {battle.turn === user.id ? <p className="your-turn">Your Turn!</p> : <p className="opponent-turn">AI Thinking...</p>}
        </div>

        {/* Player side */}
        <div className="battle-player-rse">
          <div className="player-row">
            {/* Left: Sprite and team list stacked */}
            <div className="player-left-group">
              <div className="player-sprite-container">
                {currentPlayerPokemon ? (
                  <>
                    <img src={currentPlayerPokemon.image_url || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'} alt={currentPlayerPokemon.name} className={animating ? 'shake' : ''} />
                    {playerDamage !== null && (
                      <div className="damage-number">-{playerDamage}</div>
                    )}
                  </>
                ) : <p>No Pokemon</p>}
              </div>
              <div className="player-team-list pixel-box">
                <p>Your Team:</p>
                <div className="team-mini-list">
                  {battle.player.pokemon.map((p, idx) => (
                    <div key={idx} className={`team-mini-item ${idx === battle.currentPokemon ? 'active' : ''} ${battle.player.hp[idx] <= 0 ? 'fainted' : ''}`} onClick={() => handleSwitch(idx)}>
                      <img src={p.image_url} alt={p.name} />
                      <div className="mini-hp-bar">
                        <div
                          className="mini-hp-fill"
                          style={{
                            width: `${(battle.player.hp[idx] / p.hp) * 100}%`,
                            backgroundColor: getHpBarColor((battle.player.hp[idx] / p.hp) * 100)
                          }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Right: Info box */}
            <div className="player-info-box pixel-box">
              {currentPlayerPokemon ? (
                <>
                  <div className="name-row">
                    <span className="pokemon-name">{currentPlayerPokemon.name}</span>
                    <span className="pokemon-level">Lv.{currentPlayerPokemon.level || 1}</span>
                    {currentPlayerPokemon.status && (
                      <span className="status-icon" title={currentPlayerPokemon.status}>
                        {getStatusIcon(currentPlayerPokemon.status)}
                        <span className="status-text">{getStatusText(currentPlayerPokemon.status)}</span>
                      </span>
                    )}
                  </div>
                  {renderTypeIconsWithText(currentPlayerPokemon.type)}
                  <div className="hp-bar-container">
                    <div className="hp-bar">
                      <div className="hp-fill" style={{ width: `${Math.max(0, playerHpPercent)}%`, backgroundColor: getHpBarColor(playerHpPercent) }} />
                    </div>
                    <div className="hp-numbers">{battle.player.hp[battle.currentPokemon] || 0} / {battle.player.max_hp[battle.currentPokemon] || currentPlayerPokemon.hp || 0}</div>
                  </div>
                  <div className="speed-display">Speed: {currentPlayerPokemon.speed || 0}</div>
                </>
              ) : <p>No Pokemon available</p>}
            </div>
          </div>
        </div>
      </div>

      {/* Bottom Row: Battle Log and Action Panel */}
      <div className="battle-bottom-row">
        <div className="battle-log pixel-box">
          <h4>Battle Log</h4>
          <div className="log-messages">
            {battle.battleLog.map((log, idx) => <p key={idx}>{log}</p>)}
          </div>
        </div>

        {/* Player's turn actions */}
        {battle.turn === user.id && currentPlayerPokemon && battle.player.hp[battle.currentPokemon] > 0 && !showMoveInfo && (
          <>
            {battlePhase === 'command' ? (
              <div className="command-menu pixel-box">
                <button className="command-btn fight-btn" onClick={() => setBattlePhase('move')}>
                  Fight
                </button>
                <button className="command-btn quit-btn" onClick={() => setShowQuitConfirm(true)}>
                  Quit
                </button>
              </div>
            ) : (
              <div className="move-selection pixel-box">
                <button className="back-to-command-btn" onClick={() => setBattlePhase('command')}>
                  ← Back
                </button>
                <div className="moves-grid">
                  {battle.playerMoves.map((move, idx) => (
                    <button key={idx} className={`move-button move-type-${move.type}`} onClick={() => handleMoveSelect(move, idx)}>
                      <div className="move-name">{move.name}</div>
                      <div className="move-details">
                        <span className="move-type">{move.type}</span>
                        <span className="move-pp">PP: {move.pp}</span>
                        {move.power > 0 && <span className="move-power">Power: {move.power}</span>}
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </>
        )}

        {/* Opponent's turn */}
        {battle.turn !== user.id && currentPlayerPokemon && battle.player.hp[battle.currentPokemon] > 0 && (
          <div className="move-selection pixel-box turn-waiting">
            <div className="thinking-text">Opponent is thinking...</div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Battle;