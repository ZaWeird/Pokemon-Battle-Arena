// frontend/src/components/Lobby.jsx
import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'

function Lobby({ user }) {
  const navigate = useNavigate()
  const [findingMatch, setFindingMatch] = useState(false)

  const handlePvE = async () => {
    try {
      toast.loading('Starting PvE battle...')
      const response = await axios.post('/api/battle/pve', {}, {
        headers: { Authorization: localStorage.getItem('token') }
      })
      toast.dismiss()
      console.log('PvE response:', response.data)
      navigate(`/battle/${response.data.roomId}`)
    } catch (error) {
      toast.dismiss()
      console.error('PvE error:', error)
      toast.error(error.response?.data?.message || 'Failed to start PvE battle')
    }
  }

  const handlePvP = async () => {
    setFindingMatch(true)
    toast.loading('Looking for opponent...')
    
    try {
      const response = await axios.post('/api/battle/pvp/queue', {}, {
        headers: { Authorization: localStorage.getItem('token') }
      })
      
      toast.dismiss()
      console.log('PvP response:', response.data)
      navigate(`/battle/${response.data.roomId}`)
    } catch (error) {
      toast.dismiss()
      console.error('PvP error:', error)
      toast.error(error.response?.data?.message || 'Failed to join queue')
      setFindingMatch(false)
    }
  }

  return (
    <div className="lobby">
      <div className="card">
        <h2 className="card-title">Battle Lobby</h2>
        
        <div className="player-info">
          <h3>Welcome, {user.username}!</h3>
          <p>Rank: {user.rank}</p>
          <p>Rating: {user.rating}</p>
          <p>Wins: {user.wins} | Losses: {user.losses}</p>
          <p>Coins: {user.coins}</p>
        </div>

        <div className="battle-options">
          <div className="battle-option">
            <h3>Player vs AI</h3>
            <p>Battle against AI opponents to earn coins</p>
            <ul>
              <li>Win: 50 coins</li>
              <li>Lose: 20 coins</li>
            </ul>
            <button className="btn-primary" onClick={handlePvE}>
              Start PvE Battle
            </button>
          </div>

          <div className="battle-option">
            <h3>Player vs Player</h3>
            <p>Battle against other players in real-time</p>
            <ul>
              <li>Win: +100 coins, +25 rating</li>
              <li>Lose: +20 coins, -10 rating</li>
            </ul>
            <button 
              className="btn-primary" 
              onClick={handlePvP}
              disabled={findingMatch}
            >
              {findingMatch ? 'Finding Match...' : 'Find PvP Match'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Lobby