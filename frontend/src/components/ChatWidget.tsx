import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  chatResultsUrl,
  clearChatHistory,
  fetchChatHistory,
  formatPrice,
  sendChat,
  type ChatProductCard,
  type ChatTurn,
  type PageUpdate,
  type User,
} from '../api'
import { currentPageContext } from '../pageContext'
import BulldogAvatar from './BulldogAvatar'
import { useAuth } from '../useAuth'

interface Message {
  role: 'user' | 'assistant'
  content: string
  products?: ChatProductCard[]
  page?: PageUpdate | null
  error?: boolean
  notice?: boolean // privacy notice from the server; not sent back as history
}

const HISTORY_TURNS = 12 // guests: earlier turns sent with each message (logged-in history lives in the database)

const GREETING: Message = {
  role: 'assistant',
  content: "Hi, I'm the Campus Customs assistant! Ask me about hoodies, sizes, colors or gifts for your Bulldog.",
}

// One-tap starters shown until the shopper sends their first message (Problem 10: chat feel).
const SUGGESTIONS = ['Show me hoodies', "What's going fast?", 'Gift ideas for Mom', 'Navy gear under $60']
const PRODUCT_SUGGESTIONS = ['Do you have this in another color?', 'Is my size in stock?', 'Show me similar items']

const greetingFor = (user: User, returning: boolean): Message => ({
  role: 'assistant',
  content: returning
    ? `Welcome back, ${user.first_name}! Your earlier chat is above. What can I help you find today?`
    : `Hi ${user.first_name}! I'm the Campus Customs assistant. Our chat is saved to your account, so I'll remember it next time.`,
})

