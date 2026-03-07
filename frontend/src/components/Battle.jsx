// frontend/src/components/Battle.jsx
import React, { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import io from 'socket.io-client'
import toast from 'react-hot-toast'

function Battle({ user }) {
  const { roomId } = useParams()
  const navigate = useNavigate()
  const [socket, setSocket] = useState(null)
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
  const [chatMessage, setChatMessage] = useState('')
  const [messages, setMessages] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    console.log('Setting up battle connection for room:', roomId)
    console.log('User:', user)
    
    const newSocket = io('http://localhost:5000')
    setSocket(newSocket)

    // Join the battle room
    newSocket.emit('join_battle', {
        user_id: user.id,
        room: roomId
    })

    // Battle started event
    newSocket.on('battle_started', (data) => {
        console.log('Battle started data:', data)
        
        // Set player's own Pokemon (from the server)
        const playerPokemon = data.player_pokemon || []
        const opponentPokemon = data.opponent_pokemon || []
        
        console.log('Player Pokemon:', playerPokemon)
        console.log('Opponent Pokemon:', opponentPokemon)
        
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

    // Waiting for opponent (PvP)
    newSocket.on('waiting_for_opponent', (data) => {
        setLoading(false)
        toast('Waiting for opponent...', { icon: '⏳' })
    })

    // Player joined (PvP)
    newSocket.on('player_joined', (data) => {
        toast.success('Opponent found!')
    })

    // Battle update (turn progress)
    newSocket.on('battle_update', (data) => {
        console.log('Battle update:', data)
        setBattle(prev => {
            const newBattle = { ...prev }
            
            // Update HP for both players
            data.hp_updates.forEach(update => {
                if (update.player === user.id) {
                    newBattle.player.hp = update.hp
                    newBattle.player.max_hp = update.max_hp
                } else if (update.player === 'ai') {
                    newBattle.opponent.hp = update.hp
                    newBattle.opponent.max_hp = update.max_hp
                }
            })
            
            // Update current Pokemon indices if provided
            if (data.current_pokemon) {
                if (data.current_pokemon[user.id] !== undefined) {
                    newBattle.currentPokemon = data.current_pokemon[user.id]
                }
                if (data.current_pokemon.ai !== undefined) {
                    newBattle.opponentCurrentPokemon = data.current_pokemon.ai
                }
            }
            
            // Add to battle log
            newBattle.turn = data.next_turn
            newBattle.battleLog = [...newBattle.battleLog, data.log]
            
            return newBattle
        })
    })

    // Battle ended
    newSocket.on('battle_ended', (data) => {
        console.log('Battle ended:', data)
        const isWinner = data.winner === user.id || data.winner === 'user'
        
        if (isWinner) {
            toast.success('You won!')
        } else {
            toast.error('You lost!')
        }
        
        setBattle(prev => ({
            ...prev,
            battleLog: [...prev.battleLog, ...(data.log || [])]
        }))
        
        // Return to lobby after 5 seconds
        setTimeout(() => {
            navigate('/lobby')
        }, 5000)
    })

    // Chat message
    newSocket.on('chat_message', (data) => {
        setMessages(prev => [...prev, data])
    })

    // Player left
    newSocket.on('player_left', (data) => {
        toast.error('Opponent left the battle')
        setTimeout(() => {
            navigate('/lobby')
        }, 3000)
    })

    // Error event
    newSocket.on('error', (data) => {
        toast.error(data.message)
        console.error('Socket error:', data)
    })

    // Cleanup on unmount
    return () => {
        console.log('Cleaning up battle connection')
        if (newSocket) {
            newSocket.emit('leave_battle', {
                user_id: user.id,
                room: roomId
            })
            newSocket.disconnect()
        }
    }
  }, [roomId, user.id, navigate])

  const handleAttack = () => {
    if (socket && battle.turn === user.id) {
      console.log('Attacking...')
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
        console.log('Switching to pokemon:', pokemonIndex)
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

  const sendMessage = (e) => {
    e.preventDefault()
    if (chatMessage.trim() && socket) {
      socket.emit('battle_chat', {
        room: roomId,
        message: chatMessage,
        username: user.username
      })
      setChatMessage('')
    }
  }

  // Get current Pokemon for player and opponent
  const currentPlayerPokemon = battle.player.pokemon && battle.player.pokemon.length > 0 
    ? battle.player.pokemon[battle.currentPokemon] 
    : null
    
  const currentOpponentPokemon = battle.opponent.pokemon && battle.opponent.pokemon.length > 0 
    ? battle.opponent.pokemon[battle.opponentCurrentPokemon] 
    : null

  // Calculate HP percentages
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
          
          {/* Show player's Pokemon team */}
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
            <p className="opponent-turn">Opponent's Turn</p>
          )}
        </div>

        <div className="battle-opponent">
          <h3>{roomId.startsWith('pve_') ? 'AI' : 'Opponent'}</h3>
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
          
          {/* Show opponent's Pokemon team */}
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

      {/* Chat section for PvP battles */}
      {!roomId.startsWith('pve_') && (
        <div className="battle-chat">
          <h4>Battle Chat</h4>
          <div className="chat-messages">
            {messages.map((msg, index) => (
              <div key={index} className="chat-message">
                <strong>{msg.username}:</strong> {msg.message}
              </div>
            ))}
          </div>
          
          <form onSubmit={sendMessage} className="chat-input">
            <input
              type="text"
              value={chatMessage}
              onChange={(e) => setChatMessage(e.target.value)}
              placeholder="Type a message..."
              maxLength={100}
            />
            <button type="submit">Send</button>
          </form>
        </div>
      )}
    </div>
  )
}

export default Battle