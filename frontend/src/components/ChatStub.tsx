import { useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'
import { loadChatHistory, sendChat, type ChatHistoryItem } from '../api'
import { useAuth } from '../auth'
import { useShop } from '../shop'

type Bubble = { role: 'user' | 'assistant'; content: string }

function productIdFromPath(pathname: string): string | null {
  const match = pathname.match(/^\/products\/([^/]+)$/)
  return match ? decodeURIComponent(match[1]) : null
}

export default function ChatWidget() {
  const { user } = useAuth()
  const { setSpotlight } = useShop()
  const location = useLocation()
  const productId = productIdFromPath(location.pathname)
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [suggestions, setSuggestions] = useState<string[]>([])
  const [messages, setMessages] = useState<Bubble[]>([
    {
      role: 'assistant',
      content: 'Ask about hoodies, prices, or stock by size — I’ll pull answers from the catalogue.',
    },
  ])
  const scroller = useRef<HTMLDivElement>(null)

  useEffect(() => {
    scroller.current?.scrollTo({ top: scroller.current.scrollHeight, behavior: 'smooth' })
  }, [messages, open])

  useEffect(() => {
    if (!user) return
    loadChatHistory(user.id)
      .then((rows: ChatHistoryItem[]) => {
        if (!rows.length) return
        setMessages(
          rows.map((r) => ({
            role: r.role === 'user' ? 'user' : 'assistant',
            content: r.content,
          })),
        )
        const lastProducts = [...rows].reverse().find((r) => r.products?.length)?.products
        if (lastProducts?.length) setSpotlight(lastProducts)
      })
      .catch(() => {
        /* history is best-effort */
      })
  }, [user, setSpotlight])

  async function submit(text: string) {
    const message = text.trim()
    if (!message || busy) return
    setError('')
    setBusy(true)
    setDraft('')
    setMessages((m) => [...m, { role: 'user', content: message }])
    try {
      const pageProductName =
        typeof document !== 'undefined'
          ? document.querySelector('.detail h1')?.textContent ?? null
          : null
      const res = await sendChat({
        message,
        user_id: user?.id ?? null,
        page: {
          path: location.pathname,
          product_id: productId ?? null,
          product_name: pageProductName,
        },
      })
      setMessages((m) => [...m, { role: 'assistant', content: res.reply }])
      if (res.products?.length) setSpotlight(res.products)
      setSuggestions(res.suggestions ?? [])
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Chat failed')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={`chat-stub ${open ? 'open' : ''}`}>
      {open ? (
        <div className="chat-panel">
          <header>
            <strong>Campus Customs chat</strong>
            <button type="button" onClick={() => setOpen(false)} aria-label="Close chat">
              ×
            </button>
          </header>
          <div className="chat-body" ref={scroller}>
            {user ? (
              <p className="muted tiny">Signed in as {user.first_name} — history saves for you.</p>
            ) : (
              <p className="muted tiny">Guest mode — create an account to keep chat history.</p>
            )}
            {messages.map((m, i) => (
              <div key={`${m.role}-${i}`} className={`bubble ${m.role}`}>
                {m.content}
              </div>
            ))}
            {error ? <p className="form-error">{error}</p> : null}
            {suggestions.length ? (
              <div className="chip-row">
                {suggestions.map((s) => (
                  <button key={s} type="button" className="chip" onClick={() => submit(s)}>
                    {s}
                  </button>
                ))}
              </div>
            ) : null}
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              void submit(draft)
            }}
          >
            <input
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              placeholder={busy ? 'Thinking…' : 'Ask about merch'}
              disabled={busy}
            />
            <button type="submit" disabled={busy || !draft.trim()}>
              Send
            </button>
          </form>
        </div>
      ) : (
        <button type="button" className="chat-fab" onClick={() => setOpen(true)}>
          Chat
        </button>
      )}
    </div>
  )
}
