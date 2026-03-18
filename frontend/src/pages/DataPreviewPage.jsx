import React, { useState, useEffect, useMemo, useCallback } from 'react';

const API = process.env.REACT_APP_BACKEND_URL;

/* ------------------------------------------------------------------ */
/*  Utility: fetch JSON with error handling                           */
/* ------------------------------------------------------------------ */
async function apiFetch(path) {
  const r = await fetch(`${API}${path}`);
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}`);
  return r.json();
}

/* ------------------------------------------------------------------ */
/*  Colour tokens (matches existing dark theme)                       */
/* ------------------------------------------------------------------ */
const C = {
  bg:       '#ffffff',
  card:     '#0c1527',
  border:   '#1a2540',
  accent:   '#22d3ee',   // cyan-400
  accentDim:'#0e7490',
  text:     '#e2e8f0',
  muted:    '#94a3b8',
  green:    '#34d399',
  red:      '#f87171',
  yellow:   '#fbbf24',
  purple:   '#a78bfa',
  blue:     '#60a5fa',
};

/* ------------------------------------------------------------------ */
/*  Module badge colours                                               */
/* ------------------------------------------------------------------ */
const MODULE_COLOURS = {
  portfolio: '#22d3ee', carbon: '#34d399', cbam: '#fbbf24', ecl: '#f87171',
  pcaf: '#a78bfa', supply_chain: '#60a5fa', sector: '#fb923c', regulatory: '#c084fc',
  valuation: '#2dd4bf', nature: '#4ade80', csrd: '#818cf8', esrs: '#c084fc',
  issb: '#f472b6', fi: '#38bdf8', energy: '#f59e0b', data_hub: '#94a3b8',
  scenario: '#22d3ee', auth: '#6b7280', audit: '#6b7280', system: '#475569',
  real_estate: '#fb7185', other: '#6b7280',
};

/* ------------------------------------------------------------------ */
/*  Tab button                                                         */
/* ------------------------------------------------------------------ */
function Tab({ label, active, onClick, badge }) {
  return (
    <button
      onClick={onClick}
      className="px-3 py-1.5 text-xs font-mono rounded-md transition-all whitespace-nowrap"
      style={{
        background: active ? C.accent + '22' : 'transparent',
        color: active ? C.accent : C.muted,
        border: `1px solid ${active ? C.accent + '44' : 'transparent'}`,
      }}
    >
      {label}
      {badge != null && (
        <span className="ml-1.5 px-1.5 py-0.5 rounded text-[10px]" style={{ background: C.accent + '33', color: C.accent }}>
          {badge}
        </span>
      )}
    </button>
  );
}

/* ------------------------------------------------------------------ */
/*  Module badge                                                       */
/* ------------------------------------------------------------------ */
function ModuleBadge({ module }) {
  const col = MODULE_COLOURS[module] || MODULE_COLOURS.other;
  return (
    <span
      className="px-1.5 py-0.5 rounded text-[10px] font-mono uppercase"
      style={{ background: col + '22', color: col, border: `1px solid ${col}44` }}
    >
      {module}
    </span>
  );
}

/* ------------------------------------------------------------------ */
/*  Table List Sidebar                                                 */
/* ------------------------------------------------------------------ */
function TableList({ tables, selected, onSelect, filter, onFilter, moduleFilter, onModuleFilter, modules }) {
  const filtered = useMemo(() => {
    return tables.filter(t => {
      if (filter && !t.table_name.toLowerCase().includes(filter.toLowerCase())) return false;
      if (moduleFilter && t.module !== moduleFilter) return false;
      return true;
    });
  }, [tables, filter, moduleFilter]);

  return (
    <div className="flex flex-col h-full" style={{ borderRight: `1px solid ${C.border}` }}>
      <div className="p-3 space-y-2" style={{ borderBottom: `1px solid ${C.border}` }}>
        <div className="text-xs font-mono uppercase tracking-wider" style={{ color: C.muted }}>Tables</div>
        <input
          type="text"
          placeholder="Search tables..."
          value={filter}
          onChange={e => onFilter(e.target.value)}
          className="w-full px-2 py-1.5 text-xs font-mono rounded"
          style={{ background: C.bg, color: C.text, border: `1px solid ${C.border}`, outline: 'none' }}
        />
        <select
          value={moduleFilter}
          onChange={e => onModuleFilter(e.target.value)}
          className="w-full px-2 py-1.5 text-xs font-mono rounded"
          style={{ background: C.bg, color: C.text, border: `1px solid ${C.border}`, outline: 'none' }}
        >
          <option value="">All modules</option>
          {modules.map(m => <option key={m} value={m}>{m}</option>)}
        </select>
      </div>
      <div className="flex-1 overflow-auto">
        {filtered.map(t => (
          <button
            key={t.table_name}
            onClick={() => onSelect(t.table_name)}
            className="w-full text-left px-3 py-2 flex items-center gap-2 transition-all hover:bg-[#1a2540]"
            style={{
              background: selected === t.table_name ? C.accent + '15' : 'transparent',
              borderLeft: selected === t.table_name ? `2px solid ${C.accent}` : '2px solid transparent',
            }}
          >
            <div className="flex-1 min-w-0">
              <div className="text-xs font-mono truncate" style={{ color: selected === t.table_name ? C.accent : C.text }}>
                {t.table_name}
              </div>
              <div className="flex items-center gap-2 mt-0.5">
                <ModuleBadge module={t.module} />
                <span className="text-[10px] font-mono" style={{ color: C.muted }}>
                  {t.row_count.toLocaleString()} rows
                </span>
              </div>
            </div>
          </button>
        ))}
        {filtered.length === 0 && (
          <div className="p-4 text-xs text-center" style={{ color: C.muted }}>No tables match filter</div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Data Grid (first 100 rows)                                         */
/* ------------------------------------------------------------------ */
function DataGrid({ data, loading }) {
  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-5 h-5 border-2 rounded-full animate-spin" style={{ borderColor: C.accent, borderTopColor: 'transparent' }} />
    </div>
  );
  if (!data) return (
    <div className="flex items-center justify-center h-64 text-sm font-mono" style={{ color: C.muted }}>
      Select a table to preview data
    </div>
  );

  return (
    <div className="overflow-auto" style={{ maxHeight: 'calc(100vh - 280px)' }}>
      <div className="flex items-center gap-3 px-3 py-2 text-xs font-mono" style={{ color: C.muted, borderBottom: `1px solid ${C.border}` }}>
        <span>Showing <span style={{ color: C.accent }}>{data.preview_rows}</span> of <span style={{ color: C.text }}>{data.total_rows.toLocaleString()}</span> rows</span>
        <span>|</span>
        <span>{data.columns.length} columns</span>
        <span>|</span>
        <ModuleBadge module={data.module} />
      </div>
      <table className="w-full text-xs font-mono" style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th className="px-3 py-2 text-left sticky top-0 z-10" style={{ background: C.card, color: C.muted, borderBottom: `1px solid ${C.border}`, fontSize: '10px' }}>#</th>
            {data.columns.map((col, i) => (
              <th key={col} className="px-3 py-2 text-left sticky top-0 z-10 whitespace-nowrap" style={{ background: C.card, color: C.accent, borderBottom: `1px solid ${C.border}`, fontSize: '10px' }}>
                {col}
                <div className="text-[9px] font-normal" style={{ color: C.muted }}>{data.column_types[i]}</div>
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.rows.map((row, i) => (
            <tr key={i} className="hover:bg-[#f0f0f0]" style={{ borderBottom: `1px solid ${C.border}22` }}>
              <td className="px-3 py-1.5" style={{ color: C.muted }}>{i + 1}</td>
              {data.columns.map(col => (
                <td key={col} className="px-3 py-1.5 max-w-[200px] truncate" style={{ color: C.text }}>
                  {row[col] === null ? <span style={{ color: C.muted, fontStyle: 'italic' }}>null</span> : String(row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Relationship Graph (module-level)                                  */
/* ------------------------------------------------------------------ */
function RelationshipView({ relationships, loading }) {
  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-5 h-5 border-2 rounded-full animate-spin" style={{ borderColor: C.accent, borderTopColor: 'transparent' }} />
    </div>
  );
  if (!relationships) return null;

  return (
    <div className="space-y-4 p-4">
      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Total FK Relations', value: relationships.total_relationships, color: C.accent },
          { label: 'Cross-Module Links', value: relationships.cross_module_count, color: C.purple },
          { label: 'Module Pairs', value: relationships.module_adjacency?.length || 0, color: C.green },
        ].map(kpi => (
          <div key={kpi.label} className="rounded-lg p-3" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
            <div className="text-[10px] font-mono uppercase" style={{ color: C.muted }}>{kpi.label}</div>
            <div className="text-xl font-mono mt-1" style={{ color: kpi.color }}>{kpi.value}</div>
          </div>
        ))}
      </div>

      {/* Module adjacency */}
      <div>
        <div className="text-xs font-mono uppercase tracking-wider mb-2" style={{ color: C.muted }}>Module Adjacency</div>
        <div className="space-y-1">
          {(relationships.module_adjacency || []).map((adj, i) => (
            <div key={i} className="flex items-center gap-2 px-3 py-2 rounded" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
              <ModuleBadge module={adj.source} />
              <span className="text-xs" style={{ color: C.muted }}>-&gt;</span>
              <ModuleBadge module={adj.target} />
              <span className="ml-auto text-xs font-mono" style={{ color: C.accent }}>{adj.link_count} links</span>
            </div>
          ))}
        </div>
      </div>

      {/* Detailed FK list */}
      <div>
        <div className="text-xs font-mono uppercase tracking-wider mb-2" style={{ color: C.muted }}>Foreign Key Details</div>
        <div className="overflow-auto" style={{ maxHeight: '400px' }}>
          <table className="w-full text-xs font-mono" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Source Table', 'Column', 'Target Table', 'Column', 'Type', 'Cross-Module'].map(h => (
                  <th key={h} className="px-2 py-1.5 text-left sticky top-0" style={{ background: C.card, color: C.muted, borderBottom: `1px solid ${C.border}` }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(relationships.relationships || []).map((r, i) => (
                <tr key={i} className="hover:bg-[#f0f0f0]">
                  <td className="px-2 py-1" style={{ color: C.text }}>{r.source_table}</td>
                  <td className="px-2 py-1" style={{ color: C.accent }}>{r.source_column}</td>
                  <td className="px-2 py-1" style={{ color: C.text }}>{r.target_table}</td>
                  <td className="px-2 py-1" style={{ color: C.accent }}>{r.target_column}</td>
                  <td className="px-2 py-1"><ModuleBadge module={r.relationship_type} /></td>
                  <td className="px-2 py-1" style={{ color: r.is_cross_module ? C.green : C.muted }}>{r.is_cross_module ? 'Yes' : 'No'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Datapoint Mapping View                                             */
/* ------------------------------------------------------------------ */
function DatapointMappingView({ mappings, loading }) {
  const [catFilter, setCatFilter] = useState('');
  const [confFilter, setConfFilter] = useState('');

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-5 h-5 border-2 rounded-full animate-spin" style={{ borderColor: C.accent, borderTopColor: 'transparent' }} />
    </div>
  );
  if (!mappings) return null;

  const CATEGORY_COLOURS = {
    identity_link: C.accent, financial_metric: C.green, risk_indicator: C.red,
    temporal_join: C.yellow, spatial_join: C.blue, classification: C.purple,
    aggregation_source: C.muted,
  };

  const filtered = useMemo(() => {
    return (mappings.mappings || []).filter(m => {
      if (catFilter && m.relationship_category !== catFilter) return false;
      if (confFilter && m.mapping_confidence !== confFilter) return false;
      return true;
    });
  }, [mappings, catFilter, confFilter]);

  return (
    <div className="space-y-4 p-4">
      {/* Summary */}
      <div className="grid grid-cols-4 gap-3">
        <div className="rounded-lg p-3" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
          <div className="text-[10px] font-mono uppercase" style={{ color: C.muted }}>Total Mappings</div>
          <div className="text-xl font-mono mt-1" style={{ color: C.accent }}>{mappings.total_mappings}</div>
        </div>
        <div className="rounded-lg p-3" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
          <div className="text-[10px] font-mono uppercase" style={{ color: C.muted }}>Exact FK</div>
          <div className="text-xl font-mono mt-1" style={{ color: C.green }}>{mappings.by_confidence?.exact_fk || 0}</div>
        </div>
        <div className="rounded-lg p-3" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
          <div className="text-[10px] font-mono uppercase" style={{ color: C.muted }}>Inferred</div>
          <div className="text-xl font-mono mt-1" style={{ color: C.yellow }}>{mappings.by_confidence?.inferred_name || 0}</div>
        </div>
        <div className="rounded-lg p-3" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
          <div className="text-[10px] font-mono uppercase" style={{ color: C.muted }}>Categories</div>
          <div className="text-xl font-mono mt-1" style={{ color: C.purple }}>{Object.keys(mappings.by_category || {}).length}</div>
        </div>
      </div>

      {/* Category breakdown */}
      <div className="flex flex-wrap gap-2">
        {Object.entries(mappings.by_category || {}).map(([cat, count]) => (
          <button
            key={cat}
            onClick={() => setCatFilter(catFilter === cat ? '' : cat)}
            className="px-2 py-1 rounded text-xs font-mono"
            style={{
              background: catFilter === cat ? (CATEGORY_COLOURS[cat] || C.muted) + '33' : C.bg,
              color: CATEGORY_COLOURS[cat] || C.muted,
              border: `1px solid ${catFilter === cat ? (CATEGORY_COLOURS[cat] || C.muted) : C.border}`,
            }}
          >
            {cat} ({count})
          </button>
        ))}
      </div>

      {/* Confidence filter */}
      <div className="flex gap-2">
        {['exact_fk', 'inferred_name'].map(c => (
          <button
            key={c}
            onClick={() => setConfFilter(confFilter === c ? '' : c)}
            className="px-2 py-1 rounded text-xs font-mono"
            style={{
              background: confFilter === c ? C.accent + '22' : C.bg,
              color: confFilter === c ? C.accent : C.muted,
              border: `1px solid ${confFilter === c ? C.accent : C.border}`,
            }}
          >
            {c === 'exact_fk' ? 'Exact FK' : 'Inferred Name'}
          </button>
        ))}
      </div>

      {/* Module pair summary */}
      <div>
        <div className="text-xs font-mono uppercase tracking-wider mb-2" style={{ color: C.muted }}>Module Pair Summary</div>
        <div className="grid grid-cols-2 gap-2">
          {Object.entries(mappings.module_pair_summary || {}).map(([pair, info]) => (
            <div key={pair} className="rounded px-3 py-2 flex items-center justify-between" style={{ background: C.bg, border: `1px solid ${C.border}` }}>
              <span className="text-xs font-mono" style={{ color: C.text }}>{pair}</span>
              <div className="flex items-center gap-2">
                <span className="text-xs font-mono" style={{ color: C.accent }}>{info.count}</span>
                <div className="flex gap-1">
                  {(info.categories || []).slice(0, 3).map(cat => (
                    <span key={cat} className="w-2 h-2 rounded-full" style={{ background: CATEGORY_COLOURS[cat] || C.muted }} />
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Mapping table */}
      <div>
        <div className="text-xs font-mono uppercase tracking-wider mb-2" style={{ color: C.muted }}>
          Datapoint Mappings ({filtered.length})
        </div>
        <div className="overflow-auto" style={{ maxHeight: '400px' }}>
          <table className="w-full text-xs font-mono" style={{ borderCollapse: 'collapse' }}>
            <thead>
              <tr>
                {['Source', 'Column', 'Target', 'Column', 'Category', 'Confidence', 'Modules'].map(h => (
                  <th key={h} className="px-2 py-1.5 text-left sticky top-0" style={{ background: C.card, color: C.muted, borderBottom: `1px solid ${C.border}` }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((m, i) => (
                <tr key={i} className="hover:bg-[#f0f0f0]">
                  <td className="px-2 py-1" style={{ color: C.text }}>{m.source_table}</td>
                  <td className="px-2 py-1" style={{ color: C.accent }}>{m.source_column}</td>
                  <td className="px-2 py-1" style={{ color: C.text }}>{m.target_table}</td>
                  <td className="px-2 py-1" style={{ color: C.accent }}>{m.target_column}</td>
                  <td className="px-2 py-1">
                    <span className="px-1.5 py-0.5 rounded text-[10px]" style={{ background: (CATEGORY_COLOURS[m.relationship_category] || C.muted) + '22', color: CATEGORY_COLOURS[m.relationship_category] || C.muted }}>
                      {m.relationship_category}
                    </span>
                  </td>
                  <td className="px-2 py-1">
                    <span style={{ color: m.mapping_confidence === 'exact_fk' ? C.green : C.yellow }}>
                      {m.mapping_confidence === 'exact_fk' ? 'FK' : 'Inferred'}
                    </span>
                  </td>
                  <td className="px-2 py-1">
                    <div className="flex gap-1">
                      <ModuleBadge module={m.module_source} />
                      <span style={{ color: C.muted }}>-&gt;</span>
                      <ModuleBadge module={m.module_target} />
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

/* ================================================================== */
/*  Main Page Component                                                */
/* ================================================================== */
export default function DataPreviewPage() {
  const [tables, setTables] = useState([]);
  const [selectedTable, setSelectedTable] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [relationships, setRelationships] = useState(null);
  const [mappings, setMappings] = useState(null);
  const [loadingTables, setLoadingTables] = useState(true);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [loadingRels, setLoadingRels] = useState(false);
  const [loadingMappings, setLoadingMappings] = useState(false);
  const [activeTab, setActiveTab] = useState('preview');
  const [tableFilter, setTableFilter] = useState('');
  const [moduleFilter, setModuleFilter] = useState('');

  // Load table list on mount
  useEffect(() => {
    setLoadingTables(true);
    apiFetch('/api/v1/data-preview/tables')
      .then(d => setTables(d.tables || []))
      .catch(() => setTables([]))
      .finally(() => setLoadingTables(false));
  }, []);

  // Load relationships when tab switches
  useEffect(() => {
    if (activeTab === 'relationships' && !relationships) {
      setLoadingRels(true);
      apiFetch('/api/v1/data-preview/relationships')
        .then(setRelationships)
        .catch(() => setRelationships(null))
        .finally(() => setLoadingRels(false));
    }
    if (activeTab === 'mappings' && !mappings) {
      setLoadingMappings(true);
      apiFetch('/api/v1/data-preview/datapoint-mappings')
        .then(setMappings)
        .catch(() => setMappings(null))
        .finally(() => setLoadingMappings(false));
    }
  }, [activeTab, relationships, mappings]);

  // Load preview data when table is selected
  const handleSelectTable = useCallback((tableName) => {
    setSelectedTable(tableName);
    setActiveTab('preview');
    setLoadingPreview(true);
    setPreviewData(null);
    apiFetch(`/api/v1/data-preview/tables/${tableName}/preview`)
      .then(setPreviewData)
      .catch(() => setPreviewData(null))
      .finally(() => setLoadingPreview(false));
  }, []);

  const modules = useMemo(() => {
    const s = new Set(tables.map(t => t.module));
    return [...s].sort();
  }, [tables]);

  return (
    <div className="h-full flex flex-col" style={{ background: C.bg }}>
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-3" style={{ borderBottom: `1px solid ${C.border}` }}>
        <div>
          <h1 className="text-lg font-mono font-bold" style={{ color: C.text }}>Data Preview & Mapping</h1>
          <p className="text-xs font-mono" style={{ color: C.muted }}>
            {tables.length} tables | Browse data, explore FK relationships, and view inter-module datapoint mappings
          </p>
        </div>
        <div className="flex gap-2">
          <Tab label="Data Preview" active={activeTab === 'preview'} onClick={() => setActiveTab('preview')} />
          <Tab label="Relationships" active={activeTab === 'relationships'} onClick={() => setActiveTab('relationships')} badge={relationships ? relationships.total_relationships : null} />
          <Tab label="Datapoint Mapping" active={activeTab === 'mappings'} onClick={() => setActiveTab('mappings')} badge={mappings ? mappings.total_mappings : null} />
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar: table list (always visible) */}
        <div className="w-64 flex-shrink-0 overflow-hidden" style={{ background: C.card }}>
          {loadingTables ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-5 h-5 border-2 rounded-full animate-spin" style={{ borderColor: C.accent, borderTopColor: 'transparent' }} />
            </div>
          ) : (
            <TableList
              tables={tables}
              selected={selectedTable}
              onSelect={handleSelectTable}
              filter={tableFilter}
              onFilter={setTableFilter}
              moduleFilter={moduleFilter}
              onModuleFilter={setModuleFilter}
              modules={modules}
            />
          )}
        </div>

        {/* Main content */}
        <div className="flex-1 overflow-auto" style={{ background: C.card }}>
          {activeTab === 'preview' && <DataGrid data={previewData} loading={loadingPreview} />}
          {activeTab === 'relationships' && <RelationshipView relationships={relationships} loading={loadingRels} />}
          {activeTab === 'mappings' && <DatapointMappingView mappings={mappings} loading={loadingMappings} />}
        </div>
      </div>
    </div>
  );
}
