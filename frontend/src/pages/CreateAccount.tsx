import { useState, type ChangeEvent, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../useAuth'

const MIN_PASSWORD = 8

// Fields match the users table: first_name, last_name, email, password (stored only as a hash).
export default function CreateAccount() {
  const { user, register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ firstName: '', lastName: '', email: '', password: '', confirm: '' })
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  if (user && !busy) return <Navigate to="/" replace />

  const set = (key: keyof typeof form) => (e: ChangeEvent<HTMLInputElement>) =>
    setForm((f) => ({ ...f, [key]: e.target.value }))

  async function submit(e: FormEvent) {
    e.preventDefault()
    // Quick checks in the browser; the backend checks everything again.
    if (form.password.length < MIN_PASSWORD) return setError(`Password must be at least ${MIN_PASSWORD} characters.`)
    if (form.password !== form.confirm) return setError("Passwords don't match.")
    setError('')
    setBusy(true)
    try {
      await register({
        first_name: form.firstName,
        last_name: form.lastName,
        email: form.email,
        password: form.password,
        confirm_password: form.confirm,
      })
      navigate('/', { replace: true })
    } catch (err) {
      setError((err as Error).message)
      setBusy(false)
    }
  }

  return (
    <section className="section auth">
      <form className="card auth-card glow-2" onSubmit={submit}>
        <h1>
          Join the <span className="accent-text">pack</span>
        </h1>
        <p className="muted">Create an account so our assistant can remember your size and favorites.</p>
        <div className="form-row">
          <label>
            First name
            <input required autoComplete="given-name" value={form.firstName} onChange={set('firstName')} />
          </label>
          <label>
            Last name
            <input required autoComplete="family-name" value={form.lastName} onChange={set('lastName')} />
          </label>
        </div>
        <label>
          Email
          <input type="email" required autoComplete="email" value={form.email} onChange={set('email')} />
        </label>
        <label>
          Password <span className="muted small">(at least {MIN_PASSWORD} characters)</span>
          <input type="password" required autoComplete="new-password" value={form.password} onChange={set('password')} />
        </label>
        <label>
          Confirm password
          <input type="password" required autoComplete="new-password" value={form.confirm} onChange={set('confirm')} />
        </label>
        {error && <p className="notice error">{error}</p>}
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? 'Creating account…' : 'Create Account'}
        </button>
        <p className="muted small">
          Already have an account? <Link to="/login" className="text-link">Log in</Link>
        </p>
      </form>
    </section>
  )
}