/** Floating chat panel in the bottom-right corner, answered by the PydanticAI agent (POST /api/chat). */
export default function ChatWidget() {
  const [open, setOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([GREETING])
  const [draft, setDraft] = useState('')
  const [typing, setTyping] = useState(false)
  const listRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const navigate = useNavigate()
  const { user, loading } = useAuth()
  const userId = user?.id ?? null

  // Customer memory: logged in → reload the saved chat; logged out / guest → start fresh (nothing saved).
  useEffect(() => {
    if (loading) return
    let cancelled = false
    if (!user) {
      setMessages([GREETING])
      return
    }
    fetchChatHistory()
      .then((h) => {
        if (cancelled) return
        const saved: Message[] = h.messages.map((m) => ({ role: m.role, content: m.content, products: m.products, page: m.page }))
        setMessages(saved.length ? [...saved, greetingFor(user, true)] : [greetingFor(user, false)])
      })
      .catch(() => !cancelled && setMessages([greetingFor(user, false)]))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- reload only when a different person logs in/out
  }, [userId, loading])

  async function clearHistory() {
    if (!user || !window.confirm('Delete your saved chat history?')) return
    await clearChatHistory()
    setMessages([greetingFor(user, false)])
  }

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, typing])

  useEffect(() => {
    if (open) inputRef.current?.focus()
  }, [open])

  async function send(e?: FormEvent, preset?: string) {
    e?.preventDefault()
    const text = (preset ?? draft).trim()
    if (!text || typing) return
    // Guests: earlier turns (minus the canned greeting and error bubbles) give the agent conversation memory.
    // Logged in: the server loads the saved history itself, so nothing needs to be sent.
    const history: ChatTurn[] = user
      ? []
      : messages
          .slice(1)
          .filter((m) => !m.error && !m.notice)
          .slice(-HISTORY_TURNS)
          .map(({ role, content }) => ({ role, content }))
    setMessages((m) => [...m, { role: 'user', content: text }])
    setDraft('')
    setTyping(true)
    try {
      const res = await sendChat(text, history, currentPageContext())
      setMessages((m) => [
        ...m,
        ...(res.privacy_notice ? [{ role: 'assistant' as const, content: `🔒 ${res.privacy_notice}`, notice: true }] : []),
        { role: 'assistant', content: res.reply, products: res.products, page: res.page },
      ])
      // Chat search that updates the page: open the products page showing every match.
      if (res.page) navigate(chatResultsUrl(res.page))
    } catch (err) {
      const content = err instanceof Error ? err.message : 'Something went wrong. Please try again.'
      setMessages((m) => [...m, { role: 'assistant', content, error: true }])
    } finally {
      setTyping(false)
    }
  }

  return (
    <div className="chat-root">
      {open && (
        <section className="chat-panel" aria-label="Campus Customs chat">
          <header className="chat-header">
            <BulldogAvatar size={38} />
            <div className="chat-title">
              <strong>Campus Customs Assistant</strong>
              <span className="chat-status">
                {user ? `● ${user.first_name} · chat saved to your account` : '● Guest · log in to save this chat'}
              </span>
            </div>
            {user && (
              <button className="chat-clear" onClick={() => void clearHistory()} title="Delete saved chat history">
                Clear
              </button>
            )}
            <button className="icon-btn" aria-label="Close chat" onClick={() => setOpen(false)}>
              ✕
            </button>
          </header>
          <div className="chat-messages" ref={listRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-turn ${m.role}`}>
                <div className="chat-row">
                  {m.role === 'assistant' && messages[i - 1]?.role !== 'assistant' && <BulldogAvatar size={26} />}
                  <div className={`bubble ${m.role}${m.error ? ' error' : ''}${m.notice ? ' notice' : ''}`}>{m.content}</div>
                </div>
                {m.page && (
                  <Link to={chatResultsUrl(m.page)} className="chat-page-link">
                    🔎 Showing {m.page.total} {m.page.total === 1 ? 'item' : 'items'} on the page: {m.page.title} →
                  </Link>
                )}
                {m.products && m.products.length > 0 && (
                  <div className="chat-products">
                    {m.products.map((p) => (
                      <Link key={p.product_id} to={`/products/${p.product_id}`} className="chat-product">
                        <img src={p.image_url} alt={p.name} loading="lazy" />
                        <div>
                          <strong>{p.name}</strong>
                          <span className="chat-product-meta">
                            {formatPrice(p.price)} · {p.sizes_in_stock.length ? `In stock: ${p.sizes_in_stock.join(' ')}` : 'Sold out'}
                          </span>
                          {p.sizes_out_of_stock.length > 0 && p.sizes_in_stock.length > 0 && (
                            <span className="chat-product-out">Out of stock: {p.sizes_out_of_stock.join(' ')}</span>
                          )}
                        </div>
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {typing && (
              <div className="chat-row">
                <BulldogAvatar size={26} />
                <div className="bubble assistant typing" aria-label="Assistant is typing">
                  <span />
                  <span />
                  <span />
                </div>
              </div>
            )}
            {!typing && !messages.some((m) => m.role === 'user') && (
              <div className="chat-suggestions" aria-label="Suggested questions">
                {(currentPageContext().product_id ? PRODUCT_SUGGESTIONS : SUGGESTIONS).map((q) => (
                  <button key={q} type="button" className="suggestion" onClick={() => void send(undefined, q)}>
                    {q}
                  </button>
                ))}
              </div>
            )}
          </div>
          <form className="chat-input" onSubmit={send}>
            <textarea
              ref={inputRef}
              rows={1}
              value={draft}
              placeholder="Ask about products, sizes, colors…"
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) void send(e)
              }}
            />
            <button type="submit" className="chat-send" disabled={!draft.trim() || typing} aria-label="Send message">
              ↑
            </button>
          </form>
        </section>
      )}
      <button
        className={`chat-launcher ${open ? 'open' : ''}`}
        aria-label={open ? 'Close chat' : 'Open chat with the Campus Customs assistant'}
        title={open ? 'Close chat' : 'Questions? Ask our assistant'}
        onClick={() => setOpen((o) => !o)}
      >
        {open ? '✕' : <BulldogAvatar size={62} />}
      </button>
    </div>
  )
}
