// frontend/src/components/Lobby.jsx
import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import toast from 'react-hot-toast'

function Lobby({ user, setUser }) {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(false)

  // Refresh user data when component mounts
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



  const handlePvE = async () => {
    setLoading(true)
    try {
      toast.loading('Starting PvE battle...')
      const response = await axios.post('/api/battle/pve', {}, {
        headers: { Authorization: localStorage.getItem('token') }
      })
      toast.dismiss()
      navigate(`/battle/${response.data.roomId}`)
    } catch (error) {
      toast.dismiss()
      toast.error('Failed to start battle')
    } finally {
      setLoading(false)
    }
  }
  const [fetching, setFetching] = useState(false)

  const handleFetchGen1 = async () => {
    setFetching(true)
    try {
      const response = await axios.post('/api/admin/fetch-gen1', {}, {
        headers: { Authorization: localStorage.getItem('token') }
      })
      toast.success(response.data.message)
    } catch (error) {
      toast.error('Failed to fetch Pokemon')
    } finally {
      setFetching(false)
    }
  }

  return (
    <div className="lobby">
      <div className="card">
        <h2 className="card-title">Pokemon Battle Arena</h2>

        <div className="player-info">
          <h3>Welcome, Trainer {user.username}!</h3>
          <p>Rank: {user.rank}</p>
          <p>Rating: {user.rating}</p>
          <p>Wins: {user.wins} | Losses: {user.losses}</p>
          <p>Coins: {user.coins}</p>
          <p>Pokemon: {user.pokemon_count || 0}</p>
          <button
            className="btn-secondary"
            onClick={handleFetchGen1}
            disabled={fetching}
          >
            {fetching ? 'Fetching Gen 1 Pokemon...' : 'Fetch Gen 1 Pokemon (1-151)'}
          </button>
        </div>

        <div className="battle-options">
          <div className="battle-option">
            <h3>Player vs AI</h3>
            <p>Battle against AI opponents to earn coins and experience!</p>
            <ul>
              <li>Victory: 50 coins + XP</li>
              <li>Defeat: 20 coins</li>
              <li>First-time bonus available</li>
            </ul>
            <button
              className="btn-primary"
              onClick={handlePvE}
              disabled={loading}
            >
              {loading ? 'Starting Battle...' : 'Start PvE Battle'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Lobby