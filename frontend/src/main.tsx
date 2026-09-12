import { useMemo, useState } from 'react'
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  Check,
  CircleDot,
  Clock3,
  Database,
  GitBranch,
  Play,
  RefreshCw,
  Search,
  Sparkles,
  TrendingUp,
  UploadCloud,
  Youtube,
} from 'lucide-react'
import './styles.css'

type StageStatus = 'idle' | 'active' | 'done' | 'error'

type Stage = {
  id: string
  title: string
  subtitle: string
  icon: typeof Activity
  status: StageStatus
}

const initialStages: Stage[] = [
  { id: 'ingest', title: 'Ingest', subtitle: 'YouTube source', icon: UploadCloud, status: 'idle' },
  { id: 'analyze', title: 'Story Intelligence', subtitle: 'Identify the real story', icon: BrainCircuit, status: 'idle' },
  { id: 'research', title: 'Research & Fact-check', subtitle: 'Verify claims and context', icon: Search, status: 'idle' },
  { id: 'graph', title: 'Story Graph', subtitle: 'Connect story history', icon: GitBranch, status: 'idle' },
  { id: 'related', title: 'Related Videos', subtitle: 'Rank what comes next', icon: GitBranch, status: 'idle' },
  { id: 'performance', title: 'Performance', subtitle: 'Read publication signals', icon: TrendingUp, status: 'idle' },
  { id: 'learning', title: 'Learning', subtitle: 'Improve ranking weights', icon: Sparkles, status: 'idle' },
]

