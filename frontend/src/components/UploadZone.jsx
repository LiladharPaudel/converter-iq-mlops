import { useRef, useState } from 'react'

const SAMPLES = [
  { file: 'episode_phase_c_open.json', label: 'Phase C disconnection', meta: '40 cycles' },
  { file: 'episode_harmonics.json', label: 'Harmonic distortion', meta: '40 cycles' },
  { file: 'episode_unbalance.json', label: 'Grid unbalance', meta: '40 cycles' },
  { file: 'episode_healthy.json', label: 'Nominal operation', meta: '40 cycles' },
]

export default function UploadZone({ onFile, onImage, busy, error, notice, model }) {
  const [over, setOver] = useState(false)
  const cameraRef = useRef(null)

  const handleDrop = (e) => {
    e.preventDefault()
    setOver(false)
    const f = e.dataTransfer.files?.[0]
    if (f) route(f)
  }
  const route = (f) => (f.type.startsWith('image/') ? onImage(f) : onFile(f))

  const loadSample = async (name) => {
    const res = await fetch(`/samples/${name}`)
    const blob = await res.blob()
    onFile(new File([blob], name, { type: 'application/json' }))
  }

  return (
    <section className="hero">
      <div>
        <h1>Diagnose a converter fault from its current waveform</h1>
        <p className="lede">
          Upload the logger export for a fault episode. ConverterIQ checks every 20&nbsp;ms cycle of three-phase current,
          names the fault and shows how sure it is.
        </p>

        <div
          className={`dropzone ${over ? 'over' : ''} ${busy ? 'busy' : ''}`}
          onDragOver={(e) => { e.preventDefault(); setOver(true) }}
          onDragLeave={() => setOver(false)}
          onDrop={handleDrop}
        >
          <input
            type="file"
            accept=".json,.csv,.tsv,.txt"
            aria-label="Choose an episode file"
            onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])}
            disabled={busy}
          />
          <div className="icon">
            <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 16V4m0 0 4 4m-4-4-4 4" /><path d="M4 15v3a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-3" />
            </svg>
          </div>
          {busy ? (
            <>
              <h2>Analysing episode</h2>
              <p>Parsing cycles and running the classifier</p>
              <div className="progress"><i /></div>
            </>
          ) : (
            <>
              <h2>Drop a recorded episode here</h2>
              <p>.json or .csv from the converter logger, up to 50&nbsp;MB</p>
              <div className="actions">
                <label className="btn primary">
                  Choose file
                  <input type="file" accept=".json,.csv,.tsv,.txt" hidden onChange={(e) => e.target.files?.[0] && onFile(e.target.files[0])} />
                </label>
                <button type="button" className="btn" onClick={() => cameraRef.current?.click()}>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M4 8h3l2-3h6l2 3h3v11H4z" /><circle cx="12" cy="13" r="3.5" /></svg>
                  Snap a scope photo
                </button>
                <input ref={cameraRef} type="file" accept="image/*" capture="environment" hidden onChange={(e) => e.target.files?.[0] && onImage(e.target.files[0])} />
              </div>
            </>
          )}
          {error && <div className="error" role="alert">{error}</div>}
          {notice && <div className="notice">{notice}</div>}
        </div>
      </div>

      <aside className="samples">
        <h3>Try a sample episode</h3>
        <p>Short synthetic recordings in the dataset's record format.</p>
        <ul>
          {SAMPLES.map((s) => (
            <li key={s.file}>
              <button type="button" onClick={() => loadSample(s.file)} disabled={busy}>
                <span>{s.label}</span><span>{s.meta}</span>
              </button>
            </li>
          ))}
        </ul>
        {model && (
          <div className="model-card">
            Model <b>{model.version}</b> · {model.kind}<br />
            Input {model.input_shape.join(' × ')} · {model.classes.length} classes
          </div>
        )}
      </aside>
    </section>
  )
}
