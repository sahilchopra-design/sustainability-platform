/**
 * ScenarioTemplateGallery — browsable library of official NGFS + custom templates.
 * Supports search, filter by family / category / tag, and "Use Template" action.
 */
import React from 'react';
import { useScenarioTemplates } from '../hooks/useScenarioTemplates';
import { NGFS_FAMILY_META } from '../data/ngfsData';

// ─── Sub-components ───────────────────────────────────────────────────────────

const CATEGORY_LABELS = {
  ngfs:       'Official NGFS',
  custom:     'Custom',
  stress:     'Stress Test',
  regulatory: 'Regulatory',
};

const CATEGORY_COLORS = {
  ngfs:       'text-cyan-400 bg-cyan-500/10 border-cyan-500/20',
  custom:     'text-violet-400 bg-violet-500/10 border-violet-500/20',
  stress:     'text-red-400 bg-red-500/10 border-red-500/20',
  regulatory: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
};

function FamilyBadge({ family }) {
  if (!family) return null;
  const meta = NGFS_FAMILY_META[family] || {};
  return (
    <span className={`inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold border ${meta.bgClass} ${meta.textClass} ${meta.borderClass}`}>
      {family}
    </span>
  );
}

function CategoryBadge({ category }) {
  const cls = CATEGORY_COLORS[category] || 'text-white/40 bg-white/5 border-white/10';
  return (
    <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-semibold border ${cls}`}>
      {CATEGORY_LABELS[category] || category}
    </span>
  );
}

function TemplateCard({ template, onSelect, isSelected }) {
  return (
    <div
      data-testid={`template-card-${template.id}`}
      onClick={() => onSelect(template)}
      className={`relative flex flex-col rounded-lg border cursor-pointer transition-all duration-150 p-3.5 group
        ${isSelected
          ? 'border-cyan-500/60 bg-cyan-500/8 shadow-[0_0_0_1px_rgba(34,211,238,0.15)]'
          : 'border-white/8 bg-[#0d1526] hover:border-white/16 hover:bg-[#111b30]'
        }`}
    >
      {/* Official badge */}
      {template.isOfficial && (
        <div className="absolute top-2.5 right-2.5">
          <span className="text-[9px] font-bold text-amber-400/80 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded">
            OFFICIAL
          </span>
        </div>
      )}

      {/* Header */}
      <div className="flex items-start gap-2 mb-2 pr-10">
        <div>
          <h4 className="text-[13px] font-semibold text-white/90 leading-snug mb-1">
            {template.name}
          </h4>
          <div className="flex flex-wrap gap-1 mb-1.5">
            <FamilyBadge family={template.ngfsFamily} />
            <CategoryBadge category={template.category} />
          </div>
        </div>
      </div>

      {/* Description */}
      <p className="text-[11px] text-white/45 leading-relaxed mb-3 flex-1 line-clamp-3">
        {template.description}
      </p>

      {/* Tags */}
      <div className="flex flex-wrap gap-1 mb-3">
        {template.tags.slice(0, 5).map(tag => (
          <span key={tag} className="text-[9px] text-white/30 bg-white/5 px-1.5 py-0.5 rounded">
            {tag}
          </span>
        ))}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between pt-2 border-t border-white/5">
        <div className="flex items-center gap-3 text-[10px] text-white/30">
          <span>{template.author}</span>
          <span>·</span>
          <span>{template.usageCount.toLocaleString()} uses</span>
        </div>
        <button
          onClick={(e) => { e.stopPropagation(); onSelect(template); }}
          className={`text-[11px] font-medium px-2.5 py-1 rounded transition-colors ${
            isSelected
              ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30'
              : 'bg-white/5 text-white/60 hover:bg-cyan-500/15 hover:text-cyan-300 border border-white/8'
          }`}
        >
          {isSelected ? 'Selected' : 'Use Template'}
        </button>
      </div>
    </div>
  );
}

// ─── Main component ────────────────────────────────────────────────────────────

export function ScenarioTemplateGallery({ onSelectTemplate, selectedTemplateId }) {
  const {
    searchQuery, setSearchQuery,
    selectedFamily, setSelectedFamily,
    selectedCategory, setSelectedCategory,
    sortBy, setSortBy,
    filtered, allFamilies, allCategories,
    clearFilters,
  } = useScenarioTemplates();

  const hasFilters = searchQuery || selectedFamily !== 'all' || selectedCategory !== 'all';

  return (
    <div className="flex flex-col h-full" data-testid="scenario-template-gallery">
      {/* Search + filter bar */}
      <div className="flex flex-col gap-2 mb-4">
        <div className="flex items-center gap-2">
          <div className="relative flex-1">
            <svg className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-white/30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              type="text"
              placeholder="Search templates..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full pl-8 pr-3 py-1.5 text-[12px] bg-white/5 border border-white/10 rounded text-white/80 placeholder-white/25 focus:outline-none focus:border-cyan-500/40"
              data-testid="template-search"
            />
          </div>
          {hasFilters && (
            <button
              onClick={clearFilters}
              className="text-[11px] text-white/40 hover:text-white/70 px-2 py-1.5 rounded border border-white/8 hover:border-white/16 transition-colors"
            >
              Clear
            </button>
          )}
        </div>

        {/* Filter row */}
        <div className="flex flex-wrap gap-2">
          {/* NGFS Family */}
          <select
            value={selectedFamily}
            onChange={e => setSelectedFamily(e.target.value)}
            className="text-[11px] bg-white/5 border border-white/10 rounded px-2 py-1 text-white/60 focus:outline-none focus:border-cyan-500/40"
            data-testid="filter-family"
          >
            {allFamilies.map(f => (
              <option key={f} value={f}>{f === 'all' ? 'All Families' : f}</option>
            ))}
          </select>

          {/* Category */}
          <select
            value={selectedCategory}
            onChange={e => setSelectedCategory(e.target.value)}
            className="text-[11px] bg-white/5 border border-white/10 rounded px-2 py-1 text-white/60 focus:outline-none focus:border-cyan-500/40"
            data-testid="filter-category"
          >
            {allCategories.map(c => (
              <option key={c} value={c}>
                {c === 'all' ? 'All Types' : CATEGORY_LABELS[c] || c}
              </option>
            ))}
          </select>

          {/* Sort */}
          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="text-[11px] bg-white/5 border border-white/10 rounded px-2 py-1 text-white/60 focus:outline-none focus:border-cyan-500/40"
          >
            <option value="usage">Most Used</option>
            <option value="name">A–Z</option>
            <option value="date">Newest</option>
          </select>

          {/* Result count */}
          <span className="self-center text-[10px] text-white/30 ml-auto">
            {filtered.length} template{filtered.length !== 1 ? 's' : ''}
          </span>
        </div>
      </div>

      {/* Grid */}
      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-16 text-white/20 text-sm">
          <svg className="h-10 w-10 mb-3 opacity-30" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          No templates match your filters
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 overflow-y-auto">
          {filtered.map(tpl => (
            <TemplateCard
              key={tpl.id}
              template={tpl}
              onSelect={onSelectTemplate}
              isSelected={selectedTemplateId === tpl.id}
            />
          ))}
        </div>
      )}
    </div>
  );
}

export default ScenarioTemplateGallery;
