import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, Trash2, Send, LogOut, MessageCircle, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'
import { useAuth } from '../context/AuthContext'
import { getChats, createChat, deleteChat, getMessages } from '../api'
import { useChatSocket } from '../hooks/useChatSocket'

// ── Typing indicator ─────────────────────────────────────────────────────────
function TypingDots() {
  return (
    <div className="flex gap-1 items-center px-1 py-1">
      {[0, 1, 2].map(i => (
        <span
          key={i}
          className="w-1.5 h-1.5 rounded-full bg-ink-400 animate-blink"
          style={{ animationDelay: `${i * 0.2}s` }}
        />
      ))}
    </div>
  )
}

// ── Single message bubble ────────────────────────────────────────────────────
function Bubble({ role, content, isCrisis }) {
  if (role === 'user') {
    return (
      <div className="flex justify-end mb-3 animate-fade-up">
        <div className="msg-user font-sans text-sm leading-relaxed">{content}</div>
      </div>
    )
  }
  if (isCrisis) {
    return (
      <div className="flex items-start gap-2 mb-3 animate-fade-up">
        <AlertTriangle size={14} className="text-blush-400 mt-1 shrink-0" />
        <div className="msg-crisis font-sans text-sm leading-relaxed">{content}</div>
      </div>
    )
  }
  return (
    <div className="flex justify-start mb-3 animate-fade-up">
      <div className="msg-cathy font-sans text-sm leading-relaxed whitespace-pre-wrap">{content}</div>
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

  const bottomRef = useRef(null)
  const inputRef  = useRef(null)

  // ── Fetch chats ──────────────────────────────────────────────────────────
  const { data: chats = [], isLoading: chatsLoading } = useQuery({
    queryKey: ['chats'],
    queryFn: () => getChats().then(r => r.data),
    staleTime: 0,           // always fetch fresh on mount
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
      }
    },
  })

  // ── WebSocket callbacks (stable refs — never cause reconnect) ────────────
  // Using refs so the socket hook doesn't reconnect when these change
  const onTokenRef   = useRef(null)
  const onCheckInRef = useRef(null)
  const onDoneRef    = useRef(null)
  const onErrorRef   = useRef(null)

  onTokenRef.current = useCallback((tok) => {
    // tok is a streaming chunk — just append it
    setStreaming(true)
    setStreamBuf(prev => prev + tok)
  }, [])

  onCheckInRef.current = useCallback((content) => {
    setMessages(prev => [...prev, { role: 'assistant', content, isCrisis: true }])
  }, [])

  onDoneRef.current = useCallback(() => {
    // Stream finished — move buffer into messages
    setStreamBuf(prev => {
      if (prev.trim()) {
        setMessages(m => [...m, { role: 'assistant', content: prev, isCrisis: false }])
      }
      return ''
    })
    setStreaming(false)
  }, [])

  onErrorRef.current = useCallback((msg) => {
    console.error('WS error:', msg)
    setStreaming(false)
    setStreamBuf('')
  }, [])

  // Stable wrappers that delegate to the current ref
  const stableOnToken   = useCallback((tok)     => onTokenRef.current?.(tok),   [])
  const stableOnCheckIn = useCallback((content) => onCheckInRef.current?.(content), [])
  const stableOnDone    = useCallback(()        => onDoneRef.current?.(),        [])
  const stableOnError   = useCallback((msg)     => onErrorRef.current?.(msg),    [])

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
    setStreamBuf('')
    send(text)
    inputRef.current?.focus()
  }, [input, streaming, send])

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage() }
  }

  // ── Render ───────────────────────────────────────────────────────────────
  return (
    <div className="flex h-screen bg-ink-950 overflow-hidden">
      <div className="grain" />

      {/* Sidebar */}
      <aside className={clsx(
        'flex flex-col bg-ink-900 border-r border-ink-700 transition-all duration-300 shrink-0',
        sidebarOpen ? 'w-64' : 'w-0 overflow-hidden'
      )}>
        {/* Brand */}
        <div className="px-5 py-5 border-b border-ink-700">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blush-500/20 border border-blush-400/30
                            flex items-center justify-center text-base shrink-0">
              🌸
            </div>
            <span className="font-display text-lg text-ink-100">Cathy</span>
          </div>
        </div>

        {/* New chat */}
        <div className="px-3 py-3">
          <button
            onClick={() => createMut.mutate()}
            disabled={createMut.isPending}
            className="flex items-center gap-2 w-full btn-ghost text-sm justify-start"
          >
            <Plus size={15} />
            {createMut.isPending ? 'Creating…' : 'New conversation'}
          </button>
        </div>

        {/* Chat list */}
        <div className="flex-1 overflow-y-auto px-2 space-y-0.5">
          {chatsLoading && (
            <p className="text-ink-500 text-xs px-3 py-4 text-center">Loading…</p>
          )}

          {!chatsLoading && chats.length === 0 && (
            <p className="text-ink-500 text-xs px-3 py-4 text-center">
              No conversations yet
            </p>
          )}

          {chats.map(chat => (
            <div
              key={chat.id}
              className={clsx(
                'group flex items-center justify-between rounded-lg px-3 py-2.5 cursor-pointer transition-all',
                activeChatId === chat.id
                  ? 'bg-ink-700 text-ink-100'
                  : 'text-ink-300 hover:bg-ink-800 hover:text-ink-100'
              )}
              onClick={() => setActiveChatId(chat.id)}
            >
              <div className="flex items-center gap-2 min-w-0">
                <MessageCircle size={13} className="shrink-0 opacity-60" />
                <span className="text-sm truncate">{chat.title}</span>
              </div>
              <button
                className="opacity-0 group-hover:opacity-60 hover:!opacity-100 transition-opacity p-0.5 shrink-0"
                onClick={e => { e.stopPropagation(); deleteMut.mutate(chat.id) }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>

        {/* User footer */}
        <div className="px-3 py-3 border-t border-ink-700">
          <div className="flex items-center justify-between">
            <span className="text-ink-400 text-xs truncate">{user?.username}</span>
            <button
              onClick={() => { logout(); navigate('/login') }}
              className="text-ink-500 hover:text-blush-300 transition-colors p-1"
              title="Sign out"
            >
              <LogOut size={14} />
            </button>
          </div>
        </div>
      </aside>

      {/* Chat area */}
      <div className="flex flex-col flex-1 min-w-0">

        {/* Header */}
        <header className="flex items-center gap-3 px-5 py-4 border-b border-ink-800 shrink-0">
          <button
            onClick={() => setSidebarOpen(o => !o)}
            className="text-ink-500 hover:text-ink-200 transition-colors"
          >
            <div className="flex flex-col gap-1">
              {[0,1,2].map(i => (
                <span key={i} className="block w-4 h-px bg-current" />
              ))}
            </div>
          </button>
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-sage-400 animate-pulse" />
            <span className="font-display text-ink-200 text-base">
              {chats.find(c => c.id === activeChatId)?.title || 'Cathy'}
            </span>
          </div>
        </header>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {!activeChatId ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center animate-fade-up">
                <div className="text-5xl mb-4">🌸</div>
                <p className="font-display text-xl text-ink-300 mb-2">Start a conversation</p>
                <p className="text-ink-500 text-sm font-sans">
                  Create a new chat or select one from the sidebar
                </p>
                <button onClick={() => createMut.mutate()} className="btn-primary mt-6 text-sm">
                  New conversation
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* Greeting only when chat is empty and not streaming */}
              {messages.length === 0 && !streaming && !streamBuf && (
                <div className="flex justify-start mb-3 animate-fade-up">
                  <div className="msg-cathy font-sans text-sm leading-relaxed">
                    Hey… it's good to see you. What's on your mind?
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <Bubble key={i} {...msg} />
              ))}

              {/* Live streaming bubble */}
              {streamBuf && (
                <div className="flex justify-start mb-3 animate-fade-up">
                  <div className="msg-cathy font-sans text-sm leading-relaxed whitespace-pre-wrap">
                    {streamBuf}
                    <span className="inline-block w-0.5 h-3.5 bg-ink-400 ml-0.5 animate-blink" />
                  </div>
                </div>
              )}

              {/* Waiting for first token */}
              {streaming && !streamBuf && (
                <div className="flex justify-start mb-3">
                  <div className="msg-cathy">
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
          <div className="px-5 py-4 border-t border-ink-800 shrink-0">
            <div className="flex items-end gap-3 max-w-2xl mx-auto">
              <textarea
                ref={inputRef}
                rows={1}
                className="input-field font-sans text-sm resize-none leading-relaxed"
                style={{ minHeight: '48px', maxHeight: '144px' }}
                placeholder="Say something…"
                value={input}
                onChange={e => {
                  setInput(e.target.value)
                  e.target.style.height = 'auto'
                  e.target.style.height = e.target.scrollHeight + 'px'
                }}
                onKeyDown={handleKey}
                disabled={streaming}
              />
              <button
                onClick={sendMessage}
                disabled={!input.trim() || streaming}
                className={clsx(
                  'p-3 rounded-xl transition-all duration-200 shrink-0',
                  input.trim() && !streaming
                    ? 'bg-blush-500 hover:bg-blush-400 text-white active:scale-95'
                    : 'bg-ink-700 text-ink-500 cursor-not-allowed'
                )}
              >
                <Send size={16} />
              </button>
            </div>
            <p className="text-center text-ink-600 text-xs mt-2 font-sans">
              Enter to send · Shift+Enter for new line
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
