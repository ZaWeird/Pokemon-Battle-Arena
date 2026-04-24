// frontend/src/components/Gacha.jsx
import React, { useState } from 'react';
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

function Gacha({ user, setUser }) {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [showResults, setShowResults] = useState(false);
  const [revealed, setRevealed] = useState([]); // track opened cards

  const refreshUserData = async () => {
    try {
      const response = await axios.get('/api/profile', {
        headers: { Authorization: localStorage.getItem('token') }
      });
      if (setUser) {
        setUser(response.data);
        localStorage.setItem('user', JSON.stringify(response.data));
      }
    } catch (error) {
      console.error('Failed to refresh user data:', error);
    }
  };

  const handleSummon = async (type) => {
    if (type === 'single' && user.coins < 100) {
      toast.error('Not enough coins!');
      return;
    }
    if (type === 'ten' && user.coins < 900) {
      toast.error('Not enough coins for 10x summon!');
      return;
    }

    setLoading(true);
    setShowResults(false);

    try {
      const response = await axios.post('/api/gacha/summon', 
        { type },
        { headers: { Authorization: localStorage.getItem('token') } }
      );
      setResults(response.data.results);
      setRevealed(new Array(response.data.results.length).fill(false)); // all hidden initially
      setShowResults(true);
      await refreshUserData();
      toast.success(`Summoned ${response.data.results.length} Pokemon!`);
    } catch (error) {
      toast.error(error.response?.data?.message || 'Summon failed');
    } finally {
      setLoading(false);
    }
  };

  const handleReveal = (index) => {
    const newRevealed = [...revealed];
    newRevealed[index] = true;
    setRevealed(newRevealed);
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

  const getRarityBgClass = (rarity) => {
    switch(rarity) {
      case 'Common': return 'bg-common';
      case 'Rare': return 'bg-rare';
      case 'Epic': return 'bg-epic';
      case 'Legendary': return 'bg-legendary';
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

  return (
    <div className="gacha-container">
      <div className="card">
        <h2 className="card-title">Pokémon Gacha</h2>
        
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
            <p>Summoning Pokémon...</p>
          </div>
        )}

        {showResults && results.length > 0 && (
          <div className="gacha-results">
            <h3>Summon Results</h3>
            <div className="grid">
              {results.map((pokemon, index) => (
                <div 
                  key={index} 
                  className={`pokemon-card gacha-result ${!revealed[index] ? 'gacha-card-hidden' : ''} ${getRarityBgClass(pokemon.rarity)}`}
                  onClick={() => !revealed[index] && handleReveal(index)}
                >
                  {!revealed[index] ? (
                    <div className="gacha-cover">
                      <span className="cover-text">Click to open</span>
                    </div>
                  ) : (
                    <>
                      <img 
                        src={pokemon.image_url} 
                        alt={pokemon.name}
                        className="pokemon-image"
                      />
                      <div className="pokemon-info">
                        <h4 className="pokemon-name">{pokemon.name}</h4>
                        <div className="rarity-and-types">
                          <span className={`pokemon-rarity ${getRarityClass(pokemon.rarity)}`}>
                            {pokemon.rarity}
                          </span>
                          {renderTypesWithIcons(pokemon.type)}
                        </div>
                      </div>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Gacha;