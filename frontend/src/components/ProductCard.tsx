import { useState } from 'react'
import { Link } from 'react-router-dom'
import { edgeColor } from '../edgeColor'
import { formatPrice, type ProductSummary } from '../api'
import { LOW_STOCK_TOTAL, SWATCHES } from '../swatches'

/** Storefront card (Problem 10): big image tile, small uppercase category, name, price, color swatches. */
export default function ProductCard({ product }: { product: ProductSummary }) {
  const families = product.color_families ?? []
  const lowStock = product.total_stock > 0 && product.total_stock <= LOW_STOCK_TOTAL
  const [tile, setTile] = useState<string | null>(null)
  return (
    <Link to={`/products/${product.product_id}`} className="product-card">
      <div className="product-card-image" style={tile ? { background: tile } : undefined}>
        <img src={product.image_url} alt={product.name} loading="lazy" onLoad={(e) => setTile(edgeColor(e.currentTarget))} />
        {lowStock && <span className="card-tag">Low stock</span>}
        <span className="card-quick-view" aria-hidden="true">
          View details →
        </span>
      </div>
      <div className="product-card-body">
        <span className="card-category">{product.category}</span>
        <h3>{product.name}</h3>
        <p className="muted small card-desc">{product.short_description}</p>
        <div className="card-meta">
          <span className="price">{formatPrice(product.price)}</span>
          {families.length > 0 && (
            <span className="card-swatches" aria-label={`Colors: ${product.colors.join(', ')}`}>
              {families.slice(0, 4).map((f) => (
                <span key={f} className="swatch-dot" style={{ background: SWATCHES[f] ?? '#888' }} title={f} />
              ))}
              {families.length > 4 && <span className="muted small">+{families.length - 4}</span>}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
