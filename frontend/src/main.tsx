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

const apiBase = import.meta.env.VITE_API_URL || 'http://localhost:8000/api'

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
  const [analysisTab, setAnalysisTab] = useState<AnalysisTab>('summary')
  const [analysis, setAnalysis] = useState<Record<string, unknown> | null>(null)
  const [research, setResearch] = useState<Record<string, unknown> | null>(null)
  const [related, setRelated] = useState<RelatedItem[]>([])
  const [weights, setWeights] = useState<Record<string, unknown> | null>(null)
  const [graphMatches, setGraphMatches] = useState<GraphMatch[]>([])
  const [running, setRunning] = useState(false)

  const currentVideo = videos.find((video) => video.id === selectedVideoId)
  const selected = useMemo(() => stages.find((stage) => stage.id === selectedStage) ?? stages[0], [selectedStage])
  const claims = arrayValue(analysis?.claims)
  const people = arrayValue(analysis?.people)
  const organizations = arrayValue(analysis?.organizations)
  const topics = arrayValue(analysis?.topics)
  const events = arrayValue(analysis?.events)

  const patchStage = (id: StageId, status: StageStatus) => setStageState((current) => ({ ...current, [id]: status }))

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
      setHealth('online'); setMessage('API është online.')
    } catch {
      setHealth('offline'); setMessage('API nuk është e arritshme. Kontrollo VITE_API_URL dhe CORS.')
    }
  }

  async function runIngest() {
    setRunning(true); patchStage('ingest', 'active'); setMessage('Po marr videot e reja nga YouTube...')
    try {
      const result = await apiFetch<{ imported: number; updated: number; stories_created?: number; stories_reused?: number }>(`/youtube/ingest?channel=${encodeURIComponent(channel)}&limit=${encodeURIComponent(limit)}`, { method: 'POST' })
      await loadRecent(); patchStage('ingest', 'done'); patchStage('analyze', 'active')
      setMessage(`${result.imported} video të reja, ${result.updated} të përditësuara. Story Intelligence është gati.`)
    } catch (error) {
      patchStage('ingest', 'error'); setMessage(error instanceof Error ? error.message : 'Ingest dështoi.')
    } finally { setRunning(false) }
  }

  async function analyzeCurrent() {
    if (!currentVideo) return
    patchStage('analyze', 'active'); setMessage('Po analizoj thelbin e historisë dhe lidhjet ekzistuese...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/stories/analyze-and-link', { method: 'POST', body: JSON.stringify({ title: currentVideo.title, text: `${currentVideo.title}\n\n${currentVideo.description || ''}`, source_url: currentVideo.url }) })
      setAnalysis(result)
      const graph = result.graph as Record<string, unknown> | undefined
      setGraphMatches(arrayValue(graph?.matches) as GraphMatch[])
      patchStage('analyze', 'done'); if (result.graph) patchStage('graph', 'done'); setSelectedStage('analyze'); setMessage('Story Intelligence u përfundua dhe historia u lidh me graph-in.')
    } catch (error) {
      patchStage('analyze', 'error'); setMessage(error instanceof Error ? error.message : 'Story Intelligence dështoi.')
    }
  }

  async function researchCurrent() {
    if (!currentVideo) return
    patchStage('research', 'active'); setMessage('Po kërkoj burime dhe po kontrolloj pretendimet...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/research/story', { method: 'POST', body: JSON.stringify({ query: currentVideo.title, claims: claims.map((claim) => typeof claim === 'string' ? claim : JSON.stringify(claim)) }) })
      setResearch(result); patchStage('research', 'done'); setSelectedStage('research'); setMessage('Raporti i research dhe fact-check u kthye me sukses.')
    } catch (error) {
      patchStage('research', 'error'); setMessage(error instanceof Error ? error.message : 'Research dështoi.')
    }
  }

  async function loadRelated() {
    if (!currentVideo) return
    patchStage('related', 'active'); setMessage('Po gjej videot që një shikues do të donte të shihte më pas...')
    try {
      const result = await apiFetch<{ candidates: RelatedItem[] }>(`/related/videos/${currentVideo.id}?limit=5`)
      setRelated(result.candidates); patchStage('related', 'done'); setSelectedStage('related'); setMessage(`${result.candidates.length} sugjerime të rankuara.`)
    } catch (error) {
      patchStage('related', 'error'); setMessage(error instanceof Error ? error.message : 'Related Videos dështoi.')
    }
  }

  async function loadLearning() {
    patchStage('learning', 'active'); setMessage('Po lexoj peshat e fundit të learning loop...')
    try {
      const result = await apiFetch<Record<string, unknown>>('/learning/weights')
      setWeights(result); patchStage('learning', 'done'); setSelectedStage('learning'); setMessage('Adaptive learning weights u ngarkuan.')
    } catch (error) {
      patchStage('learning', 'error'); setMessage(error instanceof Error ? error.message : 'Learning dështoi.')
    }
  }

  const runSelectedStage = async () => {
    if (selectedStage === 'ingest') return runIngest()
    if (selectedStage === 'analyze') return analyzeCurrent()
    if (selectedStage === 'research') return researchCurrent()
    if (selectedStage === 'related') return loadRelated()
    if (selectedStage === 'learning') return loadLearning()
    setMessage(`${selected.title} përdor të dhënat e ruajtura nga backend-i dhe nuk shfaqet pa rezultat real.`)
  }

  return (
    <div className="dashboard-shell">
      <aside className="sidebar">
        <div className="logo-lockup"><div className="logo-main">LAJME <span>PRIME</span></div><div className="logo-sub">STORY INTELLIGENCE</div></div>
        <nav className="sidebar-nav">
          <button className="nav-item active" onClick={() => setSelectedStage('analyze')}><Home size={19} /> Dashboard</button>
          <button className="nav-item" onClick={() => setSelectedStage('ingest')}><Video size={19} /> YouTube Ingest</button>
          <button className="nav-item" onClick={() => setSelectedStage('analyze')}><BrainCircuit size={19} /> Story Intelligence</button>
          <button className="nav-item" onClick={() => setSelectedStage('research')}><Search size={19} /> Research & Fact-check</button>
          <button className="nav-item" onClick={() => setSelectedStage('graph')}><Network size={19} /> Story Graph</button>
          <button className="nav-item" onClick={() => setSelectedStage('related')}><Link2 size={19} /> Related Videos</button>
          <button className="nav-item" onClick={() => setSelectedStage('performance')}><BarChart3 size={19} /> Performance</button>
          <button className="nav-item" onClick={() => setSelectedStage('learning')}><Sparkles size={19} /> Learning</button>
        </nav>
        <div className="sidebar-bottom"><button className="nav-item"><Settings size={19} /> Settings</button><button className="nav-item"><CircleHelp size={19} /> Help</button><div className="sidebar-quote">“Më shumë se lajme.<br />Insight që lidh gjithçka.”<br /><span>Lajme Prime</span></div></div>
      </aside>

      <section className="content-area">
        <header className="content-topbar">
          <div><h1>Mirë se vini në Lajme Prime</h1><p>AI-powered workflow për të kthyer videot në histori më të mëdha.</p></div>
          <div className="profile-area"><button className={`api-pill ${health}`} onClick={() => void checkHealth()}><span /> API {health === 'online' ? 'Online' : health === 'offline' ? 'Offline' : 'Status'}</button><div className="avatar">KX</div><div className="profile-copy"><strong>Admin</strong><span>Editorial workspace</span></div></div>
        </header>

        <main className="workspace">
          <section className="workflow-panel">{stages.map((stage, index) => { const status = stageState[stage.id]; return <div key={stage.id} className="workflow-step-wrap"><button className={`workflow-step ${selectedStage === stage.id ? 'selected' : ''}`} onClick={() => setSelectedStage(stage.id)}><div className={`step-circle ${status}`}>{status === 'done' ? <Check size={16} /> : index + 1}</div><strong>{stage.title}</strong><span>{stage.subtitle}</span></button>{index < stages.length - 1 && <div className="step-connector" />}</div> })}</section>

          <section className="ingest-bar">
            <label className="ingest-field channel-field"><div className="youtube-badge"><Video size={20} /></div><div><strong>{channel}</strong><span>Channel për të analizuar</span></div><input aria-label="YouTube channel" value={channel} onChange={(event) => setChannel(event.target.value)} /></label>
            <label className="ingest-field compact-input"><div><strong>{limit}</strong><span>Numri i videove</span></div><input aria-label="Number of videos" value={limit} onChange={(event) => setLimit(event.target.value)} inputMode="numeric" /></label>
            <button className="run-workflow" onClick={() => void runIngest()} disabled={running}>{running ? <RefreshCw className="spin" size={20} /> : <Play size={20} />}{running ? 'Po ekzekutohet...' : 'Run Workflow'}</button>
          </section>
          <div className="workflow-message"><Activity size={15} /> {message}</div>

          <section className="status-strip">{stages.map((stage) => { const status = stageState[stage.id]; const Icon = stage.icon; return <button key={stage.id} className={`status-card ${status}`} onClick={() => setSelectedStage(stage.id)}><div className="status-icon"><Icon size={18} /></div><div><strong>{stage.title}</strong><span>{status === 'done' ? 'Përfunduar' : status === 'active' ? 'Në proces' : status === 'error' ? 'Gabim' : 'Në pritje'}</span><small>{stage.id === 'ingest' ? `${videos.length || 0} video të marra` : status === 'done' ? 'Gati për hapin tjetër' : 'Ekzekutim manual'}</small></div></button> })}</section>

          <section className="dashboard-grid">
            <div className="panel recent-panel"><div className="panel-title-row"><div><h2>Videot e fundit nga YouTube</h2><span>Burimi i historisë së re</span></div><button className="text-link" onClick={() => void loadRecent()}>Rifresko →</button></div><div className="recent-list">{videos.length === 0 && <div className="empty-soft"><Video size={20} /> Nuk ka video të ngarkuara. Ekzekuto Ingest.</div>}{videos.slice(0, 5).map((video, index) => <button key={video.id} className={`recent-row ${selectedVideoId === video.id ? 'selected' : ''}`} onClick={() => setSelectedVideoId(video.id)}><VideoThumbnail video={video} index={index} /><div className="recent-copy"><strong>{video.title}</strong><span>{formatPublished(video.published_at)} · Story {video.story_id ? 'e lidhur' : 'e re'}</span></div></button>)}</div></div>

            <div className="panel intelligence-panel"><div className="panel-title-row"><div><h2><BrainCircuit size={19} /> Story Intelligence <em>AI</em></h2><span>{currentVideo ? currentVideo.title : 'Zgjidh një video për analizë'}</span></div><span className="live-tag"><span /> {stageState.analyze === 'done' ? 'Gati' : stageState.analyze === 'active' ? 'Në proces' : 'Në pritje'}</span></div>
              <div className="analysis-tabs">{(['summary', 'claims', 'entities', 'emotion'] as AnalysisTab[]).map((tab) => <button key={tab} className={analysisTab === tab ? 'active' : ''} onClick={() => setAnalysisTab(tab)}>{tab === 'summary' ? 'Përmbledhje' : tab === 'claims' ? 'Pikat kryesore' : tab === 'entities' ? 'Entitete' : 'Tona & Emocion'}</button>)}</div>
              {analysisTab === 'summary' && <><div className="analysis-box"><h3>Përmbledhje (AI)</h3><p>{typeof analysis?.summary === 'string' ? analysis.summary : currentVideo ? 'Kliko “Analizo story” për të gjeneruar përmbledhjen e strukturuar të historisë.' : 'Zgjidh një video nga lista për të nisur analizën.'}</p></div><div className="analysis-metrics"><div><span>Kategoria</span><strong>{displayValue(analysis?.category)}</strong></div><div><span>Tema kryesore</span><strong>{displayValue(topics[0])}</strong></div><div><span>Persona</span><strong>{people.length || '0'}</strong></div><div><span>Ngjarje</span><strong>{events.length || '0'}</strong></div></div></>}
              {analysisTab === 'claims' && <div className="insight-list">{claims.length ? claims.map((claim, index) => <div key={index} className="insight-list-row"><FileCheck2 size={16} /><span>{displayValue(claim)}</span></div>) : <div className="empty-soft">Nuk ka pretendime të strukturuara ende.</div>}</div>}
              {analysisTab === 'entities' && <div className="entity-grid"><div><span>Persona</span>{people.length ? people.map((item, index) => <strong key={index}>{displayValue(item)}</strong>) : <small>Nuk ka të dhëna</small>}</div><div><span>Organizata</span>{organizations.length ? organizations.map((item, index) => <strong key={index}>{displayValue(item)}</strong>) : <small>Nuk ka të dhëna</small>}</div><div><span>Tema</span>{topics.length ? topics.map((item, index) => <strong key={index}>{displayValue(item)}</strong>) : <small>Nuk ka të dhëna</small>}</div></div>}
              {analysisTab === 'emotion' && <div className="emotion-panel"><div><span>Trigger editorial</span><strong>{displayValue(analysis?.emotional_trigger, 'Përcaktohet nga analiza')}</strong></div><div><span>Pyetja e audiencës</span><strong>{displayValue(analysis?.audience_question, 'Përcaktohet nga analiza')}</strong></div><div><span>Fakt që ndalon scroll-in</span><strong>{displayValue(analysis?.scroll_stop_fact, 'Përcaktohet nga analiza')}</strong></div></div>}
              <button className="quote-box" onClick={() => { setSelectedStage('analyze'); void analyzeCurrent() }}><span>“</span>{typeof analysis?.summary === 'string' ? analysis.summary.slice(0, 180) : 'Run Story Intelligence për të gjetur thelbin e historisë dhe faktin që mund të ndalojë scroll-in.'}</button><button className="outline-button" onClick={() => { setSelectedStage('analyze'); void analyzeCurrent() }}>Analizo story →</button>
            </div>

            <div className="panel related-panel"><div className="panel-title-row"><div><h2>Related Videos</h2><span>Top 5 sugjerime për videon aktuale</span></div><Link2 size={18} /></div><div className="related-list">{related.length === 0 && <div className="empty-soft"><GitBranch size={20} /> Zgjidh një video dhe ekzekuto Related Videos.</div>}{related.slice(0, 5).map((item, index) => <button className="related-row" key={item.video_id || index} onClick={() => item.url && window.open(item.url, '_blank', 'noopener,noreferrer')}><VideoThumbnail video={item} index={index + 2} compact /><div className="related-copy"><strong>{item.title || `Sugjerim ${index + 1}`}</strong><span>{item.relationship_type || 'Editorial relationship'}</span></div><div className="score-pill">{Number(item.score || 0).toFixed(2)}</div></button>)}</div><button className="outline-button" onClick={() => void loadRelated()}>Shiko më shumë sugjerime →</button></div>
          </section>

          <section className="inspector-grid"><div className="panel inspector-panel"><div className="panel-title-row"><div><h2>{selected.title}</h2><span>{selected.subtitle}</span></div><span className={`stage-badge ${stageState[selectedStage]}`}>{stageState[selectedStage]}</span></div><div className="inspector-toolbar"><select value={selectedVideoId} onChange={(event) => setSelectedVideoId(event.target.value)}><option value="">Zgjidh një video</option>{videos.map((video) => <option key={video.id} value={video.id}>{video.title}</option>)}</select><button className="run-inspector" disabled={selectedStage !== 'learning' && !currentVideo} onClick={() => void runSelectedStage()}>{selectedStage === 'ingest' ? 'Ingest' : selectedStage === 'analyze' ? 'Analizo' : selectedStage === 'research' ? 'Fact-check' : selectedStage === 'related' ? 'Rank' : selectedStage === 'learning' ? 'Load weights' : 'Hap të dhënat'}</button></div>{selectedStage === 'research' && <div className="research-summary"><div><strong>{arrayValue(research?.sources).length}</strong><span>burime</span></div><div><strong>{arrayValue(research?.findings).length}</strong><span>findings</span></div><div><strong>{displayValue(research?.status, 'Pa status')}</strong><span>status</span></div></div>}{selectedStage === 'graph' && <div className="graph-inspector"><div className="graph-center-node"><span>VIDEO AKTUALE</span><strong>{currentVideo ? currentVideo.title : 'Zgjidh video'}</strong></div>{graphMatches.length ? <div className="graph-match-list">{graphMatches.slice(0, 6).map((match, index) => <div className="graph-match" key={`${match.relationship_type}-${index}`}><div className="graph-match-line"><span className="graph-dot" /><strong>{match.relationship_type || 'RELATIONSHIP'}</strong><b>{Number(match.score || 0).toFixed(2)}</b></div><small>{(match.reasons || []).join(' · ') || 'Lidhje e zbuluar nga Story Graph'}</small></div>)}</div> : <div className="empty-soft graph-empty"><Network size={19} /> Analizo story për të ndërtuar marrëdhëniet reale të graph-it.</div>}</div>}{selectedStage === 'performance' && <div className="empty-soft"><BarChart3 size={19} /> Performance API aktualisht pranon snapshot-et e YouTube; ky panel nuk shpik metrika pa një publication metric real.</div>}{selectedStage === 'learning' && <pre className="json-view">{weights ? JSON.stringify(weights, null, 2) : 'Load weights për të parë peshat adaptive.'}</pre>}{(selectedStage === 'ingest' || selectedStage === 'analyze' || selectedStage === 'related') && <div className="inspector-copy">{currentVideo && <VideoThumbnail video={currentVideo} index={0} compact />}<div><strong>{currentVideo?.title || 'Nuk ka video të zgjedhur'}</strong><p>{selectedStage === 'analyze' ? displayValue(analysis?.summary, 'Ekzekuto analizën për të parë përmbledhjen.') : selectedStage === 'related' ? `${related.length} lidhje të rankuara nga story graph dhe semantic index.` : `${videos.length} video janë të disponueshme në workspace.`}</p></div></div>}</div></section>

          <section className="bottom-row"><button className="bottom-card" onClick={() => setSelectedStage('performance')}><BarChart3 size={24} /><div><strong>Performance</strong><span>Analizë e performances së videove</span></div><span className="wait-pill">{stageState.performance === 'done' ? 'Gati' : 'Në pritje'}</span></button><button className="bottom-card" onClick={() => void loadLearning()}><Sparkles size={24} /><div><strong>Learning</strong><span>Përshtatje automatike e algoritmit</span></div><span className="wait-pill">{weights ? 'Gati' : 'Në pritje'}</span></button><button className="bottom-card" onClick={() => setSelectedStage('graph')}><Network size={24} /><div><strong>Story Graph</strong><span>Lidhje me temat dhe ngjarjet</span></div><span className="wait-pill">{stageState.graph === 'done' ? 'Gati' : 'Në pritje'}</span></button></section>
          <div className="workspace-footer"><span>Lajme Prime – Story Intelligence</span><span>{currentVideo ? 'Video e zgjedhur · workflow gati për veprim' : 'Zgjidh një video për të filluar'}</span><span>v1.1.0</span></div>
        </main>
      </section>
    </div>
  )
}

export default App
