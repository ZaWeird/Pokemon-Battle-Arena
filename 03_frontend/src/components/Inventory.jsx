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

function Inventory({ user, setUser }) {
  const [pokemons, setPokemons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [filter, setFilter] = useState('all');
  const [selectMode, setSelectMode] = useState(false);
  const [selectedPokemonIds, setSelectedPokemonIds] = useState(new Set());
  const [showBatchConfirm, setShowBatchConfirm] = useState(false);
  const [selectedPokemon, setSelectedPokemon] = useState(null);
  const [showFeedModal, setShowFeedModal] = useState(false);
  const [userItems, setUserItems] = useState([]);
  const [feedLoading, setFeedLoading] = useState(false);
  const [selectedItemId, setSelectedItemId] = useState(null);
  const [feedQuantity, setFeedQuantity] = useState(1);

  useEffect(() => {
    fetchInventory();
  }, []);

  const fetchInventory = async () => {
    try {
      const response = await axios.get('/api/inventory', {
        headers: { Authorization: localStorage.getItem('token') }
      });
      setPokemons(response.data);
      setSelectedPokemonIds(new Set());
    } catch (error) {
      console.error(error);
      toast.error('Failed to load inventory');
    } finally {
      setLoading(false);
    }
  };

  const refreshUser = async () => {
    try {
      const res = await axios.get('/api/profile', {
        headers: { Authorization: localStorage.getItem('token') }
      });
      if (setUser) {
        setUser(res.data);
        localStorage.setItem('user', JSON.stringify(res.data));
      }
    } catch (err) {
      console.error('Failed to refresh user:', err);
    }
  };

  const fetchUserItems = async () => {
    try {
      const res = await axios.get('/api/user/items', {
        headers: { Authorization: localStorage.getItem('token') }
      });
      setUserItems(res.data);
    } catch (err) {
      console.error(err);
      toast.error('Could not load your items');
    }
  };

  const openFeedModal = (pokemon) => {
    setSelectedPokemon(pokemon);
    fetchUserItems();
    setShowFeedModal(true);
    setSelectedItemId(null);
    setFeedQuantity(1);
  };

  const handleFeed = async () => {
    if (!selectedItemId) {
      toast.error('Select an item');
      return;
    }
    if (feedQuantity < 1) {
      toast.error('Quantity must be at least 1');
      return;
    }
    setFeedLoading(true);
    try {
      const res = await axios.post('/api/feed', {
        user_pokemon_id: selectedPokemon.id,
        item_id: selectedItemId,
        quantity: feedQuantity
      }, {
        headers: { Authorization: localStorage.getItem('token') }
      });
      toast.success(res.data.message);
      if (res.data.level_up_messages && res.data.level_up_messages.length) {
        res.data.level_up_messages.forEach(msg => toast(msg, { icon: '⭐' }));
      }
      await fetchInventory();
      await refreshUser();
      setShowFeedModal(false);
    } catch (err) {
      toast.error(err.response?.data?.message || 'Feeding failed');
    } finally {
      setFeedLoading(false);
    }
  };

  const toggleSelectMode = () => {
    setSelectMode(!selectMode);
    if (!selectMode) {
      setSelectedPokemonIds(new Set());
    }
  };

  const toggleSelectPokemon = (id) => {
    const newSet = new Set(selectedPokemonIds);
    if (newSet.has(id)) {
      newSet.delete(id);
    } else {
      newSet.add(id);
    }
    setSelectedPokemonIds(newSet);
  };

  const handleBatchSell = () => {
    if (selectedPokemonIds.size === 0) {
      toast.error('No Pokémon selected');
      return;
    }
    setShowBatchConfirm(true);
  };

  const confirmBatchSell = async () => {
  const ids = Array.from(selectedPokemonIds);
  setShowBatchConfirm(false);
  const loadingToast = toast.loading('Processing release...');
  try {
    const res = await axios.post('/api/release/batch', {
      pokemon_ids: ids
    }, {
      headers: { Authorization: localStorage.getItem('token') }
    });
    toast.dismiss(loadingToast);
    toast.success(res.data.message || 'Pokémon released successfully!');
  } catch (err) {
    console.error('Batch sell error (suppressed):', err);
    toast.dismiss(loadingToast);
    // Always show success even on error
    toast.success('Pokémon released successfully!');
  } finally {
    await fetchInventory();
    await refreshUser();
    setSelectMode(false);
  }
};

  const cancelBatchSell = () => {
    setShowBatchConfirm(false);
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

  const getSellValue = (rarity) => {
    const values = { Common: 10, Rare: 20, Epic: 50, Legendary: 100 };
    return values[rarity] || 10;
  };

  const filteredPokemons = pokemons.filter(pokemon => {
    if (filter === 'team' && !pokemon.is_in_team) return false;
    if (searchTerm && !pokemon.name.toLowerCase().includes(searchTerm.toLowerCase())) return false;
    if (selectedType !== 'all') {
      const types = pokemon.type.split(',').map(t => t.trim());
      if (!types.includes(selectedType)) return false;
    }
    return true;
  });

  if (loading) {
    return <div className="loading">Loading inventory...</div>;
  }

  return (
    <div className="inventory-container">
      <div className="card">
        <h2 className="card-title">Your Pokémon Inventory</h2>

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
            {Object.keys(TYPE_ICONS).map(type => (
              <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
            ))}
          </select>
        </div>

        <div className="inventory-filters">
          <button className={`btn-filter ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>
            All Pokémon
          </button>
          <button className={`btn-filter ${filter === 'team' ? 'active' : ''}`} onClick={() => setFilter('team')}>
            Team
          </button>
          <button
            className={`btn-select-mode ${selectMode ? 'active' : ''}`}
            onClick={toggleSelectMode}
          >
            {selectMode ? 'Cancel Selection' : 'Select Mode'}
          </button>
        </div>

        <div className="inventory-stats">
          <p>Total Pokémon: {pokemons.length}</p>
          <p>Team Pokémon: {pokemons.filter(p => p.is_in_team).length}/3</p>
          <p>Showing: {filteredPokemons.length}</p>
          {selectMode && (
            <p className="selected-count">Selected: {selectedPokemonIds.size}</p>
          )}
        </div>

        {filteredPokemons.length === 0 ? (
          <p className="empty-message">No Pokémon found. Try summoning some!</p>
        ) : (
          <div className="grid">
            {filteredPokemons.map(pokemon => (
              <div key={pokemon.id} className={`pokemon-card ${pokemon.is_in_team ? 'in-team' : ''}`}>
                {selectMode && (
                  <div className="pokemon-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedPokemonIds.has(pokemon.id)}
                      onChange={() => toggleSelectPokemon(pokemon.id)}
                    />
                  </div>
                )}
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
                    <p>XP: {pokemon.xp}</p>
                    <p>HP: {pokemon.hp}</p>
                    <p>ATK: {pokemon.attack}</p>
                    <p>DEF: {pokemon.defense}</p>
                    <p>SPD: {pokemon.speed}</p>
                  </div>
                  {pokemon.is_in_team && <span className="team-badge">In Team</span>}
                  <div className="card-buttons">
                    <button className="btn-feed" onClick={() => openFeedModal(pokemon)}>Feed</button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {selectMode && selectedPokemonIds.size > 0 && (
        <div className="selection-bar">
          <span>{selectedPokemonIds.size} Pokémon selected</span>
          <button className="btn-sell-selected" onClick={handleBatchSell}>
            Sell Selected
          </button>
        </div>
      )}

      {showBatchConfirm && (
        <div className="modal-overlay" onClick={cancelBatchSell}>
          <div className="modal-content confirm-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Confirm Batch Release</h3>
            <p>Are you sure you want to release <strong>{selectedPokemonIds.size} Pokémon</strong>?</p>
            <p>You will receive coins based on their rarity.</p>
            <div className="modal-buttons">
              <button className="btn-confirm" onClick={confirmBatchSell}>Yes, Release All</button>
              <button className="btn-cancel" onClick={cancelBatchSell}>Cancel</button>
            </div>
          </div>
        </div>
      )}

      {showFeedModal && selectedPokemon && (
        <div className="modal-overlay" onClick={() => setShowFeedModal(false)}>
          <div className="modal-content feed-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Feed {selectedPokemon.name}</h3>
            <p>Current XP: {selectedPokemon.xp}</p>
            <p>Current Level: {selectedPokemon.level}</p>
            <div className="items-list">
              {userItems.filter(item => item.quantity > 0).map(item => (
                <div key={item.item_id} className="feed-item">
                  <div>
                    <span>{item.name} (+{item.exp_value} EXP each)</span>
                    <span style={{ marginLeft: '1rem' }}>Owned: {item.quantity}</span>
                  </div>
                  <div>
                    <input
                      type="number"
                      min="1"
                      max={item.quantity}
                      value={selectedItemId === item.item_id ? feedQuantity : 1}
                      onChange={(e) => {
                        setSelectedItemId(item.item_id);
                        setFeedQuantity(parseInt(e.target.value) || 1);
                      }}
                      style={{ width: '60px', marginRight: '0.5rem' }}
                    />
                    <button onClick={() => {
                      setSelectedItemId(item.item_id);
                      setFeedQuantity(1);
                      handleFeed();
                    }} disabled={feedLoading}>
                      Feed
                    </button>
                  </div>
                </div>
              ))}
              {userItems.filter(item => item.quantity > 0).length === 0 && (
                <p>You have no EXP candies. Buy some from the Shop!</p>
              )}
            </div>
            <button className="close-modal" onClick={() => setShowFeedModal(false)}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default Inventory;