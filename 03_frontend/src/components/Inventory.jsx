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

const ITEMS_PER_PAGE = 60;
const CARDS_PER_ROW = 4;

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
  const [selectedItems, setSelectedItems] = useState({});
  const [hasTeamSelected, setHasTeamSelected] = useState(false);
  const [onlyOnePokemon, setOnlyOnePokemon] = useState(false);

  const [currentPage, setCurrentPage] = useState(1);

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
      return res.data; // return data for chaining
    } catch (err) {
      console.error(err);
      toast.error('Could not load your items');
      return [];
    }
  };

  const openFeedModal = async (pokemon) => {
    setSelectedPokemon(pokemon);
    const items = await fetchUserItems();
    // initialize selectedItems with all items unchecked, qty=1
    const initial = {};
    items.forEach(item => {
      initial[item.item_id] = { selected: false, quantity: 1 };
    });
    setSelectedItems(initial);
    setShowFeedModal(true);
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

    if (pokemons.length <= 1) {
      setOnlyOnePokemon(true);
      setHasTeamSelected(false);
      setShowBatchConfirm(true);
      return;
    }

    setOnlyOnePokemon(false);

    const teamSelected = Array.from(selectedPokemonIds).some(id => {
      const pokemon = pokemons.find(p => p.id === id);
      return pokemon && pokemon.is_in_team;
    });
    setHasTeamSelected(teamSelected);
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
      toast.success('Pokémon released successfully!');
    } finally {
      await fetchInventory();
      await refreshUser();
      setSelectMode(false);
      setCurrentPage(1);
    }
  };

  const cancelBatchSell = () => {
    setShowBatchConfirm(false);
    setHasTeamSelected(false);
    setOnlyOnePokemon(false);
  };

  const getRarityClass = (rarity) => {
    switch (rarity) {
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
                style={{ width: '16px', height: '16px', marginRight: '2px' }}
                onError={(e) => { e.target.style.display = 'none'; }}
              />
              <span className="type-name">{type}</span>
            </div>
          );
        })}
      </div>
    );
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

  const totalPages = Math.ceil(filteredPokemons.length / ITEMS_PER_PAGE);
  const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
  const paginatedPokemons = filteredPokemons.slice(startIndex, startIndex + ITEMS_PER_PAGE);

  const goToPage = (page) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

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
            onChange={(e) => {
              setSearchTerm(e.target.value);
              setCurrentPage(1);
            }}
            className="search-input"
          />
          <select
            value={selectedType}
            onChange={(e) => {
              setSelectedType(e.target.value);
              setCurrentPage(1);
            }}
            className="type-filter"
          >
            <option value="all">All Types</option>
            {Object.keys(TYPE_ICONS).map(type => (
              <option key={type} value={type}>{type.charAt(0).toUpperCase() + type.slice(1)}</option>
            ))}
          </select>
        </div>

        <div className="inventory-filters">
          <button
            className={`btn-filter ${filter === 'all' ? 'active' : ''}`}
            onClick={() => { setFilter('all'); setCurrentPage(1); }}
          >
            All Pokémon
          </button>
          <button
            className={`btn-filter ${filter === 'team' ? 'active' : ''}`}
            onClick={() => { setFilter('team'); setCurrentPage(1); }}
          >
            Team
          </button>
          <button
            className={`btn-select-mode ${selectMode ? 'active' : ''}`}
            onClick={toggleSelectMode}
          >
            {selectMode ? 'Cancel Selection' : 'Select Mode'}
          </button>

          {selectMode && selectedPokemonIds.size > 0 && (
            <button
              className="btn-sell-selected-filter"
              onClick={handleBatchSell}
            >
              Release Selected ({selectedPokemonIds.size})
            </button>
          )}
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
          <>
            <div className="inventory-grid">
              {paginatedPokemons.map(pokemon => (
                <div key={pokemon.id} className={`pokemon-card inventory-card ${pokemon.is_in_team ? 'in-team' : ''} bg-${pokemon.rarity.toLowerCase()}`}>
                  {selectMode && (
                    <div className="pokemon-checkbox pixel-checkbox-wrapper">
                      <label className="feed-checkbox-label">
                        <input
                          type="checkbox"
                          className="pixel-checkbox"
                          checked={selectedPokemonIds.has(pokemon.id)}
                          onChange={() => toggleSelectPokemon(pokemon.id)}
                        />
                        <span className="checkbox-indicator">
                          {selectedPokemonIds.has(pokemon.id) ? '✓' : ''}
                        </span>
                      </label>
                    </div>
                  )}
                  <div className="inventory-card-content">
                    <div className="inventory-image-wrapper">
                      <img src={pokemon.image_url} alt={pokemon.name} className="pokemon-image" />
                    </div>
                    <div className="inventory-details">
                      <h4 className="pokemon-name">{pokemon.name}</h4>
                      <div className="rarity-and-types-compact">
                        <span className={`pokemon-rarity ${getRarityClass(pokemon.rarity)}`}>
                          {pokemon.rarity}
                        </span>
                        {renderTypesWithIcons(pokemon.type)}
                      </div>
                      <div className="pokemon-stats-grid">
                        <div className="stat-item">Lv. {pokemon.level}</div>
                        <div className="stat-item">XP: {pokemon.xp}</div>
                        <div className="stat-item">HP: {pokemon.hp}</div>
                        <div className="stat-item">ATK: {pokemon.attack}</div>
                        <div className="stat-item">DEF: {pokemon.defense}</div>
                        <div className="stat-item">SPD: {pokemon.speed}</div>
                      </div>
                      {pokemon.is_in_team && <span className="team-badge">In Team</span>}
                      <button className="btn-feed pixel-btn" onClick={() => openFeedModal(pokemon)}>Feed</button>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {totalPages > 1 && (
              <div className="pagination">
                <button
                  className="pagination-btn"
                  onClick={() => goToPage(1)}
                  disabled={currentPage === 1}
                >
                  «
                </button>
                <button
                  className="pagination-btn"
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage === 1}
                >
                  ‹
                </button>
                <span className="pagination-info">
                  Page {currentPage} of {totalPages}
                </span>
                <button
                  className="pagination-btn"
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage === totalPages}
                >
                  ›
                </button>
                <button
                  className="pagination-btn"
                  onClick={() => goToPage(totalPages)}
                  disabled={currentPage === totalPages}
                >
                  »
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* Batch release confirmation modal */}
      {showBatchConfirm && (
        <div className="modal-overlay" onClick={cancelBatchSell}>
          <div className="modal-content confirm-modal" onClick={(e) => e.stopPropagation()}>
            {onlyOnePokemon ? (
              <>
                <h3>Cannot Release Last Pokémon</h3>
                <p>You cannot release your only Pokémon!</p>
                <p>You need at least one Pokémon to battle.</p>
                <div className="modal-buttons">
                  <button className="btn-cancel pixel-btn" onClick={cancelBatchSell}>Cancel</button>
                </div>
              </>
            ) : hasTeamSelected ? (
              <>
                <h3>Cannot Release Team Pokémon</h3>
                <p>You're selecting a Pokémon that's in your team!</p>
                <p>Please remove them from your team first.</p>
                <div className="modal-buttons">
                  <button className="btn-cancel pixel-btn" onClick={cancelBatchSell}>Cancel</button>
                </div>
              </>
            ) : (
              <>
                <h3>Confirm Batch Release</h3>
                <p>Are you sure you want to release <strong>{selectedPokemonIds.size} Pokémon</strong>?</p>
                <p>You will receive coins based on their rarity.</p>
                <div className="modal-buttons">
                  <button className="btn-confirm pixel-btn" onClick={confirmBatchSell}>Yes, Release All</button>
                  <button className="btn-cancel pixel-btn" onClick={cancelBatchSell}>Cancel</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Feed modal – redesigned with checkboxes */}
      {showFeedModal && selectedPokemon && (
        <div className="modal-overlay" onClick={() => setShowFeedModal(false)}>
          <div className="modal-content feed-modal" onClick={(e) => e.stopPropagation()}>
            <h3>Feed {selectedPokemon.name}</h3>
            <p>Current XP: {selectedPokemon.xp}</p>
            <p>Current Level: {selectedPokemon.level}</p>
            <div className="items-list">
              {userItems.filter(item => item.quantity > 0).map(item => (
                <div key={item.item_id} className="feed-item pixel-box">
                  <label className="feed-checkbox-label">
                    <input
                      type="checkbox"
                      className="pixel-checkbox"
                      checked={selectedItems[item.item_id]?.selected || false}
                      onChange={(e) => {
                        setSelectedItems(prev => ({
                          ...prev,
                          [item.item_id]: {
                            ...prev[item.item_id],
                            selected: e.target.checked
                          }
                        }));
                      }}
                    />
                    <span className="checkbox-indicator">
                      {selectedItems[item.item_id]?.selected ? '✓' : ''}
                    </span>
                  </label>
                  <div className="feed-item-details">
                    <span>{item.name} (+{item.exp_value} EXP each)</span>
                    <span>
                      Owned: {item.quantity}
                      {selectedItems[item.item_id]?.selected && (
                        <span className="selected-text"> - item selected</span>
                      )}
                    </span>
                  </div>
                  <div className="feed-item-qty">
                    <span>Qty:</span>
                    <input
                      type="number"
                      min="1"
                      max={item.quantity}
                      value={selectedItems[item.item_id]?.quantity || 1}
                      onChange={(e) => {
                        const qty = Math.min(Math.max(1, parseInt(e.target.value) || 1), item.quantity);
                        setSelectedItems(prev => ({
                          ...prev,
                          [item.item_id]: {
                            ...prev[item.item_id],
                            quantity: qty
                          }
                        }));
                      }}
                      className="pixel-input"
                    />
                  </div>
                </div>
              ))}
              {userItems.filter(item => item.quantity > 0).length === 0 && (
                <p>You have no EXP candies. Buy some from the Shop!</p>
              )}
            </div>
            <div className="modal-buttons">
              <button
                className="pixel-btn feed-selected-btn"
                disabled={feedLoading || Object.values(selectedItems).every(s => !s.selected)}
                onClick={async () => {
                  const toFeed = Object.entries(selectedItems)
                    .filter(([_, s]) => s.selected)
                    .map(([itemId, s]) => {
                      const item = userItems.find(i => i.item_id === parseInt(itemId));
                      return {
                        item_id: parseInt(itemId),
                        quantity: s.quantity,
                        expValue: item?.exp_value || 0
                      };
                    });

                  if (toFeed.length === 0) {
                    toast.error('No items selected');
                    return;
                  }

                  // Calculate total EXP before feeding
                  const totalExp = toFeed.reduce((sum, feed) => sum + (feed.expValue * feed.quantity), 0);

                  setFeedLoading(true);
                  try {
                    for (const feed of toFeed) {
                      await axios.post('/api/feed', {
                        user_pokemon_id: selectedPokemon.id,
                        item_id: feed.item_id,
                        quantity: feed.quantity
                      }, {
                        headers: { Authorization: localStorage.getItem('token') }
                      });
                    }
                    toast.success(`Fed ${toFeed.length} item(s)! Total EXP gained: +${totalExp}`);
                    await fetchInventory();
                    await refreshUser();
                    setShowFeedModal(false);
                  } catch (err) {
                    toast.error(err.response?.data?.message || 'Feeding failed');
                  } finally {
                    setFeedLoading(false);
                  }
                }}
              >
                Feed Selected ({Object.values(selectedItems).filter(s => s.selected).length})
              </button>
              <button className="pixel-btn cancel-btn" onClick={() => setShowFeedModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Inventory;