import { useRef, useCallback, useEffect } from 'react'

// Use wss:// on https pages, ws:// on http
const WS_PROTOCOL = window.location.protocol === 'https:' ? 'wss' : 'ws'
const WS_BASE = `${WS_PROTOCOL}://${window.location.host}`

export function useChatSocket({ chatId, token, onToken, onCheckIn, onDone, onError }) {
  const wsRef    = useRef(null)
  const readyRef = useRef(false)
  const queueRef = useRef([])

  // Keep latest callbacks in refs so reconnect doesn't trigger on callback change
  const cbRef = useRef({})
  cbRef.current = { onToken, onCheckIn, onDone, onError }

  const flush = useCallback(() => {
    while (queueRef.current.length && readyRef.current && wsRef.current?.readyState === 1) {
      wsRef.current.send(queueRef.current.shift())
    }
  }, [])

  const connect = useCallback(() => {
    if (!chatId || !token) return

    // Close existing connection cleanly
    if (wsRef.current && wsRef.current.readyState < 2) {
      wsRef.current.onclose = null  // prevent old onclose from firing
      wsRef.current.close()
    }

    readyRef.current = false
    const ws = new WebSocket(`${WS_BASE}/api/chat/ws/${chatId}`)
    wsRef.current = ws

    ws.onopen = () => {
      // First message must be auth token
      ws.send(JSON.stringify({ token }))
    }

    ws.onmessage = (e) => {
      let msg
      try { msg = JSON.parse(e.data) }
      catch { return }

      const { onToken, onCheckIn, onDone, onError } = cbRef.current

      switch (msg.type) {
        case 'ready':
          readyRef.current = true
          flush()
          break

        case 'stream_start':
          // Just signals streaming is beginning — no content yet, do nothing
          break

        case 'stream':
          // Individual token chunk from Ollama
          if (msg.content) onToken?.(msg.content)
          break

        case 'stream_end':
          // Ollama finished generating
          onDone?.()
          break

        case 'message':
          // Full message (used for crisis responses — not streamed)
          onToken?.(msg.content)
          onDone?.()
          break

        case 'checkin':
          onCheckIn?.(msg.content)
          break

        case 'error':
          onError?.(msg.content)
          break
      }
    }

    ws.onerror = () => {
      cbRef.current.onError?.('Connection error — retrying…')
    }

    ws.onclose = () => {
      readyRef.current = false
    }
  }, [chatId, token, flush])  // only reconnects when chatId or token changes

  const send = useCallback((message) => {
    const payload = JSON.stringify({ message })

    if (readyRef.current && wsRef.current?.readyState === 1) {
      wsRef.current.send(payload)
    } else {
      // Queue the message and reconnect if needed
      queueRef.current.push(payload)
      if (!wsRef.current || wsRef.current.readyState > 1) {
        connect()
      }
    }
  }, [connect])

  // Connect when chatId changes, disconnect on unmount
  useEffect(() => {
    connect()
    return () => {
      if (wsRef.current) {
        wsRef.current.onclose = null
        wsRef.current.close()
      }
    }
  }, [connect])

  return { send }
}
