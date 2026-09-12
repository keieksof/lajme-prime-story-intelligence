import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  BarChart3,
  BrainCircuit,
  Check,
  CircleHelp,
  FileCheck2,
  GitBranch,
  Home,
  Link2,
  Network,
  Play,
  RefreshCw,
  Search,
  Settings,
  Sparkles,
  UploadCloud,
  Video,
} from 'lucide-react'
import './styles.css'

type StageStatus = 'idle' | 'active' | 'done' | 'error'
type StageId = 'ingest' | 'analyze' | 'research' | 'graph' | 'related' | 'performance' | 'learning'
type AnalysisTab = 'summary' | 'claims' | 'entities' | 'emotion'

type Stage = { id: StageId; title: string; subtitle: string; icon: typeof Activity; status: StageStatus }
type VideoRow = { id: string; title: string; url: string; thumbnail_url?: string | null; description?: string | null; published_at?: string | null; story_id?: string | null }
type RelatedItem = Record<string, unknown> & { video_id?: string; title?: string; relationship_type?: string; score?: number; url?: string; thumbnail_url?: string | null }
type GraphMatch = { relationship_type?: string; score?: number; reasons?: string[] }

const stages: Stage[] = [
  { id: 'ingest', title: 'Ingest', subtitle: 'Nga YouTube', icon: UploadCloud, status: 'idle' },
  { id: 'analyze', title: 'Story Intelligence', subtitle: 'Analizë AI', icon: BrainCircuit, status: 'idle' },
  { id: 'research', title: 'Research & Fact-check', subtitle: 'Kontekst & Fakte', icon: Search, status: 'idle' },
  { id: 'graph', title: 'Story Graph', subtitle: 'Lidhje temash', icon: Network, status: 'idle' },
  { id: 'related', title: 'Related Videos', subtitle: 'Sugjerime inteligjente', icon: Link2, status: 'idle' },
  { id: 'performance', title: 'Performance', subtitle: 'Analiza performance', icon: BarChart3, status: 'idle' },
  { id: 'learning', title: 'Learning', subtitle: 'Përshtatje automatike', icon: Sparkles, status: 'idle' },
]

