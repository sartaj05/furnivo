import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getAnalytics } from '../lib/api'
import '../styles/profitability.css'

const money = (value) => `INR ${Number(value || 0).toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export default function AnalyticsEnhancedPage() {
  const [data, setData] = useState(null); const [error, setError] = useState('')
  useEffect(() => { getAnalytics().then(setData).catch((err) => setError(err.message)) }, [])
  if (error) return <AppShell title="Profitability & forecasting" eyebrow="Margin, cost drivers & forecast confidence"><div className="form-error">{error}</div></AppShell>
  if (!data) return <AppShell title="Profitability & forecasting" eyebrow="Margin, cost drivers & forecast confidence"><p className="muted-copy">Loading profitability…</p></AppShell>
  const profit = data.profitability || {}; const breakdown = profit.cost_breakdown || {}; const forecast = data.forecast || {}
  return <AppShell title="Profitability & forecasting" eyebrow="Material, labor, wastage, shipping & tax-aware margins">
    <section className="analytics-metrics"><article className="panel analytics-metric"><p className="eyebrow">Net project revenue</p><strong>{money(profit.revenue)}</strong></article><article className="panel analytics-metric"><p className="eyebrow">Gross profit</p><strong>{money(profit.gross_profit)}</strong></article><article className="panel analytics-metric"><p className="eyebrow">Gross margin</p><strong>{profit.margin_percent || 0}%</strong></article><article className="panel analytics-metric"><p className="eyebrow">Forecast confidence</p><strong>{forecast.confidence_percent || 0}%</strong></article></section>
    <div className="analytics-grid"><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Cost drivers</p><h3>Where margin is moving</h3></div></div>{[['Material', breakdown.material], ['Labor', breakdown.labor], ['Wastage', breakdown.wastage], ['Shipping', breakdown.shipping], ['Discounts', breakdown.discounts], ['Taxes', breakdown.taxes]].map(([label, value]) => <div className="analytics-row" key={label}><span>{label}</span><strong>{money(value)}</strong></div>)}</section><section className="panel"><div className="panel-heading"><div><p className="eyebrow">Forecast</p><h3>Weighted revenue outlook</h3></div></div><div className="forecast-grid"><div><span>Next 30 days</span><strong>{money(forecast.next_30_days)}</strong></div><div><span>Next 90 days</span><strong>{money(forecast.next_90_days)}</strong></div></div><p className="muted-copy">{forecast.method}</p>{(forecast.risks || []).map((risk) => <div className="forecast-risk" key={risk}>{risk}</div>)}</section></div>
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Project profitability</p><h3>Margin by confirmed order</h3></div></div>{(profit.projects || []).map((item) => <div className="analytics-row" key={item.order_number}><span><strong>{item.order_number}</strong><small>{item.customer} · Cost {money(item.estimated_cost)}</small></span><b className={item.margin_percent < 20 ? 'priority-high' : 'control-good'}>{item.margin_percent}% · {money(item.gross_profit)}</b></div>)}</section>
  </AppShell>
}
