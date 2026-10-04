import { useEffect, useRef, useState } from 'react'
import type { FilterOption, FilterOptions, ProductFilters } from '../api'
import { FILTERS, type FilterParam } from '../filters'

interface Props {
  options: FilterOptions | null
  selected: ProductFilters
  onChange: (param: FilterParam, values: string[]) => void
}

/** Aritzia-style filter buttons: clicking one opens a panel of options (multi-select). */
export default function FilterBar({ options, selected, onChange }: Props) {
  const [openParam, setOpenParam] = useState<FilterParam | null>(null)
  const barRef = useRef<HTMLDivElement>(null)

  // Close the open panel on outside click or Escape.
  useEffect(() => {
    if (!openParam) return
    const onClick = (e: MouseEvent) => {
      if (!barRef.current?.contains(e.target as Node)) setOpenParam(null)
    }
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpenParam(null)
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [openParam])

  function toggle(param: FilterParam, value: string) {
    const current = selected[param] ?? []
    onChange(param, current.includes(value) ? current.filter((v) => v !== value) : [...current, value])
  }

  return (
    <div className="filter-bar" ref={barRef}>
      {FILTERS.map((f) => {
        const count = selected[f.param]?.length ?? 0
        const isOpen = openParam === f.param
        const opts: FilterOption[] = options?.[f.options] ?? []
        return (
          <div key={f.param} className="filter">
            <button
              type="button"
              className={`filter-btn ${isOpen ? 'open' : ''} ${count ? 'has-value' : ''}`}
              aria-expanded={isOpen}
              onClick={() => setOpenParam(isOpen ? null : f.param)}
            >
              {f.label}
              {count > 0 && <span className="filter-count">{count}</span>}
              <span className="filter-caret" aria-hidden="true">
                {isOpen ? '▴' : '▾'}
              </span>
            </button>
            {isOpen && (
              <div className={`filter-panel filter-panel-${f.param}`} role="group" aria-label={f.label}>
                <div className="filter-options">
                  {opts.map((o, i) => (
                    <div key={o.value} className="filter-option-wrap">
                      {o.group && o.group !== opts[i - 1]?.group && <p className="filter-group">{o.group}</p>}
                      <button
                        type="button"
                        className={`filter-option ${selected[f.param]?.includes(o.value) ? 'selected' : ''}`}
                        disabled={o.count === 0}
                        aria-pressed={selected[f.param]?.includes(o.value) ?? false}
                        onClick={() => toggle(f.param, o.value)}
                      >
                        {o.swatch && <span className="swatch" style={{ background: o.swatch }} aria-hidden="true" />}
                        <span>{o.label}</span>
                        <span className="muted small">({o.count})</span>
                      </button>
                    </div>
                  ))}
                </div>
                <div className="filter-panel-actions">
                  <button type="button" className="text-link" onClick={() => onChange(f.param, [])} disabled={!count}>
                    Clear
                  </button>
                  <button type="button" className="btn btn-primary" onClick={() => setOpenParam(null)}>
                    Done
                  </button>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}
