/**
 * DCM Calculator Page
 * Complete carbon credit methodology engine — CDM / VCS / Gold Standard /
 * Nature-based Solutions / CDR / Article 6.4 / CORSIA
 *
 * All 60+ methodologies with real calculation formulas, side-by-side
 * comparison, batch calculation, CDR pathway comparison, and Art 6 guidance.
 */

import React, { useState, useEffect, useMemo } from 'react';
import { usePersonaDefaults } from '../../../context/PersonaContext';
import axios from 'axios';
import {
  Leaf, Calculator, Search, Filter, ArrowRight, RefreshCw,
  ChevronDown, ChevronRight, BarChart3, GitCompare, BookOpen,
  TreePine, Factory, Droplets, Plane, Zap, Wheat, Building,
  FlaskConical, Globe, Info, AlertCircle, CheckCircle2, Download,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend, RadarChart, PolarGrid,
  PolarAngleAxis, Radar,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

// ── Colour palette ─────────────────────────────────────────────────────────────
const SECTOR_COLOURS = {
  'Energy':       '#3b82f6',
  'Waste':        '#f59e0b',
  'Forestry':     '#10b981',
  'Agriculture':  '#84cc16',
  'Industry':     '#8b5cf6',
  'Transport':    '#06b6d4',
  'Buildings':    '#f97316',
  'Household':    '#ec4899',
  'Mining':       '#6b7280',
  'Blue Carbon':  '#0284c7',
  'Land Use':     '#65a30d',
  'CDR':          '#e11d48',
  'Cross-Sector': '#94a3b8',
};

const STANDARD_COLOURS = {
  'CDM':            '#164E8A',
  'VCS':            '#059669',
  'Gold Standard':  '#d97706',
  'Article 6.4 / ISO 14064': '#7c3aed',
  'UNFCCC Art 6.4': '#7c3aed',
  'Verra/IC-VCM':   '#059669',
  'ISO 14064 / NOAA': '#0284c7',
  'Puro.earth / Verra': '#059669',
  'ICAO CORSIA':    '#374151',
};

const SECTOR_ICONS = {
  'Energy':       <Zap className="w-4 h-4" />,
  'Waste':        <AlertCircle className="w-4 h-4" />,
  'Forestry':     <TreePine className="w-4 h-4" />,
  'Agriculture':  <Wheat className="w-4 h-4" />,
  'Industry':     <Factory className="w-4 h-4" />,
  'Transport':    <Plane className="w-4 h-4" />,
  'Buildings':    <Building className="w-4 h-4" />,
  'Household':    <Leaf className="w-4 h-4" />,
  'Mining':       <BarChart3 className="w-4 h-4" />,
  'Blue Carbon':  <Droplets className="w-4 h-4" />,
  'Land Use':     <Globe className="w-4 h-4" />,
  'CDR':          <FlaskConical className="w-4 h-4" />,
  'Cross-Sector': <Globe className="w-4 h-4" />,
};

// ── Helpers ────────────────────────────────────────────────────────────────────
function fmt(v, dec = 0) {
  if (v == null) return '—';
  return Number(v).toLocaleString('en-US', { minimumFractionDigits: dec, maximumFractionDigits: dec });
}

function stdBadge(standard) {
  const bg = STANDARD_COLOURS[standard] || '#6b7280';
  return (
    <span className="text-[10px] font-bold px-1.5 py-0.5 rounded text-white"
      style={{ background: bg }}>
      {standard}
    </span>
  );
}

// ── Methodology catalogue card ─────────────────────────────────────────────────
function MethodologyCard({ method, isSelected, onSelect }) {
  const colour = SECTOR_COLOURS[method.sector] || '#6b7280';
  return (
    <button
      onClick={() => onSelect(method.code)}
      className={`w-full text-left p-3 rounded-xl border transition-all ${
        isSelected
          ? 'border-blue-500 bg-blue-50 shadow-sm'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="text-sm" style={{ color: colour }}>
            {SECTOR_ICONS[method.sector]}
          </span>
          <div className="min-w-0">
            <p className="text-xs font-bold text-gray-700 font-mono truncate">{method.code}</p>
            <p className="text-xs text-gray-600 truncate">{method.name}</p>
          </div>
        </div>
        <div className="flex-shrink-0">{stdBadge(method.standard)}</div>
      </div>
      <p className="text-[10px] text-gray-400 mt-1">{method.sector} · {method.project_type}</p>
    </button>
  );
}

// ── Result card ─────────────────────────────────────────────────────────────────
function ResultCard({ result }) {
  if (!result) return null;
  const kpis = [
    { label: 'Baseline Emissions', value: fmt(result.baseline_emissions), unit: 'tCO₂e', colour: '#ef4444' },
    { label: 'Project Emissions',  value: fmt(result.project_emissions),  unit: 'tCO₂e', colour: '#f59e0b' },
    { label: 'Leakage',            value: fmt(result.leakage),            unit: 'tCO₂e', colour: '#f97316' },
    { label: 'ER (Reductions)',     value: fmt(result.emission_reductions), unit: 'tCO₂e', colour: '#3b82f6' },
    { label: 'Removals',           value: fmt(result.emission_removals),  unit: 'tCO₂e', colour: '#8b5cf6' },
    { label: 'Net Climate Benefit',value: fmt(result.net_climate_benefit), unit: 'tCO₂e', colour: '#10b981' },
  ];

  const chartData = [
    { name: 'Baseline', value: result.baseline_emissions, fill: '#ef4444' },
    { name: 'Project', value: result.project_emissions, fill: '#f59e0b' },
    { name: 'Leakage', value: result.leakage, fill: '#f97316' },
    { name: 'Reductions', value: result.emission_reductions, fill: '#3b82f6' },
    { name: 'Removals', value: result.emission_removals, fill: '#8b5cf6' },
    { name: 'Net Benefit', value: result.net_climate_benefit, fill: '#10b981' },
  ].filter(d => d.value > 0);

  return (
    <div className="space-y-4">
      {/* KPI strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {kpis.map(k => (
          <div key={k.label} className="rounded-xl border border-gray-200 bg-white px-3 py-2.5">
            <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{k.label}</p>
            <p className="text-base font-bold font-mono tabular-nums" style={{ color: k.colour }}>
              {k.value}
            </p>
            <p className="text-[10px] text-gray-400">{k.unit}</p>
          </div>
        ))}
      </div>

      {/* Bar chart */}
      {chartData.length > 0 && (
        <div className="rounded-xl border border-gray-200 bg-white p-4">
          <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">
            Emissions Waterfall (tCO₂e)
          </p>
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 10 }} axisLine={false} tickLine={false} width={60}
                tickFormatter={v => fmt(v)} />
              <Tooltip
                formatter={(v, n) => [fmt(v) + ' tCO₂e', n]}
                contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 11 }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {chartData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Monitoring & Additionality */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        <div className="rounded-xl border border-gray-200 bg-white p-3">
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            Monitoring Notes
          </p>
          <p className="text-xs text-gray-600">{result.monitoring_notes}</p>
        </div>
        <div className="rounded-xl border border-gray-200 bg-white p-3">
          <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-wider mb-1.5">
            Additionality
          </p>
          <p className="text-xs text-gray-600">{result.additionality_notes}</p>
        </div>
      </div>
    </div>
  );
}

// ── CDR Pathways Tab ─────────────────────────────────────────────────────────
function CDRPathwaysTab() {
  const [pathways, setPathways] = useState([]);
  const [loading, setLoading] = useState(true);
  const [results, setResults] = useState({});

  useEffect(() => {
    axios.get('/api/v1/dcm/ref/cdr-pathways')
      .then(r => setPathways(r.data))
      .catch(() => setPathways([]))
      .finally(() => setLoading(false));
  }, []);

  async function runPathway(code) {
    try {
      const r = await axios.post('/api/v1/dcm/calculate', { methodology_code: code, inputs: {} });
      setResults(p => ({ ...p, [code]: r.data }));
    } catch (_) {}
  }

  if (loading) return <div className="flex justify-center py-12"><RefreshCw className="w-5 h-5 animate-spin text-gray-400" /></div>;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4">
        <p className="text-sm font-semibold text-emerald-700 mb-1 flex items-center gap-2">
          <FlaskConical className="w-4 h-4" /> Carbon Dioxide Removal (CDR) Pathways
        </p>
        <p className="text-xs text-emerald-600">
          CDR pathways permanently remove CO₂ from the atmosphere. Unlike avoided emissions,
          CDR credits contribute to net negative emissions. The table below compares cost,
          permanence, and co-benefits across five engineered CDR pathways.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {pathways.map(p => (
          <div key={p.code} className="rounded-xl border border-gray-200 bg-white p-4">
            <div className="flex items-start justify-between mb-3">
              <div>
                <p className="text-sm font-bold text-gray-800">{p.pathway}</p>
                <p className="text-[10px] font-mono text-gray-400">{p.code}</p>
              </div>
              <span className="text-[10px] font-semibold bg-red-50 text-red-600 border border-red-200 px-2 py-0.5 rounded-full">
                CDR
              </span>
            </div>
            <div className="space-y-1.5 text-xs text-gray-600 mb-3">
              <div className="flex justify-between">
                <span className="text-gray-400">Current Cost</span>
                <span className="font-semibold">${p.current_cost_usd_per_t}/t</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">2030 Projection</span>
                <span className="font-semibold">${p['2030_cost_projection_usd_per_t']}/t</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Permanence</span>
                <span className="font-semibold text-emerald-600">{p.permanence}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Co-Benefits</span>
                <span className="italic">{p.co_benefits}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-400">Readiness</span>
                <span>{p.readiness}</span>
              </div>
            </div>
            <button
              onClick={() => runPathway(p.code)}
              className="w-full text-xs font-medium py-1.5 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-all flex items-center justify-center gap-1.5"
            >
              <Calculator className="w-3 h-3" /> Run Sample Calculation
            </button>
            {results[p.code] && (
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-[10px] text-gray-400">Removal</p>
                  <p className="text-sm font-bold text-purple-600">
                    {fmt(results[p.code].emission_removals)} t
                  </p>
                </div>
                <div className="bg-gray-50 rounded-lg p-2 text-center">
                  <p className="text-[10px] text-gray-400">Net Benefit</p>
                  <p className="text-sm font-bold text-emerald-600">
                    {fmt(results[p.code].net_climate_benefit)} t
                  </p>
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Article 6 Guidance Tab ──────────────────────────────────────────────────
function Article6Tab() {
  const [guidance, setGuidance] = useState(null);

  useEffect(() => {
    axios.get('/api/v1/dcm/ref/article6-guidance')
      .then(r => setGuidance(r.data))
      .catch(() => setGuidance({}));
  }, []);

  if (!guidance) return <div className="flex justify-center py-12"><RefreshCw className="w-5 h-5 animate-spin text-gray-400" /></div>;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-blue-200 bg-blue-50 p-4">
        <p className="text-sm font-semibold text-blue-700 mb-1 flex items-center gap-2">
          <Globe className="w-4 h-4" /> Paris Agreement Article 6 — Guidance
        </p>
        <p className="text-xs text-blue-600">
          Article 6 of the Paris Agreement enables countries to cooperate on mitigation
          via internationally transferred mitigation outcomes (ITMOs). Article 6.4
          establishes the new UN-supervised crediting mechanism replacing CDM.
        </p>
      </div>

      {Object.entries(guidance).map(([key, val]) => (
        <div key={key} className="rounded-xl border border-gray-200 bg-white p-4">
          <p className="text-sm font-bold text-gray-800 mb-3 capitalize">
            {key.replace(/_/g, ' ')}
          </p>
          {typeof val === 'object' && !Array.isArray(val) ? (
            <div className="space-y-2">
              {Object.entries(val).map(([k, v]) => (
                <div key={k} className="text-xs">
                  <span className="font-semibold text-gray-700 capitalize">{k.replace(/_/g, ' ')}: </span>
                  {Array.isArray(v) ? (
                    <ul className="mt-1 space-y-0.5 text-gray-600">
                      {v.map((item, i) => <li key={i} className="ml-3">• {item}</li>)}
                    </ul>
                  ) : (
                    <span className="text-gray-600">{v}</span>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-gray-600">{String(val)}</p>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Compare Tab ─────────────────────────────────────────────────────────────────
function CompareTab({ methodologies }) {
  const [codeA, setCodeA] = useState('VM0007');
  const [codeB, setCodeB] = useState('CDR-DACCS');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  async function runCompare() {
    setLoading(true);
    setError(null);
    try {
      const r = await axios.post('/api/v1/dcm/compare', {
        methodology_a: codeA,
        methodology_b: codeB,
        inputs_a: {},
        inputs_b: {},
      });
      setResult(r.data);
    } catch (e) {
      setError(e?.response?.data?.detail || 'Comparison failed');
    } finally {
      setLoading(false);
    }
  }

  const codes = methodologies.map(m => m.code);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-semibold text-gray-600 mb-1.5 block">Methodology A</label>
          <select value={codeA} onChange={e => setCodeA(e.target.value)}
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-200">
            {codes.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <div>
          <label className="text-xs font-semibold text-gray-600 mb-1.5 block">Methodology B</label>
          <select value={codeB} onChange={e => setCodeB(e.target.value)}
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-blue-200">
            {codes.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      <button onClick={runCompare} disabled={loading}
        className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-all disabled:opacity-60"
        style={{ background: '#164E8A' }}>
        {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <GitCompare className="w-4 h-4" />}
        {loading ? 'Comparing…' : 'Compare Methodologies'}
      </button>

      {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="space-y-4">
          {/* Comparison summary */}
          <div className="rounded-xl border border-gray-200 bg-white p-4">
            <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-3">Comparison Summary</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                { label: 'NCB Delta (A-B)', value: fmt(result.comparison.net_climate_benefit_delta_tco2e), colour: '#164E8A' },
                { label: 'ER Delta (A-B)',  value: fmt(result.comparison.emission_reductions_delta_tco2e), colour: '#3b82f6' },
                { label: 'Removal Delta',   value: fmt(result.comparison.removal_delta_tco2e), colour: '#8b5cf6' },
                { label: 'Preferred',       value: result.comparison.preferred_by_ncb, colour: '#10b981' },
              ].map(k => (
                <div key={k.label} className="rounded-xl bg-gray-50 border border-gray-200 p-3">
                  <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{k.label}</p>
                  <p className="text-sm font-bold font-mono" style={{ color: k.colour }}>{k.value}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {[
              { title: `Methodology A: ${codeA}`, data: result.methodology_a, colour: '#164E8A' },
              { title: `Methodology B: ${codeB}`, data: result.methodology_b, colour: '#059669' },
            ].map(({ title, data, colour }) => (
              <div key={title} className="rounded-xl border-2 bg-white p-4" style={{ borderColor: colour + '33' }}>
                <p className="text-xs font-bold mb-3 pb-2 border-b border-gray-100" style={{ color: colour }}>
                  {title}
                </p>
                <div className="space-y-1.5">
                  {[
                    ['Baseline', data.baseline_emissions],
                    ['Project', data.project_emissions],
                    ['Leakage', data.leakage],
                    ['Reductions', data.emission_reductions],
                    ['Removals', data.emission_removals],
                    ['Net Benefit', data.net_climate_benefit],
                  ].map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs">
                      <span className="text-gray-500">{k}</span>
                      <span className="font-mono font-semibold text-gray-800">{fmt(v)} tCO₂e</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}


// ── Main Page ──────────────────────────────────────────────────────────────────
export default function DCMCalculatorPage() {
  const d = usePersonaDefaults('dcm');
  const [tab, setTab] = useState('calculator');
  const [methodologies, setMethodologies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCode, setSelectedCode] = useState(d.methodologyCode || 'VM0007');
  const [searchQuery, setSearchQuery] = useState('');
  const [filterSector, setFilterSector] = useState(d.sector || '');
  const [filterStandard, setFilterStandard] = useState('');
  const [calcResult, setCalcResult] = useState(null);
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcError, setCalcError] = useState(null);

  /* Re-seed when persona switches */
  useEffect(() => {
    if (d.methodologyCode) setSelectedCode(d.methodologyCode);
    if (d.sector !== undefined) setFilterSector(d.sector || '');
    setCalcResult(null);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [d.methodologyCode]);

  useEffect(() => {
    axios.get('/api/v1/dcm/methodologies')
      .then(r => { setMethodologies(r.data); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const sectors = useMemo(() => [...new Set(methodologies.map(m => m.sector))].sort(), [methodologies]);
  const standards = useMemo(() => [...new Set(methodologies.map(m => m.standard))].sort(), [methodologies]);

  const filtered = useMemo(() => methodologies.filter(m => {
    if (filterSector && m.sector !== filterSector) return false;
    if (filterStandard && m.standard !== filterStandard) return false;
    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      return m.code.toLowerCase().includes(q) || m.name.toLowerCase().includes(q)
        || m.sector.toLowerCase().includes(q) || m.project_type.toLowerCase().includes(q);
    }
    return true;
  }), [methodologies, filterSector, filterStandard, searchQuery]);

  const selectedMethod = methodologies.find(m => m.code === selectedCode);

  async function runCalc() {
    if (!selectedCode) return;
    setCalcLoading(true);
    setCalcError(null);
    setCalcResult(null);
    try {
      const r = await axios.post('/api/v1/dcm/calculate', { methodology_code: selectedCode, inputs: {} });
      setCalcResult(r.data);
    } catch (e) {
      setCalcError(e?.response?.data?.detail || 'Calculation failed');
    } finally {
      setCalcLoading(false);
    }
  }

  // Sector distribution for chart
  const sectorDist = useMemo(() => {
    const counts = {};
    methodologies.forEach(m => { counts[m.sector] = (counts[m.sector] || 0) + 1; });
    return Object.entries(counts).map(([sector, count]) => ({
      sector, count, fill: SECTOR_COLOURS[sector] || '#6b7280',
    })).sort((a, b) => b.count - a.count);
  }, [methodologies]);

  const TABS = [
    { id: 'calculator', label: 'Calculator', icon: <Calculator className="w-4 h-4" /> },
    { id: 'compare',    label: 'Compare',    icon: <GitCompare className="w-4 h-4" /> },
    { id: 'cdr',        label: 'CDR Pathways', icon: <FlaskConical className="w-4 h-4" /> },
    { id: 'article6',  label: 'Article 6',  icon: <Globe className="w-4 h-4" /> },
    { id: 'overview',  label: 'Overview',   icon: <BarChart3 className="w-4 h-4" /> },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <DemoBanner message="DCM calculations use representative default inputs. Provide project-specific parameters via API or input forms for actual credit estimates." />

      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-2 bg-emerald-50 rounded-lg">
            <Leaf className="w-6 h-6 text-emerald-600" />
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">Carbon Credit DCM Engine</h1>
            <p className="text-sm text-gray-500">
              {methodologies.length}+ methodologies · CDM · VCS · Gold Standard · CDR · Article 6.4 · CORSIA
            </p>
          </div>
        </div>

        {/* KPI strip */}
        <div className="flex flex-wrap gap-3 mt-2">
          {[
            { label: 'Total Methodologies', value: methodologies.length, colour: '#164E8A' },
            { label: 'Sectors Covered',     value: sectors.length, colour: '#059669' },
            { label: 'Standards',           value: standards.length, colour: '#7c3aed' },
            { label: 'CDR Pathways',        value: 5, colour: '#e11d48' },
          ].map(k => (
            <div key={k.label} className="flex items-center gap-2 rounded-lg border border-gray-200 bg-gray-50 px-3 py-1.5">
              <span className="text-lg font-bold font-mono" style={{ color: k.colour }}>{k.value}</span>
              <span className="text-xs text-gray-500">{k.label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Tab bar */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-0">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex items-center gap-1.5 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                tab === t.id
                  ? 'border-emerald-500 text-emerald-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6">
        {/* ── Calculator Tab ── */}
        {tab === 'calculator' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: catalogue */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100">
                  <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-2">
                    Methodology Catalogue
                  </p>
                  {/* Search */}
                  <div className="relative mb-2">
                    <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-gray-400" />
                    <input
                      type="text"
                      placeholder="Search…"
                      value={searchQuery}
                      onChange={e => setSearchQuery(e.target.value)}
                      className="w-full pl-7 pr-3 py-1.5 text-xs rounded-lg border border-gray-200 focus:outline-none focus:ring-2 focus:ring-blue-200"
                    />
                  </div>
                  {/* Filters */}
                  <div className="grid grid-cols-2 gap-2">
                    <select value={filterSector} onChange={e => setFilterSector(e.target.value)}
                      className="text-xs rounded border border-gray-200 px-2 py-1 text-gray-600 focus:outline-none">
                      <option value="">All Sectors</option>
                      {sectors.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                    <select value={filterStandard} onChange={e => setFilterStandard(e.target.value)}
                      className="text-xs rounded border border-gray-200 px-2 py-1 text-gray-600 focus:outline-none">
                      <option value="">All Standards</option>
                      {standards.map(s => <option key={s} value={s}>{s.replace('Gold Standard', 'GS').replace('Article 6.4 / ISO 14064', 'Art 6.4').replace('UNFCCC Art 6.4', 'Art 6.4')}</option>)}
                    </select>
                  </div>
                  <p className="text-[10px] text-gray-400 mt-1.5">{filtered.length} methodology{filtered.length !== 1 ? 's' : ''}</p>
                </div>
                <div className="overflow-y-auto max-h-[calc(100vh-440px)] p-2 space-y-1.5">
                  {loading ? (
                    Array(8).fill(0).map((_, i) => (
                      <div key={i} className="h-14 rounded-xl bg-gray-100 animate-pulse" />
                    ))
                  ) : filtered.map(m => (
                    <MethodologyCard
                      key={m.code}
                      method={m}
                      isSelected={selectedCode === m.code}
                      onSelect={code => { setSelectedCode(code); setCalcResult(null); }}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Right: calculator */}
            <div className="lg:col-span-2 space-y-4">
              {/* Selected methodology info */}
              {selectedMethod && (
                <div className="bg-white rounded-xl border border-gray-200 p-4">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-bold font-mono text-gray-800">{selectedMethod.code}</span>
                        {stdBadge(selectedMethod.standard)}
                      </div>
                      <p className="text-base font-bold text-gray-900">{selectedMethod.name}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {selectedMethod.sector} · {selectedMethod.project_type}
                      </p>
                    </div>
                    <button
                      onClick={runCalc}
                      disabled={calcLoading}
                      className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-white transition-all disabled:opacity-60 flex-shrink-0"
                      style={{ background: '#164E8A' }}
                    >
                      {calcLoading
                        ? <><RefreshCw className="w-4 h-4 animate-spin" /> Calculating…</>
                        : <><Calculator className="w-4 h-4" /> Run Calculation</>
                      }
                    </button>
                  </div>

                  <div className="rounded-lg bg-blue-50 border border-blue-100 px-3 py-2 text-xs text-blue-700">
                    <span className="font-semibold">Default inputs:</span> Calculation runs with representative
                    project parameters. Submit custom values via POST /api/v1/dcm/calculate with an
                    <code className="ml-1 bg-blue-100 px-1 rounded">inputs</code> object.
                  </div>
                </div>
              )}

              {calcError && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-4 flex items-center gap-2 text-sm text-red-700">
                  <AlertCircle className="w-4 h-4 flex-shrink-0" />
                  {calcError}
                </div>
              )}

              {calcResult ? (
                <ResultCard result={calcResult} />
              ) : !calcLoading && (
                <div className="flex flex-col items-center justify-center py-16 text-center text-gray-400">
                  <Calculator className="w-10 h-10 mb-3" />
                  <p className="text-sm font-medium">Select a methodology and click Run Calculation</p>
                  <p className="text-xs mt-1">
                    {methodologies.length > 0
                      ? `${methodologies.length} methodologies available across ${sectors.length} sectors`
                      : 'Loading methodology catalogue…'}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Compare Tab ── */}
        {tab === 'compare' && <CompareTab methodologies={methodologies} />}

        {/* ── CDR Tab ── */}
        {tab === 'cdr' && <CDRPathwaysTab />}

        {/* ── Article 6 Tab ── */}
        {tab === 'article6' && <Article6Tab />}

        {/* ── Overview Tab ── */}
        {tab === 'overview' && (
          <div className="space-y-6">
            {/* Sector distribution chart */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-4">
                Methodologies by Sector
              </p>
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={sectorDist} layout="vertical" margin={{ top: 0, right: 20, bottom: 0, left: 80 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" horizontal={false} />
                  <XAxis type="number" tick={{ fontSize: 10 }} axisLine={false} tickLine={false} />
                  <YAxis dataKey="sector" type="category" tick={{ fontSize: 11 }} axisLine={false} tickLine={false} width={80} />
                  <Tooltip
                    formatter={v => [`${v} methodologies`, 'Count']}
                    contentStyle={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, fontSize: 11 }}
                  />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {sectorDist.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            {/* Standards breakdown */}
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider mb-4">
                Methodologies by Standard
              </p>
              <div className="flex flex-wrap gap-3">
                {standards.map(std => {
                  const count = methodologies.filter(m => m.standard === std).length;
                  const colour = STANDARD_COLOURS[std] || '#6b7280';
                  return (
                    <div key={std} className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2">
                      <div className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ background: colour }} />
                      <span className="text-xs text-gray-600">{std}</span>
                      <span className="text-xs font-bold font-mono" style={{ color: colour }}>{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Methodology quick-table */}
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <div className="px-4 py-3 border-b border-gray-100">
                <p className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Full Catalogue</p>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-100 bg-gray-50">
                      {['Code', 'Name', 'Sector', 'Standard', 'Project Type', ''].map(h => (
                        <th key={h} className="px-3 py-2 text-left text-[10px] font-semibold text-gray-500 uppercase tracking-wider">
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {methodologies.map((m, i) => (
                      <tr key={m.code} className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${i % 2 === 0 ? '' : 'bg-gray-50/50'}`}>
                        <td className="px-3 py-2 font-mono font-bold text-gray-700">{m.code}</td>
                        <td className="px-3 py-2 text-gray-800 max-w-[200px] truncate">{m.name}</td>
                        <td className="px-3 py-2">
                          <span className="flex items-center gap-1" style={{ color: SECTOR_COLOURS[m.sector] || '#6b7280' }}>
                            {SECTOR_ICONS[m.sector]}
                            <span>{m.sector}</span>
                          </span>
                        </td>
                        <td className="px-3 py-2">{stdBadge(m.standard)}</td>
                        <td className="px-3 py-2 text-gray-500">{m.project_type}</td>
                        <td className="px-3 py-2">
                          <button
                            onClick={() => { setSelectedCode(m.code); setTab('calculator'); }}
                            className="text-blue-500 hover:text-blue-700 font-medium flex items-center gap-0.5"
                          >
                            Run <ArrowRight className="w-3 h-3" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
