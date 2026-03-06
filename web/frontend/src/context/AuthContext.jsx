import { createContext, useContext, useState, useCallback, useEffect } from 'react'

const AuthContext = createContext(null)

function parseToken(t) {
  try {
    const payload = JSON.parse(atob(t.split('.')[1]))
    // Check expiry
    if (payload.exp && payload.exp * 1000 < Date.now()) return null
    return { id: payload.sub, email: payload.email, username: payload.username }
  } catch {
    return null
  }
}

export function AuthProvider({ children }) {
  const [token,   setToken]   = useState(null)
  const [user,    setUser]    = useState(null)
  const [loading, setLoading] = useState(true)  // true until we've checked localStorage

  // On mount — restore session from localStorage
  useEffect(() => {
    const stored = localStorage.getItem('cathy_token')
    if (stored) {
      const parsed = parseToken(stored)
      if (parsed) {
        setToken(stored)
        setUser(parsed)
      } else {
        // Token expired — clear it
        localStorage.removeItem('cathy_token')
      }
    }
    setLoading(false)
  }, [])

  const login = useCallback((accessToken) => {
    const parsed = parseToken(accessToken)
    if (!parsed) return
    localStorage.setItem('cathy_token', accessToken)
    setToken(accessToken)
    setUser(parsed)
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('cathy_token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{
      token,
      user,
      login,
      logout,
      loading,
      isAuthed: !!token && !!user,
    }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
