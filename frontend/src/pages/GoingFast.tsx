import { useEffect, useState } from 'react'
import { edgeColor } from '../edgeColor'
import { Link } from 'react-router-dom'
import { fetchGoingFast, formatPrice, type GoingFastItem } from '../api'

/** Urgency label from real stock numbers (never made up). */
function badge(item: GoingFastItem): string {
  if (item.units_left <= 10) return `🔥 Only ${item.units_left} left!`
  if (item.sold_out_sizes.length >= 3) return `⚡ ${item.sold_out_sizes.length} sizes sold out`
  return '🔥 Going fast!'
}

/** "Most popular" = the items closest to selling out, with honest stock facts on every card. */
export default function GoingFast() {
  const [items, setItems] = useState<GoingFastItem[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchGoingFast()
      .then(setItems)
      .catch(() => setError("We couldn't load the trending items. Please try again."))
  }, [])

  return (
    <section className="section going-fast">
      <div className="hero hero-small going-fast-hero">
        <div className="hero-glow" aria-hidden="true" />
        <p className="eyebrow">Trending now · Most popular</p>
        <h1>
          Going fast! <span className="accent-text">Lock it in.</span>
        </h1>
        <p className="lead">
          These are the Bulldog favorites flying off the shelves. They're our lowest-stock items, so once a size is
          gone, it's gone. Grab yours before the next game day.
        </p>
      </div>

      {error && <p className="notice error">{error}</p>}
      {!error && !items && <p className="muted">Loading the hottest gear…</p>}
      {items && (
        <div className="product-grid">
          {items.map((p, i) => {
            const inStock = p.sizes_in_stock
            const low = p.low_sizes.map((s) => `${s.size} (${s.quantity})`)
            return (
              <Link key={p.product_id} to={`/products/${p.product_id}`} className="product-card going-fast-card">
                <div className="product-card-image">
                  <img
                    src={p.image_url}
                    alt={p.name}
                    loading="lazy"
                    onLoad={(e) => {
                      const tile = edgeColor(e.currentTarget)
                      if (tile) e.currentTarget.parentElement!.style.background = tile
                    }}
                  />
                  <div className="card-badges">
                    <span className="urgency-badge">{badge(p)}</span>
                    {i < 3 && <span className="rank-badge">#{i + 1} trending</span>}
                  </div>
                </div>
                <div className="product-card-body">
                  <span className="card-category">{p.category}</span>
                  <h3>{p.name}</h3>
                  <span className="price">{formatPrice(p.price)}</span>
                  <div className="stock-meter" aria-label={`${p.units_left} units left`}>
                    <span style={{ width: `${Math.max(6, Math.min(100, (p.units_left / 60) * 100))}%` }} />
                  </div>
                  <p className="small">
                    <strong>{p.units_left} left</strong> across all sizes
                  </p>
                  {low.length > 0 && <p className="small stock-low">Almost gone: {low.join(', ')}</p>}
                  {p.sold_out_sizes.length > 0 && (
                    <p className="small stock-out">Sold out: {p.sold_out_sizes.join(', ')}</p>
                  )}
                  {inStock.length > 0 && <p className="small muted">Still available: {inStock.join(' ')}</p>}
                </div>
              </Link>
            )
          })}
        </div>
      )}
      <p className="muted small going-fast-note">
        Stock levels are live from our inventory. Want something else?{' '}
        <Link to="/products" className="text-link">
          Browse all products
        </Link>
      </p>
    </section>
  )
}
