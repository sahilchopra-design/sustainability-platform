/**
 * Supply Chain Scope 3 Assessment Page
 * GHG Protocol Scope 3 (15 categories), SBTi trajectory, emission factor lookup
 * Standards: GHG Protocol Scope 3 Standard, SBTi Corporate v2.0, ISO 14064-1
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line, ReferenceLine,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

/* ── GHG Protocol Scope 3 Categories ────────────────────────────────────── */
const SCOPE3_CATEGORIES = [
  { id: 'cat1_purchased_goods', label: 'Cat 1 – Purchased Goods & Services', upstream: true },
  { id: 'cat2_capital_goods', label: 'Cat 2 – Capital Goods', upstream: true },
  { id: 'cat3_fuel_energy', label: 'Cat 3 – Fuel & Energy Activities', upstream: true },
  { id: 'cat4_upstream_transport', label: 'Cat 4 – Upstream Transportation', upstream: true },
  { id: 'cat5_waste_operations', label: 'Cat 5 – Waste in Operations', upstream: true },
  { id: 'cat6_business_travel', label: 'Cat 6 – Business Travel', upstream: true },
  { id: 'cat7_employee_commuting', label: 'Cat 7 – Employee Commuting', upstream: true },
  { id: 'cat8_upstream_leased', label: 'Cat 8 – Upstream Leased Assets', upstream: true },
  { id: 'cat9_downstream_transport', label: 'Cat 9 – Downstream Transportation', upstream: false },
  { id: 'cat10_processing', label: 'Cat 10 – Processing of Sold Products', upstream: false },
  { id: 'cat11_use_of_products', label: 'Cat 11 – Use of Sold Products', upstream: false },
  { id: 'cat12_end_of_life', label: 'Cat 12 – End-of-Life Treatment', upstream: false },
  { id: 'cat13_downstream_leased', label: 'Cat 13 – Downstream Leased Assets', upstream: false },
  { id: 'cat14_franchises', label: 'Cat 14 – Franchises', upstream: false },
  { id: 'cat15_investments', label: 'Cat 15 – Investments', upstream: false },
];

const ACTIVITY_UNITS = [
  'tonne', 'kg', 'kWh', 'MWh', 'GJ', 'litre', 'km', 'tonne-km',
  'GBP_spend', 'USD_spend', 'EUR_spend', 'm2', 'unit', 'passenger-km', 'night',
];

const SBTI_PATHWAYS = [
  { v: '1.5C', l: '1.5°C Absolute Contraction' },
  { v: 'well-below-2C', l: 'Well-Below 2°C' },
  { v: '2C', l: '2°C Sectoral Decarbonisation' },
];

const CAT_COLORS = [
  '#6366f1','#8b5cf6','#a78bfa','#c4b5fd','#ddd6fe',
  '#06b6d4','#0891b2','#0e7490','#155e75','#164e63',
  '#10b981','#059669','#047857','#065f46','#064e3b',
];

