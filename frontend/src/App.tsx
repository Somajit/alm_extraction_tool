import React, { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Login from './pages/Login'
import Home from './pages/Home'
import AdminDashboard from './pages/AdminDashboard'

const App: React.FC = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [userRole, setUserRole] = useState<string>('')

  useEffect(() => {
    // Check if user is already logged in
    const user = localStorage.getItem('user')
    const role = localStorage.getItem('role')
    const domain = localStorage.getItem('domain')
    const project = localStorage.getItem('project')
    
    if (user && role && domain && project) {
      setIsAuthenticated(true)
      setUserRole(role)
    }
  }, [])

  const handleLogin = (role: string) => {
    setIsAuthenticated(true)
    setUserRole(role)
    localStorage.setItem('role', role)
  }

  const handleLogout = () => {
    setIsAuthenticated(false)
    setUserRole('')
    localStorage.removeItem('user')
    localStorage.removeItem('role')
    localStorage.removeItem('domain')
    localStorage.removeItem('project')
    localStorage.removeItem('project_group')
  }

  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />
  }

  return (
    <Router>
      <Routes>
        {/* Admin routes */}
        {userRole === 'admin' ? (
          <>
            <Route path="/admin" element={<AdminDashboard onLogout={handleLogout} />} />
            <Route path="*" element={<Navigate to="/admin" replace />} />
          </>
        ) : (
          /* Regular user routes */
          <>
            <Route path="/home" element={<Home onLogout={handleLogout} />} />
            <Route path="*" element={<Navigate to="/home" replace />} />
          </>
        )}
      </Routes>
    </Router>
  )
}

export default App
