// frontend/src/components/PokeAPIFetcher.jsx
import React, { useState, useEffect } from 'react';
import { fetchPokemonList, fetchPokemonByType, fetchPokemonTypes, fetchPokemonData } from '../services/pokeapi';

const PokeAPIFetcher = () => {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [pokemon, setPokemon] = useState([]);
  const [types, setTypes] = useState([]);
  const [selectedType, setSelectedType] = useState('');
  const [searchTerm, setSearchTerm] = useState('');
  const [error, setError] = useState(null);
  const [selectedPokemon, setSelectedPokemon] = useState(null);
  const [movesLoading, setMovesLoading] = useState(false);
  const [pokemonMoves, setPokemonMoves] = useState({});

  // Fetch all Pokémon
  const handleFetchAll = async () => {
    setLoading(true);
    setError(null);
    setProgress(0);
    
    try {
      // Fetch first 50 Pokémon
      const pokemonData = await fetchPokemonList(0, 50);
      setPokemon(pokemonData);
      setProgress(100);
    } catch (err) {
      setError('Failed to fetch Pokémon data. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Fetch Pokémon by type
  const handleFetchByType = async (type) => {
    setLoading(true);
    setError(null);
    setSelectedType(type);
    
    try {
      const pokemonData = await fetchPokemonByType(type);
      setPokemon(pokemonData);
    } catch (err) {
      setError(`Failed to fetch ${type} type Pokémon.`);
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Load types on component mount
  useEffect(() => {
    const loadTypes = async () => {
      try {
        const typeList = await fetchPokemonTypes();
        setTypes(typeList);
      } catch (err) {
        console.error('Failed to load types:', err);
      }
    };
    loadTypes();
  }, []);

  // Search Pokémon by name
  const handleSearch = async () => {
    if (!searchTerm.trim()) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const pokemonData = await fetchPokemonData(searchTerm.toLowerCase());
      setPokemon([pokemonData]);
    } catch (err) {
      setError(`Pokemon "${searchTerm}" not found.`);
      setPokemon([]);
    } finally {
      setLoading(false);
    }
  };

  // View Pokémon details with moves
  const handleViewDetails = async (pokemonName) => {
    if (pokemonMoves[pokemonName]) {
      setSelectedPokemon(pokemonMoves[pokemonName]);
      return;
    }
    
    setMovesLoading(true);
    try {
      const data = await fetchPokemonData(pokemonName);
      setPokemonMoves(prev => ({ ...prev, [pokemonName]: data }));
      setSelectedPokemon(data);
    } catch (err) {
      console.error('Failed to load Pokémon details:', err);
    } finally {
      setMovesLoading(false);
    }
  };

  // Clear all cache
  const handleClearCache = () => {
    const keys = Object.keys(localStorage);
    keys.forEach(key => {
      if (key.startsWith('pokemon_') || key.startsWith('move_') || key.startsWith('type_')) {
        localStorage.removeItem(key);
      }
    });
    alert('Cache cleared successfully!');
  };

  return (
    <div className="pokeapi-container">
      <h2>Pokémon Data Fetcher</h2>
      
      {/* Controls */}
      <div className="controls">
        <button onClick={handleFetchAll} disabled={loading}>
          Fetch First 50 Pokémon
        </button>
        
        <button onClick={handleClearCache} disabled={loading}>
          Clear Cache
        </button>
        
        <div className="search-section">
          <input
            type="text"
            placeholder="Search Pokémon by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} disabled={loading}>
            Search
          </button>
        </div>
        
        <div className="type-filters">
          <span>Filter by type:</span>
          <select 
            value={selectedType} 
            onChange={(e) => handleFetchByType(e.target.value)}
            disabled={loading}
          >
            <option value="">All Types</option>
            {types.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
        </div>
      </div>
      
      {/* Loading state */}
      {loading && (
        <div className="loading-state">
          <div className="spinner"></div>
          <p>Fetching Pokémon data...</p>
          {progress > 0 && <progress value={progress} max="100" />}
        </div>
      )}
      
      {/* Error state */}
      {error && (
        <div className="error-state">
          <p>{error}</p>
          <button onClick={() => setError(null)}>Dismiss</button>
        </div>
      )}
      
      {/* Pokémon list */}
      {!loading && pokemon.length > 0 && (
        <div className="pokemon-list">
          <h3>Found {pokemon.length} Pokémon</h3>
          <div className="pokemon-grid">
            {pokemon.map(p => (
              <div 
                key={p.name} 
                className="pokemon-card"
                onClick={() => handleViewDetails(p.name)}
              >
                <img src={p.imageUrl} alt={p.name} />
                <h4>{p.name}</h4>
                <div className="pokemon-types">
                  {p.types.map(type => (
                    <span key={type} className={`type-badge type-${type}`}>
                      {type}
                    </span>
                  ))}
                </div>
                <div className="pokemon-stats">
                  <span>HP: {p.baseStats.hp}</span>
                  <span>ATK: {p.baseStats.attack}</span>
                  <span>DEF: {p.baseStats.defense}</span>
                  <span>SPD: {p.baseStats.speed}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* Pokémon Details Modal */}
      {selectedPokemon && (
        <div className="modal-overlay" onClick={() => setSelectedPokemon(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setSelectedPokemon(null)}>×</button>
            
            <div className="pokemon-detail-header">
              <img src={selectedPokemon.imageUrl} alt={selectedPokemon.name} />
              <div>
                <h2>{selectedPokemon.name}</h2>
                <div className="pokemon-types">
                  {selectedPokemon.types.map(type => (
                    <span key={type} className={`type-badge type-${type}`}>
                      {type}
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="pokemon-detail-stats">
              <h3>Base Stats</h3>
              <div className="stats-grid">
                <div>HP: {selectedPokemon.baseStats.hp}</div>
                <div>Attack: {selectedPokemon.baseStats.attack}</div>
                <div>Defense: {selectedPokemon.baseStats.defense}</div>
                <div>Special: {selectedPokemon.baseStats.special}</div>
                <div>Speed: {selectedPokemon.baseStats.speed}</div>
              </div>
              <p>Base Experience: {selectedPokemon.baseExperience}</p>
            </div>
            
            <div className="pokemon-detail-moves">
              <h3>Level-Up Moves</h3>
              {movesLoading ? (
                <div className="loading-moves">Loading moves...</div>
              ) : (
                <div className="moves-list">
                  {selectedPokemon.levelUpMoves.slice(0, 20).map(move => (
                    <div key={move.name} className="move-item">
                      <span className="move-level">Lv.{move.learnedAt}</span>
                      <span className="move-name">{move.name}</span>
                    </div>
                  ))}
                  {selectedPokemon.levelUpMoves.length === 0 && (
                    <p>No level-up moves found</p>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
      
      {/* Empty state */}
      {!loading && pokemon.length === 0 && !error && (
        <div className="empty-state">
          <p>Click "Fetch First 50 Pokémon" to load data from PokeAPI</p>
        </div>
      )}
    </div>
  );
};

export default PokeAPIFetcher;