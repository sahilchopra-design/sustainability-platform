import { useEffect, useState } from 'react'
import { Search, Layers, ChevronRight, CheckCircle2, AlertCircle, XCircle } from 'lucide-react'
import { kpisApi } from '@/lib/api'
import type { ApplicationKpi, KpiFinderResult } from '@/types'
import Spinner from '@/components/ui/Spinner'
import EmptyState from '@/components/ui/EmptyState'
import { fmt } from '@/lib/utils'

function CoverageBadge({ status }: { status: string }) {
  const config = {
    mapped:   { label: 'Mapped',   icon: CheckCircle2, color: 'text-hub-success', bg: 'bg-hub-success/10' },
    partial:  { label: 'Partial',  icon: AlertCircle,  color: 'text-hub-warning', bg: 'bg-hub-warning/10' },
    unmapped: { label: 'Unmapped', icon: XCircle,      color: 'text-hub-error',   bg: 'bg-hub-error/10' },
  }[status] ?? { label: status, icon: AlertCircle, color: 'text-hub-text-muted', bg: 'bg-hub-muted' }
  const Icon = config.icon
  return (
    <span className={`inline-flex items-center gap-1 text-[11px] font-medium px-2 py-0.5 rounded ${config.bg} ${config.color}`}>
      <Icon size={10} />
      {config.label}
    </span>
  )
}

