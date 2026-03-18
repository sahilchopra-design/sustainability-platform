/**
 * ScenarioGalleryPage — browse, fork, and manage climate scenarios.
 *
 * Sections:
 *  - Official NGFS Phase IV (read-only, forkable)
 *  - Regulatory Presets (EBA, CRREM, TCFD)
 *  - Custom / Draft (user-created scenarios)
 *
 * Route: /scenario-gallery
 */
import React, { useState, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { SCENARIO_TEMPLATES, NGFS_FAMILY_META } from '../data/ngfsData';

// ─── Helpers ──────────────────────────────────────────────────────────────────

const CATEGORY_META = {
  ngfs:       { label: 'NGFS Official',     cls: 'bg-gray-100 text-gray-800 border-gray-300' },
  regulatory: { label: 'Regulatory Preset', cls: 'bg-violet-500/10 text-violet-300 border-violet-500/25' },
  custom:     { label: 'Custom',            cls: 'bg-white/8 text-gray-500 border-black/15' },
  stress:     { label: 'Stress Test',       cls: 'bg-red-500/10 text-red-300 border-red-500/25' },
};

const SORT_OPTIONS = [
  { value: 'name',     label: 'Name A–Z' },
  { value: 'updated',  label: 'Last Updated' },
  { value: 'family',   label: 'NGFS Family' },
  { value: 'category', label: 'Category' },
];

const FAMILIES   = ['all', 'Orderly', 'Disorderly', 'Hot house world'];
const CATEGORIES = ['all', 'ngfs', 'regulatory', 'stress', 'custom'];

// ─── Stat chip ────────────────────────────────────────────────────────────────

function StatChip({ label, value, color = 'white' }) {
  const colorCls = {
    white:   'text-gray-600',
    cyan:    'text-gray-800',
    amber:   'text-amber-300',
    emerald: 'text-emerald-300',
    red:     'text-red-300',
  }[color] ?? 'text-gray-600';

  return (
    <div className="flex flex-col gap-0.5">
      <span className={`text-[12px] font-mono font-semibold ${colorCls}`}>{value}</span>
      <span className="text-[9px] text-gray-500">{label}</span>
    </div>
  );
}

// ─── Scenario card ────────────────────────────────────────────────────────────

function ScenarioCard({ template, onEdit, onFork, onUse }) {
  const [menuOpen, setMenuOpen] = useState(false);
  const categoryMeta = CATEGORY_META[template.category] ?? CATEGORY_META.custom;
  const familyMeta   = template.ngfsFamily !== 'all'
    ? NGFS_FAMILY_META[template.ngfsFamily]
    : null;

  const isOfficial   = template.category === 'ngfs';
  const isCustom     = template.category === 'custom' || template.category === 'stress';

  // Derive some display values from the template parameters
  const carbonPrice  = template.parameters?.carbon_price_usd ?? '—';
  const tempTarget   = template.parameters?.temperature_target_c ?? '—';
  const renewable    = template.parameters?.renewable_share_pct ?? '—';

  return (
    <div
      className="bg-white border border-gray-200 rounded-xl p-4 flex flex-col gap-3 hover:border-black/16 transition-all group relative"
      data-testid={`scenario-card-${template.id}`}
    >
      {/* Top row */}
      <div className="flex items-start gap-3">
        {/* Family colour swatch */}
        <div className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center ${
          familyMeta ? familyMeta.bgClass : 'bg-gray-50'
        } border ${familyMeta ? familyMeta.borderClass : 'border-black/10'}`}>
          <svg className={`h-4 w-4 ${familyMeta ? familyMeta.textClass : 'text-gray-500'}`}
            fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round"
              d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
          </svg>
        </div>

        <div className="flex-1 min-w-0">
          <h4 className="text-[13px] font-semibold text-gray-900 truncate">{template.name}</h4>
          <p className="text-[10px] text-gray-500 mt-0.5 line-clamp-2 leading-relaxed">
            {template.description}
          </p>
        </div>

        {/* Actions menu */}
        <div className="relative">
          <button
            onClick={() => setMenuOpen(v => !v)}
            className="text-gray-400 hover:text-gray-600 transition-colors p-1 rounded hover:bg-gray-50 opacity-0 group-hover:opacity-100"
            title="More actions"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 5v.01M12 12v.01M12 19v.01" />
            </svg>
          </button>
          {menuOpen && (
            <div
              className="absolute right-0 top-6 w-40 bg-white border border-black/12 rounded-lg shadow-2xl z-10 overflow-hidden"
              onBlur={() => setMenuOpen(false)}
            >
              {[
                { label: 'Edit',           action: onEdit,  icon: 'M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z' },
                { label: 'Fork',           action: onFork,  icon: 'M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z' },
                { label: 'Use in Analysis', action: onUse,  icon: 'M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z M21 12a9 9 0 11-18 0 9 9 0 0118 0z' },
              ].map(({ label, action, icon }) => (
                <button
                  key={label}
                  onClick={() => { action(); setMenuOpen(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 text-[11px] text-gray-500 hover:text-gray-800 hover:bg-gray-50 transition-colors text-left"
                >
                  <svg className="h-3.5 w-3.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                    <path strokeLinecap="round" strokeLinejoin="round" d={icon} />
                  </svg>
                  {label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Badges */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${categoryMeta.cls}`}>
          {categoryMeta.label}
        </span>
        {familyMeta ? (
          <span className={`text-[9px] font-semibold px-1.5 py-0.5 rounded border ${familyMeta.bgClass} ${familyMeta.textClass} ${familyMeta.borderClass}`}>
            {template.ngfsFamily === 'Hot house world' ? 'Hot House' : template.ngfsFamily}
          </span>
        ) : (
          <span className="text-[9px] text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded border border-black/10">
            All Families
          </span>
        )}
        {template.tags?.slice(0, 2).map(tag => (
          <span key={tag} className="text-[9px] text-gray-400 bg-white/4 px-1.5 py-0.5 rounded border border-gray-200">
            {tag}
          </span>
        ))}
      </div>

      {/* Key parameters */}
      <div className="grid grid-cols-3 gap-2 bg-gray-50 rounded-lg p-2.5 border border-black/5">
        <StatChip label="Carbon $/t" value={`$${carbonPrice}`} color={isOfficial ? 'cyan' : 'white'} />
        <StatChip label="Temp °C"    value={`${tempTarget}°`}  color={
          tempTarget <= 2.0 ? 'emerald' : tempTarget <= 3.0 ? 'amber' : 'red'
        } />
        <StatChip label="Renewables" value={`${renewable}%`}   color="white" />
      </div>

      {/* Action row */}
      <div className="flex items-center gap-2 pt-0.5">
        <button
          onClick={onUse}
          className="flex-1 text-[11px] font-semibold py-1.5 rounded bg-gray-100 border border-gray-300 text-gray-800 hover:bg-gray-800/22 transition-colors text-center"
        >
          Use in Analysis
        </button>
        <button
          onClick={isOfficial ? onFork : onEdit}
          className="text-[11px] py-1.5 px-3 rounded border border-black/10 text-gray-500 hover:border-black/20 hover:text-gray-700 transition-colors"
        >
          {isOfficial ? 'Fork' : 'Edit'}
        </button>
      </div>

      {isOfficial && (
        <p className="text-[9px] text-gray-400 -mt-1">
          Read-only · Fork to customise
        </p>
      )}
    </div>
  );
}

