/**
 * SteelPanel — BF-BOF / EAF / DRI emission intensity vs IEA NZE glidepath.
 * Embedded in SectorAssessmentsPage.
 * Sprint 5 — WHOOP for Sustainability platform.
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  ComposedChart, Line, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const RAG_COLOURS = {
  GREEN: '#10b981', AMBER: '#f59e0b', RED: '#ef4444', GREY: '#6b7280',
};

const ROUTE_COLOURS = {
  'BF-BOF': '#ef4444',
  'BF-BOF + CCUS': '#f97316',
  'EAF (grid)': '#f59e0b',
  'DRI-EAF (gas)': '#8b5cf6',
  'DRI-EAF (H2)': '#10b981',
};

const Field = ({ label, children, hint }) => (
  <div>
    <label className="block text-xs text-gray-400 mb-1">{label}</label>
    {children}
    {hint && <p className="text-xs text-gray-600 mt-0.5">{hint}</p>}
  </div>
);

const Num = ({ value, onChange, min = 0, max, step = 'any', placeholder }) => (
  <input type="number" value={value} onChange={e => onChange(e.target.value)}
    min={min} max={max} step={step} placeholder={placeholder}
    className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60"
    style={{ fontFamily: 'IBM Plex Mono, monospace' }} />
);

// Route mix slider with live total
const RouteSlider = ({ label, value, onChange, colour }) => (
  <div className="space-y-1">
    <div className="flex justify-between items-center">
      <label className="text-xs text-gray-400">{label}</label>
      <span className="text-xs font-mono text-white">{(parseFloat(value || 0) * 100).toFixed(0)}%</span>
    </div>
    <input type="range" min={0} max={1} step={0.01} value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full h-1.5 rounded appearance-none cursor-pointer"
      style={{ accentColor: colour }} />
  </div>
);

export default function SteelPanel() {
  const [form, setForm] = useState({
    plant_name: 'Steel Plant 1',
    annual_production_mt: 3.5,
    bf_bof_pct: 0.85,
    eaf_pct: 0.10,
    dri_eaf_pct: 0.05,
    dri_h2_pct: 0.00,
    bf_bof_ccus_pct: 0.00,
    eaf_grid_carbon_intensity_kgco2_kwh: 0.38,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));
  const setN = (k, v) => setForm(p => ({ ...p, [k]: parseFloat(v) || 0 }));

  const totalMix = ['bf_bof_pct', 'eaf_pct', 'dri_eaf_pct', 'dri_h2_pct', 'bf_bof_ccus_pct']
    .reduce((s, k) => s + parseFloat(form[k] || 0), 0);
  const mixOk = Math.abs(totalMix - 1.0) < 0.05;

  const handleCalculate = async () => {
    setLoading(true); setError(null);
    try {
      const resp = await axios.post(`${API}/api/v1/sector-calculators/steel/calculate`, form);
      setResult(resp.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally { setLoading(false); }
  };

  // Route breakdown donut
  const donutData = result
    ? Object.entries(result.route_breakdown || {}).map(([k, v]) => ({ name: k, value: parseFloat(v) })).filter(d => d.value > 0)
    : [];

  // Glidepath chart
  const glidepathData = result?.glidepath_series?.map(p => ({
    year: p.year,
    current: p.weighted_intensity,
    iea: p.iea_nze_target,
    sbti: p.sbti_target,
    rag: p.rag_status,
  })) || [];

  const ragColour = result ? (RAG_COLOURS[result.rag_2030] || RAG_COLOURS.GREY) : RAG_COLOURS.GREY;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Steel Decarbonisation</h2>
        <p className="text-sm text-gray-400 mt-0.5">BF-BOF / EAF / DRI production route mix vs IEA NZE glidepath</p>
      </div>

      {/* Form */}
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <div className="col-span-2">
            <Field label="Plant Name">
              <input type="text" value={form.plant_name} onChange={e => set('plant_name', e.target.value)}
                className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60" />
            </Field>
          </div>
          <Field label="Annual Production (Mt/yr)">
            <Num value={form.annual_production_mt} onChange={v => setN('annual_production_mt', v)} min={0.01} max={200} step={0.1} />
          </Field>
          <Field label="Grid Carbon Intensity (kgCO₂/kWh)" hint="For EAF electricity">
            <Num value={form.eaf_grid_carbon_intensity_kgco2_kwh} onChange={v => setN('eaf_grid_carbon_intensity_kgco2_kwh', v)} min={0} max={2} step={0.01} />
          </Field>
        </div>

        {/* Route mix sliders */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <label className="text-sm font-semibold text-gray-300">Production Route Mix</label>
            <span className={`text-xs font-mono ${mixOk ? 'text-emerald-400' : 'text-red-400'}`}>
              Total: {(totalMix * 100).toFixed(0)}% {mixOk ? '✓' : '(must sum to 100%)'}
            </span>
          </div>
          <div className="space-y-3">
            <RouteSlider label="BF-BOF (Blast Furnace)" value={form.bf_bof_pct} onChange={v => setN('bf_bof_pct', v)} colour={ROUTE_COLOURS['BF-BOF']} />
            <RouteSlider label="BF-BOF + CCUS" value={form.bf_bof_ccus_pct} onChange={v => setN('bf_bof_ccus_pct', v)} colour={ROUTE_COLOURS['BF-BOF + CCUS']} />
            <RouteSlider label="EAF (Electric Arc — scrap)" value={form.eaf_pct} onChange={v => setN('eaf_pct', v)} colour={ROUTE_COLOURS['EAF (grid)']} />
            <RouteSlider label="DRI-EAF (Gas)" value={form.dri_eaf_pct} onChange={v => setN('dri_eaf_pct', v)} colour={ROUTE_COLOURS['DRI-EAF (gas)']} />
            <RouteSlider label="DRI-EAF (Green Hydrogen)" value={form.dri_h2_pct} onChange={v => setN('dri_h2_pct', v)} colour={ROUTE_COLOURS['DRI-EAF (H2)']} />
          </div>
        </div>
      </div>

      <button onClick={handleCalculate} disabled={loading || !mixOk}
        className="w-full py-3 rounded-lg text-sm font-semibold text-white disabled:opacity-50"
        style={{ background: 'linear-gradient(135deg, hsl(199,89%,40%), hsl(199,89%,30%))' }}
        data-testid="steel-calculate-btn">
        {loading ? 'Calculating...' : 'Calculate Emission Intensity'}
      </button>

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded p-3 text-sm text-red-400">{error}</div>}

      {result && (
        <div className="space-y-5">
          {/* Header KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Weighted Intensity', value: `${parseFloat(result.weighted_emission_intensity).toFixed(2)}`, unit: 'tCO₂/tSteel', testId: 'steel-intensity' },
              { label: 'Annual CO₂', value: `${parseFloat(result.annual_co2_mt).toFixed(2)}`, unit: 'Mt CO₂/yr' },
              { label: 'vs IEA NZE 2030', value: `${parseFloat(result.pct_vs_iea_2030) > 0 ? '+' : ''}${parseFloat(result.pct_vs_iea_2030).toFixed(1)}%`, unit: result.rag_2030 },
              { label: 'IEA 2030 Target', value: `${parseFloat(result.iea_2030_target).toFixed(2)}`, unit: 'tCO₂/tSteel' },
            ].map((k, i) => (
              <div key={i} data-testid={k.testId} className="rounded-lg p-3 border border-white/10 bg-white/3">
                <div className="text-xs text-gray-400 mb-1">{k.label}</div>
                <div className="text-xl font-bold text-white" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{k.value}</div>
                <div className="text-xs mt-0.5" style={{ color: i === 2 ? ragColour : '#6b7280' }}>{k.unit}</div>
              </div>
            ))}
          </div>

          {/* Route mix donut + glidepath chart side by side */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            {/* Route breakdown donut */}
            <div className="rounded-lg border border-white/10 p-4" style={{ background: 'hsl(222,35%,9%)' }}>
              <div className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">Production Route Mix</div>
              <ResponsiveContainer width="100%" height={200}>
                <PieChart>
                  <Pie data={donutData} cx="50%" cy="50%" innerRadius={55} outerRadius={85}
                    dataKey="value" nameKey="name" paddingAngle={2}>
                    {donutData.map((entry, i) => (
                      <Cell key={i} fill={ROUTE_COLOURS[entry.name] || '#6b7280'} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
                    formatter={v => [`${parseFloat(v).toFixed(3)} tCO₂/t`, 'Contribution']} />
                  <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            {/* Glidepath chart */}
            <div className="rounded-lg border border-white/10 p-4" style={{ background: 'hsl(222,35%,9%)' }}>
              <div className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">vs IEA NZE Glidepath</div>
              <ResponsiveContainer width="100%" height={200}>
                <ComposedChart data={glidepathData} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
                  <XAxis dataKey="year" tick={{ fill: '#9ca3af', fontSize: 10 }} />
                  <YAxis tick={{ fill: '#9ca3af', fontSize: 10 }} tickFormatter={v => `${v}`} />
                  <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
                    formatter={(v, name) => [v ? `${Number(v).toFixed(2)} tCO₂/t` : 'No data', name]} />
                  <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 10 }} />
                  <Line type="monotone" dataKey="current" stroke="#22d3ee" strokeWidth={2.5}
                    dot={{ fill: '#22d3ee', r: 4 }} name="Current intensity" connectNulls={false} />
                  <Line type="monotone" dataKey="iea" stroke="#10b981" strokeWidth={2} dot={false}
                    strokeDasharray="5 3" name="IEA NZE" />
                  <Line type="monotone" dataKey="sbti" stroke="#ffffff" strokeWidth={1.5} dot={false}
                    strokeDasharray="3 3" strokeOpacity={0.4} name="SBTi Steel" />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Scenarios */}
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg border border-white/10 bg-white/3 p-3">
              <div className="text-xs text-gray-400 mb-1">Scenario: 100% EAF + Renewable Power</div>
              <div className="text-xl font-bold text-emerald-400" style={{ fontFamily: 'IBM Plex Mono' }}>
                {parseFloat(result.scenario_full_eaf_renewable_intensity).toFixed(2)} tCO₂/t
              </div>
              <div className="text-xs text-gray-500 mt-0.5">Best-in-class achievable intensity</div>
            </div>
            <div className="rounded-lg border border-white/10 bg-white/3 p-3">
              <div className="text-xs text-gray-400 mb-1">Scenario: 50% Green H₂ DRI</div>
              <div className="text-xl font-bold text-blue-400" style={{ fontFamily: 'IBM Plex Mono' }}>
                {parseFloat(result.scenario_dri_h2_50pct_intensity).toFixed(2)} tCO₂/t
              </div>
              <div className="text-xs text-gray-500 mt-0.5">Near-term achievable via H₂ DRI pilot</div>
            </div>
          </div>

          {/* Pathway narrative */}
          {result.pathway_to_iea_2030 && (
            <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-4">
              <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">Decarbonisation Pathway</div>
              <p className="text-sm text-gray-300 leading-relaxed">{result.pathway_to_iea_2030}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