export default function KpiFinder() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState<KpiFinderResult[]>([])
  const [allKpis, setAllKpis] = useState<ApplicationKpi[]>([])
  const [categories, setCategories] = useState<Record<string, number>>({})
  const [filterCategory, setFilterCategory] = useState('')
  const [loading, setLoading] = useState(false)
  const [searching, setSearching] = useState(false)
  const [selected, setSelected] = useState<KpiFinderResult | null>(null)

  useEffect(() => {
    setLoading(true)
    Promise.all([
      kpisApi.list({ limit: 200 }),
      kpisApi.getCategories(),
    ]).then(([kpis, cats]) => {
      setAllKpis(kpis)
      setCategories(cats)
    }).finally(() => setLoading(false))
  }, [])

  const handleSearch = async (q: string) => {
    setQuery(q)
    if (!q.trim()) { setResults([]); return }
    setSearching(true)
    try {
      const res = await kpisApi.search(q)
      setResults(res)
    } finally {
      setSearching(false)
    }
  }

  const displayKpis = query.trim()
    ? results.map(r => r.kpi)
    : allKpis.filter(k => !filterCategory || k.category === filterCategory)

  return (
    <div className="flex gap-5 h-full animate-fade-in">
      {/* Left panel */}
      <div className="w-64 flex-shrink-0 flex flex-col gap-3">
        <div>
          <h1 className="text-xl font-semibold text-hub-text-primary">KPI Directory</h1>
          <p className="text-sm text-hub-text-muted mt-0.5">{fmt(allKpis.length)} KPIs defined</p>
        </div>

        {/* Search */}
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-hub-text-muted" />
          <input
            className="input pl-9"
            placeholder="Search KPIs..."
            value={query}
            onChange={e => handleSearch(e.target.value)}
          />
        </div>

        {/* Category filter */}
        <div className="card p-3">
          <div className="section-title">Category</div>
          <div className="space-y-0.5">
            <button
              onClick={() => setFilterCategory('')}
              className={`w-full flex items-center justify-between px-2 py-1.5 rounded text-[12px] transition-colors ${
                !filterCategory ? 'bg-hub-primary/15 text-hub-primary' : 'text-hub-text-secondary hover:bg-hub-muted'
              }`}
            >
              <span>All</span>
              <span className="font-mono text-[11px]">{allKpis.length}</span>
            </button>
            {Object.entries(categories).sort((a, b) => b[1] - a[1]).map(([cat, count]) => (
              <button
                key={cat}
                onClick={() => setFilterCategory(cat === filterCategory ? '' : cat)}
                className={`w-full flex items-center justify-between px-2 py-1.5 rounded text-[12px] transition-colors ${
                  filterCategory === cat ? 'bg-hub-primary/15 text-hub-primary' : 'text-hub-text-secondary hover:bg-hub-muted'
                }`}
              >
                <span className="truncate text-left">{cat}</span>
                <span className="font-mono text-[11px] ml-2 flex-shrink-0">{count}</span>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Middle: KPI list */}
      <div className="flex-1 min-w-0 flex flex-col gap-3">
        <div className="card flex-1 overflow-y-auto">
          {loading || searching ? (
            <div className="flex justify-center py-12"><Spinner /></div>
          ) : displayKpis.length === 0 ? (
            <EmptyState
              icon={<Layers size={22} />}
              title="No KPIs found"
              description={query ? 'Try a different search term.' : 'No KPIs in this category.'}
            />
          ) : (
            <div className="divide-y divide-hub-border/50">
              {displayKpis.map(kpi => {
                const result = results.find(r => r.kpi.id === kpi.id)
                const isSelected = selected?.kpi.id === kpi.id
                return (
                  <button
                    key={kpi.id}
                    onClick={() => {
                      if (result) {
                        setSelected(isSelected ? null : result)
                      } else {
                        // Load finder result
                        kpisApi.search(kpi.name).then(r => {
                          const match = r.find(x => x.kpi.id === kpi.id)
                          if (match) setSelected(match)
                        })
                      }
                    }}
                    className={`w-full flex items-center gap-3 px-5 py-3 text-left transition-colors ${
                      isSelected ? 'bg-hub-primary/10' : 'hover:bg-hub-muted/40'
                    }`}
                  >
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-hub-text-primary">{kpi.name}</span>
                        {kpi.is_required && (
                          <span className="text-[10px] bg-hub-error/15 text-hub-error px-1.5 py-0.5 rounded">Required</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-0.5">
                        {kpi.category && (
                          <span className="text-[11px] text-hub-text-muted">{kpi.category}</span>
                        )}
                        {kpi.unit && (
                          <span className="text-[11px] font-mono text-hub-text-muted">({kpi.unit})</span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {result && <CoverageBadge status={result.mapping_status} />}
                      <span className="text-[11px] font-mono text-hub-text-muted">{kpi.mapping_count ?? 0} maps</span>
                      <ChevronRight size={12} className={`text-hub-text-muted transition-transform ${isSelected ? 'rotate-90' : ''}`} />
                    </div>
                  </button>
                )
              })}
            </div>
          )}
        </div>
      </div>

      {/* Right: KPI detail panel */}
      {selected && (
        <div className="w-72 flex-shrink-0 card p-5 overflow-y-auto space-y-5 animate-slide-in">
          <div>
            <div className="text-[11px] text-hub-text-muted uppercase tracking-wider mb-1">{selected.kpi.category}</div>
            <h2 className="text-base font-semibold text-hub-text-primary">{selected.kpi.name}</h2>
            <div className="font-mono text-[11px] text-hub-text-muted mt-0.5">{selected.kpi.slug}</div>
          </div>

          <CoverageBadge status={selected.mapping_status} />

          {selected.kpi.description && (
            <p className="text-[12px] text-hub-text-secondary leading-relaxed">{selected.kpi.description}</p>
          )}

          {selected.kpi.unit && (
            <div><span className="label">Unit </span><span className="font-mono text-[12px] text-hub-text-secondary">{selected.kpi.unit}</span></div>
          )}

          {selected.kpi.target_modules && selected.kpi.target_modules.length > 0 && (
            <div>
              <div className="section-title">Target Modules</div>
              <div className="flex flex-wrap gap-1.5">
                {selected.kpi.target_modules.map(m => (
                  <span key={m} className="text-[11px] bg-hub-secondary/10 text-hub-secondary px-2 py-0.5 rounded">{m}</span>
                ))}
              </div>
            </div>
          )}

          {selected.primary_sources.length > 0 && (
            <div>
              <div className="section-title">Primary Sources</div>
              <ul className="space-y-1">
                {selected.primary_sources.map(s => (
                  <li key={s} className="flex items-center gap-2 text-[12px] text-hub-text-secondary">
                    <CheckCircle2 size={11} className="text-hub-success flex-shrink-0" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {selected.fallback_sources.length > 0 && (
            <div>
              <div className="section-title">Fallback Sources</div>
              <ul className="space-y-1">
                {selected.fallback_sources.map(s => (
                  <li key={s} className="flex items-center gap-2 text-[12px] text-hub-text-secondary">
                    <AlertCircle size={11} className="text-hub-warning flex-shrink-0" />
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {selected.approximation_method && (
            <div>
              <div className="section-title">Approximation Method</div>
              <span className="text-[11px] font-mono bg-hub-muted text-hub-text-secondary px-2 py-0.5 rounded">
                {selected.approximation_method}
              </span>
            </div>
          )}

          {selected.kpi.tags && selected.kpi.tags.length > 0 && (
            <div>
              <div className="section-title">Tags</div>
              <div className="flex flex-wrap gap-1.5">
                {selected.kpi.tags.map(t => (
                  <span key={t} className="text-[10px] font-mono bg-hub-muted text-hub-text-muted px-1.5 py-0.5 rounded">{t}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
