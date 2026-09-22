import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { getReportSummary } from '../lib/api'

const labels = [['quotes', 'Quotes'], ['leads', 'Leads'], ['orders', 'Orders'], ['invoices', 'Invoices'], ['payments', 'Payments'], ['inventory', 'Inventory']]

function money(value) { return `₹${Number(value || 0).toLocaleString('en-IN')}` }

export default function ReportsPage() {
  const [report, setReport] = useState(null); const [error, setError] = useState('')
  useEffect(() => { getReportSummary().then((result) => setReport(result.data)).catch((err) => setError(err.message)) }, [])
  function downloadCsv() { if (!report) return; const rows = [['Metric', 'Count', 'Value', 'Extra'], ...labels.map(([key, label]) => [label, report[key].count ?? report[key].items, report[key].value ?? report[key].available_units, key === 'leads' ? `Won: ${report[key].won}` : key === 'invoices' ? `Paid: ${money(report[key].paid)}; Balance: ${money(report[key].balance)}` : key === 'inventory' ? `Low stock: ${report[key].low_stock}` : ''])]; const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(',')).join('\n'); const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'furnivo-report.csv'; anchor.click(); URL.revokeObjectURL(url) }
  async function downloadPdf() { if (!report) return; const { jsPDF } = await import('jspdf'); const doc = new jsPDF(); doc.setFontSize(20); doc.text('FURNIVO REPORT', 16, 20); doc.setFontSize(11); labels.forEach(([key, label], index) => { const data = report[key]; doc.text(`${label}: ${data.count ?? data.items} | ${money(data.value ?? data.available_units)}`, 16, 36 + index * 10) }); doc.save('furnivo-report.pdf') }
  return <AppShell title="Reports & exports" eyebrow="Business intelligence" actions={<><button className="button button-small" onClick={downloadCsv}>Export CSV / Excel</button><button className="button button-small button-ghost" onClick={downloadPdf}>Export PDF</button></>}>
    {error && <div className="form-error">{error}</div>}{report && <section className="report-grid">{labels.map(([key, label]) => { const data = report[key]; return <article className="panel report-card" key={key}><p className="eyebrow">{label}</p><strong>{data.count ?? data.items}</strong><span>{money(data.value ?? data.available_units)}</span>{key === 'leads' && <small>{data.won} won</small>}{key === 'invoices' && <small>{money(data.balance)} outstanding</small>}{key === 'inventory' && <small>{data.low_stock} low-stock items</small>}</article> })}</section>}
  </AppShell>
}
