import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchProduct, formatPrice, type ProductDetail as Product } from '../api'
import ZoomImage from '../components/ZoomImage'
import { setProductSelection } from '../pageContext'

const LOW_STOCK = 5

function stockLabel(qty: number) {
  if (qty === 0) return { text: 'Sold out in this size', tone: 'out' }
  if (qty <= LOW_STOCK) return { text: `Only ${qty} left`, tone: 'low' }
  return { text: `${qty} in stock`, tone: 'ok' }
}

export default function ProductDetail() {
  const { productId = '' } = useParams()
  // Results and the chosen size are tagged with their product id, so switching products resets them.
  const [result, setResult] = useState<{ id: string; product?: Product; error?: string }>({ id: '' })
  const [picked, setPicked] = useState<{ id: string; size: string } | null>(null)
  const loaded = result.id === productId
  const product = loaded ? (result.product ?? null) : null
  const error = loaded ? (result.error ?? '') : ''
  const size =
    picked?.id === productId ? picked.size : (product?.inventory.find((s) => s.quantity > 0)?.size ?? null)
  const setSize = (s: string) => setPicked({ id: productId, size: s })

  // Tell the chat assistant which product and size are on screen ("do you have it in pink?").
  useEffect(() => {
    if (product) setProductSelection(productId, size)
  }, [product, productId, size])

  useEffect(() => {
    let cancelled = false
    fetchProduct(productId)
      .then((p) => !cancelled && setResult({ id: productId, product: p }))
      .catch(
        (e: Error) =>
          !cancelled &&
          setResult({
            id: productId,
            error: e.message === 'Not found' ? "We couldn't find that product." : 'Something went wrong loading this product.',
          }),
      )
    return () => {
      cancelled = true
    }
  }, [productId])

  if (error)
    return (
      <section className="section">
        <p className="notice error">{error}</p>
        <Link to="/products" className="text-link">
          ← Back to all products
        </Link>
      </section>
    )
  if (!product) return <p className="section muted">Loading…</p>

  const selected = product.inventory.find((s) => s.size === size)
  const label = selected ? stockLabel(selected.quantity) : null

  return (
    <section className="section">
      <Link to="/products" className="text-link">
        ← Back to all products
      </Link>
      <div className="detail">
        <ZoomImage src={product.image_url} alt={product.name} />

        <div className="detail-info">
          <span className="chip detail-category">{product.category}</span>
          <h1>{product.name}</h1>
          <p className="detail-price">{formatPrice(product.price)}</p>
          <p className="detail-description">{product.description}</p>

          <div className="detail-block">
            <h3>Colors</h3>
            <div className="color-list">
              {product.colors.map((c) => (
                <span key={c} className="chip">
                  {c}
                </span>
              ))}
            </div>
          </div>

          <div className="detail-block">
            <h3>Size</h3>
            <div className="size-grid" role="radiogroup" aria-label="Choose a size">
              {product.inventory.map((s) => (
                <button
                  key={s.size}
                  role="radio"
                  aria-checked={size === s.size}
                  className={`size-btn ${size === s.size ? 'active' : ''} ${s.quantity === 0 ? 'out' : ''}`}
                  onClick={() => setSize(s.size)}
                  title={stockLabel(s.quantity).text}
                >
                  {s.size}
                </button>
              ))}
            </div>
            {label && (
              <p className={`stock stock-${label.tone}`}>
                {size}: {label.text}
              </p>
            )}
          </div>

          <div className="detail-block">
            <h3>Stock by size</h3>
            <table className="stock-table">
              <tbody>
                {product.inventory.map((s) => (
                  <tr key={s.size}>
                    <th>{s.size}</th>
                    <td className={`stock-${stockLabel(s.quantity).tone}`}>{s.quantity === 0 ? 'Sold out' : s.quantity}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted small">{product.total_stock} total in stock across all sizes</p>
          </div>

          <div className="detail-block">
            <h3>Details</h3>
            <p className="muted small">Style: {product.garment_type}</p>
            <div className="tag-list">
              {product.search_tags.map((t) => (
                <span key={t} className="tag">
                  #{t}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
