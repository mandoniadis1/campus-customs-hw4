// What the shopper is looking at, sent with every chat message (Problem 8) so the assistant knows
// what "it" / "this one" / "the first one" means. Pages write here; the chat widget reads it on send.

import type { PageContext } from './api'

let productSelection: { productId: string; size: string | null } | null = null
let listing: { path: string; search: string; title: string; productIds: string[] } | null = null

/** Called by the product page whenever the shown product or the selected size changes. */
export function setProductSelection(productId: string, size: string | null) {
  productSelection = { productId, size }
}

/** Called by the products page when a list of products has loaded. */
export function setListing(title: string, productIds: string[]) {
  listing = { path: window.location.pathname, search: window.location.search, title, productIds: productIds.slice(0, 12) }
}

/** Build the page context for the current URL (ignores state left over from other pages). */
export function currentPageContext(): PageContext {
  const path = window.location.pathname
  const product = path.match(/^\/products\/([^/]+)$/)
  if (product) {
    const productId = decodeURIComponent(product[1])
    const size = productSelection?.productId === productId ? productSelection.size : null
    return { path, product_id: productId, selected_size: size, listing_title: null, listing_product_ids: [] }
  }
  if (listing && listing.path === path && listing.search === window.location.search) {
    return { path, product_id: null, selected_size: null, listing_title: listing.title, listing_product_ids: listing.productIds }
  }
  return { path, product_id: null, selected_size: null, listing_title: null, listing_product_ids: [] }
}
