/**
 * Data Mapping Page
 * Manual mapping of datapoints between data sources, KPIs, and platform modules.
 *
 * Tabs:
 *  1. Module Coverage — overview of which modules have data sources mapped
 *  2. KPI Catalog     — browse application KPIs with mapping status
 *  3. Source Browser   — browse fields per data source
 *  4. Mapping Editor   — create/edit/delete individual mappings
 */
import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Badge } from '../components/ui/badge';
import { Button } from '../components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../components/ui/select';
import { Separator } from '../components/ui/separator';
import {
  Database, Link2, Layers, Search, Plus, Trash2, Edit3, Check,
  X, ArrowRight, ChevronDown, ChevronRight, RefreshCw, AlertTriangle,
  CheckCircle2, Circle, Filter, Download, Upload, Zap, Target,
  BarChart3, Shield, Globe2, Leaf, Building2, Cpu, FileText, Box,
} from 'lucide-react';
import { cn } from '../lib/utils';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function authHeaders() {
  const t = localStorage.getItem('session_token');
  return t ? { Authorization: `Bearer ${t}` } : {};
}

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: { 'Content-Type': 'application/json', ...authHeaders(), ...(opts.headers || {}) },
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json();
}

// ── Module icon map ──────────────────────────────────────────────────────────
const MODULE_ICONS = {
  ecl: Shield,
  pcaf: BarChart3,
  carbon: Leaf,
  nature_risk: Globe2,
  stranded_assets: AlertTriangle,
  valuation: Building2,
  sustainability: Target,
  cbam: Globe2,
  scenario_analysis: Layers,
  supply_chain: Box,
  regulatory: FileText,
  default: Cpu,
};

function ModuleIcon({ module, className }) {
  const Icon = MODULE_ICONS[module] || MODULE_ICONS.default;
  return <Icon className={className} />;
}

// ── Confidence badge ─────────────────────────────────────────────────────────
function ConfidenceBadge({ score }) {
  if (score == null) return <Badge variant="outline" className="text-[10px] text-white/30 border-white/10">N/A</Badge>;
  const pct = Math.round(score * 100);
  const color = pct >= 80 ? 'text-emerald-400 border-emerald-400/20 bg-emerald-400/5'
    : pct >= 50 ? 'text-amber-400 border-amber-400/20 bg-amber-400/5'
    : 'text-red-400 border-red-400/20 bg-red-400/5';
  return <Badge variant="outline" className={cn('text-[10px]', color)}>{pct}%</Badge>;
}

// ══════════════════════════════════════════════════════════════════════════════
//  TAB 1 — MODULE COVERAGE
// ══════════════════════════════════════════════════════════════════════════════
function ModuleCoverageTab() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    apiFetch('/api/v1/ingestion/module-coverage')
      .then(setData)
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingState label="Loading module coverage..." />;
  if (!data) return <EmptyState label="Unable to load module coverage" />;

  return (
    <div className="space-y-4">
      {/* Summary cards */}
      <div className="grid grid-cols-3 gap-3">
        <StatCard label="Total KPIs" value={data.total_kpis} icon={Database} />
        <StatCard label="Mapped KPIs" value={data.total_mapped} icon={Link2} accent="cyan" />
        <StatCard label="Modules" value={data.modules?.length || 0} icon={Layers} accent="violet" />
      </div>

      {/* Module grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {data.modules?.map(m => (
          <Card key={m.module} className="bg-[#0d1424] border-white/[0.06]">
            <CardContent className="p-4">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-1.5 rounded bg-white/5">
                    <ModuleIcon module={m.module} className="h-4 w-4 text-cyan-400" />
                  </div>
                  <div>
                    <p className="text-sm font-medium text-white/80">{m.module.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                    <p className="text-[10px] text-white/30">{m.source_count} source{m.source_count !== 1 ? 's' : ''}</p>
                  </div>
                </div>
                <Badge variant="outline" className={cn(
                  'text-[10px]',
                  m.coverage_pct >= 80 ? 'text-emerald-400 border-emerald-400/20' :
                  m.coverage_pct >= 40 ? 'text-amber-400 border-amber-400/20' :
                  'text-red-400 border-red-400/20'
                )}>
                  {m.coverage_pct}%
                </Badge>
              </div>
              {/* Progress bar */}
              <div className="h-1.5 bg-white/5 rounded-full overflow-hidden">
                <div
                  className={cn(
                    'h-full rounded-full transition-all',
                    m.coverage_pct >= 80 ? 'bg-emerald-500' :
                    m.coverage_pct >= 40 ? 'bg-amber-500' :
                    'bg-red-500'
                  )}
                  style={{ width: `${m.coverage_pct}%` }}
                />
              </div>
              <p className="text-[10px] text-white/30 mt-1.5">{m.mapped_kpis} / {m.total_kpis} KPIs mapped</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );
}


