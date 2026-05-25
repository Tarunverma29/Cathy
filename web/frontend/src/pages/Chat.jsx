import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Send, LogOut, MessageCircle, AlertTriangle, Menu, X } from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'
import { getChats, createChat, deleteChat, getMessages } from '../api'
import { useChatSocket } from '../hooks/useChatSocket'

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-1.5 items-center px-1 py-1">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-blue-400/60 animate-blink"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  )
}

// ── Avatar ───────────────────────────────────────────────────────────────────
function Avatar({ initials, isAI }) {
  if (isAI) return (
    <div className="w-7 h-7 rounded-full bg-blue-500/20 border border-blue-400/30 flex items-center justify-center shrink-0 text-xs">
      ✦
    </div>
  )
  return (
    <div className="w-7 h-7 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center shrink-0 text-xs text-slate-300 font-mono uppercase">
      {initials?.[0] || 'U'}
    </div>
  )
}

// ── Single message bubble ────────────────────────────────────────────────────
function Bubble({ role, content, isCrisis, username }) {
  if (role === 'user') {
    return (
      <div className="flex justify-end gap-2 mb-4 animate-fade-up">
        <div className="max-w-[70%] bg-blue-600/20 border border-blue-500/25 text-slate-100 rounded-2xl rounded-br-sm px-4 py-3 font-sans text-sm leading-relaxed">
          {content}
        </div>
        <Avatar initials={username} isAI={false} />
      </div>
    )
  }
  if (isCrisis) {
    return (
      <div className="flex items-start gap-2 mb-4 animate-fade-up">
        <div className="w-7 h-7 rounded-full bg-amber-500/20 border border-amber-400/30 flex items-center justify-center shrink-0">
          <AlertTriangle size={12} className="text-amber-400" />
        </div>
        <div className="max-w-[70%] bg-amber-500/10 border border-amber-400/20 text-amber-200 rounded-2xl rounded-bl-sm px-4 py-3 font-sans text-sm leading-relaxed">
          {content}
        </div>
      </div>
    )
  }
  return (
    <div className="flex justify-start gap-2 mb-4 animate-fade-up">
      <Avatar isAI={true} />
      <div className="max-w-[70%] bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 font-sans text-sm leading-relaxed whitespace-pre-wrap">
        {content}
      </div>
    </div>
  )
}

