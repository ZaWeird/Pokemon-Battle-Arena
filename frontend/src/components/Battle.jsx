// frontend/src/components/Battle.jsx
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import io from 'socket.io-client'
import toast from 'react-hot-toast'
import axios from 'axios'

function Battle({ user, setUser }) {
  const { roomId } = useParams()
  const navigate = useNavigate()
  const [socket, setSocket] = useState(null)
  const [showQuitConfirm, setShowQuitConfirm] = useState(false)
  const [showResult, setShowResult] = useState(false)
  const [battleResult, setBattleResult] = useState({
    result: '',
    resultText: '',
    coinsGained: 0,
    xpGained: 0,
    items: []
  })
  const [battle, setBattle] = useState({
    player: { 
      hp: [], 
      max_hp: [],
      pokemon: [] 
    },
    opponent: { 
      hp: [], 
      max_hp: [],
      pokemon: [] 
    },
    currentPokemon: 0,
    opponentCurrentPokemon: 0,
    turn: null,
    battleLog: []
  })
  const [loading, setLoading] = useState(true)

  // Function to refresh user data from backend
  const refreshUserData = async () => {
    try {
      const response = await axios.get('/api/profile', {
        headers: { Authorization: localStorage.getItem('token') }
      })
      if (setUser) {
        setUser(response.data)
        // Update localStorage
        localStorage.setItem('user', JSON.stringify(response.data))
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error)
    }
  }

  useEffect(() => {
    console.log('Setting up PvE battle connection for room:', roomId)
    
    const newSocket = io('http://localhost:5000')
    setSocket(newSocket)

    newSocket.emit('join_battle', {
        user_id: user.id,
        room: roomId
    })

    newSocket.on('battle_started', (data) => {
        console.log('Battle started data:', data)
        
        const playerPokemon = data.player_pokemon || []
        const opponentPokemon = data.opponent_pokemon || []
        
        setBattle({
            player: {
                pokemon: playerPokemon,
                hp: playerPokemon.map(p => p.hp),
                max_hp: playerPokemon.map(p => p.max_hp || p.hp)
            },
            opponent: {
                pokemon: opponentPokemon,
                hp: opponentPokemon.map(p => p.hp),
                max_hp: opponentPokemon.map(p => p.max_hp || p.hp)
            },
            currentPokemon: 0,
            opponentCurrentPokemon: 0,
            turn: data.turn || user.id,
            battleLog: ['Battle started!']
        })
        
        setLoading(false)
        toast.success('Battle started!')
    })

    newSocket.on('battle_update', (data) => {
        setBattle(prev => {
            const newBattle = { ...prev }
            
            data.hp_updates.forEach(update => {
                if (update.player === user.id) {
                    newBattle.player.hp = update.hp
                    newBattle.player.max_hp = update.max_hp
                } else if (update.player === 'ai') {
                    newBattle.opponent.hp = update.hp
                    newBattle.opponent.max_hp = update.max_hp
                }
            })
            
            if (data.current_pokemon) {
                if (data.current_pokemon[user.id] !== undefined) {
                    newBattle.currentPokemon = data.current_pokemon[user.id]
                }
                if (data.current_pokemon.ai !== undefined) {
                    newBattle.opponentCurrentPokemon = data.current_pokemon.ai
                }
            }
            
            newBattle.turn = data.next_turn
            newBattle.battleLog = [...newBattle.battleLog, data.log]
            
            return newBattle
        })
    })

    newSocket.on('battle_ended', async (data) => {
        const isWinner = data.winner === user.id
        
        let coinsGained = 0
        let xpGained = 0
        let resultText = ''
        
        if (isWinner) {
            coinsGained = 50
            xpGained = 20
            resultText = 'Victory!'
            toast.success('Victory! You won the battle!')
        } else {
            coinsGained = 20
            xpGained = 10
            resultText = 'Defeat!'
            toast.error('Defeat! Better luck next time!')
        }
        
        // Refresh user data from backend to get updated coins
        await refreshUserData()
        
        setBattleResult({
            result: isWinner ? 'win' : 'lose',
            resultText: resultText,
            coinsGained: coinsGained,
            xpGained: xpGained,
            items: []
        })
        
        setBattle(prev => ({
            ...prev,
            battleLog: [...prev.battleLog, ...(data.log || [])]
        }))
        
        setShowResult(true)
    })

    newSocket.on('error', (data) => {
        toast.error(data.message)
        console.error('Socket error:', data)
    })

    return () => {
        console.log('Cleaning up battle connection')
        if (newSocket) {
            newSocket.disconnect()
        }
    }
  }, [roomId, user.id, navigate, setUser])

  const handleAttack = () => {
    if (socket && battle.turn === user.id) {
      socket.emit('battle_action', {
        room: roomId,
        user_id: user.id,
        action: 'attack'
      })
    } else {
      toast.error("It's not your turn!")
    }
  }

  const handleSwitch = (pokemonIndex) => {
    if (socket && battle.turn === user.id) {
      if (battle.player.hp[pokemonIndex] > 0) {
        socket.emit('battle_action', {
          room: roomId,
          user_id: user.id,
          action: 'switch',
          pokemon_index: pokemonIndex
        })
      } else {
        toast.error("This Pokemon has fainted and cannot be switched in!")
      }
    } else {
      toast.error("It's not your turn!")
    }
  }

  const handleQuit = async () => {
    if (socket) {
      socket.disconnect()
    }
    // Refresh user data when quitting
    await refreshUserData()
    navigate('/lobby')
    toast.success('Left battle')
  }

  const closeResultModal = async () => {
    // Refresh user data before leaving
    await refreshUserData()
    setShowResult(false)
    navigate('/lobby')
  }

  const currentPlayerPokemon = battle.player.pokemon && battle.player.pokemon.length > 0 
    ? battle.player.pokemon[battle.currentPokemon] 
    : null
    
  const currentOpponentPokemon = battle.opponent.pokemon && battle.opponent.pokemon.length > 0 
    ? battle.opponent.pokemon[battle.opponentCurrentPokemon] 
    : null

  const playerHpPercent = currentPlayerPokemon && battle.player.hp[battle.currentPokemon] !== undefined
    ? (battle.player.hp[battle.currentPokemon] / (battle.player.max_hp[battle.currentPokemon] || currentPlayerPokemon.hp)) * 100
    : 0

  const opponentHpPercent = currentOpponentPokemon && battle.opponent.hp[battle.opponentCurrentPokemon] !== undefined
    ? (battle.opponent.hp[battle.opponentCurrentPokemon] / (battle.opponent.max_hp[battle.opponentCurrentPokemon] || currentOpponentPokemon.hp)) * 100
    : 0

  if (loading) {
    return (
      <div className="battle-arena loading-screen">
        <div className="loading-content">
          <h2>Loading Battle...</h2>
          <p>Preparing your Pokemon for battle!</p>
          <div className="loading-spinner"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="battle-arena">
      {/* Quit Button */}
      <button 
        className="quit-button"
        onClick={() => setShowQuitConfirm(true)}
      >
        Quit Battle
      </button>

      {/* Confirm Quit Modal */}
      {showQuitConfirm && (
        <div className="modal-overlay">
          <div className="modal-content confirm-modal">
            <h3>Confirm Quit</h3>
            <p>Are you sure you want to quit this battle?</p>
            <p>You will not receive any rewards!</p>
            <div className="modal-buttons">
              <button 
                className="btn-confirm"
                onClick={handleQuit}
              >
                Yes, Quit
              </button>
              <button 
                className="btn-cancel"
                onClick={() => setShowQuitConfirm(false)}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Battle Result Modal */}
      {showResult && (
        <div className="modal-overlay">
          <div className="modal-content result-modal">
            <h2 className={`result-title ${battleResult.result}`}>
              {battleResult.resultText}
            </h2>
            <div className="result-details">
              <div className="result-item">
                <span className="result-label">Coins Gained:</span>
                <span className="result-value">+{battleResult.coinsGained}</span>
              </div>
              <div className="result-item">
                <span className="result-label">Experience Gained:</span>
                <span className="result-value">+{battleResult.xpGained} XP</span>
              </div>
              {battleResult.items.length > 0 && (
                <div className="result-item">
                  <span className="result-label">Items Gained:</span>
                  <span className="result-value">{battleResult.items.join(', ')}</span>
                </div>
              )}
            </div>
            <button 
              className="btn-continue"
              onClick={closeResultModal}
            >
              Continue
            </button>
          </div>
        </div>
      )}

      <div className="battle-field">
        <div className="battle-player">
          <h3>{user.username}</h3>
          {currentPlayerPokemon ? (
            <div className="pokemon-battle-card">
              <img 
                src={currentPlayerPokemon.image_url || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'} 
                alt={currentPlayerPokemon.name || 'Pokemon'}
                onError={(e) => {
                  e.target.onerror = null
                  e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'
                }}
              />
              <h4>{currentPlayerPokemon.name || 'Unknown'}</h4>
              <div className="hp-bar">
                <div 
                  className="hp-fill" 
                  style={{ width: `${Math.max(0, playerHpPercent)}%` }}
                />
              </div>
              <p>
                HP: {battle.player.hp[battle.currentPokemon] || 0}/
                {battle.player.max_hp[battle.currentPokemon] || currentPlayerPokemon.hp || 0}
              </p>
              <p>Level: {currentPlayerPokemon.level || 1}</p>
            </div>
          ) : (
            <div className="pokemon-battle-card">
              <p>No Pokemon available</p>
            </div>
          )}
          
          <div className="player-team-list">
            <h4>Your Team:</h4>
            <div className="team-mini-list">
              {battle.player.pokemon.map((pokemon, index) => (
                <div 
                  key={index} 
                  className={`team-mini-item ${index === battle.currentPokemon ? 'active' : ''} ${battle.player.hp[index] <= 0 ? 'fainted' : ''}`}
                  onClick={() => handleSwitch(index)}
                >
                  <img src={pokemon.image_url} alt={pokemon.name} />
                  <span>{pokemon.name}</span>
                  <span className="mini-hp">HP: {battle.player.hp[index]}/{pokemon.hp}</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="battle-vs">
          <h2>VS</h2>
          {battle.turn === user.id ? (
            <p className="your-turn">Your Turn!</p>
          ) : battle.turn === 'ai' ? (
            <p className="opponent-turn">AI Thinking...</p>
          ) : (
            <p className="opponent-turn">Waiting...</p>
          )}
        </div>

        <div className="battle-opponent">
          <h3>AI Opponent</h3>
          {currentOpponentPokemon ? (
            <div className="pokemon-battle-card">
              <img 
                src={currentOpponentPokemon.image_url || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'} 
                alt={currentOpponentPokemon.name || 'Pokemon'}
                onError={(e) => {
                  e.target.onerror = null
                  e.target.src = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/25.png'
                }}
              />
              <h4>{currentOpponentPokemon.name || 'Unknown'}</h4>
              <div className="hp-bar">
                <div 
                  className="hp-fill" 
                  style={{ width: `${Math.max(0, opponentHpPercent)}%` }}
                />
              </div>
              <p>
                HP: {battle.opponent.hp[battle.opponentCurrentPokemon] || 0}/
                {battle.opponent.max_hp[battle.opponentCurrentPokemon] || currentOpponentPokemon.hp || 0}
              </p>
            </div>
          ) : (
            <div className="pokemon-battle-card">
              <p>Loading Opponent...</p>
            </div>
          )}
          
          <div className="opponent-team-list">
            <h4>Opponent's Team:</h4>
            <div className="team-mini-list">
              {battle.opponent.pokemon.map((pokemon, index) => (
                <div 
                  key={index} 
                  className={`team-mini-item ${index === battle.opponentCurrentPokemon ? 'active' : ''} ${battle.opponent.hp[index] <= 0 ? 'fainted' : ''}`}
                >
                  <img src={pokemon.image_url} alt={pokemon.name} />
                  <span>{pokemon.name}</span>
                  <span className="mini-hp">HP: {battle.opponent.hp[index]}/{pokemon.hp}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="battle-log">
        <h4>Battle Log</h4>
        <div className="log-messages">
          {battle.battleLog.map((log, index) => (
            <p key={index}>{log}</p>
          ))}
        </div>
      </div>

      <div className="battle-actions">
        <button 
          className="btn-attack" 
          onClick={handleAttack}
          disabled={battle.turn !== user.id || !currentPlayerPokemon || battle.player.hp[battle.currentPokemon] <= 0}
        >
          Attack
        </button>
      </div>
    </div>
  )
}

export default Battle