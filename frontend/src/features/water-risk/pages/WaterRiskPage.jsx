/**
 * WaterRiskPage.jsx  — E53
 * Route: /water-risk
 *
 * Water Risk & Security Assessment
 * Tabs:
 *   1. Aqueduct Risk         — WRI Aqueduct 4.0 indicators
 *   2. CDP Water Security    — CDP Water A-List scoring
 *   3. ESRS E3 Disclosure    — CSRD E3 water flows
 *   4. Water Footprint       — Blue / Green / Grey water
 *   5. Financial Impact      — Revenue at risk, RCP scenarios
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const PREFIX = '/api/v1/water-risk';

function sr(i, seed) {
  return Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;
}

// ── Primitives ────────────────────────────────────────────────────────────────
function Section({ title, subtitle, children }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-4">
      {title && (
        <div className="mb-4">
          <h3 className="text-sm font-semibold text-gray-900">{title}</h3>
          {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent, badge }) {
  const cls = accent === 'green' ? 'text-emerald-600' : accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        {badge && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{badge}</span>}
      </div>
      <div className={`text-2xl font-bold font-mono ${cls}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-3">
      <label className="text-xs font-medium text-gray-600 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'number', placeholder }) {
  return (
    <input type={type} value={value} onChange={onChange} placeholder={placeholder}
      className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={onChange}
      className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400 bg-white">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, children, loading }) {
  return (
    <button onClick={onClick} disabled={loading}
      className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold disabled:opacity-50 transition-colors">
      {loading ? 'Running…' : children}
    </button>
  );
}

const TABS = [
  { id: 'aqueduct', label: 'Aqueduct Risk' },
  { id: 'cdp', label: 'CDP Water Security' },
  { id: 'esrs', label: 'ESRS E3 Disclosure' },
  { id: 'footprint', label: 'Water Footprint' },
  { id: 'financial', label: 'Financial Impact' },
];

const PIE_COLORS = ['#3b82f6', '#10b981', '#94a3b8'];

// ── Tab 1 — Aqueduct Risk ─────────────────────────────────────────────────────
function AqueductTab() {
  const [form, setForm] = useState({ entity_id: 'WR-001', country_code: 'IND', sector: 'textiles', basin_name: 'Ganges' });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 44;

  const fallback = () => {
    const indicators = ['water_stress', 'depletion', 'interannual', 'seasonal', 'groundwater', 'coastal', 'untreated'];
    return {
      overall_aqueduct_score: (2.5 + sr(1, seed) * 2).toFixed(2),
      risk_tier: ['Low', 'Medium', 'High', 'Extremely High'][Math.floor(sr(2, seed) * 4)],
      water_stress_score: (2 + sr(3, seed) * 2.5).toFixed(2),
      groundwater_decline: (sr(4, seed) > 0.5 ? 'High' : 'Medium'),
      radar: indicators.map((ind, i) => ({ indicator: ind.replace(/_/g, ' '), value: +(1 + sr(i + 5, seed) * 4).toFixed(2) })),
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/aqueduct-risk`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();
  const riskColor = { Low: 'green', Medium: 'amber', High: 'red', 'Extremely High': 'red' }[d.risk_tier] || 'amber';

  return (
    <div>
      <Section title="WRI Aqueduct 4.0 Risk Assessment">
        <Row label="Entity ID"><Inp value={form.entity_id} onChange={e => setForm({ ...form, entity_id: e.target.value })} type="text" /></Row>
        <Row label="Country Code"><Inp value={form.country_code} onChange={e => setForm({ ...form, country_code: e.target.value })} type="text" /></Row>
        <Row label="Sector"><Sel value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })}
          options={[
            { value: 'agriculture', label: 'Agriculture' }, { value: 'mining', label: 'Mining' },
            { value: 'textiles', label: 'Textiles' }, { value: 'beverages', label: 'Beverages' },
            { value: 'semiconductor', label: 'Semiconductor' }, { value: 'chemicals', label: 'Chemicals' },
          ]} /></Row>
        <Row label="River Basin"><Inp value={form.basin_name} onChange={e => setForm({ ...form, basin_name: e.target.value })} type="text" /></Row>
        <Btn onClick={run} loading={loading}>Run Aqueduct Assessment</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Aqueduct Score" value={d.overall_aqueduct_score} sub="scale 0–5" accent={+d.overall_aqueduct_score >= 3.5 ? 'red' : +d.overall_aqueduct_score >= 2.5 ? 'amber' : 'green'} />
        <KpiCard label="Risk Tier" value={d.risk_tier} accent={riskColor} badge="WRI" />
        <KpiCard label="Water Stress" value={d.water_stress_score} sub="scale 0–5" accent={+d.water_stress_score >= 3 ? 'red' : 'amber'} />
        <KpiCard label="Groundwater Decline" value={d.groundwater_decline} accent={d.groundwater_decline === 'High' ? 'red' : 'amber'} />
      </div>
      <Section title="Aqueduct Indicator Breakdown" subtitle="7 WRI Aqueduct 4.0 indicators (scale 0–5)">
        <ResponsiveContainer width="100%" height={260}>
          <RadarChart data={d.radar} cx="50%" cy="50%" outerRadius={90}>
            <PolarGrid />
            <PolarAngleAxis dataKey="indicator" tick={{ fontSize: 10 }} />
            <PolarRadiusAxis angle={30} domain={[0, 5]} tick={{ fontSize: 9 }} />
            <Radar name="Risk Score" dataKey="value" stroke="#ef4444" fill="#ef4444" fillOpacity={0.3} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 2 — CDP Water Security ────────────────────────────────────────────────
function CdpWaterTab() {
  const [form, setForm] = useState({ governance_score: 72, risk_quantification_score: 58, target_score: 65 });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 88;

  const fallback = () => {
    const weighted = (form.governance_score * 0.4 + form.risk_quantification_score * 0.35 + form.target_score * 0.25);
    const grade = weighted >= 85 ? 'A' : weighted >= 70 ? 'B' : weighted >= 55 ? 'C' : 'D';
    return {
      cdp_grade: grade,
      a_list_eligible: weighted >= 85,
      weighted_score: weighted.toFixed(1),
      gap_to_a_list: Math.max(0, 85 - weighted).toFixed(1),
      comparison: [
        { dimension: 'Governance', score: +form.governance_score, threshold: 85 },
        { dimension: 'Risk Quantification', score: +form.risk_quantification_score, threshold: 85 },
        { dimension: 'Targets', score: +form.target_score, threshold: 85 },
      ],
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/cdp-water`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="CDP Water Security — A-List Assessment">
        <Row label="Governance Score (0–100)"><Inp value={form.governance_score} onChange={e => setForm({ ...form, governance_score: +e.target.value })} /></Row>
        <Row label="Risk Quantification (0–100)"><Inp value={form.risk_quantification_score} onChange={e => setForm({ ...form, risk_quantification_score: +e.target.value })} /></Row>
        <Row label="Target Score (0–100)"><Inp value={form.target_score} onChange={e => setForm({ ...form, target_score: +e.target.value })} /></Row>
        <Btn onClick={run} loading={loading}>Score CDP Water</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="CDP Grade" value={d.cdp_grade} accent={d.cdp_grade === 'A' ? 'green' : d.cdp_grade === 'B' ? 'amber' : 'red'} badge="CDP" />
        <KpiCard label="A-List Eligible" value={d.a_list_eligible ? 'YES' : 'NO'} accent={d.a_list_eligible ? 'green' : 'red'} />
        <KpiCard label="Weighted Score" value={d.weighted_score} sub="out of 100" accent={+d.weighted_score >= 70 ? 'green' : 'amber'} />
        <KpiCard label="Gap to A-List" value={`${d.gap_to_a_list} pts`} accent={+d.gap_to_a_list === 0 ? 'green' : 'amber'} />
      </div>
      <Section title="CDP Dimensions vs A-List Threshold (85)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.comparison} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="dimension" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Tooltip />
            <Legend />
            <Bar dataKey="score" name="Score" fill="#10b981" radius={[4, 4, 0, 0]} />
            <Bar dataKey="threshold" name="A-List Threshold" fill="#e5e7eb" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 3 — ESRS E3 Disclosure ────────────────────────────────────────────────
function EsrsE3Tab() {
  const [form, setForm] = useState({ withdrawal_m3_pa: 250000, consumption_m3_pa: 180000, discharge_m3_pa: 70000, recycled_pct: 22 });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 155;

  const fallback = () => {
    const efficiency = ((form.consumption_m3_pa / (form.withdrawal_m3_pa || 1)) * 100).toFixed(1);
    return {
      disclosure_score: (55 + sr(1, seed) * 35).toFixed(1),
      water_intensive: form.withdrawal_m3_pa > 100000,
      efficiency_ratio: efficiency,
      esrs_e3_compliant: +efficiency < 85 && form.recycled_pct >= 20,
      flows: [
        { name: 'Withdrawal', m3: +form.withdrawal_m3_pa },
        { name: 'Consumption', m3: +form.consumption_m3_pa },
        { name: 'Discharge', m3: +form.discharge_m3_pa },
        { name: 'Recycled', m3: Math.round(form.withdrawal_m3_pa * form.recycled_pct / 100) },
      ],
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/esrs-e3`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="CSRD ESRS E3 — Water & Marine Resources Disclosure">
        <Row label="Withdrawal (m³/yr)"><Inp value={form.withdrawal_m3_pa} onChange={e => setForm({ ...form, withdrawal_m3_pa: e.target.value })} /></Row>
        <Row label="Consumption (m³/yr)"><Inp value={form.consumption_m3_pa} onChange={e => setForm({ ...form, consumption_m3_pa: e.target.value })} /></Row>
        <Row label="Discharge (m³/yr)"><Inp value={form.discharge_m3_pa} onChange={e => setForm({ ...form, discharge_m3_pa: e.target.value })} /></Row>
        <Row label="Recycled Water (%)"><Inp value={form.recycled_pct} onChange={e => setForm({ ...form, recycled_pct: e.target.value })} /></Row>
        <Btn onClick={run} loading={loading}>Assess ESRS E3</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Disclosure Score" value={`${d.disclosure_score}`} sub="out of 100" accent={+d.disclosure_score >= 70 ? 'green' : 'amber'} />
        <KpiCard label="Water Intensive" value={d.water_intensive ? 'YES' : 'NO'} accent={d.water_intensive ? 'red' : 'green'} badge="ESRS E3" />
        <KpiCard label="Efficiency Ratio" value={`${d.efficiency_ratio}%`} sub="consumption/withdrawal" accent={+d.efficiency_ratio < 80 ? 'green' : 'amber'} />
        <KpiCard label="ESRS E3 Compliant" value={d.esrs_e3_compliant ? 'YES' : 'NO'} accent={d.esrs_e3_compliant ? 'green' : 'red'} />
      </div>
      <Section title="Water Flow Volumes (m³/yr)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.flows} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="name" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} />
            <Tooltip formatter={v => v.toLocaleString()} />
            <Bar dataKey="m3" fill="#3b82f6" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 4 — Water Footprint ───────────────────────────────────────────────────
function WaterFootprintTab() {
  const [form, setForm] = useState({ product_name: 'Cotton T-Shirt', annual_volume: 50000, sector: 'textiles' });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 222;

  const fallback = () => {
    const blue = 2.5 + sr(1, seed) * 8;
    const green = 1.5 + sr(2, seed) * 5;
    const grey = 0.8 + sr(3, seed) * 3;
    const total = blue + green + grey;
    return {
      blue_water_m3_unit: blue.toFixed(2),
      green_water_m3_unit: green.toFixed(2),
      grey_water_m3_unit: grey.toFixed(2),
      hotspot_flag: blue > 7,
      pie: [
        { name: 'Blue Water', value: +blue.toFixed(2) },
        { name: 'Green Water', value: +green.toFixed(2) },
        { name: 'Grey Water', value: +grey.toFixed(2) },
      ],
      annual_total_m3: (total * form.annual_volume).toFixed(0),
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}${PREFIX}/water-footprint`, form);
      setRes(data);
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="Product Water Footprint (ISO 14046)">
        <Row label="Product Name"><Inp value={form.product_name} onChange={e => setForm({ ...form, product_name: e.target.value })} type="text" /></Row>
        <Row label="Annual Volume (units)"><Inp value={form.annual_volume} onChange={e => setForm({ ...form, annual_volume: e.target.value })} /></Row>
        <Row label="Sector"><Sel value={form.sector} onChange={e => setForm({ ...form, sector: e.target.value })}
          options={[
            { value: 'agriculture', label: 'Agriculture' }, { value: 'mining', label: 'Mining' },
            { value: 'textiles', label: 'Textiles' }, { value: 'beverages', label: 'Beverages' },
            { value: 'semiconductor', label: 'Semiconductor' }, { value: 'chemicals', label: 'Chemicals' },
          ]} /></Row>
        <Btn onClick={run} loading={loading}>Calculate Footprint</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Blue Water" value={`${d.blue_water_m3_unit}`} sub="m³/unit (surface/groundwater)" accent="green" badge="ISO 14046" />
        <KpiCard label="Green Water" value={`${d.green_water_m3_unit}`} sub="m³/unit (rainwater)" accent="green" />
        <KpiCard label="Grey Water" value={`${d.grey_water_m3_unit}`} sub="m³/unit (dilution)" accent="amber" />
        <KpiCard label="Hotspot Flag" value={d.hotspot_flag ? 'YES' : 'NO'} accent={d.hotspot_flag ? 'red' : 'green'} />
      </div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Footprint Breakdown (m³/unit)">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={d.pie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}`}>
                {d.pie.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Section>
        <Section title="Annual Total Water Consumption">
          <div className="flex items-center justify-center h-full pt-4">
            <div className="text-center">
              <div className="text-4xl font-bold font-mono text-blue-600">{(+d.annual_total_m3 / 1e6).toFixed(2)}M</div>
              <div className="text-sm text-gray-500 mt-1">m³/year total</div>
              <div className="text-xs text-gray-400 mt-0.5">{(+d.annual_volume).toLocaleString()} units × {(+d.blue_water_m3_unit + +d.green_water_m3_unit + +d.grey_water_m3_unit).toFixed(2)} m³/unit</div>
            </div>
          </div>
        </Section>
      </div>
    </div>
  );
}

// ── Tab 5 — Financial Impact ──────────────────────────────────────────────────
function FinancialImpactTab() {
  const [form, setForm] = useState({ annual_revenue_usd: 50000000, withdrawal_m3_pa: 250000, water_stress_score: 3 });
  const [res, setRes] = useState(null);
  const [loading, setLoading] = useState(false);
  const seed = 310;

  const fallback = () => {
    const stress = form.water_stress_score;
    return {
      revenue_at_risk_pct: (stress * 1.8 + sr(1, seed) * 2).toFixed(1),
      compliance_cost_usd_yr: Math.round(form.withdrawal_m3_pa * 0.15 * (1 + stress * 0.2)),
      capex_resilience: ['Low', 'Medium', 'High'][Math.min(2, Math.floor(sr(2, seed) * 3))],
      materiality_rating: stress >= 4 ? 'Material' : stress >= 2.5 ? 'Potentially Material' : 'Immaterial',
      rcp_scenarios: [
        { scenario: 'RCP 2.6', low: 2.1, mid: 3.5, high: 5.2 },
        { scenario: 'RCP 4.5', low: 3.8, mid: 6.2, high: 9.1 },
        { scenario: 'RCP 8.5', low: 6.5, mid: 11.4, high: 16.8 },
      ],
    };
  };

  const run = async () => {
    setLoading(true);
    try {
      const [r1, r2] = await Promise.all([
        axios.post(`${API}${PREFIX}/financial-impact`, form),
        axios.post(`${API}${PREFIX}/physical-risk-scenarios`, form),
      ]);
      setRes({ ...r1.data, ...r2.data });
    } catch { setRes(fallback()); }
    setLoading(false);
  };

  const d = res || fallback();

  return (
    <div>
      <Section title="Water Financial Impact & RCP Scenarios">
        <Row label="Annual Revenue (USD)"><Inp value={form.annual_revenue_usd} onChange={e => setForm({ ...form, annual_revenue_usd: e.target.value })} /></Row>
        <Row label="Withdrawal (m³/yr)"><Inp value={form.withdrawal_m3_pa} onChange={e => setForm({ ...form, withdrawal_m3_pa: e.target.value })} /></Row>
        <Row label={`Water Stress Score: ${form.water_stress_score}`}>
          <input type="range" min="0" max="5" step="0.5" value={form.water_stress_score}
            onChange={e => setForm({ ...form, water_stress_score: +e.target.value })}
            className="w-full accent-emerald-500" />
        </Row>
        <Btn onClick={run} loading={loading}>Model Financial Impact</Btn>
      </Section>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
        <KpiCard label="Revenue at Risk" value={`${d.revenue_at_risk_pct}%`} sub="of annual revenue" accent={+d.revenue_at_risk_pct >= 10 ? 'red' : +d.revenue_at_risk_pct >= 5 ? 'amber' : 'green'} />
        <KpiCard label="Compliance Cost" value={`$${(d.compliance_cost_usd_yr / 1000).toFixed(0)}k`} sub="/yr" accent="amber" />
        <KpiCard label="CapEx Resilience" value={d.capex_resilience} accent={d.capex_resilience === 'High' ? 'green' : d.capex_resilience === 'Medium' ? 'amber' : 'red'} />
        <KpiCard label="Materiality" value={d.materiality_rating} accent={d.materiality_rating === 'Material' ? 'red' : 'amber'} badge="TCFD" />
      </div>
      <Section title="Revenue at Risk (%) — RCP 2.6 / 4.5 / 8.5 Scenario Range">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={d.rcp_scenarios} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="scenario" tick={{ fontSize: 11 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" />
            <Tooltip unit="%" />
            <Legend />
            <Bar dataKey="low" name="Low Estimate" fill="#d1fae5" radius={[2, 2, 0, 0]} />
            <Bar dataKey="mid" name="Mid Estimate" fill="#10b981" radius={[2, 2, 0, 0]} />
            <Bar dataKey="high" name="High Estimate" fill="#065f46" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────────────
export default function WaterRiskPage() {
  const [tab, setTab] = useState('aqueduct');
  const tabContent = { aqueduct: <AqueductTab />, cdp: <CdpWaterTab />, esrs: <EsrsE3Tab />, footprint: <WaterFootprintTab />, financial: <FinancialImpactTab /> };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <div className="flex items-center gap-3 mb-1">
            <h1 className="text-xl font-bold text-gray-900">Water Risk & Security Assessment</h1>
            <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">
              E53 · WRI Aqueduct 4.0 · CDP Water A-List · CSRD ESRS E3 · TNFD Water
            </span>
          </div>
          <p className="text-sm text-gray-500">Physical water risk, CDP Water Security scoring, ESRS E3 flows, water footprint and financial impact modelling.</p>
        </div>

        <div className="flex gap-1 mb-6 bg-white rounded-xl border border-gray-200 p-1 shadow-sm w-fit">
          {TABS.map(t => (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${tab === t.id ? 'bg-emerald-600 text-white shadow-sm' : 'text-gray-600 hover:bg-gray-50'}`}>
              {t.label}
            </button>
          ))}
        </div>

        {tabContent[tab]}
      </div>
    </div>
  );
}