// ── Main Chat Page ───────────────────────────────────────────────────────────
export default function Chat() {
  const { user, token, logout } = useAuth()
  const navigate    = useNavigate()
  const queryClient = useQueryClient()

  const [activeChatId, setActiveChatId] = useState(null)
  const [messages,     setMessages]     = useState([])
  const [input,        setInput]        = useState('')
  const [streaming,    setStreaming]     = useState(false)
  const [streamBuf,    setStreamBuf]    = useState('')
  const [sidebarOpen,  setSidebarOpen]  = useState(true)

  const bottomRef    = useRef(null)
  const inputRef     = useRef(null)
  // KEY FIX: keep streamBuf accessible in callbacks without stale closure
  const streamBufRef = useRef('')

  // ── Fetch chats ──────────────────────────────────────────────────────────
  const { data: chats = [], isLoading: chatsLoading } = useQuery({
    queryKey: ['chats'],
    queryFn: () => getChats().then(r => r.data),
    staleTime: 0,
    refetchOnMount: true,
  })

  // ── Auto-select first chat on load ───────────────────────────────────────
  useEffect(() => {
    if (!chatsLoading && chats.length > 0 && !activeChatId) {
      setActiveChatId(chats[0].id)
    }
  }, [chats, chatsLoading, activeChatId])

  // ── Load messages when switching chats ───────────────────────────────────
  useEffect(() => {
    if (!activeChatId) return
    setMessages([])
    setStreamBuf('')
    streamBufRef.current = ''
    setStreaming(false)
    getMessages(activeChatId)
      .then(r => setMessages(r.data.map(m => ({ ...m, isCrisis: false }))))
      .catch(console.error)
  }, [activeChatId])

  // ── Auto-scroll ──────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, streamBuf])

  // ── Create chat ──────────────────────────────────────────────────────────
  const createMut = useMutation({
    mutationFn: () => createChat('New Chat').then(r => r.data),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      setActiveChatId(data.chat_id)
      setMessages([])
      setStreamBuf('')
      streamBufRef.current = ''
    },
  })

  // ── Delete chat ──────────────────────────────────────────────────────────
  const deleteMut = useMutation({
    mutationFn: (id) => deleteChat(id),
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: ['chats'] })
      if (activeChatId === id) {
        const remaining = chats.filter(c => c.id !== id)
        setActiveChatId(remaining[0]?.id ?? null)
        setMessages([])
        streamBufRef.current = ''
      }
    },
  })

  // ── WebSocket callbacks ──────────────────────────────────────────────────
  // All use refs so socket never reconnects on callback change
  const cbRef = useRef({})

  cbRef.current.onToken = useCallback((tok) => {
    setStreaming(true)
    streamBufRef.current += tok
    setStreamBuf(streamBufRef.current)
  }, [])

  cbRef.current.onCheckIn = useCallback((content) => {
    setMessages(prev => [...prev, { role: 'assistant', content, isCrisis: true }])
  }, [])

  cbRef.current.onDone = useCallback(() => {
    // KEY FIX: read from ref, not from stale state closure
    const finalText = streamBufRef.current
    if (finalText.trim()) {
      setMessages(m => [...m, { role: 'assistant', content: finalText, isCrisis: false }])
    }
    streamBufRef.current = ''
    setStreamBuf('')
    setStreaming(false)
  }, [])

  cbRef.current.onError = useCallback((msg) => {
    console.error('WS error:', msg)
    setStreaming(false)
    streamBufRef.current = ''
    setStreamBuf('')
  }, [])

  // Stable wrappers
  const stableOnToken   = useCallback((tok)     => cbRef.current.onToken?.(tok),    [])
  const stableOnCheckIn = useCallback((content) => cbRef.current.onCheckIn?.(content), [])
  const stableOnDone    = useCallback(()        => cbRef.current.onDone?.(),         [])
  const stableOnError   = useCallback((msg)     => cbRef.current.onError?.(msg),     [])

  const { send } = useChatSocket({
    chatId:     activeChatId,
    token,
    onToken:    stableOnToken,
    onCheckIn:  stableOnCheckIn,
    onDone:     stableOnDone,
    onError:    stableOnError,
  })

  // ── Send message ─────────────────────────────────────────────────────────
  const sendMessage = useCallback(() => {
    const text = input.trim()
    if (!text || streaming) return
    setInput('')
    setMessages(prev => [...prev, { role: 'user', content: text, isCrisis: false }])
    setStreaming(true)
    streamBufRef.current = ''
    setStreamBuf('')
    send(text)
    inputRef.current?.focus()
  }, [input, streaming, send])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  const activeChat = chats.find(c => c.id === activeChatId)

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-gray-950 overflow-hidden">
      {/* Subtle grid background */}
      <div className="fixed inset-0 pointer-events-none"
        style={{
          backgroundImage: `radial-gradient(ellipse at 20% 50%, rgba(59,130,246,0.04) 0%, transparent 60%),
                            radial-gradient(ellipse at 80% 20%, rgba(99,102,241,0.04) 0%, transparent 60%)`,
        }}
      />

      {/* ── Sidebar ────────────────────────────────────────────────────── */}
      <aside className={clsx(
        'flex flex-col bg-gray-900 border-r border-gray-800 transition-all duration-300 shrink-0 relative z-10',
        sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
      )}>
        {/* Brand */}
        <div className="px-5 py-5 border-b border-gray-800">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-sm shrink-0">
              ✦
            </div>
            <div>
              <span className="font-semibold text-slate-100 text-base tracking-tight">Companion</span>
              <div className="flex items-center gap-1.5 mt-0.5">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs text-slate-500">Online</span>
              </div>
            </div>
          </div>
        </div>

        {/* New chat button */}
        <div className="px-3 py-3">
          <button
            onClick={() => createMut.mutate()}
            disabled={createMut.isPending}
            className="flex items-center gap-2 w-full text-sm text-slate-400 hover:text-slate-200 hover:bg-gray-800 rounded-lg px-3 py-2.5 transition-all border border-transparent hover:border-gray-700"
          >
            <Plus size={14} />
            {createMut.isPending ? 'Creating…' : 'New conversation'}
          </button>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto px-2 space-y-0.5 pb-2">
          {chatsLoading && (
            <p className="text-slate-600 text-xs px-3 py-4 text-center">Loading…</p>
          )}
          {!chatsLoading && chats.length === 0 && (
            <p className="text-slate-600 text-xs px-3 py-4 text-center">No conversations yet</p>
          )}
          {chats.map(chat => (
            <div
              key={chat.id}
              className={clsx(
                'group flex items-center justify-between rounded-lg px-3 py-2.5 cursor-pointer transition-all',
                activeChatId === chat.id
                  ? 'bg-blue-600/15 text-slate-100 border border-blue-500/20'
                  : 'text-slate-400 hover:bg-gray-800 hover:text-slate-200 border border-transparent'
              )}
              onClick={() => setActiveChatId(chat.id)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <MessageCircle size={13} className="shrink-0 opacity-50" />
                <span className="text-sm truncate">{chat.title}</span>
              </div>
              <button
                className="opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity p-0.5 shrink-0 text-slate-500 hover:text-red-400"
                onClick={e => { e.stopPropagation(); deleteMut.mutate(chat.id) }}
              >
                <Trash2 size={12} />
              </button>
            </div>
          ))}
        </div>

        {/* User footer */}
        <div className="px-3 py-3 border-t border-gray-800">
          <div className="flex items-center justify-between px-1">
            <div className="flex items-center gap-2">
              <div className="w-6 h-6 rounded-full bg-slate-700 border border-slate-600 flex items-center justify-center text-xs text-slate-300 uppercase">
                {user?.username?.[0] || 'U'}
              </div>
              <span className="text-slate-400 text-xs truncate">{user?.username}</span>
            </div>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="text-slate-600 hover:text-red-400 transition-colors p-1"
              title="Sign out"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* ── Chat area ──────────────────────────────────────────────────── */}
      <div className="flex flex-col flex-1 min-w-0 relative">

        {/* Header */}
        <header className="flex items-center gap-3 px-5 py-3.5 border-b border-gray-800 shrink-0 bg-gray-950/80 backdrop-blur-sm relative z-10">
          <button
            onClick={() => setSidebarOpen(o => !o)}
            className="text-slate-500 hover:text-slate-300 transition-colors p-1 rounded-md hover:bg-gray-800"
          >
            {sidebarOpen ? <X size={16} /> : <Menu size={16} />}
          </button>
          <div className="flex items-center gap-2.5">
            <div className="w-7 h-7 rounded-lg bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-xs">
              ✦
            </div>
            <div>
              <span className="text-slate-200 text-sm font-medium">
                {activeChat?.title || 'Select a conversation'}
              </span>
            </div>
          </div>
          <div className="ml-auto flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span className="text-xs text-slate-600 font-mono">connected</span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {!activeChatId ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center animate-fade-up max-w-xs">
                <div className="w-16 h-16 rounded-2xl bg-blue-500/10 border border-blue-400/20 flex items-center justify-center mx-auto mb-5 text-2xl">
                  ✦
                </div>
                <p className="text-slate-200 text-lg font-semibold mb-2">Start a conversation</p>
                <p className="text-slate-500 text-sm mb-6">
                  Create a new chat or select one from the sidebar
                </p>
                <button onClick={() => createMut.mutate()} className="bg-blue-600 hover:bg-blue-500 text-white text-sm px-5 py-2.5 rounded-xl transition-all active:scale-95 font-medium">
                  New conversation
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Greeting only when chat is empty */}
              {messages.length === 0 && !streaming && !streamBuf && (
                <div className="flex justify-start gap-2 mb-4 animate-fade-up">
                  <Avatar isAI={true} />
                  <div className="max-w-[70%] bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 font-sans text-sm leading-relaxed">
                    Hey — good to see you. What's on your mind?
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <Bubble key={i} username={user?.username} {...msg} />
              ))}

              {/* Live streaming bubble */}
              {streamBuf && (
                <div className="flex justify-start gap-2 mb-4 animate-fade-up">
                  <Avatar isAI={true} />
                  <div className="max-w-[70%] bg-slate-800/80 border border-slate-700/50 text-slate-200 rounded-2xl rounded-bl-sm px-4 py-3 font-sans text-sm leading-relaxed whitespace-pre-wrap">
                    {streamBuf}
                    <span className="inline-block w-0.5 h-3.5 bg-blue-400 ml-0.5 animate-blink" />
                  </div>
                </div>
              )}

              {/* Waiting for first token */}
              {streaming && !streamBuf && (
                <div className="flex justify-start gap-2 mb-4">
                  <Avatar isAI={true} />
                  <div className="bg-slate-800/80 border border-slate-700/50 rounded-2xl rounded-bl-sm px-4 py-3">
                    <TypingDots />
                  </div>
                </div>
              )}

              <div ref={bottomRef} />
            </>
          )}
        </div>

        {/* Input */}
        {activeChatId && (
          <div className="px-5 py-4 border-t border-gray-800 shrink-0 bg-gray-950/80 backdrop-blur-sm">
            <div className="flex items-end gap-3 max-w-3xl mx-auto">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  rows={1}
                  className="w-full bg-gray-900 border border-gray-700 text-slate-100 rounded-xl px-4 py-3 text-sm placeholder-slate-600 focus:outline-none focus:border-blue-500/50 focus:ring-1 focus:ring-blue-500/20 transition-all resize-none leading-relaxed"
                  style={{ minHeight: '48px', maxHeight: '144px' }}
                  placeholder="Type a message…"
                  value={input}
                  onChange={e => {
                    setInput(e.target.value)
                    e.target.style.height = 'auto'
                    e.target.style.height = e.target.scrollHeight + 'px'
                  }}
                  onKeyDown={handleKey}
                  disabled={streaming}
                />
              </div>
              <button
                onClick={sendMessage}
                disabled={!input.trim() || streaming}
                className={clsx(
                  'p-3 rounded-xl transition-all duration-200 shrink-0',
                  input.trim() && !streaming
                    ? 'bg-blue-600 hover:bg-blue-500 text-white active:scale-95 shadow-lg shadow-blue-500/20'
                    : 'bg-gray-800 text-slate-600 cursor-not-allowed'
                )}
              >
                <Send size={16} />
              </button>
            </div>
            <p className="text-center text-slate-700 text-xs mt-2 font-mono">
              Enter ↵ to send · Shift+Enter for new line
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
