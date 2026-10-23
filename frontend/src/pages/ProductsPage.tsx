import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { fetchGarmentTypes, fetchProducts, type ProductCard } from '../api'
import { useShop } from '../shop'

function ProductTile({ p }: { p: ProductCard }) {
  const blurb = p.short_description || p.description || ''
  return (
    <Link className="product-card" to={`/products/${p.product_id}`}>
      <img src={`/media/${p.image_file_path}`} alt={p.name} />
      <div>
        <h2>{p.name}</h2>
        <p className="price">${Number(p.price).toFixed(2)}</p>
        <p className="snip">{blurb.slice(0, 110)}{blurb.length > 110 ? '…' : ''}</p>
      </div>
    </Link>
  )
}

export default function ProductsPage() {
  const { spotlight } = useShop()
  const [products, setProducts] = useState<ProductCard[]>([])
  const [types, setTypes] = useState<string[]>([])
  const [garment, setGarment] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchGarmentTypes().then(setTypes).catch(() => setTypes([]))
  }, [])

  useEffect(() => {
    setLoading(true)
    fetchProducts(garment ? { garment } : undefined)
      .then(setProducts)
      .catch((err) => setError(err instanceof Error ? err.message : 'Load failed'))
      .finally(() => setLoading(false))
  }, [garment])

  const grid = useMemo(() => {
    if (spotlight.length) return spotlight
    return products
  }, [spotlight, products])

  return (
    <section>
      <div className="section-head">
        <div>
          <h1>{spotlight.length ? 'Chat matches' : 'Products'}</h1>
          <p className="lede">
            {spotlight.length
              ? 'These cards came from your chat search. Click any item for the full detail page.'
              : 'Catalogue from the Campus Customs database.'}
          </p>
        </div>
        {!spotlight.length ? (
          <label className="filter">
            Filter by type
            <select value={garment} onChange={(e) => setGarment(e.target.value)}>
              <option value="">All garments</option>
              {types.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
        ) : null}
      </div>

      {error ? <p className="form-error">{error}</p> : null}
      {loading && !spotlight.length ? <p className="muted">Loading products…</p> : null}
      {!loading && !grid.length ? (
        <p className="empty-state">No products matched that filter. Try another garment type.</p>
      ) : null}

      <div className="product-grid">
        {grid.map((p) => (
          <ProductTile key={p.product_id} p={p} />
        ))}
      </div>
    </section>
  )
}
