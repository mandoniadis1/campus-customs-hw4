// Typed client for the FastAPI backend (backend/main.py). Shapes match its response models.

export interface ProductSummary {
  product_id: string
  name: string
  category: string
  garment_type: string
  price: number
  short_description: string
  product_types: string[]
  colors: string[]
  color_families: string[]
  shop_for: string[]
  sizes_in_stock: string[]
  image_url: string
  total_stock: number
}

/** Products page filters (Problem 9). Each key holds the selected option values. */
export interface ProductFilters {
  shop_for?: string[]
  category?: string[]
  color?: string[]
  size?: string[]
  price?: string[]
}

export interface FilterOption {
  value: string
  label: string
  count: number
  group: string | null
  swatch: string | null
}

export interface FilterOptions {
  shop_for: FilterOption[]
  product_type: FilterOption[]
  color: FilterOption[]
  size: FilterOption[]
  price: FilterOption[]
}

export interface GoingFastItem extends ProductSummary {
  units_left: number
  sold_out_sizes: string[]
  low_sizes: { size: string; quantity: number }[]
}

/** Filter options with counts for the current search + other filters (pass the page's query string). */
export const fetchFilters = (query = '') => getJson<FilterOptions>(`/api/filters${query ? `?${query}` : ''}`)
export const fetchGoingFast = () => getJson<GoingFastItem[]>('/api/going-fast')

export interface SizeStock {
  size: string
  quantity: number
}

export interface ProductDetail extends ProductSummary {
  description: string
  search_tags: string[]
  inventory: SizeStock[]
}

export interface Category {
  category: string
  count: number
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url)
  if (!res.ok) throw new Error(res.status === 404 ? 'Not found' : `Request failed (${res.status})`)
  return res.json() as Promise<T>
}

export function fetchProducts(
  params: { q?: string; category?: string; ids?: string[]; filters?: ProductFilters } = {},
): Promise<ProductSummary[]> {
  const search = new URLSearchParams()
  if (params.q) search.set('q', params.q)
  if (params.category) search.set('category', params.category)
  if (params.ids?.length) search.set('ids', params.ids.join(','))
  for (const [key, values] of Object.entries(params.filters ?? {})) {
    if (values?.length) search.set(key, values.join(','))
  }
  const qs = search.toString()
  return getJson(`/api/products${qs ? `?${qs}` : ''}`)
}

export const fetchProduct = (id: string) => getJson<ProductDetail>(`/api/products/${encodeURIComponent(id)}`)
export const fetchCategories = () => getJson<Category[]>('/api/categories')

export const formatPrice = (price: number) => `$${price.toFixed(2)}`

// ---------------------------------------------------------------------------
// Accounts (backend/auth.py). The session lives in an HttpOnly cookie the browser sends automatically.
// ---------------------------------------------------------------------------

export interface User {
  id: number
  first_name: string
  last_name: string
  email: string
  created_at: string
}

export interface RegisterInput {
  first_name: string
  last_name: string
  email: string
  password: string
  confirm_password: string
}

/** Turn FastAPI error bodies (string or validation list) into one readable message. */
async function errorMessage(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && body.detail.length) {
      const d = body.detail[0]
      const field = String(d.loc?.at(-1) ?? '').replace('_', ' ')
      return `${field ? field[0].toUpperCase() + field.slice(1) + ': ' : ''}${String(d.msg).replace(/^Value error, /, '')}`
    }
  } catch {
    /* fall through */
  }
  return `Something went wrong (${res.status}).`
}

async function postJson<T>(url: string, body?: unknown): Promise<T> {
  const res = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await errorMessage(res))
  return (res.status === 204 ? undefined : await res.json()) as T
}

export const fetchMe = () => getJson<User | null>('/api/auth/me')
export const login = (email: string, password: string) => postJson<User>('/api/auth/login', { email, password })
export const register = (input: RegisterInput) => postJson<User>('/api/auth/register', input)
export const logout = () => postJson<void>('/api/auth/logout')

// ---------------------------------------------------------------------------
// Chatbot (backend/agent.py via POST /api/chat). Product cards are built from the database.
// ---------------------------------------------------------------------------

export interface ChatProductCard {
  product_id: string
  name: string
  category: string
  price: number
  image_url: string
  colors: string[]
  sizes_in_stock: string[]
  sizes_out_of_stock: string[]
  short_description: string
}

export interface ChatTurn {
  role: 'user' | 'assistant'
  content: string
}

/** The search the agent ran (Problem 7). */
export interface PageSearch {
  title: string
  query: string
  category: string | null
  color: string | null
  max_price: number | null
  size: string | null
}

/** "Open the products page with these results" — sent with a chat reply when the shopper searched. */
export interface PageUpdate {
  title: string
  product_ids: string[]
  total: number
  search: PageSearch
}

export interface ChatReply {
  reply: string
  products: ChatProductCard[]
  page: PageUpdate | null
  /** Set when the server removed card numbers, phone numbers, etc. from the shopper's message. */
  privacy_notice: string | null
}

/** URL of the products page showing a chat search's results. Refresh, Back and sharing all work. */
export function chatResultsUrl(page: PageUpdate): string {
  const p = new URLSearchParams({ ids: page.product_ids.join(','), title: page.title })
  return `/products?${p.toString()}`
}

/** What the shopper is looking at (see pageContext.ts). */
export interface PageContext {
  path: string
  product_id: string | null
  selected_size: string | null
  listing_title: string | null
  listing_product_ids: string[]
}

/** history is only used for guests; logged-in customers' history comes from the database. */
export const sendChat = (message: string, history: ChatTurn[], page: PageContext) =>
  postJson<ChatReply>('/api/chat', { message, history, page })

export interface ChatHistoryMessage {
  role: 'user' | 'assistant'
  content: string
  products: ChatProductCard[]
  page: PageUpdate | null
  created_at: string
}

/** The logged-in customer's saved chat (empty for guests). */
export const fetchChatHistory = () => getJson<{ logged_in: boolean; messages: ChatHistoryMessage[] }>('/api/chat/history')

export async function clearChatHistory(): Promise<void> {
  const res = await fetch('/api/chat/history', { method: 'DELETE' })
  if (!res.ok && res.status !== 401) throw new Error(await errorMessage(res))
}
