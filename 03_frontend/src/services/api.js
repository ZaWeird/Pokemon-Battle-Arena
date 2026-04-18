// frontend/src/services/api.js
import axios from 'axios';

const API_BASE = '/api'; // Proxied to backend

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = token;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// ========== AUTH ==========
export const register = (userData) => api.post('/register', userData);
export const login = (userData) => api.post('/login', userData);
export const getProfile = () => api.get('/profile');

// ========== GACHA ==========
export const summonPokemon = (type) => api.post('/gacha/summon', { type });

// ========== INVENTORY ==========
export const getInventory = () => api.get('/inventory');

// ========== TEAM ==========
export const saveTeam = (teamIds) => api.post('/team/save', { team: teamIds });

// ========== LEADERBOARD ==========
export const getLeaderboard = () => api.get('/leaderboard');

// ========== BATTLE ==========
export const startPvEBattle = () => api.post('/battle/pve');

// ========== SHOP & ITEMS ==========
export const getShopItems = () => api.get('/shop/items');
export const buyItem = (itemId, quantity = 1) => api.post('/shop/buy', { item_id: itemId, quantity });
export const getUserItems = () => api.get('/user/items');
export const feedPokemon = (userPokemonId, itemId, quantity = 1) =>
  api.post('/feed', { user_pokemon_id: userPokemonId, item_id: itemId, quantity });

export default api;