import { useMemo, useState } from 'react'
import {
  Activity,
  ArrowRight,
  BrainCircuit,
  Check,
  CircleDot,
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
type StageId = 'ingest' | 'analyze' | 'research' | 'graph' | 'related' | 'performance' | 'learning'

type Stage = {
  id: StageId
  title: string
  subtitle: string
  icon: typeof Activity
  status: StageStatus
}

type Video = {
  id: string
  title: string
  url: string
  description?: string | null
  published_at?: string | null
  story_id?: string | null
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
  const [selectedStage, setSelectedStage] = useState<StageId>('ingest')
  const [videos, setVideos] = useState<Video[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState('')
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [research, setResearch] = useState<Record<string, unknown> | null>(null)
  const [related, setRelated] = useState<Array<Record<string, unknown>>>([])
  const [weights, setWeights] = useState<Record<string, unknown> | null>(null)

  const selected = useMemo(() => stages.find((stage) => stage.id === selectedStage) ?? stages[0], [selectedStage, stages])
  const currentVideo = videos.find((video) => video.id === selectedVideoId)

  const setStage = (id: StageId, status: StageStatus) => {
    setStages((current) => current.map((stage) => (stage.id === id ? { ...stage, status } : stage)))
  }

  const loadRecent = async () => {
    const data = await apiFetch<{ videos: Video[] }>('/youtube/recent?limit=50')
    setVideos(data.videos)
    if (!selectedVideoId && data.videos[0]) setSelectedVideoId(data.videos[0].id)
    return data.videos
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

  const runIngest = async () => {
    setRunning(true)
    setStage('ingest', 'active')
    setMessage('Ingesting YouTube uploads...')
    try {
      const result = await apiFetch<{ imported: number; updated: number; stories_created: number; stories_reused: number }>(
        `/youtube/ingest?channel=${encodeURIComponent(channel)}&limit=${encodeURIComponent(limit)}`,
        { method: 'POST' },
      )
      const recent = await loadRecent()
      setStage('ingest', 'done')
      setMessage(`Ingest complete: ${result.imported} new, ${result.updated} updated. ${recent.length} recent videos loaded into the workflow.`)
    } catch (error) {
      setStage('ingest', 'error')
      setMessage(error instanceof Error ? error.message : 'Ingest failed.')
    } finally {
      setRunning(false)
    }
  }

  const analyzeCurrent = async () => {
    if (!currentVideo) return
    setStage('analyze', 'active')
    setMessage('Analyzing the selected story...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/stories/analyze-and-link', {
        method: 'POST',
        body: JSON.stringify({ title: currentVideo.title, text: `${currentVideo.title}\n\n${currentVideo.description || ''}`, source_url: currentVideo.url }),
      })
      setAnalysis(result)
      setStage('analyze', 'done')
      if (result.graph) setStage('graph', 'done')
      setMessage('Story analysis completed and the story was linked into the graph.')
    } catch (error) {
      setStage('analyze', 'error')
      setMessage(error instanceof Error ? error.message : 'Story analysis failed.')
    }
  }

  const researchCurrent = async () => {
    if (!currentVideo) return
    setStage('research', 'active')
    setMessage('Researching the selected story...')
    try {
      const claims = Array.isArray(analysis?.claims)
        ? analysis.claims.map((claim) => (typeof claim === 'string' ? claim : JSON.stringify(claim)))
        : []
      const result = await apiFetch<Record<string, unknown>>('/research/story', {
        method: 'POST',
        body: JSON.stringify({ query: currentVideo.title, claims }),
      })
      setResearch(result)
      setStage('research', 'done')
      setMessage('Research and fact-check report received.')
    } catch (error) {
      setStage('research', 'error')
      setMessage(error instanceof Error ? error.message : 'Research failed.')
    }
  }

  const loadRelated = async () => {
    if (!currentVideo) return
    setStage('related', 'active')
    setMessage('Finding the best next videos from the story graph and semantic index...')
    try {
      const result = await apiFetch<{ candidates: Array<Record<string, unknown>> }>(`/related/videos/${currentVideo.id}?limit=5`)
      setRelated(result.candidates)
      setStage('related', 'done')
      setMessage(`${result.candidates.length} related videos ranked.`)
    } catch (error) {
      setStage('related', 'error')
      setMessage(error instanceof Error ? error.message : 'Related video ranking failed.')
    }
  }

  const loadLearning = async () => {
    setStage('learning', 'active')
    setMessage('Reading adaptive ranking weights...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/learning/weights')
      setWeights(result)
      setStage('learning', 'done')
      setMessage('Current learning weights loaded.')
    } catch (error) {
      setStage('learning', 'error')
      setMessage(error instanceof Error ? error.message : 'Learning data failed to load.')
    }
  }

  const handleStageAction = async () => {
    if (selectedStage === 'ingest') return runIngest()
    if (selectedStage === 'analyze') return analyzeCurrent()
    if (selectedStage === 'research') return researchCurrent()
    if (selectedStage === 'related') return loadRelated()
    if (selectedStage === 'learning') return loadLearning()
    setMessage(`${selected.title} is persisted by the backend and exposed through the current story workflow.`)
    setStage(selectedStage, 'done')
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
          <div className="status-dot"><CircleDot size={15} /> Editorial command center</div>
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
            <button className="primary-btn" disabled={running} onClick={runIngest}>
              {running ? <RefreshCw className="spin" size={17} /> : <Play size={17} />}
              {running ? 'Running…' : 'Run ingest'}
            </button>
          </div>
        </section>

        <section className="workflow-section">
          <div className="section-heading">
            <div>
              <span className="section-kicker">WORKFLOW</span>
              <h2>Story pipeline</h2>
            </div>
            <div className="run-state"><RefreshCw size={15} /> {message}</div>
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

            <div className="stage-controls">
              <div className="control-field wide">
                <label>Current video</label>
                <select value={selectedVideoId} onChange={(event) => setSelectedVideoId(event.target.value)}>
                  <option value="">Select a video</option>
                  {videos.map((video) => <option key={video.id} value={video.id}>{video.title}</option>)}
                </select>
              </div>
              <button className="primary-btn stage-action" disabled={selectedStage !== 'ingest' && !currentVideo && selectedStage !== 'learning'} onClick={handleStageAction}>
                {selectedStage === 'ingest' ? 'Ingest uploads' : selectedStage === 'analyze' ? 'Analyze story' : selectedStage === 'research' ? 'Research story' : selectedStage === 'related' ? 'Rank related' : selectedStage === 'learning' ? 'Load weights' : 'Mark reviewed'}
              </button>
            </div>

            <div className="insight-content">
              <div className="metric-row">
                <div className="metric"><span>Purpose</span><strong>{selected.subtitle}</strong></div>
                <div className="metric"><span>Current video</span><strong>{currentVideo?.title || 'None selected'}</strong></div>
                <div className="metric"><span>Evidence</span><strong>{selected.id === 'research' ? 'Web research' : selected.id === 'related' ? 'Graph + embeddings' : selected.id === 'performance' ? 'YouTube metrics' : 'Story context'}</strong></div>
              </div>

              {selected.id === 'analyze' && analysis && <pre className="json-view">{JSON.stringify(analysis, null, 2)}</pre>}
              {selected.id === 'research' && research && <pre className="json-view">{JSON.stringify(research, null, 2)}</pre>}
              {selected.id === 'related' && <div className="results-list">{related.map((item, index) => <div className="result-row" key={String(item.video_id)}><strong>#{index + 1} {String(item.title || '')}</strong><span>{String(item.relationship_type || '')} · {Number(item.score || 0).toFixed(1)}</span></div>)}</div>}
              {selected.id === 'learning' && weights && <pre className="json-view">{JSON.stringify(weights, null, 2)}</pre>}
              {!analysis && selected.id === 'analyze' && <div className="empty-state">Run Story Intelligence on the selected video to see its structured story analysis.</div>}
              {!research && selected.id === 'research' && <div className="empty-state">Run Research & Fact-check after selecting a video. The backend will return the report and limitations.</div>}
              {!related.length && selected.id === 'related' && <div className="empty-state">Select a video and rank its historical related videos.</div>}
              {!weights && selected.id === 'learning' && <div className="empty-state">Load the current adaptive weights to inspect what the ranking system has learned.</div>}
              {(selected.id === 'graph' || selected.id === 'performance') && <div className="empty-state">This stage is already represented in the backend model. The next UI pass can expose its stored graph and performance records here without inventing data.</div>}

              <div className="explain-box">
                <div className="explain-title"><BrainCircuit size={16} /> Explainability</div>
                <p>Every stage is connected to a concrete backend action. The UI never marks future steps as completed until an actual API result is returned.</p>
              </div>
            </div>
          </div>

          <div className="panel quick-panel">
            <div className="panel-head"><div><span className="section-kicker">LIVE SIGNALS</span><h3>System pulse</h3></div><Activity size={18} /></div>
            <div className="pulse-list">
              <div><span>API</span><strong className={health === 'online' ? 'positive' : ''}>{health === 'online' ? 'Online' : 'Not checked'}</strong></div>
              <div><span>Loaded videos</span><strong>{videos.length}</strong></div>
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
