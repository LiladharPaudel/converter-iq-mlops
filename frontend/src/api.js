const BASE = import.meta.env.VITE_API_BASE ?? ''

async function handle(res) {
  if (res.ok) return res.json()
  let detail = res.statusText
  try { detail = (await res.json()).detail ?? detail } catch { /* not json */ }
  throw new Error(detail)
}

export const getHealth = () => fetch(`${BASE}/api/health`).then(handle)
export const getModel = () => fetch(`${BASE}/api/model`).then(handle)

export function predictFile(file) {
  const body = new FormData()
  body.append('file', file)
  return fetch(`${BASE}/api/predict`, { method: 'POST', body }).then(handle)
}

export function predictImage(file) {
  const body = new FormData()
  body.append('file', file)
  return fetch(`${BASE}/api/predict/image`, { method: 'POST', body }).then(handle)
}

// ---- RAG assistant (milestone 2) ----
export const getRagStatus = () => fetch(`${BASE}/api/rag/status`).then(handle)

export function explainVerdict(result, question) {
  const cycles = result.cycles
  const mean = (key) => cycles.reduce((s, c) => s + c[key], 0) / cycles.length
  const body = {
    verdict: result.verdict,
    episode: result.episode,
    question: question || undefined,
    mean_unbalance: Number(mean('unbalance').toFixed(4)),
    mean_distortion: Number(mean('distortion').toFixed(4)),
    in_distribution: result.in_distribution,
  }
  return fetch(`${BASE}/api/rag/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }).then(handle)
}