// Same-origin in production. Set VITE_API_URL only when the API lives on another host.
const apiBase = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '')

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${apiBase}${path}`, { ...init, headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) } })
  if (!response.ok) throw new Error((await response.text()) || `Request failed: ${response.status}`)
  return response.json() as Promise<T>
}

function formatPublished(value?: string | null) {
  if (!value) return 'Pa datë'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Pa datë'
  const hours = Math.max(1, Math.round((Date.now() - date.getTime()) / 3600000))
  return hours < 24 ? `${hours} orë më parë` : `${Math.round(hours / 24)} ditë më parë`
}

function thumbnailClass(index: number) { return `thumb thumb-${(index % 6) + 1}` }
function arrayValue(value: unknown) { return Array.isArray(value) ? value : [] }
function displayValue(value: unknown, fallback = 'Në pritje') { return value === null || value === undefined || value === '' ? fallback : typeof value === 'string' ? value : JSON.stringify(value) }

function VideoThumbnail({ video, index, compact = false }: { video?: VideoRow | RelatedItem; index: number; compact?: boolean }) {
  const thumbnail = typeof video?.thumbnail_url === 'string' ? video.thumbnail_url : undefined
  return (
    <div className={`${thumbnailClass(index)} ${compact ? 'thumb-compact' : ''}`}>
      {thumbnail ? <img src={thumbnail} alt="" loading="lazy" /> : <Video size={compact ? 17 : 22} />}
      <span>▶</span>
    </div>
  )
}

function App() {
  const [stageState, setStageState] = useState<Record<StageId, StageStatus>>(Object.fromEntries(stages.map((stage) => [stage.id, stage.status])) as Record<StageId, StageStatus>)
  const [channel, setChannel] = useState('@LajmePrime')
  const [limit, setLimit] = useState('10')
  const [health, setHealth] = useState<'unknown' | 'online' | 'offline'>('unknown')
  const [message, setMessage] = useState('Gati për workflow-in e radhës.')
  const [videos, setVideos] = useState<VideoRow[]>([])
  const [selectedVideoId, setSelectedVideoId] = useState('')
  const [selectedStage, setSelectedStage] = useState<StageId>('analyze')
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [research, setResearch] = useState<Record<string, unknown> | null>(null)
  const [related, setRelated] = useState<RelatedItem[]>([])
  const [graphMatches, setGraphMatches] = useState<GraphMatch[]>([])
  const [learning, setLearning] = useState<Record<string, unknown> | null>(null)
  const [analysisTab, setAnalysisTab] = useState<AnalysisTab>('summary')
  const [running, setRunning] = useState(false)

  const selectedVideo = useMemo(() => videos.find((video) => video.id === selectedVideoId) || videos[0], [videos, selectedVideoId])

  useEffect(() => {
    void checkHealth()
    void loadRecent()
  }, [])

  useEffect(() => {
    if (selectedVideo?.id) setSelectedVideoId(selectedVideo.id)
  }, [selectedVideo?.id])

  async function checkHealth() {
    try {
      await apiFetch('/../health')
      setHealth('online')
    } catch {
      setHealth('offline')
    }
  }

  async function loadRecent() {
    try {
      const data = await apiFetch<{ videos: VideoRow[] }>(`/youtube/recent?limit=${Math.max(1, Number(limit) || 10)}`)
      setVideos(data.videos || [])
      if (data.videos?.[0]) setSelectedVideoId(data.videos[0].id)
    } catch {
      setMessage('Backend-i nuk është ende i disponueshëm.')
    }
  }

  function setStage(id: StageId, status: StageStatus) {
    setStageState((current) => ({ ...current, [id]: status }))
  }

  async function runWorkflow() {
    setRunning(true)
    setMessage('Po ekzekutohet workflow-i...')
    setStage('ingest', 'active')
    try {
      const ingest = await apiFetch<{ videos?: VideoRow[] }>('/youtube/ingest', { method: 'POST', body: JSON.stringify({ channel, limit: Math.max(1, Number(limit) || 10) }) })
      setStage('ingest', 'done')
      await loadRecent()
      const ingestVideos = ingest.videos || []
      const video = ingestVideos[0] || videos[0]
      if (!video) throw new Error('Nuk u kthye asnjë video nga ingest.')
      setSelectedVideoId(video.id)

      setStage('analyze', 'active')
      const result = await apiFetch<Record<string, unknown>>('/stories/analyze-and-link', { method: 'POST', body: JSON.stringify({ video_id: video.id }) })
      setAnalysis(result)
      setGraphMatches((result.graph as { matches?: GraphMatch[] } | undefined)?.matches || [])
      setStage('analyze', 'done')

      setStage('research', 'active')
      try {
        const researchResult = await apiFetch<Record<string, unknown>>('/research/story', { method: 'POST', body: JSON.stringify({ video_id: video.id }) })
        setResearch(researchResult)
        setStage('research', 'done')
      } catch {
        setStage('research', 'error')
      }

      setStage('graph', 'done')
      setStage('related', 'active')
      try {
        const relatedResult = await apiFetch<{ items?: RelatedItem[] }>(`/related/videos/${video.id}?limit=5`)
        setRelated(relatedResult.items || [])
        setStage('related', 'done')
      } catch {
        setStage('related', 'error')
      }
      setStage('performance', 'idle')
      setStage('learning', 'idle')
      setMessage('Workflow-i përfundoi. Të dhënat u morën nga backend-i.')
    } catch (error) {
      setStage('ingest', 'error')
      setMessage(error instanceof Error ? error.message : 'Workflow-i dështoi.')
    } finally {
      setRunning(false)
    }
  }

  async function analyzeSelected() {
    if (!selectedVideo) return
    setStage('analyze', 'active')
    try {
      const result = await apiFetch<Record<string, unknown>>('/stories/analyze-and-link', { method: 'POST', body: JSON.stringify({ video_id: selectedVideo.id }) })
      setAnalysis(result)
      setGraphMatches((result.graph as { matches?: GraphMatch[] } | undefined)?.matches || [])
      setStage('analyze', 'done')
      setMessage('Story Intelligence u përditësua.')
    } catch (error) {
      setStage('analyze', 'error')
      setMessage(error instanceof Error ? error.message : 'Analiza dështoi.')
    }
  }

  async function loadRelated() {
    if (!selectedVideo) return
    setStage('related', 'active')
    try {
      const result = await apiFetch<{ items?: RelatedItem[] }>(`/related/videos/${selectedVideo.id}?limit=5`)
      setRelated(result.items || [])
      setStage('related', 'done')
    } catch (error) {
      setStage('related', 'error')
      setMessage(error instanceof Error ? error.message : 'Related Videos dështoi.')
    }
  }

  const analysisPeople = arrayValue(analysis?.people)
  const analysisTopics = arrayValue(analysis?.topics)
  const analysisClaims = arrayValue(analysis?.claims)

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand"><div className="brand-mark">LP</div><div><strong>LAJME PRIME</strong><small>Story Intelligence</small></div></div>
        <nav>
          <button className="nav-item active"><Home size={17} /> Dashboard</button>
          {stages.map((stage) => <button key={stage.id} className={`nav-item ${selectedStage === stage.id ? 'selected' : ''}`} onClick={() => setSelectedStage(stage.id)}><stage.icon size={17} /> {stage.title}</button>)}
          <div className="nav-divider" />
          <button className="nav-item"><Settings size={17} /> Settings</button>
          <button className="nav-item"><CircleHelp size={17} /> Help</button>
        </nav>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div><div className="eyebrow">NEWSROOM CONTROL CENTER</div><h1>Mirë se vini në Lajme Prime</h1><p>Story intelligence, research, related videos dhe learning në një workflow.</p></div>
          <div className="top-actions"><span className={`status-pill ${health}`}>{health === 'online' ? '● Backend online' : health === 'offline' ? '● Backend offline' : '● Kontrollohet...'}</span><button className="icon-btn" onClick={() => { void checkHealth(); void loadRecent() }}><RefreshCw size={17} /></button><div className="avatar">KP</div></div>
        </header>

        <section className="workflow-card">
          <div className="section-head"><div><h2>Workflow</h2><span>{message}</span></div><button className="primary-btn" disabled={running} onClick={() => void runWorkflow()}><Play size={16} /> {running ? 'Po ekzekutohet...' : 'Run Workflow'}</button></div>
          <div className="workflow-steps">{stages.map((stage, index) => { const Icon = stage.icon; const status = stageState[stage.id]; return <button key={stage.id} className={`workflow-step ${status}`} onClick={() => setSelectedStage(stage.id)}><span className="step-index">{status === 'done' ? <Check size={13} /> : index + 1}</span><Icon size={16} /><div><strong>{stage.title}</strong><small>{stage.subtitle}</small></div></button> })}</div>
          <div className="workflow-controls"><label>YouTube Channel<input value={channel} onChange={(event) => setChannel(event.target.value)} /></label><label>Videos<input type="number" min="1" max="50" value={limit} onChange={(event) => setLimit(event.target.value)} /></label><button className="secondary-btn" onClick={() => void loadRecent()}><RefreshCw size={15} /> Refresh</button></div>
        </section>

        <section className="status-grid">{stages.map((stage) => <div key={stage.id} className={`status-card ${stageState[stage.id]}`}><div className="status-card-icon"><stage.icon size={18} /></div><div><strong>{stage.title}</strong><span>{stageState[stage.id] === 'done' ? 'Completed' : stageState[stage.id] === 'active' ? 'Running' : stageState[stage.id] === 'error' ? 'Error' : 'Waiting'}</span></div></div>)}</section>

        <section className="dashboard-grid">
          <div className="panel recent-panel"><div className="panel-head"><div><h3>Recent YouTube Videos</h3><span>{videos.length ? `${videos.length} video të ngarkuara` : 'Nga backend-i'}</span></div><Video size={18} /></div>{videos.length ? <div className="video-list">{videos.map((video, index) => <button key={video.id} className={`video-row ${selectedVideo?.id === video.id ? 'selected' : ''}`} onClick={() => setSelectedVideoId(video.id)}><VideoThumbnail video={video} index={index} /><div className="video-copy"><strong>{video.title}</strong><span>{formatPublished(video.published_at)}</span></div></button>)}</div> : <div className="empty-state"><Video size={25} /><strong>Nuk ka video të ngarkuara</strong><span>Ekzekuto Run Workflow për të nisur ingest-in.</span></div>}</div>

          <div className="panel intelligence-panel"><div className="panel-head"><div><h3>Story Intelligence</h3><span>{selectedVideo?.title || 'Zgjidh një video'}</span></div><BrainCircuit size={18} /></div><div className="tabs">{(['summary', 'claims', 'entities', 'emotion'] as AnalysisTab[]).map((tab) => <button key={tab} className={analysisTab === tab ? 'active' : ''} onClick={() => setAnalysisTab(tab)}>{tab === 'summary' ? 'Summary' : tab === 'claims' ? 'Claims' : tab === 'entities' ? 'Entities' : 'Emotion'}</button>)}</div>{analysis ? <div className="analysis-body">{analysisTab === 'summary' && <><div className="metric-row"><span>Category</span><strong>{displayValue(analysis.category)}</strong></div><div className="metric-row"><span>Summary</span><p>{displayValue(analysis.summary)}</p></div><div className="metric-row"><span>People</span><div className="tag-list">{analysisPeople.map((item, i) => <span key={i}>{displayValue(item)}</span>)}</div></div></>}{analysisTab === 'claims' && <div className="claim-list">{analysisClaims.length ? analysisClaims.map((claim, i) => <div key={i} className="claim"><FileCheck2 size={15} /><span>{displayValue(claim)}</span></div>) : <div className="empty-inline">Nuk ka claims të strukturuara.</div>}</div>}{analysisTab === 'entities' && <><div className="metric-row"><span>People</span><div className="tag-list">{analysisPeople.map((item, i) => <span key={i}>{displayValue(item)}</span>)}</div></div><div className="metric-row"><span>Topics</span><div className="tag-list">{analysisTopics.map((item, i) => <span key={i}>{displayValue(item)}</span>)}</div></div></>}{analysisTab === 'emotion' && <div className="empty-inline">Emotion analysis do të shfaqet kur backend-i ta kthejë këtë sinjal.</div>}</div> : <div className="empty-state"><BrainCircuit size={25} /><strong>Story Intelligence pret analizën</strong><span>Zgjidh një video dhe nis analizën.</span><button className="secondary-btn" disabled={!selectedVideo} onClick={() => void analyzeSelected()}>Analyze selected</button></div>}</div>

          <div className="panel related-panel"><div className="panel-head"><div><h3>Related Videos</h3><span>Çfarë do të donte të shihte më pas shikuesi?</span></div><Link2 size={18} /></div>{related.length ? <div className="related-list">{related.map((item, index) => <button key={item.video_id || index} className="related-row" onClick={() => item.video_id && setSelectedVideoId(item.video_id)}><VideoThumbnail video={item} index={index} compact /><div><strong>{displayValue(item.title)}</strong><span>{displayValue(item.relationship_type, 'RELATED')} · {typeof item.score === 'number' ? `${Math.round(item.score * 100)}%` : 'n/a'}</span></div><span className="rank">#{index + 1}</span></button>)}</div> : <div className="empty-state"><Link2 size={25} /><strong>Nuk ka related videos</strong><span>Ngarko dhe analizo një video për të gjeneruar lidhjet.</span><button className="secondary-btn" disabled={!selectedVideo} onClick={() => void loadRelated()}>Find related</button></div>}</div>
        </section>

        <section className="bottom-grid">
          <div className="panel compact-panel"><div className="panel-head"><div><h3>Performance</h3><span>Outcome feedback</span></div><BarChart3 size={18} /></div><div className="big-number">{displayValue((analysis?.performance as Record<string, unknown> | undefined)?.outcome, 'Në pritje')}</div><p>Performance snapshots ndikojnë në ranking, jo në retraining të modelit bazë për çdo upload.</p></div>
          <div className="panel compact-panel"><div className="panel-head"><div><h3>Learning</h3><span>Adaptive ranking</span></div><Sparkles size={18} /></div><div className="learning-list">{learning ? <div className="metric-row"><span>Signals</span><strong>{displayValue(learning.signals_count)}</strong></div> : <div className="empty-inline">Learning signals do të shfaqen pasi të ketë performance data.</div>}</div></div>
          <div className="panel compact-panel"><div className="panel-head"><div><h3>Story Graph</h3><span>Relationship Inspector</span></div><Network size={18} /></div>{graphMatches.length ? <div className="graph-list">{graphMatches.slice(0, 4).map((match, index) => <div key={index} className="graph-row"><GitBranch size={15} /><div><strong>{displayValue(match.relationship_type)}</strong><span>{typeof match.score === 'number' ? `${Math.round(match.score * 100)}% confidence` : ''}</span></div></div>)}</div> : <div className="empty-inline">Graph links do të shfaqen pas Story Intelligence.</div>}</div>
        </section>

        {research && <section className="research-strip"><FileCheck2 size={17} /><div><strong>Research & Fact-check</strong><span>{displayValue(research.summary, 'Research u ekzekutua dhe rezultatet janë gati.')}</span></div></section>}
      </main>
    </div>
  )
}

export default App
