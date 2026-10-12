import { useEffect, useRef } from 'react'

const COLORS = ['#f2b134', '#22c1d8', '#e5569d']

/** Draws `cycles` consecutive 60-value records ending at `index`, phase-major. */
export default function WaveformScope({ waveform, index, span = 4 }) {
  const ref = useRef(null)

  useEffect(() => {
    const cv = ref.current
    if (!cv) return
    const dpr = window.devicePixelRatio || 1
    const rect = cv.getBoundingClientRect()
    cv.width = rect.width * dpr
    cv.height = rect.height * dpr
    const ctx = cv.getContext('2d')
    const W = cv.width, H = cv.height

    ctx.clearRect(0, 0, W, H)
    ctx.strokeStyle = '#1c2a3a'
    ctx.lineWidth = dpr
    for (let x = 0; x <= 10; x++) { ctx.beginPath(); ctx.moveTo((x * W) / 10, 0); ctx.lineTo((x * W) / 10, H); ctx.stroke() }
    for (let y = 0; y <= 4; y++) { ctx.beginPath(); ctx.moveTo(0, (y * H) / 4); ctx.lineTo(W, (y * H) / 4); ctx.stroke() }

    const start = Math.max(0, index - span + 1)
    const slice = waveform.slice(start, index + 1)
    if (!slice.length) return

    let peak = 1
    for (const c of slice) for (const v of c) peak = Math.max(peak, Math.abs(v))
    peak *= 1.1
    const n = slice.length * 20
    const mid = H / 2

    for (let p = 0; p < 3; p++) {
      ctx.strokeStyle = COLORS[p]
      ctx.lineWidth = 2 * dpr
      ctx.lineJoin = 'round'
      ctx.beginPath()
      let k = 0
      for (const c of slice) {
        for (let i = 0; i < 20; i++, k++) {
          const x = (k / (n - 1)) * W
          const y = mid - (c[p * 20 + i] / peak) * (H / 2)
          k ? ctx.lineTo(x, y) : ctx.moveTo(x, y)
        }
      }
      ctx.stroke()
    }

    // highlight the current cycle
    const cw = W / slice.length
    ctx.fillStyle = 'rgba(255,255,255,0.04)'
    ctx.fillRect(W - cw, 0, cw, H)
  }, [waveform, index, span])

  return (
    <div className="scope">
      <canvas ref={ref} role="img" aria-label="Three-phase current waveform" />
      <span className="marker num">cycle {index + 1}</span>
    </div>
  )
}