// ─── Empty state ──────────────────────────────────────────────────────────────

function EmptyState({ onNew }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-gray-400">
      <svg className="h-12 w-12 mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
        <path strokeLinecap="round" strokeLinejoin="round"
          d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064" />
      </svg>
      <p className="text-[14px] font-medium mb-1">No scenarios match your filters</p>
      <p className="text-[12px] text-gray-500 mb-4">Try clearing filters or create a new custom scenario</p>
      <button
        onClick={onNew}
        className="text-[12px] px-4 py-2 rounded bg-gray-200 border border-gray-300 text-gray-800 hover:bg-gray-300 transition-colors font-semibold"
      >
        + New Scenario
      </button>
    </div>
  );
}

// ─── Section header ───────────────────────────────────────────────────────────

function SectionHeader({ label, count, accentColor = 'cyan' }) {
  const accent = {
    cyan:   'text-gray-500 border-gray-200',
    violet: 'text-violet-400/60 border-violet-400/20',
    amber:  'text-amber-400/60 border-amber-400/20',
    white:  'text-gray-500 border-black/15',
  }[accentColor] ?? 'text-gray-500 border-black/15';

  return (
    <div className={`flex items-center gap-3 pb-1 border-b ${accent.split(' ')[1]}`}>
      <h3 className={`text-[11px] font-semibold uppercase tracking-[0.1em] ${accent.split(' ')[0]}`}>
        {label}
      </h3>
      <span className="text-[9px] text-gray-400 bg-gray-50 px-1.5 py-0.5 rounded font-mono">
        {count}
      </span>
    </div>
  );
}

// ─── Summary stats bar ────────────────────────────────────────────────────────

