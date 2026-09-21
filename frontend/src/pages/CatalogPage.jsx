import { useEffect, useMemo, useState } from 'react'
import AppShell from '../components/AppShell'
import { getProducts } from '../lib/api'

export default function CatalogPage() {
  const [products, setProducts] = useState([])
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('All')
  const [mode, setMode] = useState('')

  useEffect(() => {
    getProducts().then((result) => {
      setProducts(result.items)
      setMode(result.mode || 'api')
    })
  }, [])

  const categories = ['All', ...new Set(products.map((item) => item.category))]

  const filtered = useMemo(
    () =>
      products.filter((item) => {
        const searchMatch = `${item.name} ${item.sku} ${item.material}`
          .toLowerCase()
          .includes(query.toLowerCase())
        const categoryMatch = category === 'All' || item.category === category
        return searchMatch && categoryMatch
      }),
    [products, query, category],
  )

  return (
    <AppShell
      title="Product catalog"
      eyebrow="Commercial library"
      actions={<span className="mode-chip">{mode === 'demo' ? 'Local demo data' : 'Live catalog'}</span>}
    >
      <div className="toolbar">
        <input
          className="search-input"
          placeholder="Search name, SKU or material…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <div className="filter-row">
          {categories.map((item) => (
            <button
              className={category === item ? 'filter-chip active' : 'filter-chip'}
              key={item}
              onClick={() => setCategory(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </div>

      <section className="product-grid">
        {filtered.map((product) => (
          <article className="product-card" key={product.id}>
            <div className="product-image">
              <img src={product.image} alt={product.name} />
              <span>{product.category}</span>
            </div>
            <div className="product-body">
              <small>{product.sku}</small>
              <h3>{product.name}</h3>
              <p>{product.material}</p>
              <div className="product-price">
                <strong>₹{Number(product.price).toLocaleString('en-IN')}</strong>
                <span>/ {product.unit}</span>
              </div>
            </div>
          </article>
        ))}
      </section>
    </AppShell>
  )
}
