import { Link } from 'react-router-dom'

export default function Footer() {
  return (
    <footer className="footer">
      <div className="navy-bar" aria-hidden="true" />
      <div className="footer-inner">
        <div>
          <strong>Campus Customs</strong>
          <p className="muted">Yale gear for every kind of Bulldog, from New Haven, Connecticut.</p>
        </div>
        <nav className="footer-links">
          <Link to="/products">Shop</Link>
          <Link to="/about">About Us</Link>
          <Link to="/login">Log In</Link>
        </nav>
      </div>
    </footer>
  )
}
