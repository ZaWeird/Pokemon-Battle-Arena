import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'
import { startPvEBattle } from '../services/api';

function Lobby({ user, setUser }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)
  const [showStageModal, setShowStageModal] = useState(false);

  const stages = [
    { name: 'Tiny Path', level: 5 },
    { name: 'Grass Challenge', level: 10 },
    { name: 'Stone Badge', level: 20 },
    { name: 'Heat Badge', level: 30 },
    { name: 'Balance Badge', level: 40 },
    { name: 'Rainbow Badge', level: 50 },
    { name: 'Soul Badge', level: 60 },
    { name: 'Marsh Badge', level: 70 },
    { name: 'Volcan Badge', level: 80 },
    { name: 'Earth Badge', level: 90 },
  ]

  useEffect(() => {
    refreshUserData()
  }, [])

  const refreshUserData = async () => {
    try {
      const response = await axios.get('/api/profile', {
        headers: { Authorization: localStorage.getItem('token') }
      })
      if (setUser) {
        setUser(response.data)
        localStorage.setItem('user', JSON.stringify(response.data))
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error)
    }
  }

  const handlePvE = async (level) => {
    setLoading(true)
    try {
      toast.loading('Starting PvE battle...')
      const response = await axios.post('/api/battle/pve',
        { level },
        { headers: { Authorization: localStorage.getItem('token') } }
      )
      toast.dismiss()
      navigate(`/battle/${response.data.roomId}`)
    } catch (error) {
      toast.dismiss()
      toast.error('Failed to start battle')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="lobby">
      <div className="card">
        <h2 className="card-title">Pokemon Battle Arena</h2>

        <div className="player-info">
          <h3>Welcome, Trainer {user.username}!</h3>
          <p>Rank: {user.rank}</p>
          <p>Wins: {user.wins} | Losses: {user.losses}</p>
          <p>Coins: {user.coins}</p>
          <p>Pokemon: {user.pokemon_count || 0}</p>
        </div>

        <div className="battle-options">
          <div className="battle-option">
            <h3>Player vs AI</h3>
            <p>Battle against AI opponents to earn coins and experience!</p>
            <ul>
              <li>Gain more coins on winning, so try your best!</li>
              <li>Higher level stages give better rewards, but are tougher!</li>
              <li>Always gain experience for your pokemon!</li>
            </ul>
            <button className="btn-primary" onClick={() => setShowStageModal(true)} disabled={loading}>
              {loading ? 'Starting Battle...' : 'Start PvE Battle'}
            </button>
          </div>
        </div>
      </div>
      {showStageModal && (
        <div className="modal-overlay" onClick={() => setShowStageModal(false)}>
          <div className="stage-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Choose a Stage</h3>
            <div className="stage-grid">
              {stages.map((stage, idx) => (
                <div
                  key={idx}
                  className="stage-card pixel-box"
                  onClick={() => {
                    setShowStageModal(false);
                    handlePvE(stage.level);
                  }}
                >
                  <img
                    src={stage.image || 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/poke-ball.png'}
                    alt={stage.name}
                    className="stage-image"
                  />
                  <div className="stage-info">
                    <span className="stage-number">Stage {idx + 1}</span>
                    <span className="stage-name">{stage.name}</span>
                    <span className="stage-level">Lv.{stage.level}</span>
                  </div>
                </div>
              ))}
            </div>
            <button className="pixel-btn cancel-loading-btn" onClick={() => setShowStageModal(false)}>
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default Lobby