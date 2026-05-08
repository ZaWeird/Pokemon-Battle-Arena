import React, { useState, useRef, useEffect } from 'react'
import api from '../services/api'

const SUGGESTIONS = [
  "Type matchups guide",
  "Team building tips",
  "How does gacha work?",
  "PvE stage guide",
  "How to level up Pokémon?",
  "Battle strategy tips"
]

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState([
    {
      role: 'bot',
      text: "Hey there, Trainer! ★ I'm Tazuna88, your Pokémon Battle Arena guide! Ask me anything about battles, team building, gacha, or game mechanics!"
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isOffline, setIsOffline] = useState(false)
  const [sessionId] = useState(() => crypto.randomUUID())
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isLoading])

  // Focus input when chat opens
  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus()
    }
  }, [isOpen])

  const sendMessage = async (text) => {
    const userMessage = text || input.trim()
    if (!userMessage || isLoading) return

    // Add user message
    setMessages(prev => [...prev, { role: 'user', text: userMessage }])
    setInput('')
    setIsLoading(true)

    try {
      const res = await api.post('/chat', {
        message: userMessage,
        session_id: sessionId
      })

      // Detect offline / fallback mode
      if (res.data.mode === 'offline' && !isOffline) {
        setIsOffline(true)
      }

      setMessages(prev => [...prev, { role: 'bot', text: res.data.response }])
    } catch (err) {
      console.error('Chat error:', err)
      setIsOffline(true)
      setMessages(prev => [
        ...prev,
        { role: 'bot', text: "Oops! I'm having trouble right now, Trainer. ★ Please try again!" }
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const handleSuggestion = (suggestion) => {
    sendMessage(suggestion)
  }

  // Show suggestions only when there's just the welcome message
  const showSuggestions = messages.length === 1

  return (
    <div className="chat-widget-container">
      {/* Chat Window */}
      {isOpen && (
        <div className="chat-window pixel-box">
          {/* Header */}
          <div className="chat-header">
            <div className="chat-header-info">
              <img src="/tazuna88.png" alt="Tazuna88" className="chat-header-avatar" />
              <div>
                <span className="chat-header-name">Tazuna88</span>
                <span className="chat-header-role">
                  {isOffline ? (
                    <>Battle Guide <span className="chat-offline-badge">OFFLINE</span></>
                  ) : (
                    'Battle Guide'
                  )}
                </span>
              </div>
            </div>
            <button
              className="chat-close-btn"
              onClick={() => setIsOpen(false)}
              aria-label="Close chat"
            >
              ✕
            </button>
          </div>

          {/* Offline Banner */}
          {isOffline && (
            <div className="chat-offline-banner">
              ♦ Running in offline mode — answers are pre-built guides
            </div>
          )}

          {/* Messages Area */}
          <div className="chat-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message chat-message-${msg.role}`}>
                {msg.role === 'bot' && (
                  <img src="/tazuna88.png" alt="" className="chat-msg-avatar" />
                )}
                <div className={`chat-bubble chat-bubble-${msg.role}`}>
                  {msg.text}
                </div>
              </div>
            ))}

            {/* Typing indicator */}
            {isLoading && (
              <div className="chat-message chat-message-bot">
                <img src="/tazuna88.png" alt="" className="chat-msg-avatar" />
                <div className="chat-bubble chat-bubble-bot chat-typing">
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                  <span className="typing-dot"></span>
                </div>
              </div>
            )}

            {/* Suggestions */}
            {showSuggestions && (
              <div className="chat-suggestions">
                {SUGGESTIONS.map((s, i) => (
                  <button
                    key={i}
                    className="chat-suggestion-chip"
                    onClick={() => handleSuggestion(s)}
                  >
                    {s}
                  </button>
                ))}
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input Area */}
          <div className="chat-input-area">
            <input
              ref={inputRef}
              type="text"
              className="chat-input"
              placeholder={isOffline ? "Ask about game topics..." : "Ask Tazuna88..."}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              disabled={isLoading}
              maxLength={500}
            />
            <button
              className="chat-send-btn"
              onClick={() => sendMessage()}
              disabled={isLoading || !input.trim()}
              aria-label="Send message"
            >
              ▶
            </button>
          </div>
        </div>
      )}

      {/* Floating Toggle Button */}
      <button
        className={`chat-toggle-btn ${isOpen ? 'chat-toggle-active' : ''}`}
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle chat guide"
        id="chat-widget-toggle"
      >
        {isOpen ? (
          <span className="chat-toggle-close">✕</span>
        ) : (
          <img src="/tazuna88.png" alt="Chat Guide" className="chat-toggle-icon" />
        )}
      </button>
    </div>
  )
}

