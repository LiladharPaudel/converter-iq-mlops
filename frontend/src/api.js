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
