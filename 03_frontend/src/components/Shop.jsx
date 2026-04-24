// 03_frontend/src/components/Shop.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import toast from 'react-hot-toast';

function Shop({ user, setUser }) {
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        fetchItems();
    }, []);

    const fetchItems = async () => {
        try {
            const res = await axios.get('/api/shop/items');
            setItems(res.data);
        } catch (err) {
            toast.error('Failed to load shop');
        }
    };

    const buyItem = async (itemId, price) => {
        if (user.coins < price) {
            toast.error('Not enough coins');
            return;
        }
        setLoading(true);
        try {
            const res = await axios.post('/api/shop/buy', { item_id: itemId, quantity: 1 }, {
                headers: { Authorization: localStorage.getItem('token') }
            });
            toast.success(res.data.message);
            const profileRes = await axios.get('/api/profile', {
                headers: { Authorization: localStorage.getItem('token') }
            });
            setUser(profileRes.data);
        } catch (err) {
            toast.error(err.response?.data?.message || 'Purchase failed');
        } finally {
            setLoading(false);
        }
    };

    // Determine rarity class based on item size/name/exp_value
    const getItemRarityClass = (item) => {
        const name = item.name.toLowerCase();
        if (name.includes('large') || item.exp_value > 150) return 'bg-legendary';
        if (name.includes('medium') || item.exp_value > 50) return 'bg-epic';
        return 'bg-rare'; // small or default
    };

    return (
        <div className="shop-container">
            <div className="card">
                <h2 className="card-title">Item Shop</h2>
                
                <div className="shop-info">
                    <p>Your Coins: <strong>{user.coins}</strong></p>
                </div>

                <div className="items-grid">
                    {items.map(item => (
                        <div 
                            key={item.id} 
                            className={`item-card pixel-item-card ${getItemRarityClass(item)}`}
                        >
                            <h3>{item.name}</h3>
                            <p className="item-description">{item.description}</p>
                            <div className="item-stats">
                                <p>EXP: <strong>+{item.exp_value}</strong></p>
                                <p>Price: <strong>{item.price}</strong> coins</p>
                            </div>
                            <button 
                                className="pixel-btn buy-btn"
                                onClick={() => buyItem(item.id, item.price)} 
                                disabled={loading || user.coins < item.price}
                            >
                                Buy
                            </button>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}

export default Shop;