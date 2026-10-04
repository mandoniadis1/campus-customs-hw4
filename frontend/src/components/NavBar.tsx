import { useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../useAuth'
import ThemeToggle from './ThemeToggle'

const PAGES = [
  { to: '/', label: 'Home', end: true },
  { to: '/products', label: 'Products' },
  { to: '/going-fast', label: '🔥 Going Fast' },
  { to: '/about', label: 'About Us' },
]
const GUEST_LINKS = [
  { to: '/login', label: 'Log In' },
  { to: '/create-account', label: 'Create Account', cta: true },
]

export default function NavBar() {
  const [open, setOpen] = useState(false)
  const { user, loading, logout } = useAuth()
  const navigate = useNavigate()

  const linkClass = (cta?: boolean) => ({ isActive }: { isActive: boolean }) =>
    `nav-link ${cta ? 'nav-cta' : ''} ${isActive ? 'active' : ''}`

  return (
    <header className="nav">
      <div className="nav-inner">
        <Link to="/" className="brand" onClick={() => setOpen(false)}>
          <span className="brand-mark" aria-hidden="true">CC</span>
          <span className="brand-text">
            Campus <span className="accent-text">Customs</span>
          </span>
        </Link>
        <button
          className="nav-toggle"
          aria-label="Toggle menu"
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          ☰
        </button>
        <nav className={`nav-links ${open ? 'open' : ''}`}>
          {PAGES.map((l) => (
            <NavLink key={l.to} to={l.to} end={l.end} className={linkClass()} onClick={() => setOpen(false)}>
              {l.label}
            </NavLink>
          ))}
          {!loading && !user &&
            GUEST_LINKS.map((l) => (
              <NavLink key={l.to} to={l.to} className={linkClass(l.cta)} onClick={() => setOpen(false)}>
                {l.label}
              </NavLink>
            ))}
          {user && (
            <>
              <span className="nav-user">Hi, {user.first_name}</span>
              <button
                className="nav-link nav-button"
                onClick={async () => {
                  setOpen(false)
                  await logout()
                  navigate('/')
                }}
              >
                Log Out
              </button>
            </>
          )}
          <ThemeToggle />
        </nav>
      </div>
      <div className="navy-bar" aria-hidden="true" />
    </header>
  )
}
