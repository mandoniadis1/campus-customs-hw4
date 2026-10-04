import { useEffect, useRef, useState } from 'react'

/** A little Handsome Dan–style bulldog that trots after the cursor (home page only).
 *  Decorative: ignores clicks, hidden on touch screens and for people who prefer reduced motion. */
export default function BulldogFollower() {
  const dogRef = useRef<HTMLDivElement>(null)
  const [enabled] = useState(
    () =>
      window.matchMedia('(pointer: fine)').matches && !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  )

  useEffect(() => {
    if (!enabled) return
    const dog = dogRef.current
    if (!dog) return
    const target = { x: window.innerWidth / 2, y: window.innerHeight / 2 }
    const pos = { ...target }
    let facing = 1
    let visible = false
    let frame = 0

    const onMove = (e: MouseEvent) => {
      target.x = e.clientX
      target.y = e.clientY
      if (!visible) {
        visible = true
        pos.x = e.clientX - 60
        pos.y = e.clientY
        dog.classList.add('visible')
      }
    }
    const onLeave = () => {
      visible = false
      dog.classList.remove('visible')
    }

    const tick = () => {
      // Ease toward a spot just behind the cursor, so the dog follows rather than sits under the pointer.
      const goalX = target.x - 34 * facing
      const goalY = target.y + 18
      const dx = goalX - pos.x
      const dy = goalY - pos.y
      pos.x += dx * 0.08
      pos.y += dy * 0.08
      if (Math.abs(dx) > 4) facing = dx > 0 ? 1 : -1
      const moving = Math.hypot(dx, dy) > 3
      dog.style.transform = `translate(${pos.x - 28}px, ${pos.y - 24}px) scaleX(${facing})`
      dog.classList.toggle('running', moving)
      frame = requestAnimationFrame(tick)
    }

    window.addEventListener('mousemove', onMove)
    document.addEventListener('mouseleave', onLeave)
    frame = requestAnimationFrame(tick)
    return () => {
      window.removeEventListener('mousemove', onMove)
      document.removeEventListener('mouseleave', onLeave)
      cancelAnimationFrame(frame)
    }
  }, [enabled])

  if (!enabled) return null
  return (
    <div className="bulldog-follower" ref={dogRef} aria-hidden="true">
      <svg viewBox="0 0 64 52" width="56" height="46">
        {/* tail */}
        <path className="dog-tail" d="M9 22 q-6 -6 -3 -10" stroke="#c9a27a" strokeWidth="4" fill="none" strokeLinecap="round" />
        {/* body */}
        <ellipse cx="26" cy="30" rx="17" ry="11" fill="#e8c9a3" />
        <ellipse cx="28" cy="34" rx="11" ry="6" fill="#f6e7d3" />
        {/* legs */}
        <g className="dog-legs" fill="#d7b088">
          <rect className="leg a" x="12" y="36" width="6" height="10" rx="3" />
          <rect className="leg b" x="20" y="37" width="6" height="9" rx="3" />
          <rect className="leg a" x="31" y="37" width="6" height="9" rx="3" />
          <rect className="leg b" x="38" y="36" width="6" height="10" rx="3" />
        </g>
        {/* Yale navy sweater with Y */}
        <path d="M14 24 Q26 18 40 23 L41 33 Q27 37 13 32 Z" fill="#00356b" />
        <text x="27" y="31.5" textAnchor="middle" fontSize="8" fontWeight="900" fill="#ffffff" fontFamily="Georgia, serif">
          Y
        </text>
        {/* head */}
        <g className="dog-head">
          <ellipse cx="48" cy="20" rx="13" ry="12" fill="#e8c9a3" />
          <path d="M37 11 q-3 -8 4 -6 l2 6 z" fill="#c9a27a" />
          <path d="M57 10 q4 -7 6 0 l-3 5 z" fill="#c9a27a" />
          <ellipse cx="50" cy="26" rx="9" ry="6" fill="#f6e7d3" />
          <circle cx="44" cy="17" r="2" fill="#1b1b1b" />
          <circle cx="53" cy="17" r="2" fill="#1b1b1b" />
          <ellipse cx="50" cy="22" rx="3" ry="2" fill="#2a1a12" />
          <path d="M45 27 q5 4 10 0" stroke="#2a1a12" strokeWidth="1.6" fill="none" strokeLinecap="round" />
          <path d="M47 28 l1 2.5 l1 -2.5 M51 28 l1 2.5 l1 -2.5" stroke="#ffffff" strokeWidth="1" fill="none" />
        </g>
      </svg>
    </div>
  )
}
