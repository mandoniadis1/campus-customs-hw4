import { useState } from 'react'
import { applyTheme, savedTheme, type Theme } from '../theme'

/** Sun / moon switch in the nav bar: ☀ / ☾ (HTML entities &#9728; and &#9790;). */
export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme>(savedTheme)
  const next: Theme = theme === 'dark' ? 'light' : 'dark'

  return (
    <button
      type="button"
      className="theme-toggle"
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
      onClick={() => {
        applyTheme(next)
        setTheme(next)
      }}
    >
      <span className={theme === 'light' ? 'on' : ''} aria-hidden="true">
        &#9728;
      </span>
      <span className="slash" aria-hidden="true">
        /
      </span>
      <span className={theme === 'dark' ? 'on' : ''} aria-hidden="true">
        &#9790;
      </span>
    </button>
  )
}
