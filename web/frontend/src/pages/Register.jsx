import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { register as apiRegister } from '../api'

export default function Register() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [err,  setErr]  = useState('')
  const [loading, setLoading] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setErr('')
    if (form.password.length < 6) { setErr('Password must be at least 6 characters'); return }
    setLoading(true)
    try {
      const { data } = await apiRegister(form)
      login(data.access_token)
      navigate('/')
    } catch (e) {
      setErr(e.response?.data?.detail || 'Something went wrong')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4">
      <div className="grain" />
      <div className="fixed inset-0 bg-gradient-to-br from-ink-950 via-ink-900 to-ink-950" />
      <div className="fixed inset-0 opacity-20"
        style={{ backgroundImage: 'radial-gradient(circle at 70% 30%, #d45a4820 0%, transparent 60%), radial-gradient(circle at 30% 70%, #4a714220 0%, transparent 60%)' }} />

      <div className="relative w-full max-w-sm animate-fade-up">
        <div className="text-center mb-10">
          <div className="w-14 h-14 rounded-full bg-sage-400/20 border border-sage-300/30
                          flex items-center justify-center mx-auto mb-5">
            <span className="text-2xl">✨</span>
          </div>
          <h1 className="font-display text-3xl text-ink-100 mb-1">Meet Cathy</h1>
          <p className="text-ink-400 text-sm font-sans">Create your account to begin</p>
        </div>

        <form onSubmit={submit} className="space-y-4">
          <div>
            <label className="block text-xs text-ink-400 uppercase tracking-widest mb-2">Email</label>
            <input
              type="email"
              className="input-field font-sans"
              placeholder="you@example.com"
              value={form.email}
              onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
              required
            />
          </div>

          <div>
            <label className="block text-xs text-ink-400 uppercase tracking-widest mb-2">Name</label>
            <input
              type="text"
              className="input-field font-sans"
              placeholder="What should she call you?"
              value={form.username}
              onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
              required
            />
          </div>

          <div>
            <label className="block text-xs text-ink-400 uppercase tracking-widest mb-2">Password</label>
            <input
              type="password"
              className="input-field font-sans"
              placeholder="••••••••"
              value={form.password}
              onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
              required
            />
          </div>

          {err && (
            <p className="text-blush-300 text-sm text-center bg-blush-500/10 rounded-lg px-3 py-2">
              {err}
            </p>
          )}

          <button type="submit" className="btn-primary w-full mt-2" disabled={loading}>
            {loading ? 'Creating account…' : 'Get started'}
          </button>
        </form>

        <p className="text-center text-ink-400 text-sm mt-8 font-sans">
          Already have an account?{' '}
          <Link to="/login" className="text-blush-300 hover:text-blush-200 transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  )
}
