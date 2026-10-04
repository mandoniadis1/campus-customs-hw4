// Light/dark theme (Problem 9): saved in localStorage, applied as <html data-theme="…">.

export type Theme = 'dark' | 'light'
const STORAGE_KEY = 'cc-theme'

/** The saved theme (dark by default). Applied in main.tsx before the first render, so there's no flash. */
export function savedTheme(): Theme {
  return localStorage.getItem(STORAGE_KEY) === 'light' ? 'light' : 'dark'
}

export function applyTheme(theme: Theme) {
  document.documentElement.dataset.theme = theme
  localStorage.setItem(STORAGE_KEY, theme)
}
