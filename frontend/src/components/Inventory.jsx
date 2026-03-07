import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function Inventory({ user }) {
  const [pokemons, setPokemons] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, team, rarity
  const [selectedPokemon, setSelectedPokemon] = useState(null)

  useEffect(() => {
    fetchInventory()
  }, [])

  const fetchInventory = async () => {
    try {
      const response = await axios.get('/api/inventory', {
        headers: { Authorization: localStorage.getItem('token') }
      })
      setPokemons(response.data)
    } catch (error) {
      toast.error('Failed to load inventory')
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

  const filteredPokemons = pokemons.filter(pokemon => {
    if (filter === 'team') return pokemon.is_in_team
    return true
  })

  if (loading) {
    return <div className="loading">Loading inventory...</div>
  }

  return (
    <div className="inventory-container">
      <div className="card">
        <h2 className="card-title">Your Pokémon Inventory</h2>
        
        <div className="inventory-filters">
          <button 
            className={`btn-filter ${filter === 'all' ? 'active' : ''}`}
            onClick={() => setFilter('all')}
          >
            All Pokémon
          </button>
          <button 
            className={`btn-filter ${filter === 'team' ? 'active' : ''}`}
            onClick={() => setFilter('team')}
          >
            Team
          </button>
        </div>

        <div className="inventory-stats">
          <p>Total Pokémon: {pokemons.length}</p>
          <p>Team Pokémon: {pokemons.filter(p => p.is_in_team).length}/3</p>
        </div>

        {filteredPokemons.length === 0 ? (
          <p className="empty-message">No Pokémon found. Try summoning some!</p>
        ) : (
          <div className="grid">
            {filteredPokemons.map(pokemon => (
              <div 
                key={pokemon.id} 
                className={`pokemon-card ${pokemon.is_in_team ? 'in-team' : ''}`}
                onClick={() => setSelectedPokemon(pokemon)}
              >
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
                  <div className="pokemon-stats">
                    <p>Level: {pokemon.level}</p>
                    <p>HP: {pokemon.hp}</p>
                    <p>ATK: {pokemon.attack}</p>
                    <p>DEF: {pokemon.defense}</p>
                    <p>SPD: {pokemon.speed}</p>
                  </div>
                  {pokemon.is_in_team && (
                    <span className="team-badge">In Team</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {selectedPokemon && (
          <div className="modal">
            <div className="modal-content">
              <h3>{selectedPokemon.name}</h3>
              <img src={selectedPokemon.image_url} alt={selectedPokemon.name} />
              <p>Level: {selectedPokemon.level}</p>
              <p>XP: {selectedPokemon.xp}</p>
              <p>Type: {selectedPokemon.type}</p>
              <button onClick={() => setSelectedPokemon(null)}>Close</button>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Inventory