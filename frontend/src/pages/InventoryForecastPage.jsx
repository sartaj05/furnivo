import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getInventoryForecast } from '../lib/api'

export default function InventoryForecastPage() {
  const [items, setItems] = useState([]); const [horizon, setHorizon] = useState(30)
  useEffect(() => { getInventoryForecast().then((result) => { setItems(result.items || []); setHorizon(result.horizon_days || 30) }) }, [])
  return <AppShell title="Inventory forecasting" eyebrow="Demand, reorder automation & stockout risk"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Forecast horizon</p><h3>{horizon}-day demand view</h3></div></div>{items.map((item) => <div className="order-meta" key={item.inventory_id}><span><strong>{item.product}</strong><small>Available {item.available_quantity} · Demand {item.forecast_demand} · Projected {item.projected_quantity}</small></span><b className={item.risk === 'Stockout risk' ? 'priority-urgent' : ''}>{item.risk} · Order {item.suggested_order_quantity}</b></div>)}{!items.length && <p className="muted-copy">No inventory forecast data yet.</p>}</section></AppShell>
}
