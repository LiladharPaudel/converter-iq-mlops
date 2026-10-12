import { useEffect, useState } from 'react'
import UploadZone from './components/UploadZone.jsx'
import Results from './components/Results.jsx'
import History from './components/History.jsx'
import About from './components/About.jsx'
import { getHealth, getModel, predictFile, predictImage } from './api.js'

const TABS = [
  { id: 'diagnose', label: 'Diagnose' },
  { id: 'history', label: 'History' },
  { id: 'about', label: 'How it works' },
]

export default function App() {
  const [tab, setTab] = useState('diagnose')
  const [health, setHealth] = useState(null)
  const [model, setModel] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState('')
  const [result, setResult] = useState(null)
  const [history, setHistory] = useState([])

  useEffect(() => {
    getHealth().then(setHealth).catch(() => setHealth({ status: 'down' }))
    getModel().then(setModel).catch(() => {})
  }, [])

  const analyse = async (file) => {
    setBusy(true); setError(''); setNotice('')
    try {
      const res = await predictFile(file)
      setResult(res)
      setHistory((h) => [{ id: Date.now(), at: new Date().toLocaleTimeString(), result: res }, ...h])
      setTab('diagnose')
    } catch (e) {
      setError(e.message || 'The episode could not be analysed.')
    } finally {
      setBusy(false)
    }
  }

  const analyseImage = async (file) => {
    setBusy(true); setError(''); setNotice('')
    try {
      const res = await predictImage(file)
      setResult(res)
    } catch (e) {
      setNotice(e.message)
    } finally {
      setBusy(false)
    }
  }

  const reset = () => { setResult(null); setError(''); setNotice('') }

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <svg width="26" height="26" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#1a4062" /><path d="M5 16c3-8 5-8 8 0s5 8 8 0 5-8 8 0" fill="none" stroke="#2cb1a3" strokeWidth="2.4" strokeLinecap="round" /></svg>
          ConverterIQ <small>fault diagnosis</small>
        </div>
        <nav aria-label="Primary">
          {TABS.map((t) => (
            <button key={t.id} type="button" className={tab === t.id ? 'active' : ''} onClick={() => setTab(t.id)}>{t.label}</button>
          ))}
        </nav>
        <div className="status">
          <span className={`dot ${health?.status === 'ok' ? 'ok' : health ? 'down' : ''}`} />
          {health?.status === 'ok' ? `API online · ${health.model_version}` : health ? 'API offline' : 'Connecting…'}
        </div>
      </header>

      <main className="main">
        {tab === 'diagnose' && (result
          ? <Results result={result} onReset={reset} />
          : <UploadZone onFile={analyse} onImage={analyseImage} busy={busy} error={error} notice={notice} model={model} />
        )}
        {tab === 'history' && <History items={history} onOpen={(r) => { setResult(r); setTab('diagnose') }} />}
        {tab === 'about' && <About model={model} />}
      </main>
    </div>
  )
}
