import { useEffect, useState } from 'react'
import AppShell from '../components/AppShell'
import { addLeadNote, addLeadTask, createLead, getLeads, updateLead, updateLeadStage, updateLeadTask } from '../lib/api'

const stages = ['New', 'Qualified', 'Proposal', 'Won', 'Lost']

export default function LeadsPage() {
  const [leads, setLeads] = useState([])
  const [team, setTeam] = useState([])
  const [selectedId, setSelectedId] = useState(null)
  const [note, setNote] = useState('')
  const [task, setTask] = useState({ title: '', due_date: '' })
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ name: '', company: '', email: '', phone: '', source: 'Website', value: 0, owner_id: '' })
  const [error, setError] = useState('')

  async function load() {
    const result = await getLeads()
    setLeads(result.items)
    setTeam(result.team || [])
    if (!selectedId && result.items[0]) setSelectedId(result.items[0].id)
  }
  useEffect(() => { load() }, [])

  const selected = leads.find((lead) => Number(lead.id) === Number(selectedId))

  async function changeStage(id, stage) { await updateLeadStage(id, stage); await load() }
  async function changeOwner(id, ownerId) { await updateLead(id, { owner_id: ownerId || null }); await load() }
  async function submitNote(event) { event.preventDefault(); if (!note.trim()) return; await addLeadNote(selected.id, note); setNote(''); await load() }
  async function submitTask(event) { event.preventDefault(); if (!task.title.trim()) return; await addLeadTask(selected.id, task); setTask({ title: '', due_date: '' }); await load() }
  async function toggleTask(taskItem) { await updateLeadTask(selected.id, taskItem.id, { is_done: !taskItem.is_done }); await load() }

  async function submitLead(event) {
    event.preventDefault()
    setError('')
    try {
      await createLead(form)
      setForm({ name: '', company: '', email: '', phone: '', source: 'Website', value: 0, owner_id: '' })
      setShowForm(false)
      await load()
    } catch (err) {
      setError(err.message || 'Unable to create lead')
    }
  }

  return <AppShell title="Lead CRM" eyebrow="Sales pipeline" actions={<button className="button button-small" onClick={() => setShowForm((value) => !value)}>{showForm ? 'Close' : 'New lead'}</button>}>
    {showForm && <form className="panel customer-editor" onSubmit={submitLead}><div className="panel-heading"><div><p className="eyebrow">Lead capture</p><h3>Add a new enquiry</h3></div><button type="button" className="text-button dark-text-button" onClick={() => setShowForm(false)}>Close</button></div><div className="form-grid form-grid-3">
      <label>Name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
      <label>Company<input value={form.company} onChange={(e) => setForm({ ...form, company: e.target.value })} /></label>
      <label>Phone<input value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} /></label>
      <label>Email<input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      <label>Source<select value={form.source} onChange={(e) => setForm({ ...form, source: e.target.value })}><option>Website</option><option>Referral</option><option>Instagram</option><option>Exhibition</option><option>Other</option></select></label>
      <label>Opportunity value<input type="number" min="0" value={form.value} onChange={(e) => setForm({ ...form, value: e.target.value })} /></label>
      <label>Owner<select value={form.owner_id} onChange={(e) => setForm({ ...form, owner_id: e.target.value })}><option value="">Current user</option>{team.map((member) => <option value={member.id} key={member.id}>{member.name}</option>)}</select></label>
    </div>{error && <div className="form-error">{error}</div>}<button className="button">Create lead</button></form>}
    <section className="crm-summary">{stages.slice(0, 4).map((stage) => { const stageLeads = leads.filter((lead) => lead.stage === stage); const total = stageLeads.reduce((sum, lead) => sum + Number(lead.value), 0); return <div key={stage}><span>{stage}</span><strong>{stageLeads.length}</strong><small>₹{total.toLocaleString('en-IN')}</small></div> })}</section>

    <div className="lead-workspace">
      <section className="lead-grid">{leads.map((lead) => <article className={`lead-card ${Number(selectedId) === Number(lead.id) ? 'selected' : ''}`} key={lead.id} onClick={() => setSelectedId(lead.id)}>
        <div className="lead-top"><div><h3>{lead.name}</h3><p>{lead.company}</p></div><span className="source-chip">{lead.source}</span></div>
        <div className="lead-details"><span>{lead.phone}</span><strong>₹{Number(lead.value).toLocaleString('en-IN')}</strong></div>
        <label onClick={(e) => e.stopPropagation()}>Pipeline stage<select value={lead.stage} onChange={(e) => changeStage(lead.id, e.target.value)}>{stages.map((stage) => <option key={stage}>{stage}</option>)}</select></label>
        <small className="owner-line">Owner: {lead.owner?.name || 'Unassigned'} · {(lead.tasks || []).filter((item) => !item.is_done).length} open tasks</small>
      </article>)}</section>

      {selected && <aside className="lead-detail panel">
        <div className="panel-heading"><div><p className="eyebrow">Lead workspace</p><h3>{selected.name}</h3></div><span className={`status status-${selected.stage.toLowerCase()}`}>{selected.stage}</span></div>
        <label>Owner<select value={selected.owner_id || ''} onChange={(e) => changeOwner(selected.id, e.target.value)}><option value="">Unassigned</option>{team.map((member) => <option value={member.id} key={member.id}>{member.name}</option>)}</select></label>

        <section className="lead-section"><h4>Enquiry</h4><p className="lead-interest">{selected.interest || 'General enquiry'}</p>{selected.message && <p className="lead-message">{selected.message}</p>}</section>

        <section className="lead-section"><h4>Tasks & reminders</h4><form className="mini-form" onSubmit={submitTask}><input placeholder="Follow-up task" value={task.title} onChange={(e) => setTask({ ...task, title: e.target.value })} /><input type="date" value={task.due_date} onChange={(e) => setTask({ ...task, due_date: e.target.value })} /><button className="button button-small">Add</button></form><div className="task-list">{(selected.tasks || []).map((item) => <label className={`task-item ${item.is_done ? 'done' : ''}`} key={item.id}><input type="checkbox" checked={Boolean(item.is_done)} onChange={() => toggleTask(item)} /><span><strong>{item.title}</strong><small>{item.due_date || 'No due date'}</small></span></label>)}</div></section>

        <section className="lead-section"><h4>Activity notes</h4><form className="mini-form note-form" onSubmit={submitNote}><textarea rows="2" placeholder="Add customer context, call notes, next step…" value={note} onChange={(e) => setNote(e.target.value)} /><button className="button button-small">Add note</button></form><div className="note-list">{(selected.notes || []).map((item) => <div key={item.id}><p>{item.body}</p><small>{item.author} · {new Date(item.created_at).toLocaleDateString()}</small></div>)}</div></section>
      </aside>}
    </div>
  </AppShell>
}
