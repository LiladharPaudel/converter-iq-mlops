export default function History({ items, onOpen }) {
  return (
    <section className="panel history">
      <h2>Episode history</h2>
      <p>Everything analysed in this session. Persisting history to a database is planned for milestone 4.</p>
      {items.length === 0 ? (
        <div className="empty">Nothing analysed yet. Upload an episode to see it here.</div>
      ) : (
        <table>
          <thead>
            <tr><th>Time</th><th>Episode</th><th>Cycles</th><th>Verdict</th><th>Confidence</th><th></th></tr>
          </thead>
          <tbody>
            {items.map((h) => (
              <tr key={h.id}>
                <td className="num">{h.at}</td>
                <td>{h.result.episode.filename}</td>
                <td className="num">{h.result.episode.n_cycles}</td>
                <td><span className={`pill ${h.result.verdict.healthy ? 'healthy' : 'fault'}`}>{h.result.verdict.label}</span></td>
                <td className="num">{Math.round(h.result.verdict.confidence * 100)}%</td>
                <td><button type="button" className="btn ghost sm" onClick={() => onOpen(h.result)}>Open</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
