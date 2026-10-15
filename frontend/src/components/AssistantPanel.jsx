import { useEffect, useRef, useState } from 'react'
import { explainVerdict, getRagStatus } from '../api.js'

const SUGGESTIONS = [
  'What should I inspect first?',
  'Could this be a sensor fault instead?',
  'Why is the confidence not higher?',
]

/**
 * Grounded explanation of the current verdict, with follow-up questions.
 * Each answer is produced by the RAG pipeline (backend/app/rag): the verdict
 * and episode features go in as context, passages from converter papers and
 * datasheets are retrieved from ChromaDB, and Gemini writes a cited answer.
 */
export default function AssistantPanel({ result }) {
  const [status, setStatus] = useState(null)
  const [turns, setTurns] = useState([])      // {q, a, passages, model, latency_ms, error}
  const [question, setQuestion] = useState('')
  const [busy, setBusy] = useState(false)
  const [openSources, setOpenSources] = useState(null)
  const endRef = useRef(null)

  useEffect(() => {
    getRagStatus().then(setStatus).catch(() => setStatus({ available: false }))
  }, [])

  // Reset when a new episode is analysed.
  useEffect(() => { setTurns([]); setOpenSources(null) }, [result])
  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth', block: 'nearest' }) }, [turns])

  const ask = async (q) => {
    if (busy) return
    const label = q || 'Explain this verdict'
    setBusy(true); setQuestion('')
    setTurns((t) => [...t, { q: label, pending: true }])
    try {
      const res = await explainVerdict(result, q)
      setTurns((t) => t.map((x) => (x.pending ? { q: label, ...res } : x)))
    } catch (e) {
      setTurns((t) => t.map((x) => (x.pending ? { q: label, error: e.message } : x)))
    } finally {
      setBusy(false)
    }
  }

  if (status && !status.available) {
    return (
      <div className="panel assistant off">
        <h3>Assistant</h3>
        <p>The knowledge base is not loaded. Run <code>docker compose run --rm rag-index</code> to build it.</p>
      </div>
    )
  }

  return (
    <div className="panel assistant">
      <div className="assistant-head">
        <h3>Assistant</h3>
        <small>{status ? `${status.chunks} passages indexed` : 'Checking knowledge base…'}</small>
      </div>

      {turns.length === 0 && (
        <div className="assistant-empty">
          <p>Get a grounded explanation of <b>{result.verdict.label}</b>, with citations to converter papers and datasheets.</p>
          <button type="button" className="btn primary sm" onClick={() => ask('')} disabled={!status || busy}>
            Explain this verdict
          </button>
        </div>
      )}

      <div className="assistant-thread">
        {turns.map((t, i) => (
          <div className="turn" key={i}>
            <div className="q">{t.q}</div>
            {t.pending && <div className="a pending">Retrieving passages and writing an answer…</div>}
            {t.error && <div className="a error">{t.error}</div>}
            {t.answer && (
              <div className="a">
                {t.answer.split(/\n{2,}/).map((para, j) => <p key={j}>{para}</p>)}
                <div className="a-meta">
                  <button type="button" className="btn ghost sm" onClick={() => setOpenSources(openSources === i ? null : i)}>
                    {openSources === i ? 'Hide' : 'Show'} {t.passages.length} sources
                  </button>
                  <span className="num">{t.model} · {Math.round(t.latency_ms)} ms</span>
                </div>
                {openSources === i && (
                  <ol className="sources">
                    {t.passages.map((p, k) => (
                      <li key={k}>
                        <b>{p.source}</b> <span className="num">chunk {p.chunk_index} · d={p.distance}</span>
                        <p>{p.text}</p>
                      </li>
                    ))}
                  </ol>
                )}
              </div>
            )}
          </div>
        ))}
        <div ref={endRef} />
      </div>

      {turns.length > 0 && (
        <>
          <div className="suggestions">
            {SUGGESTIONS.map((s) => (
              <button key={s} type="button" className="chip" onClick={() => ask(s)} disabled={busy}>{s}</button>
            ))}
          </div>
          <div className="ask">
            <input
              type="text" value={question} placeholder="Ask about this diagnosis…"
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter' && question.trim()) ask(question.trim()) }}
              disabled={busy}
            />
            <button type="button" className="btn primary sm" onClick={() => ask(question.trim())} disabled={busy || !question.trim()}>Ask</button>
          </div>
        </>
      )}
      <p className="footnote">Answers are grounded in retrieved documents and cite their file names. Verify before acting.</p>
    </div>
  )
}