function SummaryStatsBar({ templates }) {
  const counts = templates.reduce((acc, t) => {
    acc[t.category] = (acc[t.category] || 0) + 1;
    return acc;
  }, {});

  return (
    <div className="flex items-center gap-4 p-3 bg-white border border-gray-200 rounded-lg text-[10px]">
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-gray-800" />
        <span className="text-gray-500">{counts.ngfs ?? 0} NGFS official</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-violet-400" />
        <span className="text-gray-500">{counts.regulatory ?? 0} regulatory presets</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-red-400" />
        <span className="text-gray-500">{counts.stress ?? 0} stress tests</span>
      </div>
      <div className="flex items-center gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-white/30" />
        <span className="text-gray-500">{counts.custom ?? 0} custom</span>
      </div>
      <div className="flex-1" />
      <span className="text-gray-400 font-mono">{templates.length} total</span>
    </div>
  );
}

// ─── Main page ────────────────────────────────────────────────────────────────

export default function ScenarioGalleryPage() {
  const navigate         = useNavigate();
  const [search,  setSearch]  = useState('');
  const [family,  setFamily]  = useState('all');
  const [category, setCategory] = useState('all');
  const [sortBy,  setSortBy]  = useState('category');
  const [view,    setView]    = useState('grid'); // 'grid' | 'list'

  // Enrich SCENARIO_TEMPLATES with some mock usage stats for display
  const enriched = useMemo(() => SCENARIO_TEMPLATES.map(t => ({
    ...t,
    // derive top-level parameter shortcuts for display
    parameters: {
      carbon_price_usd:     t.parameterOverrides?.carbon_price_usd     ?? 85,
      temperature_target_c: t.parameterOverrides?.temperature_target_c ?? 2.0,
      renewable_share_pct:  t.parameterOverrides?.renewable_share_pct  ?? 55,
    },
  })), []);

  const filtered = useMemo(() => {
    let list = enriched;

    if (search.trim()) {
      const q = search.toLowerCase();
      list = list.filter(t =>
        t.name.toLowerCase().includes(q) ||
        t.description.toLowerCase().includes(q) ||
        t.tags?.some(tag => tag.toLowerCase().includes(q))
      );
    }
    if (family !== 'all') {
      list = list.filter(t => t.ngfsFamily === family || t.ngfsFamily === 'all');
    }
    if (category !== 'all') {
      list = list.filter(t => t.category === category);
    }

    // Sort
    list = [...list].sort((a, b) => {
      if (sortBy === 'name')     return a.name.localeCompare(b.name);
      if (sortBy === 'family')   return (a.ngfsFamily || '').localeCompare(b.ngfsFamily || '');
      if (sortBy === 'category') return (a.category || '').localeCompare(b.category || '');
      return 0; // updated — keep insertion order
    });

    return list;
  }, [enriched, search, family, category, sortBy]);

  // Group by category order
  const grouped = useMemo(() => ({
    ngfs:       filtered.filter(t => t.category === 'ngfs'),
    regulatory: filtered.filter(t => t.category === 'regulatory'),
    stress:     filtered.filter(t => t.category === 'stress'),
    custom:     filtered.filter(t => t.category === 'custom'),
  }), [filtered]);

  const handleEdit  = useCallback((template) => {
    navigate('/scenario-builder-v2', { state: { templateId: template.id } });
  }, [navigate]);

  const handleFork  = useCallback((template) => {
    // Fork = navigate to builder with forked template (same as edit but marks as new custom)
    navigate('/scenario-builder-v2', { state: { templateId: template.id, fork: true } });
  }, [navigate]);

  const handleUse   = useCallback((template) => {
    navigate('/scenario-analysis', { state: { scenarioTemplateId: template.id } });
  }, [navigate]);

  const handleNew   = useCallback(() => {
    navigate('/scenario-builder-v2');
  }, [navigate]);

  const clearFilters = useCallback(() => {
    setSearch(''); setFamily('all'); setCategory('all'); setSortBy('category');
  }, []);

  const hasFilters = search.trim() || family !== 'all' || category !== 'all';

  const renderGrid = (templates, empty) => {
    if (templates.length === 0) {
      return empty ? <p className="text-[11px] text-gray-400 py-4">None yet</p> : null;
    }
    return (
      <div className={`grid gap-3 ${view === 'grid' ? 'grid-cols-1 md:grid-cols-2 xl:grid-cols-3' : 'grid-cols-1'}`}>
        {templates.map(t => (
          <ScenarioCard
            key={t.id}
            template={t}
            onEdit={() => handleEdit(t)}
            onFork={() => handleFork(t)}
            onUse={() => handleUse(t)}
          />
        ))}
      </div>
    );
  };

  // Flat view when filters are active
  const useGroupedView = !hasFilters && sortBy === 'category';

  return (
    <div className="flex flex-col h-full">
      {/* ── Page header ────────────────────────────────────────────────────── */}
      <div className="h-11 border-b border-gray-200 px-4 flex items-center gap-3 shrink-0 bg-white">
        <h1 className="text-[13px] font-semibold text-gray-800">Scenario Gallery</h1>
        <span className="text-[9px] text-gray-500 bg-gray-50 px-1.5 py-0.5 rounded font-mono">
          {filtered.length} scenarios
        </span>
        <div className="flex-1" />
        <button
          onClick={handleNew}
          className="text-[11px] font-semibold px-3 py-1.5 rounded bg-gray-200 border border-gray-300 text-gray-800 hover:bg-gray-300 transition-colors flex items-center gap-1.5"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          New Scenario
        </button>
      </div>

      {/* ── Content ────────────────────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Summary stats */}
        <SummaryStatsBar templates={enriched} />

        {/* Filters bar */}
        <div className="flex items-center gap-2 flex-wrap">
          {/* Search */}
          <div className="relative flex-1 min-w-[180px]">
            <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search scenarios…"
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-[11px] bg-gray-50 border border-black/10 rounded text-gray-700 placeholder-gray-400 focus:outline-none focus:border-blue-500"
            />
          </div>

          {/* Family filter */}
          <select
            value={family}
            onChange={e => setFamily(e.target.value)}
            className="text-[11px] bg-gray-50 border border-black/10 rounded px-2 py-1.5 text-gray-500 focus:outline-none"
          >
            <option value="all">All Families</option>
            {FAMILIES.slice(1).map(f => (
              <option key={f} value={f}>{f === 'Hot house world' ? 'Hot House World' : f}</option>
            ))}
          </select>

          {/* Category filter */}
          <select
            value={category}
            onChange={e => setCategory(e.target.value)}
            className="text-[11px] bg-gray-50 border border-black/10 rounded px-2 py-1.5 text-gray-500 focus:outline-none"
          >
            <option value="all">All Categories</option>
            {CATEGORIES.slice(1).map(c => (
              <option key={c} value={c}>{CATEGORY_META[c]?.label ?? c}</option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="text-[11px] bg-gray-50 border border-black/10 rounded px-2 py-1.5 text-gray-500 focus:outline-none"
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>

          {/* View toggle */}
          <div className="flex border border-black/10 rounded overflow-hidden">
            {[
              { v: 'grid', d: 'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z' },
              { v: 'list', d: 'M4 6h16M4 10h16M4 14h16M4 18h16' },
            ].map(({ v, d }) => (
              <button
                key={v}
                onClick={() => setView(v)}
                className={`px-2 py-1.5 transition-colors ${view === v ? 'bg-gray-100 text-gray-700' : 'text-gray-500 hover:text-gray-500'}`}
              >
                <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
                  <path strokeLinecap="round" strokeLinejoin="round" d={d} />
                </svg>
              </button>
            ))}
          </div>

          {/* Clear */}
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="text-[10px] text-gray-500 hover:text-gray-600 underline transition-colors"
            >
              Clear filters
            </button>
          )}
        </div>

        {/* ── Scenario grid ─────────────────────────────────────────────────── */}
        {filtered.length === 0 ? (
          <EmptyState onNew={handleNew} />
        ) : useGroupedView ? (
          /* Grouped view (default — no filters active) */
          <div className="space-y-6">
            {grouped.ngfs.length > 0 && (
              <div className="space-y-3">
                <SectionHeader label="NGFS Phase IV — Official" count={grouped.ngfs.length} accentColor="cyan" />
                {renderGrid(grouped.ngfs)}
              </div>
            )}
            {grouped.regulatory.length > 0 && (
              <div className="space-y-3">
                <SectionHeader label="Regulatory Presets" count={grouped.regulatory.length} accentColor="violet" />
                {renderGrid(grouped.regulatory)}
              </div>
            )}
            {grouped.stress.length > 0 && (
              <div className="space-y-3">
                <SectionHeader label="Stress Tests" count={grouped.stress.length} accentColor="amber" />
                {renderGrid(grouped.stress)}
              </div>
            )}
            {grouped.custom.length > 0 && (
              <div className="space-y-3">
                <SectionHeader label="Custom Scenarios" count={grouped.custom.length} accentColor="white" />
                {renderGrid(grouped.custom)}
              </div>
            )}
          </div>
        ) : (
          /* Flat filtered view */
          renderGrid(filtered)
        )}

        {/* Spacer */}
        <div className="h-6" />
      </div>
    </div>
  );
}
