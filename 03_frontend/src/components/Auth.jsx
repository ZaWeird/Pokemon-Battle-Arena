import React, { useState } from 'react'
import axios from 'axios'
import toast from 'react-hot-toast'

function Auth({ onLogin }) {
  const [isLogin, setIsLogin] = useState(true)
  const [loading, setLoading] = useState(false)
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: ''
  })

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    })
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    if (!isLogin && formData.password !== formData.confirmPassword) {
      toast.error('Passwords do not match')
      return
    }

    setLoading(true)
    
    try {
      const endpoint = isLogin ? '/api/login' : '/api/register'
      const payload = isLogin 
        ? { username: formData.username, password: formData.password }
        : { username: formData.username, email: formData.email, password: formData.password }
      
      console.log('Sending request to:', endpoint)
      console.log('Payload:', payload)
      
      const response = await axios.post(endpoint, payload, {
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log('Response:', response.data)
      
      if (response.data.token && response.data.user) {
        onLogin(response.data.user, response.data.token)
        toast.success(isLogin ? 'Welcome back!' : 'Account created successfully!')
      } else {
        toast.error('Invalid response from server')
      }
    } catch (error) {
      console.error('API Error:', error)
      console.error('Response:', error.response)
      
      if (error.response) {
        toast.error(error.response.data?.message || 'Server error')
      } else if (error.request) {
        toast.error('Cannot connect to server. Make sure backend is running on port 5000')
      } else {
        toast.error(error.message || 'An error occurred')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="auth-container">
      <div className="auth-tabs">
        <button 
          className={`auth-tab ${isLogin ? 'active' : ''}`}
          onClick={() => setIsLogin(true)}
        >
          Login
        </button>
        <button 
          className={`auth-tab ${!isLogin ? 'active' : ''}`}
          onClick={() => setIsLogin(false)}
        >
          Register
        </button>
      </div>

      <form onSubmit={handleSubmit} className="auth-form">
        <div className="form-group">
          <label htmlFor="username">Username</label>
          <input
            type="text"
            id="username"
            name="username"
            value={formData.username}
            onChange={handleChange}
            required
            minLength={3}
            maxLength={50}
          />
        </div>

        {!isLogin && (
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              type="email"
              id="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
        )}

        <div className="form-group">
          <label htmlFor="password">Password</label>
          <input
            type="password"
            id="password"
            name="password"
            value={formData.password}
            onChange={handleChange}
            required
            minLength={6}
          />
        </div>

        {!isLogin && (
          <div className="form-group">
            <label htmlFor="confirmPassword">Confirm Password</label>
            <input
              type="password"
              id="confirmPassword"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleChange}
              required
            />
          </div>
        )}

        <button type="submit" className="btn-primary" disabled={loading}>
          {loading ? 'Please wait...' : (isLogin ? 'Login' : 'Register')}
        </button>
      </form>
    </div>
  )
}

export default Auth