import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import { register as apiRegister } from '../api'
import { Eye, EyeOff, Check } from 'lucide-react'

export default function Register() {
  const { login } = useAuth()
  const navigate  = useNavigate()
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const [err,  setErr]  = useState('')
  const [loading, setLoading] = useState(false)
  const [showPw, setShowPw]   = useState(false)

  const pwStrength = (() => {
    const p = form.password
    if (!p) return 0
    let s = 0
    if (p.length >= 6) s++
    if (p.length >= 10) s++
    if (/[A-Z]/.test(p) && /[0-9]/.test(p)) s++
    return s
  })()

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
    <div className="min-h-screen flex items-center justify-center px-4 bg-gray-950 relative overflow-hidden">
      {/* Background glows */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-indigo-600/6 rounded-full blur-3xl" />
        <div className="absolute bottom-1/3 left-1/4 w-96 h-96 bg-blue-600/6 rounded-full blur-3xl" />
      </div>

      <div className="relative w-full max-w-sm">
        <div className="bg-gray-900 border border-gray-800 rounded-2xl p-8 shadow-2xl">
          {/* Header */}
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-xl bg-indigo-500/15 border border-indigo-400/25 flex items-center justify-center mx-auto mb-4">
              <span className="text-lg">✦</span>
            </div>
            <h1 className="text-xl font-semibold text-slate-100 mb-1">Create account</h1>
            <p className="text-slate-500 text-sm">Join and start a conversation</p>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-widest mb-1.5 font-mono">
                Email
              </label>
              <input
                type="email"
                className="w-full bg-gray-950 border border-gray-700 text-slate-200 rounded-xl px-4 py-3 text-sm placeholder-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all"
                placeholder="you@example.com"
                value={form.email}
                onChange={e => setForm(p => ({ ...p, email: e.target.value }))}
                required
              />
            </div>

            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-widest mb-1.5 font-mono">
                Name
              </label>
              <input
                type="text"
                className="w-full bg-gray-950 border border-gray-700 text-slate-200 rounded-xl px-4 py-3 text-sm placeholder-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all"
                placeholder="What should she call you?"
                value={form.username}
                onChange={e => setForm(p => ({ ...p, username: e.target.value }))}
                required
              />
            </div>

            <div>
              <label className="block text-xs text-slate-500 uppercase tracking-widest mb-1.5 font-mono">
                Password
              </label>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  className="w-full bg-gray-950 border border-gray-700 text-slate-200 rounded-xl px-4 py-3 pr-10 text-sm placeholder-slate-700 focus:outline-none focus:border-blue-500/60 focus:ring-1 focus:ring-blue-500/20 transition-all"
                  placeholder="••••••••"
                  value={form.password}
                  onChange={e => setForm(p => ({ ...p, password: e.target.value }))}
                  required
                />
                <button
                  type="button"
                  onClick={() => setShowPw(s => !s)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-600 hover:text-slate-400 transition-colors"
                >
                  {showPw ? <EyeOff size={15} /> : <Eye size={15} />}
                </button>
              </div>
              {/* Password strength */}
              {form.password && (
                <div className="flex gap-1 mt-2">
                  {[1, 2, 3].map(level => (
                    <div
                      key={level}
                      className={`h-0.5 flex-1 rounded-full transition-all ${
                        pwStrength >= level
                          ? level === 1 ? 'bg-red-500' : level === 2 ? 'bg-yellow-500' : 'bg-emerald-500'
                          : 'bg-gray-700'
                      }`}
                    />
                  ))}
                </div>
              )}
            </div>

            {err && (
              <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2.5">
                <p className="text-red-400 text-sm text-center">{err}</p>
              </div>
            )}

            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-xl px-6 py-3 text-sm transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed mt-2"
              disabled={loading}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Creating account…
                </span>
              ) : 'Get started'}
            </button>
          </form>

          <p className="text-center text-slate-600 text-sm mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-blue-400 hover:text-blue-300 transition-colors">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}
