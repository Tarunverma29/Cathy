import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { isAuthed, loading } = useAuth()

  // Don't redirect while we're still reading localStorage
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ink-950">
        <div className="flex gap-2">
          {[0,1,2].map(i => (
            <span
              key={i}
              className="w-2 h-2 rounded-full bg-blush-400 animate-blink"
              style={{ animationDelay: `${i * 0.15}s` }}
            />
          ))}
        </div>
      </div>
    )
  }

  return isAuthed ? children : <Navigate to="/login" replace />
}
