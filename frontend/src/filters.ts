/** The filter buttons, in display order. `options` is the key in FilterOptions, `param` the URL/API key. */
export const FILTERS = [
  { param: 'shop_for', options: 'shop_for', label: 'Shop For' },
  { param: 'category', options: 'product_type', label: 'Product Type' },
  { param: 'color', options: 'color', label: 'Color' },
  { param: 'size', options: 'size', label: 'Size' },
  { param: 'price', options: 'price', label: 'Price' },
] as const

export type FilterParam = (typeof FILTERS)[number]['param']
