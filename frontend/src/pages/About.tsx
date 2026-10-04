import { Link } from 'react-router-dom'

const VALUES = [
  { title: 'Officially Yale', text: 'Licensed Yale designs, so every crest, wordmark and bulldog is the real thing.' },
  { title: 'The whole community', text: 'Fourteen residential colleges, dozens of varsity teams and the graduate and professional schools. Every corner of Yale gets its own gear.' },
  { title: 'Family first', text: 'Moms, dads, grandparents, siblings and cousins are part of the Bulldog story too, and we make gear with their names on it.' },
  { title: 'Built to be worn', text: 'Soft tees, heavyweight crewnecks and fleece that holds up through New Haven winters and many reunions.' },
]

export default function About() {
  return (
    <>
      <section className="hero hero-small">
        <div className="hero-glow" aria-hidden="true" />
        <p className="eyebrow">About Campus Customs</p>
        <h1>
          Where Yale pride <span className="accent-text">gets dressed up</span>
        </h1>
        <p className="lead">
          We're a New Haven shop with one job: help everyone connected to Yale show it. Whether you just moved into
          Old Campus, are cheering from the stands, or are sending love from three time zones away, we have something
          blue for you.
        </p>
      </section>

      <section className="section two-col">
        <div>
          <h2>Our story</h2>
          <p>
            Campus Customs started with a simple idea: school spirit shouldn't feel generic. Yale isn't one community,
            it's many. Pierson and Saybrook, the crew team and the a cappella groups, the School of Nursing and the Law
            School. Each deserves gear that feels like it belongs.
          </p>
          <p>
            So we design for all of them. From everyday hoodies with a big bold YALE to small embroidered college
            crests, our collection is meant for people who wear their Yale connection every day, not just on game day.
          </p>
        </div>
        <div className="card glow-3">
          <h3>Visit us</h3>
          <p className="muted">
            Our shop is in New Haven, Connecticut, a short walk from campus. Stop by before The Game, during Family
            Weekend, or any time you need a new favorite sweatshirt.
          </p>
          <Link to="/products" className="btn btn-primary">
            Browse online
          </Link>
        </div>
      </section>

      <section className="section">
        <h2>What we stand for</h2>
        <div className="audience-grid">
          {VALUES.map((v, i) => (
            <div key={v.title} className={`card glow-${i % 6}`}>
              <h3>{v.title}</h3>
              <p className="muted">{v.text}</p>
            </div>
          ))}
        </div>
      </section>
    </>
  )
}
