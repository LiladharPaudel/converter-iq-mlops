export default function About({ model }) {
  return (
    <section className="panel about">
      <h2>How ConverterIQ works</h2>
      <p>
        Power converters record their three-phase grid current continuously. When a protection relay trips, the
        logger exports an episode: a sequence of 20 ms windows, each sampled at 1 kHz on all three phases.
      </p>
      <ol>
        <li><b>Parse.</b> Each record is checked for 60 values (20 samples × 3 phases) and converted to amperes.</li>
        <li><b>Features.</b> Per-phase RMS, unbalance, distortion and DC offset are computed and shown next to the waveform.</li>
        <li><b>Classify.</b> A model scores every cycle against {model?.classes.length ?? 8} classes; the episode verdict is the fault that dominates the faulty cycles.</li>
        <li><b>Screen.</b> An out-of-distribution check warns when the signal looks unlike anything in the training data.</li>
      </ol>
      <p style={{ marginTop: 16 }}>
        The current model is <b>{model?.version ?? 'loading…'}</b>, {model?.kind ?? ''}. {model?.note}
      </p>
    </section>
  )
}
