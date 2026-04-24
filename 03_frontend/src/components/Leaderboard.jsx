import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function Leaderboard() {
  const [players, setPlayers] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLeaderboard()
  }, [])

  const fetchLeaderboard = async () => {
    try {
      const response = await axios.get('/api/leaderboard')
      setPlayers(response.data)
    } catch (error) {
      toast.error('Failed to load leaderboard')
    } finally {
      setLoading(false)
    }
  }

  const getRankClass = (rank) => {
    if (rank === 1) return 'rank-1'
    if (rank === 2) return 'rank-2'
    if (rank === 3) return 'rank-3'
    return ''
  }

  if (loading) {
    return <div className="loading">Loading leaderboard...</div>
  }

  return (
    <div className="leaderboard">
      <div className="card">
        <h2 className="card-title">Trainer Rankings</h2>
        
        <div className="leaderboard-table pixel-table">
          <div className="leaderboard-header pixel-header">
            <div>Rank</div>
            <div>Trainer</div>
            <div>Wins</div>
            <div>Losses</div>
            <div>Win Rate</div>
            <div>Pokémon</div>
          </div>
          
          {players.map(player => (
            <div 
              key={player.rank} 
              className={`leaderboard-row pixel-row ${getRankClass(player.rank)}`}
            >
              <div className="rank">#{player.rank}</div>
              <div className="player-name">{player.username}</div>
              <div className="wins">{player.wins}</div>
              <div className="losses">{player.losses}</div>
              <div className="win-rate">{player.win_rate}%</div>
              <div className="pokemon-count">{player.pokemon_count}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default Leaderboard