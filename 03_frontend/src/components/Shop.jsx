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
            // Refresh user data
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

    return (
        <div className="shop-container">
            <h2>Item Shop</h2>
            <div className="items-grid">
                {items.map(item => (
                    <div key={item.id} className="item-card">
                        <h3>{item.name}</h3>
                        <p>{item.description}</p>
                        <p>EXP: +{item.exp_value}</p>
                        <p>Price: {item.price} coins</p>
                        <button onClick={() => buyItem(item.id, item.price)} disabled={loading}>
                            Buy
                        </button>
                    </div>
                ))}
            </div>
        </div>
    );
}

export default Shop;