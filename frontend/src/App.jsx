import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import Auth from './components/Auth'
import Gacha from './components/Gacha'
import Inventory from './components/Inventory'
import TeamBuilder from './components/TeamBuilder'
import Battle from './components/Battle'
import Lobby from './components/Lobby'
import Leaderboard from './components/Leaderboard'
import './App.css'

function App() {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const token = localStorage.getItem('token')
    const savedUser = localStorage.getItem('user')
    if (token && savedUser) {
      setUser(JSON.parse(savedUser))
    }
    setLoading(false)
  }, [])

  const handleLogin = (userData, token) => {
    setUser(userData)
    localStorage.setItem('token', token)
    localStorage.setItem('user', JSON.stringify(userData))
  }

  const handleLogout = () => {
    setUser(null)
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  if (loading) {
    return <div className="loading">Loading...</div>
  }

  return (
    <Router>
      <div className="app">
        <Toaster position="top-right" />
        
        {user && (
          <nav className="navbar">
            <div className="nav-brand">Pokémon Battle Arena</div>
            <div className="nav-menu">
              <a href="/lobby">Lobby</a>
              <a href="/gacha">Gacha</a>
              <a href="/inventory">Inventory</a>
              <a href="/team">Team Builder</a>
              <a href="/leaderboard">Leaderboard</a>
            </div>
            <div className="nav-user">
              <span>{user.username}</span>
              <span className="coins">💰 {user.coins}</span>
              <button onClick={handleLogout} className="btn-logout">Logout</button>
            </div>
          </nav>
        )}

        <div className="container">
          <Routes>
            <Route path="/" element={
              user ? <Navigate to="/lobby" /> : <Auth onLogin={handleLogin} />
            } />
            <Route path="/lobby" element={
              user ? <Lobby user={user} /> : <Navigate to="/" />
            } />
            <Route path="/gacha" element={
              user ? <Gacha user={user} setUser={setUser} /> : <Navigate to="/" />
            } />
            <Route path="/inventory" element={
              user ? <Inventory user={user} /> : <Navigate to="/" />
            } />
            <Route path="/team" element={
              user ? <TeamBuilder user={user} /> : <Navigate to="/" />
            } />
            <Route path="/battle/:roomId" element={
              user ? <Battle user={user} /> : <Navigate to="/" />
            } />
            <Route path="/leaderboard" element={
              user ? <Leaderboard /> : <Navigate to="/" />
            } />
          </Routes>
        </div>
      </div>
    </Router>
  )
}

export default App