/* ── Tiny helpers ─────────────────────────────────────────────────────────── */
function Badge({ label, color = 'bg-white/[0.06] text-white/60' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}

function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] shadow-sm ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.04]">
          {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
          {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatCard({ label, value, unit, sub, color = 'text-white' }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] shadow-sm p-5">
      <p className="text-xs text-white/40 font-medium mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : value}
        {unit && <span className="text-sm font-normal text-white/40 ml-1">{unit}</span>}
      </p>
      {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
    </div>
  );
}

/* ── Activity row inside a category ─────────────────────────────────────── */
function ActivityRow({ activity, onChange, onRemove }) {
  return (
    <div className="grid grid-cols-12 gap-2 items-center py-2 border-b border-white/[0.02] last:border-0">
      <div className="col-span-4">
        <input
          className="w-full text-xs border border-white/[0.06] rounded px-2 py-1.5 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
          placeholder="Activity description"
          value={activity.description || ''}
          onChange={e => onChange({ ...activity, description: e.target.value })}
        />
      </div>
      <div className="col-span-2">
        <input
          type="number" min="0"
          className="w-full text-xs border border-white/[0.06] rounded px-2 py-1.5 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
          placeholder="Quantity"
          value={activity.quantity || ''}
          onChange={e => onChange({ ...activity, quantity: parseFloat(e.target.value) || 0 })}
        />
      </div>
      <div className="col-span-2">
        <select
          className="w-full text-xs border border-white/[0.06] rounded px-2 py-1.5 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
          value={activity.unit || 'tonne'}
          onChange={e => onChange({ ...activity, unit: e.target.value })}
        >
          {ACTIVITY_UNITS.map(u => <option key={u} value={u}>{u}</option>)}
        </select>
      </div>
      <div className="col-span-2">
        <input
          type="number" min="0"
          className="w-full text-xs border border-white/[0.06] rounded px-2 py-1.5 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
          placeholder="EF (kgCO₂e/unit)"
          value={activity.emission_factor_kgco2e_per_unit || ''}
          onChange={e => onChange({ ...activity, emission_factor_kgco2e_per_unit: parseFloat(e.target.value) || null })}
        />
      </div>
      <div className="col-span-1">
        <input
          className="w-full text-xs border border-white/[0.06] rounded px-2 py-1.5 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
          placeholder="ISO2"
          value={activity.supplier_country_iso || ''}
          onChange={e => onChange({ ...activity, supplier_country_iso: e.target.value })}
        />
      </div>
      <div className="col-span-1 text-right">
        <button onClick={onRemove} className="text-red-400 hover:text-red-600 text-xs px-1">✕</button>
      </div>
    </div>
  );
}

/* ── Scope 3 Panel ───────────────────────────────────────────────────────── */
function Scope3Panel() {
  const [entityId, setEntityId] = useState('');
  const [reportingYear, setReportingYear] = useState(2024);
  const [activitiesByCategory, setActivitiesByCategory] = useState({});
  const [includeHotspot, setIncludeHotspot] = useState(true);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [expandedCats, setExpandedCats] = useState({});

  const toggleCat = id => setExpandedCats(prev => ({ ...prev, [id]: !prev[id] }));

  const addActivity = useCallback((catId) => {
    setActivitiesByCategory(prev => ({
      ...prev,
      [catId]: [...(prev[catId] || []), { description: '', quantity: 0, unit: 'tonne', emission_factor_kgco2e_per_unit: null, supplier_country_iso: '' }]
    }));
  }, []);

  const updateActivity = useCallback((catId, idx, updated) => {
    setActivitiesByCategory(prev => {
      const arr = [...(prev[catId] || [])];
      arr[idx] = updated;
      return { ...prev, [catId]: arr };
    });
  }, []);

  const removeActivity = useCallback((catId, idx) => {
    setActivitiesByCategory(prev => {
      const arr = [...(prev[catId] || [])];
      arr.splice(idx, 1);
      return { ...prev, [catId]: arr };
    });
  }, []);

  const handleCalculate = async () => {
    setLoading(true); setError(null); setResult(null);
    // Strip empty categories
    const cleanedActivities = {};
    for (const [cat, acts] of Object.entries(activitiesByCategory)) {
      const valid = acts.filter(a => a.quantity > 0);
      if (valid.length > 0) cleanedActivities[cat] = valid;
    }
    if (Object.keys(cleanedActivities).length === 0) {
      setError('Add at least one activity with a quantity > 0.'); setLoading(false); return;
    }
    try {
      const { data } = await axios.post(`${API}/api/v1/supply-chain/scope3-assessment`, {
        entity_id: entityId || 'entity_001',
        reporting_year: reportingYear,
        activities_by_category: cleanedActivities,
        include_hotspot_analysis: includeHotspot,
      });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const pieData = result?.by_category?.map((c, i) => ({
    name: c.category.replace(/_/g, ' ').replace('cat', 'Cat'),
    value: parseFloat(c.total_tco2e.toFixed(1)),
    color: CAT_COLORS[i % CAT_COLORS.length],
  })) || [];

  return (
    <div className="space-y-6">
      {/* Header & Entity */}
      <div className="flex flex-wrap items-end gap-4">
        <div>
          <label className="block text-xs font-medium text-white/60 mb-1">Entity / Company ID</label>
          <input className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 w-48 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
            value={entityId} onChange={e => setEntityId(e.target.value)} placeholder="company_001" />
        </div>
        <div>
          <label className="block text-xs font-medium text-white/60 mb-1">Reporting Year</label>
          <input type="number" min="2000" max="2100"
            className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 w-32 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
            value={reportingYear} onChange={e => setReportingYear(parseInt(e.target.value))} />
        </div>
        <label className="flex items-center gap-2 text-xs text-white/60 cursor-pointer">
          <input type="checkbox" className="rounded" checked={includeHotspot}
            onChange={e => setIncludeHotspot(e.target.checked)} />
          Include Hotspot Analysis
        </label>
        <div className="flex gap-2 flex-wrap">
          <Badge label="GHG Protocol Scope 3" color="bg-emerald-500/10 text-emerald-700" />
          <Badge label="SBTi Corporate v2.0" color="bg-blue-500/10 text-blue-700" />
          <Badge label="ISO 14064-1" color="bg-white/[0.06] text-white/60" />
        </div>
      </div>

      {/* Categories */}
      <Card title="Scope 3 Activity Data — All 15 Categories" subtitle="Enter activity data per GHG Protocol Scope 3 category. Leave empty to exclude from calculation.">
        {/* Column headers */}
        <div className="grid grid-cols-12 gap-2 text-[10px] font-semibold text-white/30 uppercase tracking-wide mb-2 px-1">
          <div className="col-span-4">Description</div>
          <div className="col-span-2">Quantity</div>
          <div className="col-span-2">Unit</div>
          <div className="col-span-2">EF (kgCO₂e/unit)</div>
          <div className="col-span-1">Country</div>
          <div className="col-span-1" />
        </div>

        <div className="space-y-2">
          {SCOPE3_CATEGORIES.map((cat, ci) => {
            const acts = activitiesByCategory[cat.id] || [];
            const isOpen = expandedCats[cat.id];
            const catTotal = acts.reduce((s, a) => s + (a.quantity || 0) * (a.emission_factor_kgco2e_per_unit || 0) / 1000, 0);
            return (
              <div key={cat.id} className="border border-white/[0.06] rounded-lg overflow-hidden">
                <button
                  className="w-full flex items-center justify-between px-4 py-2.5 bg-white/[0.02] hover:bg-white/[0.06] transition-colors"
                  onClick={() => toggleCat(cat.id)}
                >
                  <div className="flex items-center gap-3">
                    <span className={`w-2 h-2 rounded-full ${cat.upstream ? 'bg-cyan-400/10' : 'bg-teal-400'}`} />
                    <span className="text-xs font-medium text-white/70">{cat.label}</span>
                    <span className="text-[10px] text-white/30">{cat.upstream ? 'Upstream' : 'Downstream'}</span>
                    {acts.length > 0 && (
                      <span className="text-[10px] bg-cyan-400/10 text-cyan-400 px-1.5 py-0.5 rounded font-medium">
                        {acts.length} activities · {catTotal.toFixed(2)} tCO₂e est.
                      </span>
                    )}
                  </div>
                  <span className="text-white/30 text-xs">{isOpen ? '▲' : '▼'}</span>
                </button>

                {isOpen && (
                  <div className="px-4 pb-3 pt-2 bg-[#0d1424]">
                    {acts.map((act, ai) => (
                      <ActivityRow key={ai} activity={act}
                        onChange={u => updateActivity(cat.id, ai, u)}
                        onRemove={() => removeActivity(cat.id, ai)} />
                    ))}
                    <button
                      className="mt-2 text-xs text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1"
                      onClick={() => addActivity(cat.id)}
                    >
                      + Add Activity
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>

      <div className="flex justify-end">
        <button
          onClick={handleCalculate}
          disabled={loading}
          className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors"
        >
          {loading ? 'Calculating…' : 'Calculate Scope 3 Emissions'}
        </button>
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-700">{error}</div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* KPI Row */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Total Scope 3 Emissions" value={result.total_scope3_tco2e} unit="tCO₂e"
              color="text-cyan-300" sub={`${result.reporting_year} reporting year`} />
            <StatCard label="Categories Active" value={result.by_category?.length || 0}
              sub="of 15 GHG Protocol categories" />
            <StatCard label="Data Quality Score" value={`${((result.validation_summary?.data_quality_score || 0) * 100).toFixed(0)}%`}
              color={(result.validation_summary?.data_quality_score || 0) > 0.7 ? 'text-emerald-700' : 'text-amber-600'}
              sub="ISO 14064-1 quality scale" />
            <StatCard label="Hotspots Identified" value={result.hotspots?.length || 0}
              color={result.hotspots?.length > 0 ? 'text-amber-600' : 'text-emerald-700'}
              sub="High-priority reduction targets" />
          </div>

          {/* Charts row */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="Emissions by Category (tCO₂e)">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={result.by_category?.map((c, i) => ({
                  name: c.category.replace(/^cat\d+_/, '').replace(/_/g, ' ').slice(0, 18),
                  tco2e: parseFloat(c.total_tco2e.toFixed(1)),
                  hotspot: c.hotspot_flag,
                  fill: CAT_COLORS[i % CAT_COLORS.length],
                }))}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip formatter={(v) => [`${v.toLocaleString()} tCO₂e`]} />
                  <Bar dataKey="tco2e" name="tCO₂e">
                    {result.by_category?.map((c, i) => (
                      <Cell key={i} fill={c.hotspot_flag ? '#ef4444' : CAT_COLORS[i % CAT_COLORS.length]} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Emissions Share by Category">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={110}
                    label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}>
                    {pieData.map((e, i) => <Cell key={i} fill={e.color} />)}
                  </Pie>
                  <Tooltip formatter={(v) => [`${v.toLocaleString()} tCO₂e`]} />
                </PieChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Category breakdown table */}
          <Card title="Category Breakdown" subtitle="GHG Protocol Scope 3 Standard — all 15 categories">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    {['Category','tCO₂e','% of Total','Data Quality','Hotspot'].map(h => (
                      <th key={h} className="text-left text-white/40 font-semibold py-2 pr-4">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.by_category?.sort((a, b) => b.total_tco2e - a.total_tco2e).map((c, i) => (
                    <tr key={i} className="border-b border-white/[0.02] hover:bg-white/[0.02]">
                      <td className="py-2 pr-4 font-medium text-white/70">{c.category.replace(/_/g, ' ')}</td>
                      <td className="pr-4 font-mono">{c.total_tco2e.toLocaleString(undefined, { maximumFractionDigits: 1 })}</td>
                      <td className="pr-4">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 bg-white/[0.06] rounded-full w-16 overflow-hidden">
                            <div className="h-full bg-cyan-400/10 rounded-full" style={{ width: `${Math.min(c.pct_of_total, 100)}%` }} />
                          </div>
                          <span>{c.pct_of_total?.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="pr-4">
                        <span className={`font-medium ${c.data_quality_score > 0.7 ? 'text-emerald-600' : c.data_quality_score > 0.4 ? 'text-amber-600' : 'text-red-500'}`}>
                          {(c.data_quality_score * 100).toFixed(0)}%
                        </span>
                      </td>
                      <td>
                        {c.hotspot_flag
                          ? <Badge label="Hotspot" color="bg-red-500/10 text-red-600" />
                          : <Badge label="Normal" color="bg-emerald-500/10 text-emerald-600" />}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>

          {/* Hotspots */}
          {result.hotspots?.length > 0 && (
            <Card title="Hotspot Analysis — Priority Reduction Targets"
              subtitle="Activities contributing disproportionately to total Scope 3 footprint">
              <div className="space-y-3">
                {result.hotspots.map((h, i) => (
                  <div key={i} className="flex items-start gap-4 p-3 bg-red-500/10 border border-red-100 rounded-lg">
                    <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center text-red-600 font-bold text-sm flex-shrink-0">
                      {i + 1}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-3 flex-wrap mb-1">
                        <span className="text-xs font-semibold text-white/90">{h.activity}</span>
                        <Badge label={h.category.replace(/_/g, ' ')} color="bg-red-100 text-red-700" />
                        <span className="text-xs text-white/40">{h.tco2e?.toFixed(1)} tCO₂e ({h.pct_of_total?.toFixed(1)}% of total)</span>
                      </div>
                      <p className="text-xs text-white/60">{h.recommended_action}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Validation */}
          <Card title="Validation Summary — ISO 14064-1 Compliance">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <div className={`rounded-lg p-3 ${result.validation_summary?.is_valid ? 'bg-emerald-500/10 border border-emerald-500/20' : 'bg-red-500/10 border border-red-500/20'}`}>
                <p className="text-xs font-semibold text-white/60 mb-1">Validity Status</p>
                <p className={`text-sm font-bold ${result.validation_summary?.is_valid ? 'text-emerald-700' : 'text-red-700'}`}>
                  {result.validation_summary?.is_valid ? 'Valid Disclosure' : 'Incomplete Disclosure'}
                </p>
              </div>
              <div className="rounded-lg p-3 bg-blue-500/10 border border-blue-500/20">
                <p className="text-xs font-semibold text-white/60 mb-1">Data Quality</p>
                <p className="text-sm font-bold text-blue-700">
                  {((result.validation_summary?.data_quality_score || 0) * 100).toFixed(0)}% — Tier {
                    (result.validation_summary?.data_quality_score || 0) > 0.8 ? '1' :
                    (result.validation_summary?.data_quality_score || 0) > 0.6 ? '2' : '3'
                  } (GHG Protocol)
                </p>
              </div>
              <div className="rounded-lg p-3 bg-amber-500/10 border border-amber-200">
                <p className="text-xs font-semibold text-white/60 mb-1">Standard</p>
                <p className="text-sm font-bold text-amber-700">GHG Protocol Scope 3 Corporate Standard</p>
              </div>
            </div>
            {result.validation_summary?.warnings?.length > 0 && (
              <div>
                <p className="text-xs font-semibold text-amber-700 mb-2">Warnings ({result.validation_summary.warnings.length})</p>
                <ul className="space-y-1">
                  {result.validation_summary.warnings.map((w, i) => (
                    <li key={i} className="text-xs text-amber-700 flex items-start gap-2">
                      <span className="text-amber-400 mt-0.5">▲</span>{w}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── SBTi Trajectory Panel ────────────────────────────────────────────────── */
function SBTiPanel() {
  const [form, setForm] = useState({
    entity_id: '',
    base_year: 2019,
    base_year_emissions_tco2e: 100000,
    target_year: 2030,
    reduction_pct: 42,
    sbti_pathway: '1.5C',
  });
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/supply-chain/sbti-trajectory`, form);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  // Build trajectory chart from milestones
  const chartData = result?.trajectory_milestones?.map(m => ({
    year: m.year,
    target: parseFloat(m.target_emissions_tco2e?.toFixed(0)),
    required_reduction: parseFloat(m.cumulative_reduction_pct?.toFixed(1)),
  })) || [];

  return (
    <div className="space-y-6">
      <Card title="SBTi Target Setting & Trajectory" subtitle="Science Based Targets initiative — Corporate Net-Zero Standard v2.0">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Entity ID</label>
            <input className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.entity_id} onChange={e => set('entity_id', e.target.value)} placeholder="company_001" />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Base Year</label>
            <input type="number" className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.base_year} onChange={e => set('base_year', parseInt(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Base Year Emissions (tCO₂e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.base_year_emissions_tco2e} onChange={e => set('base_year_emissions_tco2e', parseFloat(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Target Year</label>
            <input type="number" min="2025" max="2050"
              className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.target_year} onChange={e => set('target_year', parseInt(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Absolute Reduction Target (%)</label>
            <input type="number" min="0" max="100"
              className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.reduction_pct} onChange={e => set('reduction_pct', parseFloat(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">SBTi Pathway</label>
            <select className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={form.sbti_pathway} onChange={e => set('sbti_pathway', e.target.value)}>
              {SBTI_PATHWAYS.map(p => <option key={p.v} value={p.v}>{p.l}</option>)}
            </select>
          </div>
        </div>
        <div className="mt-4 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-6 py-2.5 rounded-lg shadow transition-colors">
            {loading ? 'Calculating…' : 'Generate Trajectory'}
          </button>
        </div>
      </Card>

      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-700">{error}</div>}

      {result && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Base Year Emissions" value={result.base_year_emissions_tco2e} unit="tCO₂e" />
            <StatCard label="Target Emissions" value={result.target_emissions_tco2e} unit="tCO₂e"
              color="text-emerald-700" sub={`by ${result.target_year}`} />
            <StatCard label="Annual Reduction Rate" value={`${result.required_annual_reduction_pct?.toFixed(1)}%`}
              color="text-blue-700" sub="per year CAGR" />
            <StatCard label="SBTi Aligned"
              value={result.is_sbti_aligned ? 'Aligned' : 'Misaligned'}
              color={result.is_sbti_aligned ? 'text-emerald-700' : 'text-red-600'}
              sub={result.sbti_pathway} />
          </div>

          <Card title="Decarbonisation Trajectory" subtitle={`${result.base_year} → ${result.target_year} — ${result.sbti_pathway} pathway`}>
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="year" tick={{ fontSize: 10 }} />
                <YAxis tick={{ fontSize: 10 }} />
                <Tooltip formatter={(v, n) => [
                  n === 'target' ? `${v?.toLocaleString()} tCO₂e` : `${v}%`, n === 'target' ? 'Target Emissions' : 'Cumulative Reduction'
                ]} />
                <Legend />
                <Line type="monotone" dataKey="target" stroke="#6366f1" strokeWidth={2} dot={false} name="Target Emissions (tCO₂e)" />
                <ReferenceLine y={result.target_emissions_tco2e} stroke="#10b981" strokeDasharray="4 4" label={{ value: 'Target', fill: '#10b981', fontSize: 10 }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          <Card title="Milestone Years">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-white/[0.06]">
                    {['Year','Target Emissions (tCO₂e)','Cumulative Reduction','Annual Required Reduction'].map(h => (
                      <th key={h} className="text-left text-white/40 font-semibold py-2 pr-6">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.trajectory_milestones?.map((m, i) => (
                    <tr key={i} className="border-b border-white/[0.02] hover:bg-white/[0.02]">
                      <td className="py-2 pr-6 font-semibold text-cyan-400">{m.year}</td>
                      <td className="pr-6 font-mono">{m.target_emissions_tco2e?.toLocaleString(undefined, { maximumFractionDigits: 0 })}</td>
                      <td className="pr-6">
                        <div className="flex items-center gap-2">
                          <div className="h-1.5 bg-white/[0.06] rounded-full w-20 overflow-hidden">
                            <div className="h-full bg-emerald-400 rounded-full" style={{ width: `${Math.min(m.cumulative_reduction_pct || 0, 100)}%` }} />
                          </div>
                          <span className="font-medium text-emerald-700">{m.cumulative_reduction_pct?.toFixed(1)}%</span>
                        </div>
                      </td>
                      <td className="text-white/60">{m.annual_reduction_required_tco2e?.toLocaleString(undefined, { maximumFractionDigits: 0 })} tCO₂e/yr</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ── Emission Factor Lookup ───────────────────────────────────────────────── */
function EmissionFactorPanel() {
  const [activity, setActivity] = useState('');
  const [country, setCountry] = useState('GB');
  const [year, setYear] = useState(2024);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleLookup = async () => {
    if (!activity.trim()) { setError('Enter an activity type.'); return; }
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.get(`${API}/api/v1/supply-chain/emission-factors`, {
        params: { activity_type: activity, country_iso: country, year }
      });
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <Card title="Emission Factor Lookup" subtitle="GHG Protocol / DEFRA / IPCC AR6 emission factor database">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Activity Type</label>
            <input className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 w-64 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              placeholder="e.g. grid_electricity, natural_gas, diesel"
              value={activity} onChange={e => setActivity(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Country (ISO2)</label>
            <input className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 w-24 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={country} onChange={e => setCountry(e.target.value)} />
          </div>
          <div>
            <label className="block text-xs font-medium text-white/60 mb-1">Year</label>
            <input type="number" className="border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 w-24 focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
              value={year} onChange={e => setYear(parseInt(e.target.value))} />
          </div>
          <button onClick={handleLookup} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-5 py-2.5 rounded-lg shadow transition-colors">
            {loading ? 'Looking up…' : 'Lookup Factor'}
          </button>
        </div>
      </Card>

      {error && <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-700">{error}</div>}

      {result && (
        <Card title="Emission Factor Results">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <StatCard label="Emission Factor" value={result.emission_factor_kgco2e_per_unit?.toFixed(4)} unit="kgCO₂e/unit" color="text-cyan-300" />
            <StatCard label="GWP Basis" value={result.gwp_basis || 'AR6'} sub="IPCC Global Warming Potential" />
            <StatCard label="Source" value={result.source || 'DEFRA 2024'} sub={result.version} />
            <StatCard label="Uncertainty" value={`±${result.uncertainty_pct?.toFixed(0) || '?'}%`}
              color={result.uncertainty_pct < 10 ? 'text-emerald-700' : 'text-amber-600'} />
          </div>
          {result.notes && (
            <div className="bg-white/[0.02] rounded-lg p-3 text-xs text-white/60">
              <strong>Notes:</strong> {result.notes}
            </div>
          )}
        </Card>
      )}
    </div>
  );
}

/* ── China Supplier Intelligence Panel ──────────────────────────────────── */
const CT_API = process.env.REACT_APP_BACKEND_URL || process.env.REACT_APP_API_URL || '';
const CT_BASE_SC = `${CT_API}/api/v1/china-trade`;

function ChinaSupplierPanel() {
  const [sector, setSector] = React.useState('');
  const [exporters, setExporters] = React.useState([]);
  const [scope3Factors, setScope3Factors] = React.useState(null);
  const [loading, setLoading] = React.useState(false);
  const [factsLoading, setFactsLoading] = React.useState(false);
  const [selectedEntity, setSelectedEntity] = React.useState(null);
  const [entityHub, setEntityHub] = React.useState(null);

  const SECTORS = ['', 'Steel', 'Aluminium', 'Cement', 'Chemicals', 'Renewables'];

  const fetchExporters = React.useCallback(async () => {
    setLoading(true);
    try {
      const url = sector
        ? `${CT_BASE_SC}/exporters/search?sector=${encodeURIComponent(sector)}&cbam_applicable=true&limit=30`
        : `${CT_BASE_SC}/exporters/search?cbam_applicable=true&limit=30`;
      const r = await fetch(url);
      const d = await r.json();
      setExporters(d.exporters || d || []);
    } catch { setExporters([]); }
    finally { setLoading(false); }
  }, [sector]);

  const fetchScope3Factors = React.useCallback(async () => {
    setFactsLoading(true);
    try {
      const url = sector
        ? `${CT_BASE_SC}/cross-module/scope3-cat1?sector=${encodeURIComponent(sector)}`
        : `${CT_BASE_SC}/cross-module/scope3-cat1`;
      const r = await fetch(url);
      const d = await r.json();
      setScope3Factors(d);
    } catch { setScope3Factors(null); }
    finally { setFactsLoading(false); }
  }, [sector]);

  const fetchEntityHub = async (name) => {
    setSelectedEntity(name);
    try {
      const r = await fetch(`${CT_BASE_SC}/cross-module/entity-hub/${encodeURIComponent(name)}`);
      const d = await r.json();
      setEntityHub(d);
    } catch { setEntityHub(null); }
  };

  React.useEffect(() => { fetchExporters(); fetchScope3Factors(); }, [fetchExporters, fetchScope3Factors]);

  const READINESS_COLOR = (s) => {
    if (s >= 75) return 'text-emerald-400';
    if (s >= 50) return 'text-cyan-400';
    if (s >= 25) return 'text-amber-400';
    return 'text-red-400';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white">China Supplier Intelligence</h2>
          <p className="text-xs text-white/40 mt-0.5">
            GHG Protocol Scope 3 Cat 1 emission factors from CETS-verified Chinese exporters
          </p>
        </div>
        <div className="flex gap-2 items-center">
          <select
            value={sector}
            onChange={e => setSector(e.target.value)}
            className="text-xs border border-white/[0.06] rounded px-3 py-1.5 bg-[#0b1120] text-white/70 focus:outline-none focus:ring-1 focus:ring-cyan-400/50"
          >
            {SECTORS.map(s => <option key={s} value={s}>{s || 'All Sectors'}</option>)}
          </select>
          <span className="text-[10px] text-white/30">
            {exporters.length} exporters · {scope3Factors?.total_factors || 0} EF records
          </span>
        </div>
      </div>

      {/* Scope 3 Cat 1 Emission Factors */}
      {scope3Factors && (
        <Card
          title="Scope 3 Category 1 — Purchased Goods & Services"
          subtitle={`${scope3Factors.ghg_protocol_category} · Source: ${scope3Factors.data_source}`}
        >
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">HS-4</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">Product</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">Sector</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">EF (tCO2/t)</th>
                  <th className="text-right py-2 text-white/40 font-medium">EU Benchmark</th>
                </tr>
              </thead>
              <tbody>
                {(scope3Factors.factors || []).map((f, i) => (
                  <tr key={i} className="border-b border-white/[0.02] hover:bg-white/[0.02]">
                    <td className="py-2 pr-4 font-mono text-white/60">{f.hs4 || f.hs_code?.substring(0, 4) || '—'}</td>
                    <td className="py-2 pr-4 text-white/80">{f.product || f.product_name}</td>
                    <td className="py-2 pr-4">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-cyan-500/10 text-cyan-400">{f.sector}</span>
                    </td>
                    <td className="py-2 pr-4 text-right font-bold text-white">{Number(f.ef_tco2_t || f.embedded_carbon_tco2_per_tonne || 0).toFixed(3)}</td>
                    <td className="py-2 text-right text-white/50">{f.eu_benchmark_tco2_per_tonne ? Number(f.eu_benchmark_tco2_per_tonne).toFixed(3) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="text-[10px] text-white/20 mt-3 pt-2 border-t border-white/[0.04]">
            Use these factors in Scope 3 Cat 1 calculations for imported Chinese goods. · View full data at <a href="/china-trade" className="text-cyan-400 hover:underline">/china-trade</a>
          </p>
        </Card>
      )}

      {/* Exporter Supplier List */}
      <Card
        title="Chinese Exporters — CBAM Readiness Supplier Ranking"
        subtitle="Click an exporter to view cross-module entity hub (CBAM · ETS · ESG)"
      >
        {loading ? (
          <div className="text-center py-8 text-white/30 text-sm">Loading exporters…</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">Entity</th>
                  <th className="text-left py-2 pr-4 text-white/40 font-medium">Sector</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">CBAM Readiness</th>
                  <th className="text-right py-2 pr-4 text-white/40 font-medium">Carbon Int. (tCO2/t)</th>
                  <th className="text-right py-2 text-white/40 font-medium">ESG Tier</th>
                </tr>
              </thead>
              <tbody>
                {(exporters.slice(0, 15)).map((e, i) => (
                  <tr
                    key={i}
                    className={`border-b border-white/[0.02] cursor-pointer transition-colors ${
                      selectedEntity === e.entity_name ? 'bg-cyan-400/5' : 'hover:bg-white/[0.02]'
                    }`}
                    onClick={() => fetchEntityHub(e.entity_name)}
                  >
                    <td className="py-2 pr-4 text-white/80 font-medium">{e.entity_name}</td>
                    <td className="py-2 pr-4">
                      <span className="px-1.5 py-0.5 rounded text-[10px] bg-white/[0.06] text-white/50">{e.sector}</span>
                    </td>
                    <td className={`py-2 pr-4 text-right font-bold ${READINESS_COLOR(e.cbam_readiness_score)}`}>
                      {e.cbam_readiness_score}
                    </td>
                    <td className="py-2 pr-4 text-right text-white/70">
                      {e.carbon_intensity_tco2_per_tonne ? Number(e.carbon_intensity_tco2_per_tonne).toFixed(2) : '—'}
                    </td>
                    <td className="py-2 text-right">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] ${
                        e.esg_tier === 'Leader' ? 'bg-emerald-500/10 text-emerald-400' :
                        e.esg_tier === 'Advanced' ? 'bg-cyan-500/10 text-cyan-400' :
                        e.esg_tier === 'Developing' ? 'bg-amber-500/10 text-amber-400' :
                        'bg-red-500/10 text-red-400'
                      }`}>{e.esg_tier || '—'}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Entity Hub */}
      {entityHub && !entityHub.error && (
        <Card
          title={`Entity Hub — ${entityHub.entity_name}`}
          subtitle={`${entityHub.sector} · ESG ${entityHub.esg_tier} · CBAM Readiness ${entityHub.cbam_readiness_score}`}
        >
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            <StatCard label="CBAM Readiness" value={entityHub.cbam_readiness_score} unit="/100" color={READINESS_COLOR(entityHub.cbam_readiness_score)} />
            <StatCard label="ETS Registered" value={entityHub.ets_registered ? 'Yes' : 'No'} color={entityHub.ets_registered ? 'text-emerald-400' : 'text-amber-400'} />
            {entityHub.esg_disclosure?.scope1_tco2e && (
              <StatCard label="Scope 1" value={entityHub.esg_disclosure.scope1_tco2e?.toLocaleString()} unit="tCO2e" />
            )}
            {entityHub.cbam_liability?.net_cbam_liability_eur && (
              <StatCard label="Net CBAM Liability" value={`€${(entityHub.cbam_liability.net_cbam_liability_eur / 1000).toFixed(0)}k`} color="text-amber-400" />
            )}
          </div>
          <div className="flex gap-2 flex-wrap">
            {Object.entries(entityHub.module_links || {}).map(([mod, href]) => (
              <a key={mod} href={href}
                className="text-[10px] px-2.5 py-1 rounded border border-cyan-400/20 text-cyan-400/70 hover:text-cyan-300 hover:border-cyan-400/40 transition-colors capitalize">
                {mod.replace(/_/g, ' ')}
              </a>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────────── */
const PANELS = [
  { id: 'scope3', label: 'Scope 3 Calculator', sub: '15 GHG Protocol Categories' },
  { id: 'sbti', label: 'SBTi Trajectory', sub: 'Science Based Target Setting' },
  { id: 'factors', label: 'Emission Factor Lookup', sub: 'DEFRA / IPCC AR6' },
  { id: 'china', label: 'China Supplier Intelligence', sub: 'CBAM · CETS · Scope 3' },
];

export default function SupplyChainPage() {
  const [activePanel, setActivePanel] = useState('scope3');

  return (
    <div className="flex flex-col h-full bg-white/[0.02]">
      {/* Page header */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-8 py-5">
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-xl font-bold text-white">Supply Chain Emissions</h1>
            <p className="text-sm text-white/40 mt-0.5">
              Scope 3 value-chain assessment, SBTi target trajectories, and emission factor database
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Badge label="GHG Protocol Scope 3" color="bg-emerald-500/10 text-emerald-700" />
            <Badge label="SBTi Corporate v2.0" color="bg-blue-500/10 text-blue-700" />
            <Badge label="ISO 14064-1:2023" color="bg-white/[0.06] text-white/60" />
            <Badge label="TCFD Scope 3" color="bg-purple-50 text-purple-700" />
          </div>
        </div>
      </div>

      {/* Sub-nav */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-8">
        <div className="flex gap-0">
          {PANELS.map(p => (
            <button
              key={p.id}
              onClick={() => setActivePanel(p.id)}
              className={`px-5 py-3.5 border-b-2 transition-all ${
                activePanel === p.id
                  ? 'border-cyan-400/20 text-cyan-300'
                  : 'border-transparent text-white/40 hover:text-white/70 hover:border-white/[0.08]'
              }`}
            >
              <span className="text-sm font-semibold block">{p.label}</span>
              <span className="text-[10px] text-white/30">{p.sub}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-8">
        {activePanel === 'scope3' && <Scope3Panel />}
        {activePanel === 'sbti' && <SBTiPanel />}
        {activePanel === 'factors' && <EmissionFactorPanel />}
        {activePanel === 'china' && <ChinaSupplierPanel />}
      </div>
    </div>
  );
}
