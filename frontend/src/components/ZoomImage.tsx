import { useState, type MouseEvent } from 'react'
import { edgeColor } from '../edgeColor'

const ZOOM = 2.5

/** Large product photo that magnifies around the cursor on hover (click/tap toggles zoom on touch screens). */
export default function ZoomImage({ src, alt }: { src: string; alt: string }) {
  const [zoomed, setZoomed] = useState(false)
  const [origin, setOrigin] = useState('50% 50%')
  const [tile, setTile] = useState<string | null>(null) // frame matches the photo's own background

  function track(e: MouseEvent<HTMLDivElement>) {
    const rect = e.currentTarget.getBoundingClientRect()
    const x = ((e.clientX - rect.left) / rect.width) * 100
    const y = ((e.clientY - rect.top) / rect.height) * 100
    setOrigin(`${x}% ${y}%`)
  }

  return (
    <div
      className={`zoom-frame ${zoomed ? 'zoomed' : ''}`}
      onMouseEnter={() => setZoomed(true)}
      onMouseLeave={() => setZoomed(false)}
      onMouseMove={track}
      onClick={(e) => {
        track(e)
        setZoomed((z) => !z)
      }}
      role="img"
      aria-label={`${alt} (hover or tap to zoom)`}
      style={tile ? { background: tile } : undefined}
    >
      <img
        src={src}
        alt={alt}
        onLoad={(e) => setTile(edgeColor(e.currentTarget))}
        style={{ transformOrigin: origin, transform: zoomed ? `scale(${ZOOM})` : 'scale(1)' }}
        draggable={false}
      />
      <span className="zoom-hint">{zoomed ? 'Move to explore' : '🔍 Hover to zoom'}</span>
    </div>
  )
}
