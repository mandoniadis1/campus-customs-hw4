import { useEffect, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { fetchFilters, fetchProducts, type FilterOptions, type ProductFilters, type ProductSummary } from '../api'
import FilterBar from '../components/FilterBar'
import { FILTERS, type FilterParam } from '../filters'
import ProductCard from '../components/ProductCard'
import { setListing } from '../pageContext'

export default function Products() {
  const [params, setParams] = useSearchParams()
  const category = params.get('category') ?? ''
  const q = params.get('q') ?? ''
  // Filters live in the URL (e.g. ?shop_for=women&category=Hoodies&color=Navy,Gray) so Back/Refresh/sharing work.
  const filters: ProductFilters = Object.fromEntries(
    FILTERS.map((f) => [f.param, (params.get(f.param) ?? '').split(',').filter(Boolean)]),
  )
  const filterCount = FILTERS.reduce((n, f) => n + (filters[f.param]?.length ?? 0), 0)
  // Chat search results (Problem 7): /products?ids=a,b,c&title=… — set by the chat widget.
  const idsParam = params.get('ids') ?? ''
  const chatTitle = params.get('title') ?? 'Chat results'
  const fromChat = idsParam !== ''
  const [search, setSearch] = useState(q)
  const [filterOptions, setFilterOptions] = useState<FilterOptions | null>(null)
  // Results are tagged with the query they belong to, so "loading" is simply "tag doesn't match yet".
  const key = params.toString()
  const [result, setResult] = useState<{ key: string; products?: ProductSummary[]; error?: string }>({ key: '' })
  const loaded = result.key === key
  const products = loaded ? (result.products ?? null) : null
  const error = loaded ? (result.error ?? '') : ''

  // Counts depend on the search and the other filters, so they never promise results that aren't there.
  const facetQuery = fromChat ? '' : key
  useEffect(() => {
    let cancelled = false
    fetchFilters(facetQuery)
      .then((f) => !cancelled && setFilterOptions(f))
      .catch(() => !cancelled && setFilterOptions(null))
    return () => {
      cancelled = true
    }
  }, [facetQuery])

  useEffect(() => {
    let cancelled = false
    const request = idsParam ? fetchProducts({ ids: idsParam.split(',') }) : fetchProducts({ q, filters })
    request
      .then((p) => !cancelled && setResult({ key, products: p }))
      .catch(() => !cancelled && setResult({ key, error: "We couldn't load products. Is the backend running on port 8000?" }))
    return () => {
      cancelled = true
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `key` is the whole query string, so it covers q and filters
  }, [key])

  // Tell the chat assistant what's listed, so "the first one" makes sense.
  useEffect(() => {
    if (products) setListing(fromChat ? chatTitle : category || (q ? `Search: ${q}` : 'All products'), products.map((p) => p.product_id))
  }, [products, fromChat, chatTitle, category, q])


  useEffect(() => {
    if (fromChat) window.scrollTo({ top: 0, behavior: 'smooth' })
  }, [fromChat, idsParam])

  /** Change the search or one filter. Leaves chat-results mode, since the shopper is now browsing themselves. */
  function update(next: { q?: string } & Partial<Record<FilterParam, string[]>>) {
    const p = new URLSearchParams()
    const nextQ = next.q ?? q
    if (nextQ) p.set('q', nextQ)
    for (const f of FILTERS) {
      const values = next[f.param] ?? filters[f.param] ?? []
      if (values.length) p.set(f.param, values.join(','))
    }
    setParams(p)
  }

  function clearAll() {
    setSearch('')
    setParams(new URLSearchParams())
  }

  const optionLabel = (param: FilterParam, value: string) => {
    const key = FILTERS.find((f) => f.param === param)!.options
    return filterOptions?.[key].find((o) => o.value === value)?.label ?? value
  }

  return (
    <section className="section">
      <h1>
        Shop <span className="accent-text">Campus Customs</span>
      </h1>
      <form
        className="search-bar"
        onSubmit={(e) => {
          e.preventDefault()
          update({ q: search.trim() })
        }}
      >
        <input
          type="search"
          value={search}
          placeholder="Search bulldog, crest, hockey, Yale Mom…"
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search products"
        />
        <button className="btn btn-primary" type="submit">
          Search
        </button>
      </form>

      <FilterBar options={filterOptions} selected={fromChat ? {} : filters} onChange={(param, values) => update({ [param]: values })} />

      {!fromChat && (filterCount > 0 || q) && (
        <div className="active-filters" aria-label="Active filters">
          {q && (
            <button
              className="active-filter"
              onClick={() => {
                setSearch('')
                update({ q: '' })
              }}
              aria-label={`Remove search ${q}`}
            >
              Search: “{q}” ✕
            </button>
          )}
          {FILTERS.flatMap((f) =>
            (filters[f.param] ?? []).map((v) => (
              <button
                key={`${f.param}-${v}`}
                className="active-filter"
                onClick={() => update({ [f.param]: (filters[f.param] ?? []).filter((x) => x !== v) })}
                aria-label={`Remove ${optionLabel(f.param, v)}`}
              >
                {f.label}: {optionLabel(f.param, v)} ✕
              </button>
            )),
          )}
          <button className="text-link" onClick={clearAll}>
            Clear all
          </button>
        </div>
      )}

      {fromChat && (
        <div className="chat-results-banner" role="status">
          <span>
            🔎 From your chat with the assistant: <strong>{chatTitle}</strong>
          </span>
          <Link to="/products" className="text-link">
            Show all products
          </Link>
        </div>
      )}

      {error && <p className="notice error">{error}</p>}
      {!error && products === null && <p className="muted">Loading products…</p>}
      {products && (
        <>
          <p className="muted small">
            {products.length} {products.length === 1 ? 'product' : 'products'}
            {q && !fromChat && ` matching “${q}”`}
            {fromChat && ' found by the assistant'}
          </p>
          {products.length === 0 ? (
            <p className="notice">
              No products match those filters.{' '}
              <button className="text-link" onClick={clearAll}>
                Clear all filters
              </button>
            </p>
          ) : (
            <div className={`product-grid${fromChat ? ' from-chat' : ''}`} key={key}>
              {products.map((p) => (
                <ProductCard key={p.product_id} product={p} />
              ))}
            </div>
          )}
        </>
      )}
    </section>
  )
}
