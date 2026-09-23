import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getPredictiveAnalytics } from '../lib/api'

export default function PredictiveAnalyticsPage() {
  const [data, setData] = useState({ supplier_lead_times: [], quality: {}, purchase_recommendations: [] })
  useEffect(() => { getPredictiveAnalytics().then(setData) }, [])
  const quality = data.quality || {}
  return <AppShell title="Predictive procurement & quality" eyebrow="Lead-time risk, defects & purchase recommendations"><section className="metrics-grid"><article className="metric-card"><span>Inspection defect rate</span><strong>{quality.defect_rate || data.defect_rate || 0}%</strong></article><article className="metric-card"><span>Rework cost</span><strong>₹{Number(quality.rework_cost || data.rework_cost || 0).toLocaleString('en-IN')}</strong></article><article className="metric-card"><span>Suggested purchases</span><strong>{(data.purchase_recommendations || []).length}</strong></article></section><div className="analytics-grid"><section className="panel"><h3>Supplier lead times</h3>{(data.supplier_lead_times || []).map((item) => <div className="analytics-row" key={item.supplier}><span>{item.supplier}<small>{item.orders} orders · {item.late_rate}% late</small></span><b>{item.average_lead_days} days</b></div>)}{!data.supplier_lead_times?.length && <p className="muted-copy">No purchase history available yet.</p>}</section><section className="panel"><h3>Purchase recommendations</h3>{(data.purchase_recommendations || []).map((item) => <div className="analytics-row" key={item.inventory_id}><span>{item.product}<small>Available {item.available_quantity} · Reorder level {item.reorder_level}</small></span><b className={item.risk === 'Critical' ? 'priority-urgent' : ''}>{item.risk} · Order {item.suggested_order_quantity}</b></div>)}{!data.purchase_recommendations?.length && <p className="muted-copy">Stock levels look healthy.</p>}</section></div></AppShell>
}
