const DESCRIPTIONS = {
  'Nominal operation': 'Balanced three-phase current, fundamental intact.',
  'Phase A disconnection': 'Phase A current collapses to zero; B and C carry the load.',
  'Phase B disconnection': 'Phase B current collapses to zero; A and C carry the load.',
  'Phase C disconnection': 'Phase C current collapses to zero; A and B carry the load.',
  'Grid unbalance': 'Phase magnitudes differ well beyond normal tolerance.',
  'Harmonic distortion': 'Waveform shape corrupted; fundamental still present.',
  'DC offset / bus abnormality': 'Current carries a DC component, pointing at the bus.',
  'Overcurrent / short circuit': 'Peak current far above rating.',
}

export default function DiagnosisPanel({ result, onReset }) {
  const v = result.verdict
  const pct = Math.round(v.confidence * 100)
  const hint =
    pct >= 90 ? 'High confidence on a known class. Safe to act on without a manual waveform review.'
    : pct >= 70 ? 'Moderate confidence. Worth a quick look at the replay before acting.'
    : 'Low confidence. Treat as a prompt for engineering review, not a diagnosis.'

  return (
    <aside className="panel">
      <div className={`verdict ${v.healthy ? 'healthy' : 'fault'}`}>
        <div className="tag">
          {v.healthy ? 'Healthy' : 'Fault detected'}
        </div>
        <h2>{v.label}</h2>
        <p>{DESCRIPTIONS[v.label] ?? ''}</p>
        {v.first_fault_cycle != null && (
          <p>First seen at cycle <span className="num">{v.first_fault_cycle + 1}</span> of {result.episode.n_cycles}.</p>
        )}
      </div>

      <div className="confidence">
        <div className="row"><span>Confidence</span><b className="num">{pct}%</b></div>
        <div className="meter"><i style={{ width: `${pct}%` }} /></div>
        <p className="hint">{hint}</p>
      </div>

      <div className="alts">
        <h4>Next most likely</h4>
        {v.alternatives.map((a) => (
          <div className="alt" key={a.label}>
            <span>{a.label}</span>
            <span className="bar"><i style={{ width: `${Math.max(2, a.probability * 100)}%` }} /></span>
            <span className="num">{Math.round(a.probability * 100)}%</span>
          </div>
        ))}
      </div>

      <div className="screen">
        <span className={`dot ${result.in_distribution ? 'ok' : 'warn'}`} />
        <div>
          {result.in_distribution ? 'Signature matches the training distribution.' : 'Signature is outside the training distribution.'}
          <small>
            {result.in_distribution
              ? 'Amplitudes and shape are in the range the model has seen.'
              : 'Treat the diagnosis with caution and flag this episode for review.'}
          </small>
        </div>
      </div>

      <div className="side-actions">
        <button type="button" className="btn primary" onClick={() => downloadReport(result)}>Download report</button>
        <button type="button" className="btn" onClick={onReset}>Analyse another episode</button>
      </div>
      <p className="footnote">
        Model {result.model_version} · inference <span className="num">{result.inference_ms} ms</span> · input 20 × 3 @ 1 kHz
      </p>
    </aside>
  )
}

function downloadReport(result) {
  const { episode, verdict, cycles } = result
  const lines = [
    'ConverterIQ diagnosis report',
    `Episode: ${episode.filename}`,
    `Cycles: ${episode.n_cycles}`,
    `Verdict: ${verdict.label} (${Math.round(verdict.confidence * 100)}% confidence)`,
    verdict.first_fault_cycle != null ? `First fault cycle: ${verdict.first_fault_cycle + 1}` : 'No fault cycles',
    `In distribution: ${result.in_distribution ? 'yes' : 'no'}`,
    `Model: ${result.model_version}`,
    '',
    'cycle,rms_a,rms_b,rms_c,unbalance,distortion,label,confidence',
    ...cycles.map((c) => [c.index + 1, ...c.rms, c.unbalance, c.distortion, c.label, c.confidence].join(',')),
  ]
  const blob = new Blob([lines.join('\n')], { type: 'text/plain' })
  const a = document.createElement('a')
  a.href = URL.createObjectURL(blob)
  a.download = `${episode.filename.replace(/\.[^.]+$/, '')}_report.csv`
  a.click()
  URL.revokeObjectURL(a.href)
}
