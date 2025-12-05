import React, { useState, useEffect } from 'react'
import Login from './pages/Login'
import Home from './pages/Home'

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Check if user is already logged in
    const user = localStorage.getItem('user')
    const domain = localStorage.getItem('domain')
    const project = localStorage.getItem('project')
    if (user && domain && project) {
      setIsAuthenticated(true)
    }
  }, [])

  const handleLogin = () => {
    setIsAuthenticated(true)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    localStorage.removeItem('user')
    localStorage.removeItem('domain')
    localStorage.removeItem('project')
  }

  return isAuthenticated ? (
    <Home onLogout={handleLogout} />
  ) : (
    <Login onLogin={handleLogin} />
  )
}

export default App
