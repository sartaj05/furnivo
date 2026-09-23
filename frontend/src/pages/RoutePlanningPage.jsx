import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getRoutePlan, optimizeRoutePlan } from '../lib/api'

export default function RoutePlanningPage() {
  const [route, setRoute] = useState([]); const [distance, setDistance] = useState(0); const [message, setMessage] = useState('')
  async function load() { const result = await getRoutePlan(); setRoute(result.route || []); setDistance(result.total_distance_km || 0) }
  useEffect(() => { load() }, [])
  async function optimize() { const result = await optimizeRoutePlan(route.map((item) => item.id)); setRoute(result.route || []); setMessage('Route order optimized by scheduled date and stop sequence.') }
  return <AppShell title="Delivery route planning" eyebrow="Drivers, ETA & installation stops" actions={<button className="button button-small" onClick={optimize}>Optimize route</button>}><section className="metrics-grid"><article className="metric-card"><span>Stops</span><strong>{route.length}</strong></article><article className="metric-card"><span>Estimated distance</span><strong>{distance} km</strong></article></section><section className="panel"><div className="panel-heading"><h3>Today's route</h3></div>{route.map((item, index) => <div className="order-meta" key={item.id}><span><strong>Stop {item.route_order || index + 1}</strong> · {item.order_number} · {item.customer}<small>{item.driver_name || item.assigned_team || 'Driver not assigned'} · ETA {item.eta || item.time_slot}</small></span><b>{item.status}</b></div>)}{!route.length && <p className="muted-copy">No open delivery or installation stops.</p>}</section>{message && <div className="success-message">{message}</div>}</AppShell>
}
