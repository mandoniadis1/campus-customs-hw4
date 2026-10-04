// Swatch colors for the catalogue's color families (same groups as backend catalog.COLOR_FAMILIES).
export const SWATCHES: Record<string, string> = {
  Navy: '#0b2a5b',
  White: '#ffffff',
  Gray: '#9aa3ad',
  Blue: '#3d7bff',
  Red: '#d62839',
  Black: '#111111',
  'Yellow & Gold': '#f2c230',
  Green: '#2e8b57',
  Cream: '#f3ead7',
  Coral: '#f08a7e',
  Multicolor: 'conic-gradient(#d62839, #f2c230, #2e8b57, #3d7bff, #d62839)',
}

/** Units across all sizes at or below which a card shows "Low stock" (real inventory, never invented). */
export const LOW_STOCK_TOTAL = 25
