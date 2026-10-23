import { Link } from 'react-router-dom'

export default function HomePage() {
  return (
    <section className="home-hero">
      <p className="brand-mark">Campus Customs</p>
      <h1>Yale gear for every college story</h1>
      <p className="lede">
        Browse hoodies, crewnecks, and college classics — then create an account to pick up where you
        left off.
      </p>
      <div className="cta-row">
        <Link className="btn primary" to="/products">
          Shop products
        </Link>
        <Link className="btn ghost" to="/signup">
          Create account
        </Link>
      </div>
    </section>
  )
}
