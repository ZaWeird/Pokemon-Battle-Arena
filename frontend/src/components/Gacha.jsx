// frontend/src/components/Gacha.jsx
import React, { useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function Gacha({ user, setUser }) {
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState([])
  const [showResults, setShowResults] = useState(false)

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

  const handleSummon = async (type) => {
    if (type === 'single' && user.coins < 100) {
      toast.error('Not enough coins!')
      return
    }
    
    if (type === 'ten' && user.coins < 900) {
      toast.error('Not enough coins for 10x summon!')
      return
    }

    setLoading(true)
    setShowResults(false)

    try {
      const response = await axios.post('/api/gacha/summon', 
        { type },
        { headers: { Authorization: localStorage.getItem('token') } }
      )

      setResults(response.data.results)
      setShowResults(true)
      
      // Refresh user data to get updated coins
      await refreshUserData()
      
      toast.success(`Summoned ${response.data.results.length} Pokemon!`)
    } catch (error) {
      toast.error(error.response?.data?.message || 'Summon failed')
    } finally {
      setLoading(false)
    }
  }

  const getRarityClass = (rarity) => {
    switch(rarity) {
      case 'Common': return 'rarity-Common'
      case 'Rare': return 'rarity-Rare'
      case 'Epic': return 'rarity-Epic'
      case 'Legendary': return 'rarity-Legendary'
      default: return ''
    }
  }

  return (
    <div className="gacha-container">
      <div className="card">
        <h2 className="card-title">Pokemon Gacha</h2>
        
        <div className="gacha-info">
          <p>Your Coins: <strong>{user.coins}</strong></p>
          <p>Single Summon: 100 coins</p>
          <p>10x Summon: 900 coins (10% discount)</p>
        </div>

        <div className="gacha-actions">
          <button 
            className="btn-primary" 
            onClick={() => handleSummon('single')}
            disabled={loading || user.coins < 100}
          >
            Single Summon (100)
          </button>
          <button 
            className="btn-primary" 
            onClick={() => handleSummon('ten')}
            disabled={loading || user.coins < 900}
          >
            10x Summon (900)
          </button>
        </div>

        {loading && (
          <div className="loading-spinner">
            <p>Summoning Pokemon...</p>
          </div>
        )}

        {showResults && results.length > 0 && (
          <div className="gacha-results">
            <h3>Summon Results</h3>
            <div className="grid">
              {results.map((pokemon, index) => (
                <div key={index} className="pokemon-card gacha-result">
                  <img 
                    src={pokemon.image_url} 
                    alt={pokemon.name}
                    className="pokemon-image"
                  />
                  <div className="pokemon-info">
                    <h4 className="pokemon-name">{pokemon.name}</h4>
                    <span className={`pokemon-rarity ${getRarityClass(pokemon.rarity)}`}>
                      {pokemon.rarity}
                    </span>
                    <p>Level: {pokemon.level}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Gacha