const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, {
    ...init,
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
  })
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`)
  return response.json() as Promise<T>
}

function App() {
  const [stages, setStages] = useState(initialStages)
  const [channel, setChannel] = useState('@LajmePrime')
  const [limit, setLimit] = useState('25')
  const [running, setRunning] = useState(false)
  const [message, setMessage] = useState('Ready for a new story.')
  const [health, setHealth] = useState<'unknown' | 'online' | 'offline'>('unknown')
  const [selectedStage, setSelectedStage] = useState('ingest')

  const selected = useMemo(() => stages.find((stage) => stage.id === selectedStage) ?? stages[0], [selectedStage, stages])

  const setStage = (id: string, status: StageStatus) => {
    setStages((current) => current.map((stage) => (stage.id === id ? { ...stage, status } : stage)))
  }

  const checkHealth = async () => {
    try {
      await fetch(`${apiBase.replace(/\/api$/, '')}/health`)
      setHealth('online')
      setMessage('Backend is online.')
    } catch {
      setHealth('offline')
      setMessage('Backend is not reachable. Check VITE_API_URL and CORS.')
    }
  }

  const runWorkflow = async () => {
    setRunning(true)
    setMessage('Starting ingestion workflow...')
    setStages(initialStages)
    try {
      setStage('ingest', 'active')
      const result = await apiFetch<{ imported: number; updated: number; stories_created: number; stories_reused: number }>(
        `/youtube/ingest?channel=${encodeURIComponent(channel)}&limit=${encodeURIComponent(limit)}`,
        { method: 'POST' },
      )
      setStage('ingest', 'done')
      setStage('analyze', 'done')
      setMessage(`Ingest + story analysis complete. ${result.imported} new, ${result.updated} updated, ${result.stories_created} new stories.`)
    } catch (error) {
      setStage('ingest', 'error')
      setMessage(error instanceof Error ? error.message : 'Workflow failed.')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="brand-wrap">
          <div className="brand-mark">LP</div>
          <div>
            <div className="brand-name">Lajme Prime</div>
            <div className="brand-sub">Story Intelligence</div>
          </div>
        </div>
        <div className="top-actions">
          <button className="ghost-btn" onClick={checkHealth}>
            <Activity size={16} />
            {health === 'online' ? 'API online' : health === 'offline' ? 'API offline' : 'Check API'}
          </button>
          <div className="status-dot"><CircleDot size={15} /> Production workflow</div>
        </div>
      </header>

      <main className="main-grid">
        <section className="hero">
          <div className="eyebrow"><Sparkles size={14} /> Editorial command center</div>
          <h1>From a new upload to the next best story decision.</h1>
          <p>Run the Lajme Prime intelligence loop from one screen, inspect every stage, and keep the reasoning explainable.</p>
          <div className="control-card">
            <div className="control-field wide">
              <label>YouTube channel</label>
              <div className="input-wrap"><Youtube size={17} /><input value={channel} onChange={(event) => setChannel(event.target.value)} /></div>
            </div>
            <div className="control-field small">
              <label>Uploads</label>
              <div className="input-wrap"><Database size={17} /><input value={limit} onChange={(event) => setLimit(event.target.value)} inputMode="numeric" /></div>
            </div>
            <button className="primary-btn" disabled={running} onClick={runWorkflow}>
              {running ? <RefreshCw className="spin" size={17} /> : <Play size={17} />}
              {running ? 'Running…' : 'Run workflow'}
            </button>
          </div>
        </section>

        <section className="workflow-section">
          <div className="section-heading">
            <div>
              <span className="section-kicker">WORKFLOW</span>
              <h2>Story pipeline</h2>
            </div>
            <div className="run-state"><Clock3 size={15} /> {message}</div>
          </div>

          <div className="workflow-board">
            {stages.map((stage, index) => {
              const Icon = stage.icon
              return (
                <div key={stage.id} className="stage-row">
                  <button className={`stage-card ${selectedStage === stage.id ? 'selected' : ''}`} onClick={() => setSelectedStage(stage.id)}>
                    <div className={`stage-icon ${stage.status}`}><Icon size={18} /></div>
                    <div className="stage-copy">
                      <div className="stage-title">{stage.title}</div>
                      <div className="stage-sub">{stage.subtitle}</div>
                    </div>
                    <div className="stage-status">
                      {stage.status === 'done' ? <><Check size={15} /> Done</> : stage.status === 'active' ? <><RefreshCw className="spin" size={15} /> Working</> : stage.status === 'error' ? 'Error' : 'Ready'}
                    </div>
                  </button>
                  {index < stages.length - 1 && <ArrowRight className="workflow-arrow" size={17} />}
                </div>
              )
            })}
          </div>
        </section>

        <section className="insight-grid">
          <div className="panel large-panel">
            <div className="panel-head">
              <div><span className="section-kicker">SELECTED STAGE</span><h3>{selected.title}</h3></div>
              <span className={`badge ${selected.status}`}>{selected.status}</span>
            </div>
            <div className="insight-content">
              <div className="metric-row">
                <div className="metric"><span>Purpose</span><strong>{selected.subtitle}</strong></div>
                <div className="metric"><span>System role</span><strong>{selected.id === 'related' ? 'Viewer-next ranking' : 'Editorial intelligence'}</strong></div>
                <div className="metric"><span>Evidence</span><strong>{selected.id === 'performance' ? 'YouTube metrics' : 'Story + source context'}</strong></div>
              </div>
              <div className="explain-box">
                <div className="explain-title"><BrainCircuit size={16} /> Explainability</div>
                <p>Only completed backend actions are marked as done. The remaining cards represent the next editorial stages and their supporting intelligence systems.</p>
              </div>
            </div>
          </div>
          <div className="panel quick-panel">
            <div className="panel-head"><div><span className="section-kicker">LIVE SIGNALS</span><h3>System pulse</h3></div><Activity size={18} /></div>
            <div className="pulse-list">
              <div><span>API</span><strong className={health === 'online' ? 'positive' : ''}>{health === 'online' ? 'Online' : 'Not checked'}</strong></div>
              <div><span>Semantic retrieval</span><strong>pgvector</strong></div>
              <div><span>Story memory</span><strong>Persistent</strong></div>
              <div><span>Learning</span><strong>Adaptive weights</strong></div>
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

export default App
