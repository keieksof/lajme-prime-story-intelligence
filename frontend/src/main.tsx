import { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  BarChart3,
  BrainCircuit,
  Check,
  CircleHelp,
  CircleUserRound,
  Database,
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

type Stage = {
  id: StageId
  title: string
  subtitle: string
  short: string
  icon: typeof Activity
  status: StageStatus
}

type VideoRow = {
  id: string
  title: string
  url: string
  description?: string | null
  published_at?: string | null
  story_id?: string | null
}

type RelatedItem = Record<string, unknown> & {
  video_id?: string
  title?: string
  relationship_type?: string
  score?: number
  url?: string
}

const stages: Stage[] = [
  { id: 'ingest', title: 'Ingest', subtitle: 'Nga YouTube', short: 'YouTube', icon: UploadCloud, status: 'idle' },
  { id: 'analyze', title: 'Story Intelligence', subtitle: 'Analizë AI', short: 'AI', icon: BrainCircuit, status: 'idle' },
  { id: 'research', title: 'Research & Fact-check', subtitle: 'Kontekst & Fakte', short: 'Research', icon: Search, status: 'idle' },
  { id: 'graph', title: 'Story Graph', subtitle: 'Lidhje temash', short: 'Graph', icon: Network, status: 'idle' },
  { id: 'related', title: 'Related Videos', subtitle: 'Sugjerime inteligjente', short: 'Related', icon: Link2, status: 'idle' },
  { id: 'performance', title: 'Performance', subtitle: 'Analiza performance', short: 'Metrics', icon: BarChart3, status: 'idle' },
  { id: 'learning', title: 'Learning', subtitle: 'Përshtatje automatike', short: 'Learning', icon: Sparkles, status: 'idle' },
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

function formatPublished(value?: string | null) {
  if (!value) return 'Pa datë'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Pa datë'
  const hours = Math.max(1, Math.round((Date.now() - date.getTime()) / 3600000))
  return hours < 24 ? `${hours} orë më parë` : `${Math.round(hours / 24)} ditë më parë`
}

function thumbnailClass(index: number) {
  return `thumb thumb-${(index % 6) + 1}`
}

function App() {
  const [stageState, setStageState] = useState<Record<StageId, StageStatus>>(
    Object.fromEntries(stages.map((stage) => [stage.id, stage.status])) as Record<StageId, StageStatus>,
  )
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
  const [weights, setWeights] = useState<Record<string, unknown> | null>(null)
  const [running, setRunning] = useState(false)

  const currentVideo = videos.find((video) => video.id === selectedVideoId)
  const selected = useMemo(() => stages.find((stage) => stage.id === selectedStage) ?? stages[0], [selectedStage])

  const patchStage = (id: StageId, status: StageStatus) => {
    setStageState((current) => ({ ...current, [id]: status }))
  }

  const loadRecent = async () => {
    const result = await apiFetch<{ videos: VideoRow[] }>('/youtube/recent?limit=50')
    setVideos(result.videos)
    if (!selectedVideoId && result.videos[0]) setSelectedVideoId(result.videos[0].id)
    return result.videos
  }

  useEffect(() => {
    void checkHealth()
    void loadRecent().catch(() => undefined)
  }, [])

  async function checkHealth() {
    try {
      const response = await fetch(`${apiBase.replace(/\/api$/, '')}/health`)
      if (!response.ok) throw new Error('health')
      setHealth('online')
      setMessage('API është online.')
    } catch {
      setHealth('offline')
      setMessage('API nuk është e arritshme. Kontrollo VITE_API_URL dhe CORS.')
    }
  }

  async function runIngest() {
    setRunning(true)
    patchStage('ingest', 'active')
    setMessage('Po marr videot e reja nga YouTube...')
    try {
      const result = await apiFetch<{ imported: number; updated: number; stories_created?: number; stories_reused?: number }>(
        `/youtube/ingest?channel=${encodeURIComponent(channel)}&limit=${encodeURIComponent(limit)}`,
        { method: 'POST' },
      )
      await loadRecent()
      patchStage('ingest', 'done')
      patchStage('analyze', 'active')
      setMessage(`${result.imported} video të reja, ${result.updated} të përditësuara. Story Intelligence është gati.`)
    } catch (error) {
      patchStage('ingest', 'error')
      setMessage(error instanceof Error ? error.message : 'Ingest dështoi.')
    } finally {
      setRunning(false)
    }
  }

  async function analyzeCurrent() {
    if (!currentVideo) return
    patchStage('analyze', 'active')
    setMessage('Po analizoj thelbin e historisë dhe lidhjet ekzistuese...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/stories/analyze-and-link', {
        method: 'POST',
        body: JSON.stringify({
          title: currentVideo.title,
          text: `${currentVideo.title}\n\n${currentVideo.description || ''}`,
          source_url: currentVideo.url,
        }),
      })
      setAnalysis(result)
      patchStage('analyze', 'done')
      if (result.graph) patchStage('graph', 'done')
      setMessage('Story Intelligence u përfundua dhe historia u lidh me graph-in.')
    } catch (error) {
      patchStage('analyze', 'error')
      setMessage(error instanceof Error ? error.message : 'Story Intelligence dështoi.')
    }
  }

  async function researchCurrent() {
    if (!currentVideo) return
    patchStage('research', 'active')
    setMessage('Po kërkoj burime dhe po kontrolloj pretendimet...')
    try {
      const claims = Array.isArray(analysis?.claims)
        ? analysis.claims.map((claim) => (typeof claim === 'string' ? claim : JSON.stringify(claim)))
        : []
      const result = await apiFetch<Record<string, unknown>>('/research/story', {
        method: 'POST',
        body: JSON.stringify({ query: currentVideo.title, claims }),
      })
      setResearch(result)
      patchStage('research', 'done')
      setMessage('Raporti i research dhe fact-check u kthye me sukses.')
    } catch (error) {
      patchStage('research', 'error')
      setMessage(error instanceof Error ? error.message : 'Research dështoi.')
    }
  }

  async function loadRelated() {
    if (!currentVideo) return
    patchStage('related', 'active')
    setMessage('Po gjej videot që një shikues do të donte të shihte më pas...')
    try {
      const result = await apiFetch<{ candidates: RelatedItem[] }>(`/related/videos/${currentVideo.id}?limit=5`)
      setRelated(result.candidates)
      patchStage('related', 'done')
      setMessage(`${result.candidates.length} sugjerime të rankuara.`)
    } catch (error) {
      patchStage('related', 'error')
      setMessage(error instanceof Error ? error.message : 'Related Videos dështoi.')
    }
  }

  async function loadLearning() {
    patchStage('learning', 'active')
    setMessage('Po lexoj peshat e fundit të learning loop...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/learning/weights')
      setWeights(result)
      patchStage('learning', 'done')
      setMessage('Adaptive learning weights u ngarkuan.')
    } catch (error) {
      patchStage('learning', 'error')
      setMessage(error instanceof Error ? error.message : 'Learning dështoi.')
    }
  }

  const runSelectedStage = async () => {
    if (selectedStage === 'ingest') return runIngest()
    if (selectedStage === 'analyze') return analyzeCurrent()
    if (selectedStage === 'research') return researchCurrent()
    if (selectedStage === 'related') return loadRelated()
    if (selectedStage === 'learning') return loadLearning()
    setMessage(`${selected.title} është i lidhur me modelet e backend-it dhe do të shfaqet këtu pa shpikur të dhëna.`)
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="logo-lockup">
          <div className="logo-main">LAJME <span>PRIME</span></div>
          <div className="logo-sub">STORY INTELLIGENCE</div>
        </div>

        <nav className="sidebar-nav">
          <button className="nav-item active"><Home size={19} /> Dashboard</button>
          <button className="nav-item"><Video size={19} /> YouTube Ingest</button>
          <button className="nav-item"><BrainCircuit size={19} /> Story Intelligence</button>
          <button className="nav-item"><Search size={19} /> Research & Fact-check</button>
          <button className="nav-item"><Network size={19} /> Story Graph</button>
          <button className="nav-item"><Link2 size={19} /> Related Videos</button>
          <button className="nav-item"><BarChart3 size={19} /> Performance</button>
          <button className="nav-item"><Sparkles size={19} /> Learning</button>
        </nav>

        <div className="sidebar-bottom">
          <button className="nav-item"><Settings size={19} /> Settings</button>
          <button className="nav-item"><CircleHelp size={19} /> Help</button>
          <div className="sidebar-quote">“Më shumë se lajme.<br />Insight që lidh gjithçka.”<br /><span>Lajme Prime</span></div>
        </div>
      </aside>

      <section className="content-area">
        <header className="content-topbar">
          <div>
            <h1>Mirë se vini në Lajme Prime</h1>
            <p>AI-powered workflow për të kthyer videot në histori më të mëdha.</p>
          </div>
          <div className="profile-area">
            <div className={`api-pill ${health}`}><span /> API {health === 'online' ? 'Online' : health === 'offline' ? 'Offline' : 'Status'}</div>
            <div className="avatar">KX</div>
            <div className="profile-copy"><strong>Krenar Xhafaj</strong><span>Admin</span></div>
            <span className="chevron">⌄</span>
          </div>
        </header>

        <main className="workspace">
          <section className="workflow-panel">
            {stages.map((stage, index) => {
              const status = stageState[stage.id]
              return (
                <div key={stage.id} className="workflow-step-wrap">
                  <button className={`workflow-step ${selectedStage === stage.id ? 'selected' : ''}`} onClick={() => setSelectedStage(stage.id)}>
                    <div className={`step-circle ${status}`}>
                      {status === 'done' ? <Check size={16} /> : index + 1}
                    </div>
                    <strong>{stage.title}</strong>
                    <span>{stage.subtitle}</span>
                  </button>
                  {index < stages.length - 1 && <div className="step-connector" />}
                </div>
              )
            })}
          </section>

          <section className="ingest-bar">
            <div className="ingest-field channel-field">
              <div className="youtube-badge"><Video size={20} /></div>
              <div><strong>{channel}</strong><span>Channel për të analizuar</span></div>
            </div>
            <div className="ingest-field">
              <div><strong>{limit}</strong><span>Numri i videove</span></div>
            </div>
            <button className="run-workflow" onClick={runIngest} disabled={running}>
              {running ? <RefreshCw className="spin" size={20} /> : <Play size={20} />}
              {running ? 'Po ekzekutohet...' : 'Run Workflow'}
            </button>
          </section>

          <section className="status-strip">
            {stages.map((stage) => {
              const status = stageState[stage.id]
              const Icon = stage.icon
              return (
                <button key={stage.id} className={`status-card ${status}`} onClick={() => setSelectedStage(stage.id)}>
                  <div className="status-icon"><Icon size={18} /></div>
                  <div><strong>{stage.title}</strong><span>{status === 'done' ? 'Përfunduar' : status === 'active' ? 'Në proces' : status === 'error' ? 'Gabim' : 'Në pritje'}</span><small>{stage.id === 'ingest' ? `${videos.length || 0} video të marra` : status === 'done' ? 'Gati për hapin tjetër' : 'Do të ekzekutohet'}</small></div>
                </button>
              )
            })}
          </section>

          <section className="dashboard-grid">
            <div className="panel recent-panel">
              <div className="panel-title-row"><div><h2>Videot e fundit nga YouTube</h2><span>Burimi i historisë së re</span></div><button className="text-link" onClick={() => void loadRecent()}>Shiko të gjitha →</button></div>
              <div className="recent-list">
                {videos.length === 0 && <div className="empty-soft"><Video size={20} /> Nuk ka video të ngarkuara. Ekzekuto Ingest.</div>}
                {videos.slice(0, 5).map((video, index) => (
                  <button key={video.id} className={`recent-row ${selectedVideoId === video.id ? 'selected' : ''}`} onClick={() => setSelectedVideoId(video.id)}>
                    <div className={thumbnailClass(index)}><Video size={22} /><span>▶</span></div>
                    <div className="recent-copy"><strong>{video.title}</strong><span>{formatPublished(video.published_at)} · Story {video.story_id ? 'e lidhur' : 'e re'}</span></div>
                  </button>
                ))}
              </div>
            </div>

            <div className="panel intelligence-panel">
              <div className="panel-title-row"><div><h2><BrainCircuit size={19} /> Story Intelligence <em>AI</em></h2><span>{currentVideo ? currentVideo.title : 'Zgjidh një video për analizë'}</span></div><span className="live-tag"><span /> {stageState.analyze === 'done' ? 'Gati' : stageState.analyze === 'active' ? 'Në proces' : 'Në pritje'}</span></div>
              <div className="analysis-tabs"><span className="active">Përmbledhje</span><span>Pikat kryesore</span><span>Entitete</span><span>Tona & Emocion</span></div>
              <div className="analysis-box">
                <h3>Përmbledhje (AI)</h3>
                <p>{typeof analysis?.summary === 'string' ? analysis.summary : currentVideo ? 'Kliko “Analizo story” për të gjeneruar përmbledhjen e strukturuar të historisë.' : 'Zgjidh një video nga lista për të nisur analizën.'}</p>
              </div>
              <div className="analysis-metrics">
                <div><span>Tema kryesore</span><strong>{Array.isArray(analysis?.topics) && analysis.topics.length ? String(analysis.topics[0]) : 'Në pritje'}</strong></div>
                <div><span>Entitete kryesore</span><strong>{Array.isArray(analysis?.people) && analysis.people.length ? String(analysis.people[0]) : 'Në pritje'}</strong></div>
                <div><span>Ndjeshmëria</span><strong className="neutral">Neutral</strong></div>
                <div><span>Rëndësia për publikun</span><strong className="high">Në analizë</strong></div>
              </div>
              <button className="quote-box" onClick={() => { setSelectedStage('analyze'); void analyzeCurrent() }}><span>“</span>{typeof analysis?.summary === 'string' ? analysis.summary.slice(0, 145) : 'Run Story Intelligence për të gjetur thelbin, pyetjen dhe faktin që ndalon scroll-in.'}</button>
              <button className="outline-button" onClick={() => { setSelectedStage('analyze'); void analyzeCurrent() }}>Analizo story →</button>
            </div>

            <div className="panel related-panel">
              <div className="panel-title-row"><div><h2>Related Videos</h2><span>Top 5 sugjerime</span></div><Link2 size={18} /></div>
              <div className="related-list">
                {related.length === 0 && <div className="empty-soft"><GitBranch size={20} /> Zgjidh një video dhe ekzekuto Related Videos.</div>}
                {related.slice(0, 5).map((item, index) => (
                  <div className="related-row" key={item.video_id || index}>
                    <div className={thumbnailClass(index + 2)}><Link2 size={17} /></div>
                    <div className="related-copy"><strong>{item.title || `Sugjerim ${index + 1}`}</strong><span>{item.relationship_type || 'Editorial relationship'}</span></div>
                    <div className="score-pill">{Number(item.score || 0).toFixed(2)}</div>
                  </div>
                ))}
              </div>
              <button className="outline-button" onClick={() => { setSelectedStage('related'); void loadRelated() }}>Shiko më shumë sugjerime →</button>
            </div>
          </section>

          <section className="bottom-row">
            <button className="bottom-card" onClick={() => setSelectedStage('performance')}><BarChart3 size={24} /><div><strong>Performance</strong><span>Analizë e performances së videove</span></div><span className="wait-pill">Në pritje</span></button>
            <button className="bottom-card" onClick={() => { setSelectedStage('learning'); void loadLearning() }}><Sparkles size={24} /><div><strong>Learning</strong><span>Përshtatje automatike e algoritmit</span></div><span className="wait-pill">{weights ? 'Gati' : 'Në pritje'}</span></button>
            <button className="bottom-card" onClick={() => setSelectedStage('graph')}><Network size={24} /><div><strong>Story Graph</strong><span>Lidhje me temat dhe ngjarjet</span></div><span className="wait-pill">{stageState.graph === 'done' ? 'Gati' : 'Në pritje'}</span></button>
          </section>

          <div className="workspace-footer"><span>Lajme Prime – Story Intelligence</span><span>AI për lajme më të mira. Nga Shqipëria, për botën.</span><span>v1.0.0</span></div>
        </main>
      </section>
    </div>
  )
}

export default App
