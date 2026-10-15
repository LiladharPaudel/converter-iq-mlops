import { useEffect, useState } from 'react'
import WaveformScope from './WaveformScope.jsx'
import DiagnosisPanel from './DiagnosisPanel.jsx'
import AssistantPanel from './AssistantPanel.jsx'

const SPEEDS = [0.5, 1, 3]

export default function Results({ result, onReset }) {
  const n = result.episode.n_cycles
  const [idx, setIdx] = useState(0)
  const [playing, setPlaying] = useState(true)
  const [speed, setSpeed] = useState(1)

  useEffect(() => {
    if (!playing) return
    const id = setInterval(() => setIdx((i) => (i + 1 >= n ? 0 : i + 1)), 400 / speed)
    return () => clearInterval(id)
  }, [playing, speed, n])

  const c = result.cycles[idx]
  const fmtA = (v) => Math.round(v)
  const pct = (v) => (v * 100).toFixed(1)

  return (
    <section className="results">
      <div className="results-head">
        <div className="file">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6" /></svg>
          {result.episode.filename}
          <span>· {n} cycles · 20 × 3 @ 1 kHz</span>
        </div>
        <button type="button" className="btn ghost sm" onClick={onReset}>Upload another</button>
      </div>

      <div>
        <div className="panel">
          <div className="scope-wrap">
            <div className="scope-head">
              <h2>Three-phase grid current — instantaneous</h2>
              <div className="legend">
                <span><i style={{ background: 'var(--phase-a)' }} />Phase A</span>
                <span><i style={{ background: 'var(--phase-b)' }} />Phase B</span>
                <span><i style={{ background: 'var(--phase-c)' }} />Phase C</span>
              </div>
            </div>
            <WaveformScope waveform={result.waveform} index={idx} />
            <div className="replay">
              <button type="button" className="btn sm" onClick={() => setPlaying((p) => !p)} aria-pressed={playing}>
                {playing ? 'Pause' : 'Play'}
              </button>
              <input
                type="range" min="0" max={n - 1} value={idx} aria-label="Cycle"
                onChange={(e) => { setPlaying(false); setIdx(Number(e.target.value)) }}
              />
              <span className="cycle-label num">cycle {idx + 1} / {n}</span>
              <div className="speed" role="group" aria-label="Replay speed">
                {SPEEDS.map((s) => (
                  <button key={s} type="button" className={s === speed ? 'on' : ''} onClick={() => setSpeed(s)}>{s}×</button>
                ))}
              </div>
            </div>
          </div>
          <div className="metrics">
            <div className="metric a"><small>RMS phase A</small><b className="num">{fmtA(c.rms[0])}<em>A</em></b></div>
            <div className="metric b"><small>RMS phase B</small><b className="num">{fmtA(c.rms[1])}<em>A</em></b></div>
            <div className="metric c"><small>RMS phase C</small><b className="num">{fmtA(c.rms[2])}<em>A</em></b></div>
            <div className="metric"><small>Unbalance</small><b className="num">{pct(c.unbalance)}<em>%</em></b></div>
            <div className="metric"><small>Distortion</small><b className="num">{pct(c.distortion)}<em>%</em></b></div>
          </div>
        </div>

        <div className="panel timeline">
          <h3>Cycle-by-cycle</h3>
          <p>Each bar is one cycle. Click a bar to jump the replay to it. Current cycle: <b>{c.label}</b> ({Math.round(c.confidence * 100)}%)</p>
          <div className="strip">
            {result.cycles.map((cy) => (
              <button
                key={cy.index} type="button"
                className={`${cy.label === 'Nominal operation' ? '' : 'fault'} ${cy.index === idx ? 'current' : ''}`}
                title={`Cycle ${cy.index + 1}: ${cy.label} (${Math.round(cy.confidence * 100)}%)`}
                onClick={() => { setPlaying(false); setIdx(cy.index) }}
              />
            ))}
          </div>
        </div>

        <AssistantPanel result={result} />
      </div>

      <DiagnosisPanel result={result} onReset={onReset} />
    </section>
  )
}
