import React, { useState, useEffect } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function TeamBuilder({ user }) {
  const [pokemons, setPokemons] = useState([])
  const [team, setTeam] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchInventory()
  }, [])

  const fetchInventory = async () => {
    try {
      const response = await axios.get('/api/inventory', {
        headers: { Authorization: localStorage.getItem('token') }
      })
      setPokemons(response.data)
      
      // Load current team
      const currentTeam = response.data
        .filter(p => p.is_in_team)
        .sort((a, b) => a.team_position - b.team_position)
      setTeam(currentTeam)
    } catch (error) {
      toast.error('Failed to load inventory')
    } finally {
      setLoading(false)
    }
  }

  const addToTeam = (pokemon) => {
    if (team.length >= 3) {
      toast.error('Team can only have 3 Pokémon')
      return
    }
    
    if (team.find(p => p.id === pokemon.id)) {
      toast.error('Pokémon is already in team')
      return
    }

    setTeam([...team, pokemon])
  }

  const removeFromTeam = (pokemonId) => {
    setTeam(team.filter(p => p.id !== pokemonId))
  }

  const saveTeam = async () => {
    try {
      await axios.post('/api/team/save', 
        { team: team.map(p => p.id) },
        { headers: { Authorization: localStorage.getItem('token') } }
      )
      toast.success('Team saved successfully!')
    } catch (error) {
      toast.error('Failed to save team')
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

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <div className="team-builder">
      <div className="card">
        <h2 className="card-title">Team Builder</h2>
        
        <div className="team-section">
          <h3>Your Team ({team.length}/3)</h3>
          <div className="team-slots">
            {[0, 1, 2].map(index => (
              <div key={index} className="team-slot">
                {team[index] ? (
                  <div className="team-pokemon">
                    <img src={team[index].image_url} alt={team[index].name} />
                    <p>{team[index].name}</p>
                    <button onClick={() => removeFromTeam(team[index].id)}>
                      Remove
                    </button>
                  </div>
                ) : (
                  <div className="empty-slot">
                    Empty Slot
                  </div>
                )}
              </div>
            ))}
          </div>
          
          {team.length > 0 && (
            <button className="btn-primary" onClick={saveTeam}>
              Save Team
            </button>
          )}
        </div>

        <div className="available-pokemon">
          <h3>Available Pokémon</h3>
          <div className="grid">
            {pokemons
              .filter(p => !team.find(t => t.id === p.id))
              .map(pokemon => (
                <div 
                  key={pokemon.id} 
                  className="pokemon-card"
                  onClick={() => addToTeam(pokemon)}
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
                    <p>Level: {pokemon.level}</p>
                  </div>
                </div>
              ))}
          </div>
        </div>
      </div>
    </div>
  )
}

export default TeamBuilder