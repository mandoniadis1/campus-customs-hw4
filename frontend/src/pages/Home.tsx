import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchCategories, fetchProducts, type Category, type ProductSummary } from '../api'
import BulldogFollower from '../components/BulldogFollower'
import ProductCard from '../components/ProductCard'

const FEATURED_IDS = [
  'basic-hoodie-big-yale',
  '2025-yale-vs-harvard-t-shirt',
  'district-vit-hoodie-vintage-bulldog',
  'yale-mom-crewneck',
]

const AUDIENCES = [
  { icon: '🎓', title: 'Students', text: 'Hoodies for late nights in the library and loud tees for game day at the Bowl.' },
  { icon: '👪', title: 'Families', text: 'Yale Mom, Dad, Grandma and more, so the whole family can show where their student belongs.' },
  { icon: '🏛️', title: 'Alumni', text: 'Classic crests and quarter-zips that go from reunion weekend to Monday morning.' },
  { icon: '🏈', title: 'Fans', text: 'Team gear for every sport, from the football field to the squash court.' },
]

export default function Home() {
  const [featured, setFeatured] = useState<ProductSummary[]>([])
  const [categories, setCategories] = useState<Category[]>([])

  useEffect(() => {
    fetchProducts()
      .then((all) => setFeatured(FEATURED_IDS.map((id) => all.find((p) => p.product_id === id)).filter((p) => !!p)))
      .catch(() => setFeatured([]))
    fetchCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  return (
    <>
      <BulldogFollower />
      <section className="hero">
        <div className="hero-glow" aria-hidden="true" />
        <p className="eyebrow">New Haven · Est. for Bulldogs everywhere</p>
        <h1>
          Bleed blue. <span className="accent-text">Wear it loud.</span>
        </h1>
        <p className="lead">
          Campus Customs outfits the whole Yale community: students, families, alumni and fans. Gear up for every
          college, every team and every milestone, from move-in day to The Game.
        </p>
        <div className="hero-actions">
          <Link to="/products" className="btn btn-primary">
            Shop the collection
          </Link>
          <Link to="/about" className="btn btn-ghost">
            Our story
          </Link>
        </div>
      </section>

      {categories.length > 0 && (
        <section className="section">
          <h2>Shop by style</h2>
          <div className="category-grid">
            {categories.map((c, i) => (
              <Link
                key={c.category}
                to={`/products?category=${encodeURIComponent(c.category)}`}
                className={`category-tile glow-${i % 6}`}
              >
                <strong>{c.category}</strong>
                <span className="muted small">{c.count} styles</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      <section className="section">
        <h2>Made for every kind of Bulldog</h2>
        <div className="audience-grid">
          {AUDIENCES.map((a, i) => (
            <div key={a.title} className={`card glow-${i % 6}`}>
              <span className="audience-icon" aria-hidden="true">
                {a.icon}
              </span>
              <h3>{a.title}</h3>
              <p className="muted">{a.text}</p>
            </div>
          ))}
        </div>
      </section>

      {featured.length > 0 && (
        <section className="section">
          <div className="section-head">
            <h2>Fan favorites</h2>
            <Link to="/products" className="text-link">
              See all products →
            </Link>
          </div>
          <div className="product-grid">
            {featured.map((p) => (
              <ProductCard key={p.product_id} product={p} />
            ))}
          </div>
        </section>
      )}

      <section className="section banner">
        <div>
          <h2>Rep your college, your team, your school</h2>
          <p className="muted">
            Residential college crests, varsity sports, graduate and professional schools: find the design that tells
            your part of the Yale story.
          </p>
        </div>
        <Link to="/products" className="btn btn-primary">
          Find yours
        </Link>
      </section>
    </>
  )
}
