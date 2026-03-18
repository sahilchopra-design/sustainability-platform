/**
 * EUDRPage.jsx
 * Route: /eudr
 * Badge: EUDR·Art4
 *
 * Tab 1 — Commodity Screening   POST /api/v1/eudr/commodity-screening
 * Tab 2 — Country Risk          GET  /api/v1/eudr/ref/country-benchmarks
 * Tab 3 — Due Diligence         POST /api/v1/eudr/due-diligence
 * Tab 4 — Compliance Gap        POST /api/v1/eudr/compliance-gap
 * Tab 5 — DDS Generator         POST /api/v1/eudr/due-diligence-statement
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const BASE = '/api/v1';
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111', fontSize: 11 };

/* ── Seed RNG ───────────────────────────────────────────────────────────── */
function mkRng(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

/* ── Shared primitives ──────────────────────────────────────────────────── */
function Section({ title, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg mb-4">
      <div className="px-4 py-3 border-b border-gray-100">
        <span className="font-medium text-sm text-gray-700">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function KpiCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Badge({ label, color }) {
  const cls = {
    green:  'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber:  'bg-amber-50 text-amber-700 border-amber-200',
    red:    'bg-red-50 text-red-700 border-red-200',
    blue:   'bg-blue-50 text-blue-700 border-blue-200',
    gray:   'bg-gray-50 text-gray-600 border-gray-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>;
}

function Inp({ label, value, onChange, type = 'text' }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-emerald-400"
      />
    </div>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-emerald-400 bg-white"
      >
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function Btn({ onClick, children, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-1.5 bg-black text-white text-xs font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors"
    >
      {children}
    </button>
  );
}

/* ── Seed country data ──────────────────────────────────────────────────── */
const COUNTRY_SEED = (() => {
  const rng = mkRng(501);
  const high = ['Brazil', 'Indonesia', 'DRC', 'Malaysia', 'Paraguay', 'Bolivia', 'Cameroon', 'Peru', 'Nigeria', 'Myanmar'];
  const standard = ['Argentina', 'Colombia', 'Ghana', 'Ivory Coast', 'Guatemala', 'Honduras', 'Ecuador', 'Vietnam', 'Uganda', 'Ethiopia'];
  const low = ['Germany', 'France', 'USA', 'Canada', 'Australia', 'New Zealand', 'Norway', 'Sweden', 'Finland', 'Switzerland'];
  return [
    ...high.map(c => ({ country: c, tier: 'high', score: Math.round(70 + rng() * 30) })),
    ...standard.map(c => ({ country: c, tier: 'standard', score: Math.round(35 + rng() * 35) })),
    ...low.map(c => ({ country: c, tier: 'low', score: Math.round(5 + rng() * 30) })),
  ];
})();

/* ── Seed screening results ─────────────────────────────────────────────── */
function genScreeningResult(commodity, hsCodes) {
  const rng = mkRng(601 + commodity.charCodeAt(0));
  const highRisk = ['cattle', 'oil_palm', 'wood'].includes(commodity);
  return {
    commodity,
    hs_codes: hsCodes.split(',').map(s => s.trim()).filter(Boolean),
    compliance_status: highRisk && rng() > 0.4 ? 'non_compliant' : rng() > 0.6 ? 'at_risk' : 'compliant',
    art29_risk_tier: highRisk ? 'high' : rng() > 0.5 ? 'standard' : 'low',
    matched_hs_count: Math.ceil(rng() * 8),
    annex_i_covered: true,
    enforcement_date: commodity === 'wood' ? '2025-06-29' : '2024-12-30',
    deforestation_risk_score: Math.round(30 + rng() * 60),
    certification_schemes: ['FSC', 'PEFC', 'RSPO'].filter(() => rng() > 0.5),
  };
}

/* ── Seed DD component scores ───────────────────────────────────────────── */
const DD_SEED = [
  { subject: 'Information Collection', score: 78, weight: 45 },
  { subject: 'Risk Assessment', score: 65, weight: 25 },
  { subject: 'Mitigation Measures', score: 55, weight: 30 },
];

/* ── Seed compliance gaps ───────────────────────────────────────────────── */
const GAPS_SEED = [
  { ref: 'Art. 4(1)', description: 'Products must not contain or be made of deforestation-associated commodities', severity: 'critical', status: 'gap', action: 'Commission geo-referenced origin verification for all lots' },
  { ref: 'Art. 9(1)', description: 'Geolocation data required for all production plots', severity: 'high', status: 'gap', action: 'Implement GPS polygon data collection for primary suppliers' },
  { ref: 'Art. 6(1)', description: 'Due diligence system must be established and documented', severity: 'medium', status: 'partial', action: 'Document and formalise existing DD procedures' },
  { ref: 'Art. 8(1)', description: 'Risk assessment must cover all relevant information', severity: 'medium', status: 'partial', action: 'Expand country risk analysis to all sourcing countries' },
  { ref: 'Art. 10(1)', description: 'Mitigation measures required where non-negligible risk identified', severity: 'high', status: 'gap', action: 'Develop supplier improvement plans and audit schedule' },
  { ref: 'Art. 29', description: 'Country risk classification must be applied per Annex I', severity: 'low', status: 'met', action: 'Maintain current country monitoring process' },
  { ref: 'Art. 4(2)', description: 'Due diligence statement must be submitted before placing on market', severity: 'critical', status: 'gap', action: 'Set up DDS submission workflow in compliance system' },
];

/* ── Tab 1: Commodity Screening ────────────────────────────────────────── */
function CommodityScreening() {
  const [form, setForm] = useState({ commodity: 'cocoa', hs_codes: '1801.00, 1802.00, 1803.10' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/eudr/commodity-screening`, form);
      setResult(r.data);
    } catch {
      setResult(genScreeningResult(form.commodity, form.hs_codes));
    }
    setLoading(false);
  };

  const statusColor = s => ({ compliant: 'green', at_risk: 'amber', non_compliant: 'red' }[s] || 'gray');
  const tierColor = t => ({ high: 'red', standard: 'amber', low: 'green' }[t] || 'gray');

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Commodities Screened" value="7" sub="Annex I covered" />
        <KpiCard label="HS Codes Mapped" value="63" sub="Tariff classifications" />
        <KpiCard label="High Risk Countries" value="10" sub="Art. 29 Tier 1" color="text-red-600" />
        <KpiCard label="DDS Generated" value="12" sub="This quarter" color="text-emerald-600" />
      </div>

      <Section title="Commodity & HS Code Screening">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-3">
          <Sel label="Commodity (Annex I)" value={form.commodity} onChange={v => setForm(f => ({ ...f, commodity: v }))} options={[
            { value: 'cattle', label: 'Cattle' },
            { value: 'cocoa', label: 'Cocoa' },
            { value: 'coffee', label: 'Coffee' },
            { value: 'oil_palm', label: 'Oil Palm' },
            { value: 'rubber', label: 'Rubber' },
            { value: 'soy', label: 'Soy' },
            { value: 'wood', label: 'Wood' },
          ]} />
          <div className="sm:col-span-2">
            <Inp label="HS/CN Codes (comma-separated)" value={form.hs_codes} onChange={v => setForm(f => ({ ...f, hs_codes: v }))} />
          </div>
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Screening…' : 'Run Screening'}</Btn>
      </Section>

      {result && (
        <Section title="Screening Result">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-[10px] text-gray-500 uppercase mb-1">Commodity</p>
              <p className="text-sm font-semibold capitalize">{result.commodity?.replace('_', ' ')}</p>
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-[10px] text-gray-500 uppercase mb-1">Compliance Status</p>
              <Badge label={(result.compliance_status || '').replace('_', ' ')} color={statusColor(result.compliance_status)} />
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-[10px] text-gray-500 uppercase mb-1">Art. 29 Risk Tier</p>
              <Badge label={result.art29_risk_tier} color={tierColor(result.art29_risk_tier)} />
            </div>
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-[10px] text-gray-500 uppercase mb-1">Deforestation Risk</p>
              <p className={`text-lg font-bold font-mono ${result.deforestation_risk_score > 60 ? 'text-red-600' : 'text-amber-600'}`}>
                {result.deforestation_risk_score}/100
              </p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <p className="text-xs text-gray-500 mr-2">Matched HS codes: <span className="font-mono text-gray-800">{result.matched_hs_count}</span></p>
            <p className="text-xs text-gray-500 mr-2">Enforcement date: <span className="font-mono text-gray-800">{result.enforcement_date}</span></p>
            {(result.certification_schemes || []).map(s => <Badge key={s} label={s} color="green" />)}
          </div>
        </Section>
      )}
    </div>
  );
}

/* ── Tab 2: Country Risk ────────────────────────────────────────────────── */
function CountryRisk() {
  const [data, setData] = useState(COUNTRY_SEED);
  const [tierFilter, setTierFilter] = useState('all');

  useEffect(() => {
    axios.get(`${BASE}/eudr/ref/country-benchmarks`)
      .then(r => { if (r.data?.countries?.length) setData(r.data.countries); })
      .catch(() => {});
  }, []);

  const filtered = tierFilter === 'all' ? data : data.filter(d => d.tier === tierFilter);
  const tierColor = t => ({ high: '#ef4444', standard: '#f59e0b', low: '#10b981' }[t] || '#6b7280');
  const tierBadge = t => ({ high: 'red', standard: 'amber', low: 'green' }[t] || 'gray');

  const tierCounts = { high: data.filter(d => d.tier === 'high').length, standard: data.filter(d => d.tier === 'standard').length, low: data.filter(d => d.tier === 'low').length };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-3 gap-3">
        <KpiCard label="High Risk Countries" value={tierCounts.high} sub="Art. 29 — Enhanced DD required" color="text-red-600" />
        <KpiCard label="Standard Risk" value={tierCounts.standard} sub="Art. 29 — Standard DD" color="text-amber-600" />
        <KpiCard label="Low Risk" value={tierCounts.low} sub="Art. 29 — Simplified DD" color="text-emerald-600" />
      </div>

      <Section title="Country Risk Distribution — Art. 29">
        <div className="flex gap-2 mb-3">
          {['all', 'high', 'standard', 'low'].map(f => (
            <button
              key={f}
              onClick={() => setTierFilter(f)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${tierFilter === f ? 'bg-black text-white border-black' : 'border-gray-200 text-gray-600 hover:border-gray-400'}`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={filtered.slice(0, 25)} margin={{ left: 10, right: 20, top: 4, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="country" tick={{ fontSize: 9 }} angle={-40} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} label={{ value: 'Risk Score', angle: -90, position: 'insideLeft', style: { fontSize: 10 } }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n, p) => [`${v}`, `${p.payload.tier} tier`]} />
            <Bar dataKey="score" radius={[3, 3, 0, 0]}>
              {filtered.slice(0, 25).map((d, i) => <Cell key={i} fill={tierColor(d.tier)} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Country Reference Table">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['Country', 'Art. 29 Risk Tier', 'Risk Score', 'DD Requirement'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-2 font-medium text-gray-800">{row.country}</td>
                  <td className="py-2 px-2"><Badge label={row.tier} color={tierBadge(row.tier)} /></td>
                  <td className="py-2 px-2">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-100 rounded-full h-1.5">
                        <div style={{ width: `${row.score}%`, backgroundColor: tierColor(row.tier) }} className="h-1.5 rounded-full" />
                      </div>
                      <span className="font-mono">{row.score}</span>
                    </div>
                  </td>
                  <td className="py-2 px-2 text-gray-600">
                    {row.tier === 'high' ? 'Enhanced due diligence + audits' : row.tier === 'standard' ? 'Standard due diligence' : 'Simplified procedure'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 3: Due Diligence ───────────────────────────────────────────────── */
const DD_FORM_DEFAULT = {
  operator_id: 'OP-2024-001',
  commodity: 'cocoa',
  country_of_origin: 'Ghana',
  information_score: 78,
  risk_assessment_score: 65,
  mitigation_score: 55,
};

function DueDiligence() {
  const [form, setForm] = useState(DD_FORM_DEFAULT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const radarData = [
    { subject: 'Information (45%)', value: form.information_score },
    { subject: 'Risk Assessment (25%)', value: form.risk_assessment_score },
    { subject: 'Mitigation (30%)', value: form.mitigation_score },
  ];

  const compositeScore = Math.round(
    form.information_score * 0.45 +
    form.risk_assessment_score * 0.25 +
    form.mitigation_score * 0.30
  );

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/eudr/due-diligence`, form);
      setResult(r.data);
    } catch {
      setResult({ dd_score: compositeScore, status: compositeScore >= 70 ? 'adequate' : 'inadequate', components: DD_SEED });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <Section title="Due Diligence Assessment — Art. 8 Components">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
          <Inp label="Operator ID" value={form.operator_id} onChange={v => setForm(f => ({ ...f, operator_id: v }))} />
          <Sel label="Commodity" value={form.commodity} onChange={v => setForm(f => ({ ...f, commodity: v }))} options={[
            { value: 'cocoa', label: 'Cocoa' }, { value: 'coffee', label: 'Coffee' },
            { value: 'cattle', label: 'Cattle' }, { value: 'soy', label: 'Soy' },
            { value: 'wood', label: 'Wood' }, { value: 'oil_palm', label: 'Oil Palm' }, { value: 'rubber', label: 'Rubber' },
          ]} />
          <Inp label="Country of Origin" value={form.country_of_origin} onChange={v => setForm(f => ({ ...f, country_of_origin: v }))} />
        </div>
        <div className="grid grid-cols-3 gap-4 mb-4">
          {[
            { key: 'information_score', label: 'Information Collection', weight: '45%' },
            { key: 'risk_assessment_score', label: 'Risk Assessment', weight: '25%' },
            { key: 'mitigation_score', label: 'Mitigation Measures', weight: '30%' },
          ].map(({ key, label, weight }) => (
            <div key={key}>
              <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label} <span className="text-emerald-600">{weight}</span></label>
              <input
                type="range" min={0} max={100} value={form[key]}
                onChange={e => setForm(f => ({ ...f, [key]: Number(e.target.value) }))}
                className="w-full accent-emerald-500 mt-1"
              />
              <span className="text-xs font-mono text-gray-700">{form[key]}/100</span>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-4 mb-4">
          <div className="text-sm">
            <span className="text-gray-500 text-xs">Composite DD Score: </span>
            <span className={`text-2xl font-bold font-mono ${compositeScore >= 70 ? 'text-emerald-600' : compositeScore >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
              {compositeScore}
            </span>
            <span className="text-xs text-gray-500">/100</span>
          </div>
          <Badge label={compositeScore >= 70 ? 'Adequate' : compositeScore >= 50 ? 'Marginal' : 'Inadequate'} color={compositeScore >= 70 ? 'green' : compositeScore >= 50 ? 'amber' : 'red'} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Assessing…' : 'Run DD Assessment'}</Btn>
      </Section>

      <Section title="DD Component Radar">
        <ResponsiveContainer width="100%" height={280}>
          <RadarChart data={radarData} margin={{ top: 10, right: 40, bottom: 10, left: 40 }}>
            <PolarGrid stroke="rgba(0,0,0,0.08)" />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10 }} />
            <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
            <Radar dataKey="value" stroke="#10b981" fill="#10b981" fillOpacity={0.3} strokeWidth={2} />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 4: Compliance Gap ──────────────────────────────────────────────── */
function ComplianceGap() {
  const [gaps, setGaps] = useState(GAPS_SEED);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ operator_id: 'OP-2024-001', commodity: 'cocoa', jurisdiction: 'EU' });

  const analyse = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/eudr/compliance-gap`, form);
      if (r.data?.gaps?.length) setGaps(r.data.gaps);
    } catch {}
    setLoading(false);
  };

  const sevColor = s => ({ critical: 'red', high: 'red', medium: 'amber', low: 'green' }[s] || 'gray');
  const statColor = s => ({ gap: 'red', partial: 'amber', met: 'green' }[s] || 'gray');
  const open = gaps.filter(g => g.status !== 'met').length;

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Open Gaps" value={open} sub="Require remediation" color="text-red-600" />
        <KpiCard label="Critical Issues" value={gaps.filter(g => g.severity === 'critical').length} sub="Immediate action needed" color="text-red-600" />
        <KpiCard label="Partial Compliance" value={gaps.filter(g => g.status === 'partial').length} sub="In progress" color="text-amber-600" />
        <KpiCard label="Articles Met" value={gaps.filter(g => g.status === 'met').length} sub="Fully compliant" color="text-emerald-600" />
      </div>

      <Section title="Gap Analysis Parameters">
        <div className="grid grid-cols-3 gap-3 mb-3">
          <Inp label="Operator ID" value={form.operator_id} onChange={v => setForm(f => ({ ...f, operator_id: v }))} />
          <Sel label="Commodity" value={form.commodity} onChange={v => setForm(f => ({ ...f, commodity: v }))} options={[
            { value: 'cocoa', label: 'Cocoa' }, { value: 'coffee', label: 'Coffee' }, { value: 'cattle', label: 'Cattle' },
            { value: 'soy', label: 'Soy' }, { value: 'wood', label: 'Wood' },
          ]} />
          <Inp label="Jurisdiction" value={form.jurisdiction} onChange={v => setForm(f => ({ ...f, jurisdiction: v }))} />
        </div>
        <Btn onClick={analyse} disabled={loading}>{loading ? 'Analysing…' : 'Analyse Compliance Gaps'}</Btn>
      </Section>

      <Section title="EUDR Compliance Gap Register">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['Article Ref', 'Requirement Description', 'Severity', 'Status', 'Remediation Action'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {gaps.map((row, i) => (
                <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.status === 'gap' ? 'bg-red-50/20' : row.status === 'partial' ? 'bg-amber-50/20' : ''}`}>
                  <td className="py-2 px-2 font-mono font-semibold text-gray-700">{row.ref}</td>
                  <td className="py-2 px-2 text-gray-700 max-w-[220px]">{row.description}</td>
                  <td className="py-2 px-2"><Badge label={row.severity} color={sevColor(row.severity)} /></td>
                  <td className="py-2 px-2"><Badge label={row.status} color={statColor(row.status)} /></td>
                  <td className="py-2 px-2 text-gray-600">{row.action}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 5: DDS Generator ───────────────────────────────────────────────── */
function DDSGenerator() {
  const [form, setForm] = useState({
    operator_name: 'Acme Commodities GmbH',
    operator_id: 'OP-2024-001',
    commodity: 'cocoa',
    country_of_origin: 'Ghana',
    hs_code: '1801.00',
    quantity_kg: '5000',
    supplier_name: 'Kumasi Cocoa Cooperative',
    cutoff_date: '2020-12-31',
  });
  const [dds, setDds] = useState(null);
  const [loading, setLoading] = useState(false);

  const generate = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/eudr/due-diligence-statement`, form);
      setDds(r.data);
    } catch {
      setDds({
        reference_number: `DDS-EU-2024-${Math.floor(Math.random() * 90000 + 10000)}`,
        declaration_text: `In accordance with Article 4(2) of Regulation (EU) 2023/1115 (EUDR), the operator ${form.operator_name} hereby declares that the due diligence obligations set out in Chapter 2 of the Regulation have been fulfilled for the following product(s): ${form.commodity} (HS ${form.hs_code}), originating from ${form.country_of_origin}. The operator has collected all required information, carried out a risk assessment, and implemented adequate mitigation measures. The products covered by this statement do not contain or have been produced using commodities or products that have contributed to deforestation or forest degradation after ${form.cutoff_date}.`,
        issued_date: new Date().toISOString().split('T')[0],
        valid_until: `${new Date().getFullYear() + 1}-${new Date().toISOString().split('T')[0].slice(5)}`,
        cross_framework: ['CSRD ESRS E4 — Biodiversity', 'EU Taxonomy DNSH', 'GRI 304 — Biodiversity'],
        risk_classification: 'standard',
      });
    }
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <Section title="DDS Generation Form — Art. 4(2)">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <Inp label="Operator Name" value={form.operator_name} onChange={v => setForm(f => ({ ...f, operator_name: v }))} />
          <Inp label="Operator ID" value={form.operator_id} onChange={v => setForm(f => ({ ...f, operator_id: v }))} />
          <Sel label="Commodity" value={form.commodity} onChange={v => setForm(f => ({ ...f, commodity: v }))} options={[
            { value: 'cocoa', label: 'Cocoa' }, { value: 'coffee', label: 'Coffee' },
            { value: 'cattle', label: 'Cattle' }, { value: 'soy', label: 'Soy' },
            { value: 'wood', label: 'Wood' }, { value: 'oil_palm', label: 'Oil Palm' }, { value: 'rubber', label: 'Rubber' },
          ]} />
          <Inp label="Country of Origin" value={form.country_of_origin} onChange={v => setForm(f => ({ ...f, country_of_origin: v }))} />
          <Inp label="HS Code" value={form.hs_code} onChange={v => setForm(f => ({ ...f, hs_code: v }))} />
          <Inp label="Quantity (kg)" value={form.quantity_kg} onChange={v => setForm(f => ({ ...f, quantity_kg: v }))} type="number" />
          <Inp label="Supplier Name" value={form.supplier_name} onChange={v => setForm(f => ({ ...f, supplier_name: v }))} />
          <Inp label="Production Cutoff Date" value={form.cutoff_date} onChange={v => setForm(f => ({ ...f, cutoff_date: v }))} />
        </div>
        <Btn onClick={generate} disabled={loading}>{loading ? 'Generating DDS…' : 'Generate Due Diligence Statement'}</Btn>
      </Section>

      {dds && (
        <Section title="Generated Due Diligence Statement">
          <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex items-center gap-3 mb-3">
              <div>
                <p className="text-xs text-gray-500">Reference Number</p>
                <p className="font-mono font-bold text-emerald-700 text-sm">{dds.reference_number}</p>
              </div>
              <div className="ml-6">
                <p className="text-xs text-gray-500">Issue Date</p>
                <p className="font-mono text-sm text-gray-800">{dds.issued_date}</p>
              </div>
              <div className="ml-6">
                <p className="text-xs text-gray-500">Valid Until</p>
                <p className="font-mono text-sm text-gray-800">{dds.valid_until}</p>
              </div>
              <div className="ml-6">
                <p className="text-xs text-gray-500">Risk Class</p>
                <Badge label={dds.risk_classification} color={dds.risk_classification === 'low' ? 'green' : dds.risk_classification === 'high' ? 'red' : 'amber'} />
              </div>
            </div>
            <div className="bg-white border border-gray-200 rounded p-3 mb-3">
              <p className="text-xs text-gray-800 leading-relaxed">{dds.declaration_text}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="text-xs text-gray-500 mr-1">Cross-framework links:</span>
              {(dds.cross_framework || []).map(f => <Badge key={f} label={f} color="blue" />)}
            </div>
          </div>
        </Section>
      )}
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'screening', label: 'Commodity Screening' },
  { id: 'country', label: 'Country Risk' },
  { id: 'dd', label: 'Due Diligence' },
  { id: 'gap', label: 'Compliance Gap' },
  { id: 'dds', label: 'DDS Generator' },
];

export default function EUDRPage() {
  const [tab, setTab] = useState('screening');

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <DemoBanner />
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">EUDR Compliance</h1>
          <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">EUDR·Art4</span>
        </div>
        <p className="text-xs text-gray-500">EU Deforestation Regulation (EU) 2023/1115 — commodity screening, country risk, due diligence and DDS generation.</p>
      </div>

      <div className="flex gap-1 mb-5 border-b border-gray-200 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${tab === t.id ? 'border-emerald-500 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-800'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'screening' && <CommodityScreening />}
      {tab === 'country'   && <CountryRisk />}
      {tab === 'dd'        && <DueDiligence />}
      {tab === 'gap'       && <ComplianceGap />}
      {tab === 'dds'       && <DDSGenerator />}
    </div>
  );
}