// ══════════════════════════════════════════════════════════════════════════════
//  TAB 2 — KPI CATALOG
// ══════════════════════════════════════════════════════════════════════════════
function KpiCatalogTab({ onSelectKpi }) {
  const [kpis, setKpis] = useState([]);
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('__all__');
  const [moduleFilter, setModuleFilter] = useState('__all__');

  const load = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '500' });
    if (catFilter && catFilter !== '__all__') params.set('category', catFilter);
    if (moduleFilter && moduleFilter !== '__all__') params.set('module', moduleFilter);
    if (search) params.set('search', search);

    Promise.all([
      apiFetch(`/api/v1/ingestion/kpis?${params}`),
      apiFetch('/api/v1/ingestion/kpi-categories'),
    ])
      .then(([kData, cData]) => {
        setKpis(kData.kpis || []);
        setCategories(cData.categories || []);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [catFilter, moduleFilter, search]);

  useEffect(() => { load(); }, [load]);

  // Unique modules across all KPIs
  const modules = useMemo(() => {
    const s = new Set();
    kpis.forEach(k => (k.target_modules || []).forEach(m => s.add(m)));
    return [...s].sort();
  }, [kpis]);

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex items-center gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px] max-w-xs">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-white/30" />
          <input
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Search KPIs..."
            className="w-full h-8 pl-8 pr-3 bg-[#0d1424] border border-white/[0.06] rounded text-xs text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
          />
        </div>
        <Select value={catFilter} onValueChange={setCatFilter}>
          <SelectTrigger className="w-44 h-8 bg-[#0d1424] border-white/[0.06] text-xs text-white/60">
            <SelectValue placeholder="Category" />
          </SelectTrigger>
          <SelectContent className="bg-[#0d1424] border-white/[0.06]">
            <SelectItem value="__all__" className="text-xs text-white/60">All Categories</SelectItem>
            {categories.map(c => (
              <SelectItem key={c.category} value={c.category} className="text-xs text-white/60">
                {c.category} ({c.count})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={moduleFilter} onValueChange={setModuleFilter}>
          <SelectTrigger className="w-40 h-8 bg-[#0d1424] border-white/[0.06] text-xs text-white/60">
            <SelectValue placeholder="Module" />
          </SelectTrigger>
          <SelectContent className="bg-[#0d1424] border-white/[0.06]">
            <SelectItem value="__all__" className="text-xs text-white/60">All Modules</SelectItem>
            {modules.map(m => (
              <SelectItem key={m} value={m} className="text-xs text-white/60">
                {m.replace(/_/g, ' ')}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Badge variant="outline" className="text-[10px] text-white/40 border-white/10">
          {kpis.length} KPI{kpis.length !== 1 ? 's' : ''}
        </Badge>
      </div>

      {loading ? <LoadingState label="Loading KPIs..." /> : (
        <div className="border border-white/[0.06] rounded-lg overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0a1020] text-white/40">
                <th className="text-left px-3 py-2 font-medium">KPI Name</th>
                <th className="text-left px-3 py-2 font-medium w-28">Category</th>
                <th className="text-left px-3 py-2 font-medium w-20">Unit</th>
                <th className="text-left px-3 py-2 font-medium w-28">Modules</th>
                <th className="text-center px-3 py-2 font-medium w-20">Mappings</th>
                <th className="text-center px-3 py-2 font-medium w-16">Req.</th>
                <th className="text-right px-3 py-2 font-medium w-20"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {kpis.map(k => (
                <tr key={k.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-3 py-2">
                    <p className="text-white/80 font-medium">{k.name}</p>
                    {k.description && <p className="text-white/30 text-[10px] mt-0.5 line-clamp-1">{k.description}</p>}
                  </td>
                  <td className="px-3 py-2 text-white/50">{k.category}</td>
                  <td className="px-3 py-2 text-white/40">{k.unit || '--'}</td>
                  <td className="px-3 py-2">
                    <div className="flex flex-wrap gap-1">
                      {(k.target_modules || []).slice(0, 3).map(m => (
                        <Badge key={m} variant="outline" className="text-[9px] text-cyan-400/60 border-cyan-400/10 px-1">
                          {m}
                        </Badge>
                      ))}
                      {(k.target_modules || []).length > 3 && (
                        <Badge variant="outline" className="text-[9px] text-white/30 border-white/10 px-1">
                          +{k.target_modules.length - 3}
                        </Badge>
                      )}
                    </div>
                  </td>
                  <td className="px-3 py-2 text-center">
                    <Badge variant="outline" className={cn(
                      'text-[10px]',
                      k.mapping_count > 0
                        ? 'text-emerald-400 border-emerald-400/20'
                        : 'text-white/30 border-white/10'
                    )}>
                      {k.mapping_count}
                    </Badge>
                  </td>
                  <td className="px-3 py-2 text-center">
                    {k.is_required
                      ? <CheckCircle2 className="h-3.5 w-3.5 text-amber-400 mx-auto" />
                      : <Circle className="h-3.5 w-3.5 text-white/15 mx-auto" />}
                  </td>
                  <td className="px-3 py-2 text-right">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-2 text-[10px] text-cyan-400 hover:text-cyan-300 hover:bg-cyan-400/5"
                      onClick={() => onSelectKpi && onSelectKpi(k)}
                    >
                      Map <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {kpis.length === 0 && <EmptyState label="No KPIs match your filters" />}
        </div>
      )}
    </div>
  );
}


// ══════════════════════════════════════════════════════════════════════════════
//  TAB 3 — SOURCE BROWSER
// ══════════════════════════════════════════════════════════════════════════════
function SourceBrowserTab() {
  const [sources, setSources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedSource, setSelectedSource] = useState(null);
  const [fields, setFields] = useState([]);
  const [fieldsLoading, setFieldsLoading] = useState(false);
  const [search, setSearch] = useState('');
  const [catFilter, setCatFilter] = useState('__all__');

  useEffect(() => {
    setLoading(true);
    apiFetch('/api/v1/ingestion/sources?limit=200')
      .then(d => setSources(d.sources || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedSource) { setFields([]); return; }
    setFieldsLoading(true);
    apiFetch(`/api/v1/ingestion/source-fields?source_id=${selectedSource.id}&limit=500`)
      .then(d => setFields(d.fields || []))
      .catch(() => setFields([]))
      .finally(() => setFieldsLoading(false));
  }, [selectedSource]);

  const cats = useMemo(() => {
    const s = new Set(sources.map(s => s.category).filter(Boolean));
    return [...s].sort();
  }, [sources]);

  const filtered = useMemo(() => {
    let f = sources;
    if (catFilter && catFilter !== '__all__') f = f.filter(s => s.category === catFilter);
    if (search) {
      const q = search.toLowerCase();
      f = f.filter(s => s.name.toLowerCase().includes(q) || (s.category || '').toLowerCase().includes(q));
    }
    return f;
  }, [sources, catFilter, search]);

  if (loading) return <LoadingState label="Loading sources..." />;

  return (
    <div className="flex gap-4 h-[calc(100vh-240px)] min-h-[500px]">
      {/* Left: source list */}
      <div className="w-80 shrink-0 flex flex-col border border-white/[0.06] rounded-lg overflow-hidden">
        <div className="p-2 bg-[#0a1020] border-b border-white/[0.04] space-y-2">
          <div className="relative">
            <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-white/30" />
            <input
              value={search}
              onChange={e => setSearch(e.target.value)}
              placeholder="Search sources..."
              className="w-full h-7 pl-7 pr-2 bg-[#0d1424] border border-white/[0.06] rounded text-[11px] text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
            />
          </div>
          <Select value={catFilter} onValueChange={setCatFilter}>
            <SelectTrigger className="w-full h-7 bg-[#0d1424] border-white/[0.06] text-[11px] text-white/60">
              <SelectValue placeholder="All categories" />
            </SelectTrigger>
            <SelectContent className="bg-[#0d1424] border-white/[0.06]">
              <SelectItem value="__all__" className="text-[11px] text-white/60">All ({sources.length})</SelectItem>
              {cats.map(c => (
                <SelectItem key={c} value={c} className="text-[11px] text-white/60">{c}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="flex-1 overflow-auto">
          {filtered.map(s => (
            <button
              key={s.id}
              onClick={() => setSelectedSource(s)}
              className={cn(
                'w-full text-left px-3 py-2 border-b border-white/[0.03] transition-colors',
                selectedSource?.id === s.id
                  ? 'bg-cyan-500/10 border-l-2 border-l-cyan-500'
                  : 'hover:bg-white/[0.02]'
              )}
            >
              <p className={cn('text-[11px] font-medium', selectedSource?.id === s.id ? 'text-cyan-300' : 'text-white/70')}>{s.name}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Badge variant="outline" className="text-[9px] text-white/30 border-white/[0.06] px-1">{s.category}</Badge>
                {s.sync_enabled && <Badge variant="outline" className="text-[9px] text-emerald-400/60 border-emerald-400/10 px-1">sync</Badge>}
                {s.quality_rating && <Badge variant="outline" className="text-[9px] text-white/25 border-white/[0.06] px-1">{s.quality_rating}</Badge>}
              </div>
            </button>
          ))}
          {filtered.length === 0 && <EmptyState label="No sources match" />}
        </div>
      </div>

      {/* Right: source detail + fields */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {!selectedSource ? (
          <div className="flex-1 flex items-center justify-center text-white/20 text-sm">
            <div className="text-center">
              <Database className="h-8 w-8 mx-auto mb-2 opacity-30" />
              <p>Select a data source to view its fields</p>
            </div>
          </div>
        ) : (
          <>
            {/* Source header */}
            <Card className="bg-[#0d1424] border-white/[0.06] mb-3 shrink-0">
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-sm font-semibold text-white/90">{selectedSource.name}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant="outline" className="text-[10px] text-white/40 border-white/10">{selectedSource.category}</Badge>
                      <Badge variant="outline" className="text-[10px] text-white/40 border-white/10">{selectedSource.access_type}</Badge>
                      {selectedSource.assessment_score != null && (
                        <Badge variant="outline" className="text-[10px] text-cyan-400/60 border-cyan-400/15">
                          Score: {selectedSource.assessment_score.toFixed(1)}
                        </Badge>
                      )}
                    </div>
                  </div>
                  <Badge variant="outline" className="text-[10px] text-white/30 border-white/10">
                    {fields.length} field{fields.length !== 1 ? 's' : ''}
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Fields table */}
            {fieldsLoading ? <LoadingState label="Loading fields..." /> : (
              fields.length === 0 ? (
                <div className="flex-1 flex items-center justify-center">
                  <div className="text-center text-white/20 text-sm">
                    <AlertTriangle className="h-6 w-6 mx-auto mb-2 opacity-40" />
                    <p>No fields catalogued for this source yet.</p>
                    <p className="text-[10px] mt-1">Fields are registered during ingestion or manually via the mapping editor.</p>
                  </div>
                </div>
              ) : (
                <div className="flex-1 overflow-auto border border-white/[0.06] rounded-lg">
                  <table className="w-full text-xs">
                    <thead className="sticky top-0 bg-[#0a1020]">
                      <tr className="text-white/40">
                        <th className="text-left px-3 py-2 font-medium">Field Name</th>
                        <th className="text-left px-3 py-2 font-medium w-24">Type</th>
                        <th className="text-left px-3 py-2 font-medium w-20">Unit</th>
                        <th className="text-left px-3 py-2 font-medium">Path</th>
                        <th className="text-left px-3 py-2 font-medium">Description</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/[0.04]">
                      {fields.map(f => (
                        <tr key={f.id} className="hover:bg-white/[0.02]">
                          <td className="px-3 py-2 text-white/80 font-mono">{f.field_name}</td>
                          <td className="px-3 py-2 text-white/40">{f.data_type || '--'}</td>
                          <td className="px-3 py-2 text-white/40">{f.unit || '--'}</td>
                          <td className="px-3 py-2 text-white/30 font-mono text-[10px]">{f.field_path || '--'}</td>
                          <td className="px-3 py-2 text-white/30 text-[10px] line-clamp-1">{f.description || '--'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}
          </>
        )}
      </div>
    </div>
  );
}


// ══════════════════════════════════════════════════════════════════════════════
//  TAB 4 — MAPPING EDITOR
// ══════════════════════════════════════════════════════════════════════════════
function MappingEditorTab({ preselectedKpi }) {
  const [mappings, setMappings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [sources, setSources] = useState([]);
  const [kpis, setKpis] = useState([]);
  const [kpiFilter, setKpiFilter] = useState(preselectedKpi?.id || '__all__');
  const [sourceFilter, setSourceFilter] = useState('__all__');
  const [showCreate, setShowCreate] = useState(false);

  // load sources + kpis once
  useEffect(() => {
    Promise.all([
      apiFetch('/api/v1/ingestion/sources?limit=200'),
      apiFetch('/api/v1/ingestion/kpis?limit=500'),
    ]).then(([sData, kData]) => {
      setSources(sData.sources || []);
      setKpis(kData.kpis || []);
    }).catch(() => {});
  }, []);

  const loadMappings = useCallback(() => {
    setLoading(true);
    const params = new URLSearchParams({ limit: '500' });
    if (kpiFilter && kpiFilter !== '__all__') params.set('kpi_id', kpiFilter);
    if (sourceFilter && sourceFilter !== '__all__') params.set('source_id', sourceFilter);
    apiFetch(`/api/v1/ingestion/mappings?${params}`)
      .then(d => setMappings(d.mappings || []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [kpiFilter, sourceFilter]);

  useEffect(() => { loadMappings(); }, [loadMappings]);

  // Update kpi filter if preselected changes
  useEffect(() => {
    if (preselectedKpi?.id) setKpiFilter(preselectedKpi.id);
  }, [preselectedKpi]);

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this mapping?')) return;
    try {
      await apiFetch(`/api/v1/ingestion/mappings/${id}`, { method: 'DELETE' });
      loadMappings();
    } catch (e) {
      alert('Failed to delete: ' + e.message);
    }
  };

  const handleToggleActive = async (m) => {
    try {
      await apiFetch(`/api/v1/ingestion/mappings/${m.id}`, {
        method: 'PUT',
        body: JSON.stringify({ is_active: !m.is_active }),
      });
      loadMappings();
    } catch (e) {
      alert('Failed to update: ' + e.message);
    }
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex items-center gap-3 flex-wrap">
        <Select value={kpiFilter} onValueChange={setKpiFilter}>
          <SelectTrigger className="w-56 h-8 bg-[#0d1424] border-white/[0.06] text-xs text-white/60">
            <SelectValue placeholder="Filter by KPI" />
          </SelectTrigger>
          <SelectContent className="bg-[#0d1424] border-white/[0.06] max-h-64">
            <SelectItem value="__all__" className="text-xs text-white/60">All KPIs</SelectItem>
            {kpis.map(k => (
              <SelectItem key={k.id} value={k.id} className="text-xs text-white/60">{k.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Select value={sourceFilter} onValueChange={setSourceFilter}>
          <SelectTrigger className="w-56 h-8 bg-[#0d1424] border-white/[0.06] text-xs text-white/60">
            <SelectValue placeholder="Filter by source" />
          </SelectTrigger>
          <SelectContent className="bg-[#0d1424] border-white/[0.06] max-h-64">
            <SelectItem value="__all__" className="text-xs text-white/60">All Sources</SelectItem>
            {sources.map(s => (
              <SelectItem key={s.id} value={s.id} className="text-xs text-white/60">{s.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex-1" />
        <Badge variant="outline" className="text-[10px] text-white/40 border-white/10">
          {mappings.length} mapping{mappings.length !== 1 ? 's' : ''}
        </Badge>
        <Button
          size="sm"
          className="h-8 text-xs bg-cyan-600 hover:bg-cyan-500 text-white gap-1"
          onClick={() => setShowCreate(true)}
        >
          <Plus className="h-3.5 w-3.5" /> New Mapping
        </Button>
      </div>

      {/* Create form */}
      {showCreate && (
        <CreateMappingForm
          kpis={kpis}
          sources={sources}
          preselectedKpiId={kpiFilter !== '__all__' ? kpiFilter : null}
          onCreated={() => { setShowCreate(false); loadMappings(); }}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Mappings table */}
      {loading ? <LoadingState label="Loading mappings..." /> : (
        <div className="border border-white/[0.06] rounded-lg overflow-hidden">
          <table className="w-full text-xs">
            <thead>
              <tr className="bg-[#0a1020] text-white/40">
                <th className="text-left px-3 py-2 font-medium">KPI</th>
                <th className="text-left px-3 py-2 font-medium">Source</th>
                <th className="text-left px-3 py-2 font-medium">Field</th>
                <th className="text-center px-3 py-2 font-medium w-16">Priority</th>
                <th className="text-center px-3 py-2 font-medium w-20">Confidence</th>
                <th className="text-left px-3 py-2 font-medium w-32">Transform</th>
                <th className="text-center px-3 py-2 font-medium w-16">Active</th>
                <th className="text-right px-3 py-2 font-medium w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {mappings.map(m => (
                <tr key={m.id} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-3 py-2">
                    <p className="text-white/80">{m.kpi_name}</p>
                    <p className="text-[10px] text-white/25">{m.kpi_category}</p>
                  </td>
                  <td className="px-3 py-2 text-white/60">{m.source_name}</td>
                  <td className="px-3 py-2 text-white/50 font-mono text-[10px]">{m.source_field_name || '--'}</td>
                  <td className="px-3 py-2 text-center text-white/50">{m.priority_order ?? '--'}</td>
                  <td className="px-3 py-2 text-center">
                    <ConfidenceBadge score={m.confidence_score} />
                  </td>
                  <td className="px-3 py-2 text-white/30 font-mono text-[10px] truncate max-w-[120px]">{m.transform_formula || 'direct'}</td>
                  <td className="px-3 py-2 text-center">
                    <button onClick={() => handleToggleActive(m)} className="inline-flex">
                      {m.is_active
                        ? <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400" />
                        : <Circle className="h-3.5 w-3.5 text-white/20" />}
                    </button>
                  </td>
                  <td className="px-3 py-2 text-right">
                    <button
                      onClick={() => handleDelete(m.id)}
                      className="text-red-400/60 hover:text-red-400 transition-colors"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {mappings.length === 0 && (
            <div className="py-8 text-center text-white/20 text-sm">
              <Link2 className="h-6 w-6 mx-auto mb-2 opacity-30" />
              <p>No mappings yet. Click "New Mapping" to start linking data sources to KPIs.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}


// ── Create Mapping Form ──────────────────────────────────────────────────────
function CreateMappingForm({ kpis, sources, preselectedKpiId, onCreated, onCancel }) {
  const [kpiId, setKpiId] = useState(preselectedKpiId || '');
  const [sourceId, setSourceId] = useState('');
  const [fields, setFields] = useState([]);
  const [fieldId, setFieldId] = useState('');
  const [priority, setPriority] = useState('1');
  const [confidence, setConfidence] = useState('');
  const [transform, setTransform] = useState('');
  const [unitFrom, setUnitFrom] = useState('');
  const [unitTo, setUnitTo] = useState('');
  const [note, setNote] = useState('');
  const [saving, setSaving] = useState(false);

  // Load fields when source changes
  useEffect(() => {
    if (!sourceId) { setFields([]); return; }
    apiFetch(`/api/v1/ingestion/source-fields?source_id=${sourceId}&limit=500`)
      .then(d => setFields(d.fields || []))
      .catch(() => setFields([]));
  }, [sourceId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!kpiId || !sourceId) return;
    setSaving(true);
    try {
      await apiFetch('/api/v1/ingestion/mappings', {
        method: 'POST',
        body: JSON.stringify({
          kpi_id: kpiId,
          source_id: sourceId,
          source_field_id: fieldId || null,
          priority_order: parseInt(priority) || 1,
          confidence_score: confidence ? parseFloat(confidence) : null,
          transform_formula: transform || null,
          unit_from: unitFrom || null,
          unit_to: unitTo || null,
          change_note: note || null,
        }),
      });
      onCreated();
    } catch (e) {
      alert('Failed to create mapping: ' + e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card className="bg-[#0d1424] border-cyan-500/20">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm text-white/80 flex items-center gap-2">
          <Plus className="h-4 w-4 text-cyan-400" /> Create New Mapping
        </CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            {/* KPI */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Application KPI *</label>
              <Select value={kpiId} onValueChange={setKpiId}>
                <SelectTrigger className="h-8 bg-[#0a1020] border-white/[0.06] text-xs text-white/60">
                  <SelectValue placeholder="Select KPI..." />
                </SelectTrigger>
                <SelectContent className="bg-[#0d1424] border-white/[0.06] max-h-64">
                  {kpis.map(k => (
                    <SelectItem key={k.id} value={k.id} className="text-xs text-white/60">{k.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* Source */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Data Source *</label>
              <Select value={sourceId} onValueChange={v => { setSourceId(v); setFieldId(''); }}>
                <SelectTrigger className="h-8 bg-[#0a1020] border-white/[0.06] text-xs text-white/60">
                  <SelectValue placeholder="Select source..." />
                </SelectTrigger>
                <SelectContent className="bg-[#0d1424] border-white/[0.06] max-h-64">
                  {sources.map(s => (
                    <SelectItem key={s.id} value={s.id} className="text-xs text-white/60">{s.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* Source field */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Source Field</label>
              <Select value={fieldId} onValueChange={setFieldId}>
                <SelectTrigger className="h-8 bg-[#0a1020] border-white/[0.06] text-xs text-white/60">
                  <SelectValue placeholder={fields.length ? 'Select field...' : 'No fields catalogued'} />
                </SelectTrigger>
                <SelectContent className="bg-[#0d1424] border-white/[0.06] max-h-64">
                  {fields.map(f => (
                    <SelectItem key={f.id} value={f.id} className="text-xs text-white/60">
                      {f.field_name} {f.data_type ? `(${f.data_type})` : ''}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            {/* Priority */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Priority Order</label>
              <input
                value={priority}
                onChange={e => setPriority(e.target.value)}
                type="number"
                min="1"
                className="w-full h-8 px-2 bg-[#0a1020] border border-white/[0.06] rounded text-xs text-white/80 focus:outline-none focus:border-cyan-500/30"
              />
            </div>
            {/* Transform */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Transform Formula</label>
              <input
                value={transform}
                onChange={e => setTransform(e.target.value)}
                placeholder="e.g. value * 1000, log(value)"
                className="w-full h-8 px-2 bg-[#0a1020] border border-white/[0.06] rounded text-xs text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30 font-mono"
              />
            </div>
            {/* Confidence */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Confidence (0-1)</label>
              <input
                value={confidence}
                onChange={e => setConfidence(e.target.value)}
                type="number"
                min="0"
                max="1"
                step="0.05"
                placeholder="0.85"
                className="w-full h-8 px-2 bg-[#0a1020] border border-white/[0.06] rounded text-xs text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
              />
            </div>
            {/* Unit from/to */}
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Unit From</label>
              <input
                value={unitFrom}
                onChange={e => setUnitFrom(e.target.value)}
                placeholder="e.g. tCO2"
                className="w-full h-8 px-2 bg-[#0a1020] border border-white/[0.06] rounded text-xs text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
              />
            </div>
            <div>
              <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Unit To</label>
              <input
                value={unitTo}
                onChange={e => setUnitTo(e.target.value)}
                placeholder="e.g. ktCO2e"
                className="w-full h-8 px-2 bg-[#0a1020] border border-white/[0.06] rounded text-xs text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
              />
            </div>
          </div>
          {/* Note */}
          <div>
            <label className="text-[10px] text-white/40 uppercase tracking-wider block mb-1">Change Note</label>
            <input
              value={note}
              onChange={e => setNote(e.target.value)}
              placeholder="Reason for this mapping..."
              className="w-full h-8 px-2 bg-[#0a1020] border border-white/[0.06] rounded text-xs text-white/80 placeholder:text-white/20 focus:outline-none focus:border-cyan-500/30"
            />
          </div>
          {/* Actions */}
          <div className="flex items-center gap-2 pt-1">
            <Button type="submit" size="sm" className="h-7 text-xs bg-cyan-600 hover:bg-cyan-500 text-white gap-1" disabled={!kpiId || !sourceId || saving}>
              {saving ? <RefreshCw className="h-3 w-3 animate-spin" /> : <Check className="h-3 w-3" />}
              {saving ? 'Saving...' : 'Create Mapping'}
            </Button>
            <Button type="button" variant="ghost" size="sm" className="h-7 text-xs text-white/40 hover:text-white/60" onClick={onCancel}>
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}


// ── Shared components ────────────────────────────────────────────────────────
function StatCard({ label, value, icon: Icon, accent }) {
  const colors = {
    cyan: 'text-cyan-400',
    violet: 'text-violet-400',
    emerald: 'text-emerald-400',
  };
  return (
    <Card className="bg-[#0d1424] border-white/[0.06]">
      <CardContent className="p-4 flex items-center gap-3">
        <div className="p-2 rounded bg-white/5">
          <Icon className={cn('h-4 w-4', colors[accent] || 'text-white/40')} />
        </div>
        <div>
          <p className="text-[10px] text-white/30 uppercase tracking-wider">{label}</p>
          <p className={cn('text-xl font-semibold', colors[accent] || 'text-white/80')}>{value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function LoadingState({ label }) {
  return (
    <div className="flex items-center justify-center py-12 text-white/30 text-sm gap-2">
      <RefreshCw className="h-4 w-4 animate-spin" />
      {label}
    </div>
  );
}

function EmptyState({ label }) {
  return (
    <div className="flex items-center justify-center py-8 text-white/20 text-sm">
      {label}
    </div>
  );
}


// ══════════════════════════════════════════════════════════════════════════════
//  MAIN PAGE
// ══════════════════════════════════════════════════════════════════════════════
export default function DataMappingPage() {
  const [activeTab, setActiveTab] = useState('coverage');
  const [selectedKpi, setSelectedKpi] = useState(null);

  const handleSelectKpi = useCallback((kpi) => {
    setSelectedKpi(kpi);
    setActiveTab('editor');
  }, []);

  return (
    <div className="p-4 space-y-4 max-w-[1600px] mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-lg font-semibold text-white/90">Data Mapping</h1>
          <p className="text-xs text-white/40 mt-0.5">
            Map external data source fields to application KPIs and platform modules
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="outline" className="text-[10px] text-cyan-400/60 border-cyan-400/15 gap-1">
            <Database className="h-3 w-3" /> 103 Sources
          </Badge>
          <Badge variant="outline" className="text-[10px] text-violet-400/60 border-violet-400/15 gap-1">
            <Target className="h-3 w-3" /> 51 KPIs
          </Badge>
        </div>
      </div>

      <Separator className="bg-white/[0.06]" />

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-[#0a1020] border border-white/[0.06]">
          <TabsTrigger value="coverage" className="text-xs data-[state=active]:bg-white/5 data-[state=active]:text-cyan-300 text-white/40 gap-1.5">
            <Layers className="h-3.5 w-3.5" /> Module Coverage
          </TabsTrigger>
          <TabsTrigger value="kpis" className="text-xs data-[state=active]:bg-white/5 data-[state=active]:text-cyan-300 text-white/40 gap-1.5">
            <Target className="h-3.5 w-3.5" /> KPI Catalog
          </TabsTrigger>
          <TabsTrigger value="sources" className="text-xs data-[state=active]:bg-white/5 data-[state=active]:text-cyan-300 text-white/40 gap-1.5">
            <Database className="h-3.5 w-3.5" /> Source Browser
          </TabsTrigger>
          <TabsTrigger value="editor" className="text-xs data-[state=active]:bg-white/5 data-[state=active]:text-cyan-300 text-white/40 gap-1.5">
            <Link2 className="h-3.5 w-3.5" /> Mapping Editor
          </TabsTrigger>
        </TabsList>

        <TabsContent value="coverage" className="mt-4">
          <ModuleCoverageTab />
        </TabsContent>

        <TabsContent value="kpis" className="mt-4">
          <KpiCatalogTab onSelectKpi={handleSelectKpi} />
        </TabsContent>

        <TabsContent value="sources" className="mt-4">
          <SourceBrowserTab />
        </TabsContent>

        <TabsContent value="editor" className="mt-4">
          <MappingEditorTab preselectedKpi={selectedKpi} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
