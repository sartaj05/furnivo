import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { createBackgroundJob, getBackgroundJobs, getWorkerStatus, retryBackgroundJob } from '../lib/api'
import '../styles/worker.css'

export default function DataAdminEnhancedPage() {
  const [jobs, setJobs] = useState([]); const [worker, setWorker] = useState(null); const [message, setMessage] = useState(''); const [error, setError] = useState('')
  async function load() { const [jobResult, workerResult] = await Promise.all([getBackgroundJobs(), getWorkerStatus()]); setJobs(jobResult.items || []); setWorker(workerResult.worker) }
  useEffect(() => { load().catch((err) => setError(err.message)) }, [])
  async function run(type) { setError(''); try { await createBackgroundJob(type); setMessage(`${type} queued.`); await load() } catch (err) { setError(err.message) } }
  async function retry(id) { setError(''); try { await retryBackgroundJob(id); setMessage('Job retry queued.'); await load() } catch (err) { setError(err.message) } }
  return <AppShell title="Background work" eyebrow="Reports, reindexing & worker health">
    {(error || message) && <div className={error ? 'form-error' : 'success-message'}>{error || message}</div>}
    {worker && <section className="panel worker-status"><div><p className="eyebrow">Worker status</p><h3>{worker.provider}</h3><small>{worker.mode} mode · capacity {worker.capacity} · retries enabled</small></div><span className="status status-complete">Ready</span></section>}
    <section className="panel"><div className="panel-heading"><div><p className="eyebrow">Queue controls</p><h3>Run maintenance work</h3></div><div className="card-actions"><button className="button button-small" onClick={() => run('catalog-reindex')}>Reindex catalog</button><button className="button button-small" onClick={() => run('report-refresh')}>Refresh reports</button></div></div></section>
    <section className="panel"><div className="panel-heading"><h3>Recent jobs</h3><span>{jobs.length} shown</span></div>{jobs.map((job) => <div className="data-row" key={job.id}><span><strong>{job.job_type}</strong><small>{new Date(job.created_at).toLocaleString()}{job.error ? ` · ${job.error}` : ''}</small></span><span className="card-actions"><b>{job.status}</b>{job.status === 'Failed' && <button className="button-link" onClick={() => retry(job.id)}>Retry</button>}</span></div>)}{!jobs.length && <p className="muted-copy">No background jobs have been queued.</p>}</section>
  </AppShell>
}
