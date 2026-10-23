import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useShop } from '../shop'

type Product = {
  product_id: string
  name: string
  description: string
  price: number
  image_file_path: string
  garment_type: string
  colors: string
  stock?: { size: string; quantity: number }[]
}

export default function ProductDetailPage() {
  const { productId } = useParams()
  const { pushRecent } = useShop()
  const [product, setProduct] = useState<Product | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    if (!productId) return
    fetch(`/api/products/${productId}`)
      .then(async (res) => {
        if (!res.ok) throw new Error('Product not found')
        return res.json()
      })
      .then((data: Product) => {
        setProduct(data)
        pushRecent(data.product_id)
      })
      .catch((err) => setError(err instanceof Error ? err.message : 'Load failed'))
  }, [productId, pushRecent])

  if (error) return <p className="form-error">{error}</p>
  if (!product) return <p className="muted">Loading…</p>

  return (
    <section className="detail">
      <Link className="back" to="/products">
        ← All products
      </Link>
      <div className="detail-grid">
        <img src={`/media/${product.image_file_path}`} alt={product.name} />
        <div>
          <p className="eyebrow">{product.garment_type}</p>
          <h1>{product.name}</h1>
          <p className="price">${product.price.toFixed(2)}</p>
          <p>{product.description}</p>
          <p className="muted">Colors: {product.colors}</p>
          {product.stock?.length ? (
            <div className="stock-board" aria-label="Stock by size">
              <h2>Stock by size</h2>
              <ul>
                {product.stock.map((s) => (
                  <li key={s.size} className={s.quantity === 0 ? 'oos' : ''}>
                    <span>{s.size}</span>
                    <span>{s.quantity === 0 ? 'Out of stock' : `${s.quantity} left`}</span>
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </div>
      </div>
    </section>
  )
}
