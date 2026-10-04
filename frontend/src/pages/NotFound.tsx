import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <section className="section">
      <h1>
        Lost on <span className="accent-text">Old Campus?</span>
      </h1>
      <p className="muted">We couldn't find that page.</p>
      <Link to="/" className="btn btn-primary">
        Back home
      </Link>
    </section>
  )
}
