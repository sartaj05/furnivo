import { useState } from 'react'
import AppShell from '../components/AppShell'
import { getRecommendations } from '../lib/api'

export default function RecommendationsPage() {
  const [form, setForm] = useState({ room: 'Living room', material: '', color: '', budget: 150000 }); const [items, setItems] = useState([]); const [engine, setEngine] = useState('');
  async function submit(event) { event.preventDefault(); const result = await getRecommendations(form); setItems(result.items || []); setEngine(result.engine || 'Recommendation engine') }
  return <AppShell title="Furniture recommendations" eyebrow="Smart products, materials & price guidance"><section className="panel"><form className="mini-form" onSubmit={submit}><select value={form.room} onChange={(event) => setForm({ ...form, room: event.target.value })}><option>Living room</option><option>Bedroom</option><option>Office</option><option>Dining room</option></select><input placeholder="Preferred material" value={form.material} onChange={(event) => setForm({ ...form, material: event.target.value })} /><input placeholder="Preferred color" value={form.color} onChange={(event) => setForm({ ...form, color: event.target.value })} /><input type="number" min="0" value={form.budget} onChange={(event) => setForm({ ...form, budget: event.target.value })} /><button className="button">Get recommendations</button></form></section><section className="inventory-grid">{items.map((item) => <article className="panel inventory-card" key={item.product.id}><p className="eyebrow">Score {item.score}</p><h3>{item.product.name}</h3><p>{item.reason}</p><strong>₹{Number(item.suggested_price || 0).toLocaleString('en-IN')}</strong></article>)}</section>{engine && <p className="muted-copy">Powered by {engine}.</p>}</AppShell>
}
