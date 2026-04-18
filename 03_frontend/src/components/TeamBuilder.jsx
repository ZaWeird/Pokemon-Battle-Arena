// frontend/src/components/TeamBuilder.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

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

function TeamBuilder({ user }) {
  const [pokemons, setPokemons] = useState([]);
  const [team, setTeam] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await axios.get('/api/inventory', {
        headers: { Authorization: localStorage.getItem('token') }
      });
      setPokemons(response.data);
      const currentTeam = response.data.filter(p => p.is_in_team).sort((a, b) => a.team_position - b.team_position);
      setTeam(currentTeam);
    } catch (error) {
      toast.error('Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const addToTeam = (pokemon) => {
    if (team.length >= 3) {
      toast.error('Team can only have 3 Pokémon');
      return;
    }
    if (team.find(p => p.id === pokemon.id)) {
      toast.error('Pokémon is already in team');
      return;
    }
    setTeam([...team, pokemon]);
  };

  const removeFromTeam = (pokemonId) => {
    setTeam(team.filter(p => p.id !== pokemonId));
  };

  const saveTeam = async () => {
    try {
      await axios.post('/api/team/save', 
        { team: team.map(p => p.id) },
        { headers: { Authorization: localStorage.getItem('token') } }
      );
      toast.success('Team saved successfully!');
    } catch (error) {
      toast.error('Failed to save team');
    }
  };

  const getRarityClass = (rarity) => {
    switch(rarity) {
      case 'Common': return 'rarity-Common';
      case 'Rare': return 'rarity-Rare';
      case 'Epic': return 'rarity-Epic';
      case 'Legendary': return 'rarity-Legendary';
      default: return '';
    }
  };

  const renderTypesWithIcons = (typeString) => {
    if (!typeString) return null;
    const types = typeString.split(',');
    return (
      <div className="type-group">
        {types.map(t => {
          const type = t.trim();
          const iconUrl = TYPE_ICONS[type];
          if (!iconUrl) return null;
          return (
            <div key={type} className="type-item">
              <img
                src={iconUrl}
                alt={type}
                title={type}
                className="type-icon"
                style={{ width: '20px', height: '20px', marginRight: '4px' }}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
              <span className="type-name">{type}</span>
            </div>
          );
        })}
      </div>
    );
  };

  // Filter available Pokémon (not in team, search, type)
  const availablePokemons = pokemons.filter(p => {
    if (team.some(t => t.id === p.id)) return false;
    if (searchTerm && !p.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (selectedType !== 'all') {
      const types = p.type.split(',').map(t => t.trim());
      if (!types.includes(selectedType)) return false;
    }
    return true;
  });

  if (loading) {
    return <div className="loading">Loading...</div>;
  }

  return (
    <div className="team-builder">
      <div className="card">
        <h2 className="card-title">Team Builder</h2>

        {/* Team Slots */}
        <div className="team-section">
          <h3>Your Team ({team.length}/3)</h3>
          <div className="team-slots">
            {[0, 1, 2].map(index => (
              <div key={index} className="team-slot">
                {team[index] ? (
                  <div className="team-pokemon">
                    <img src={team[index].image_url} alt={team[index].name} />
                    <p>{team[index].name}</p>
                    <div className="team-pokemon-stats">
                      <span>Lv.{team[index].level}</span>
                      <span>{team[index].hp} HP</span>
                    </div>
                    <button onClick={() => removeFromTeam(team[index].id)}>Remove</button>
                  </div>
                ) : (
                  <div className="empty-slot">Empty Slot</div>
                )}
              </div>
            ))}
          </div>
          {team.length > 0 && (
            <button className="btn-primary" onClick={saveTeam}>Save Team</button>
          )}
        </div>

        {/* Available Pokémon with Search and Type Filter */}
        <div className="available-pokemon">
          <h3>Available Pokémon</h3>
          <div className="search-filter-bar">
            <input
              type="text"
              placeholder="Search by name..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="type-filter"
            >
              <option value="all">All Types</option>
              <option value="normal">Normal</option>
              <option value="fire">Fire</option>
              <option value="water">Water</option>
              <option value="electric">Electric</option>
              <option value="grass">Grass</option>
              <option value="ice">Ice</option>
              <option value="fighting">Fighting</option>
              <option value="poison">Poison</option>
              <option value="ground">Ground</option>
              <option value="flying">Flying</option>
              <option value="psychic">Psychic</option>
              <option value="bug">Bug</option>
              <option value="rock">Rock</option>
              <option value="ghost">Ghost</option>
              <option value="dragon">Dragon</option>
              <option value="dark">Dark</option>
              <option value="steel">Steel</option>
              <option value="fairy">Fairy</option>
            </select>
          </div>
          <div className="inventory-stats">
            <p>Showing: {availablePokemons.length} Pokémon</p>
          </div>
          <div className="grid">
            {availablePokemons.map(pokemon => (
              <div key={pokemon.id} className="pokemon-card" onClick={() => addToTeam(pokemon)}>
                <img src={pokemon.image_url} alt={pokemon.name} className="pokemon-image" />
                <div className="pokemon-info">
                  <h4 className="pokemon-name">{pokemon.name}</h4>
                  <div className="rarity-and-types">
                    <span className={`pokemon-rarity ${getRarityClass(pokemon.rarity)}`}>
                      {pokemon.rarity}
                    </span>
                    {renderTypesWithIcons(pokemon.type)}
                  </div>
                  <div className="pokemon-stats">
                    <p>Level: {pokemon.level}</p>
                    <p>HP: {pokemon.hp}</p>
                    <p>ATK: {pokemon.attack}</p>
                    <p>DEF: {pokemon.defense}</p>
                    <p>SPD: {pokemon.speed}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

export default TeamBuilder;