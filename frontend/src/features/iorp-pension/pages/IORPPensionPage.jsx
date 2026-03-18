/**
 * IORPPensionPage.jsx
 * Route: /iorp-pension
 *
 * IORP II Pension Climate Risk — EIOPA Stress Test · Art 28 ORA · ALM · SFDR FMP Classification
 *
 * Tab 1 — Stress Test         POST /api/v1/iorp-pension/assess
 * Tab 2 — ORA Checklist       GET  /api/v1/iorp-pension/ref/ora-checklist
 * Tab 3 — Funding Ratio       (derived from stress test result)
 * Tab 4 — SFDR Classification GET  /api/v1/iorp-pension/ref/sfdr-classes
 * Tab 5 — Framework Reference GET  /api/v1/iorp-pension/ref/frameworks
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend,
  AreaChart, Area, ReferenceLine,
  PieChart, Pie, Sector,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const BASE = `${API}/api/v1/iorp-pension`;
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111' };

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
    amber:  'bg-amber-50  text-amber-700  border-amber-200',
    red:    'bg-red-50    text-red-700    border-red-200',
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

function Inp({ label, value, onChange, type = 'text', readOnly = false }) {
  return (
    <div>
      <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        readOnly={readOnly}
        className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-emerald-500 bg-white disabled:bg-gray-50"
      />
    </div>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div>
      <label className="block text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="w-full border border-gray-200 rounded-md px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:ring-1 focus:ring-emerald-500 bg-white"
      >
        {options.map(o => (
          <option key={o.value} value={o.value}>{o.label}</option>
        ))}
      </select>
    </div>
  );
}

function Btn({ onClick, children, loading = false, variant = 'primary' }) {
  const base = 'px-4 py-2 rounded-md text-xs font-semibold transition-all focus:outline-none';
  const variants = {
    primary: 'bg-black text-white hover:bg-gray-800 disabled:opacity-50',
    secondary: 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50',
  };
  return (
    <button onClick={onClick} disabled={loading} className={`${base} ${variants[variant]}`}>
      {loading ? (
        <span className="flex items-center gap-1.5">
          <span className="w-3 h-3 border-2 border-gray-300 border-t-white rounded-full animate-spin" />
          Running…
        </span>
      ) : children}
    </button>
  );
}

/* ── Seed / fallback data ───────────────────────────────────────────────── */
const SEED_SCENARIOS = [
  { id: 'net_zero_2050',    label: 'Net Zero 2050',    pre: 111.1, post: 103.2 },
  { id: 'below_2c',         label: 'Below 2°C',        pre: 111.1, post: 97.5  },
  { id: 'hot_house_world',  label: 'Hot-House World',  pre: 111.1, post: 87.3  },
  { id: 'current_policies', label: 'Current Policies', pre: 111.1, post: 108.4 },
];

const SEED_ASSET_LOSSES = [
  { scenario: 'Net Zero 2050',    equity: -8.2,  sov_bonds: -2.1, corp_ig: -3.4, corp_hy: -9.8, real_estate: -5.1, infra: -4.3 },
  { scenario: 'Below 2°C',        equity: -12.5, sov_bonds: -3.0, corp_ig: -5.2, corp_hy: -14.2, real_estate: -8.3, infra: -6.1 },
  { scenario: 'Hot-House World',  equity: -22.4, sov_bonds: -4.8, corp_ig: -7.6, corp_hy: -21.5, real_estate: -14.7, infra: -9.8 },
  { scenario: 'Current Policies', equity: -4.1,  sov_bonds: -1.2, corp_ig: -1.8, corp_hy: -5.2, real_estate: -2.9, infra: -2.2 },
];

// Funding ratio over time for the area chart (seed data, per scenario)
function genFundingTimeSeries() {
  const years = [2024, 2026, 2028, 2030, 2035, 2040, 2050];
  return years.map((yr, i) => ({
    year: yr.toString(),
    net_zero:    parseFloat((111.1 - i * Math.sin(i * 0.9) * 1.2).toFixed(1)),
    below_2c:    parseFloat((111.1 - i * Math.sin(i * 1.1) * 2.1).toFixed(1)),
    hot_house:   parseFloat((111.1 - i * Math.sin(i * 1.3) * 3.5).toFixed(1)),
    cur_policies:parseFloat((111.1 - i * Math.sin(i * 0.7) * 0.6).toFixed(1)),
  }));
}

const SEED_LIABILITY_PIE = [
  { name: 'Duration Impact', value: 52 },
  { name: 'Longevity Risk',  value: 28 },
  { name: 'Inflation',       value: 20 },
];

const SEED_ORA_CHECKLIST = [
  { id: 'ORA-1',  title: 'Climate risk identified in risk register',         article: 'Art. 28(1)',   blocking: true,  status: 'met' },
  { id: 'ORA-2',  title: 'Board-level climate risk oversight established',   article: 'Art. 28(1)',   blocking: true,  status: 'met' },
  { id: 'ORA-3',  title: 'Climate scenario analysis conducted (short-term)', article: 'EIOPA 2022',   blocking: true,  status: 'met' },
  { id: 'ORA-4',  title: 'Long-term (>30yr) scenarios included',            article: 'EIOPA 2022',   blocking: false, status: 'gap' },
  { id: 'ORA-5',  title: 'Physical risk quantified in funding assessment',   article: 'Art. 28(2)',   blocking: true,  status: 'gap' },
  { id: 'ORA-6',  title: 'Transition risk quantified in asset allocation',   article: 'Art. 28(2)',   blocking: true,  status: 'met' },
  { id: 'ORA-7',  title: 'Sponsor covenant assessed under climate scenarios', article: 'Art. 28(3)', blocking: false, status: 'met' },
  { id: 'ORA-8',  title: 'Recovery plan trigger thresholds defined',         article: 'Art. 38',      blocking: true,  status: 'met' },
  { id: 'ORA-9',  title: 'Data quality limitations disclosed to regulator',  article: 'Art. 28(4)',   blocking: false, status: 'gap' },
  { id: 'ORA-10', title: 'Investment policy updated for climate constraints', article: 'Art. 19',     blocking: false, status: 'gap' },
  { id: 'ORA-11', title: 'SFDR FMP classification determined and reported',  article: 'SFDR Art. 6', blocking: true,  status: 'met' },
  { id: 'ORA-12', title: 'NZIF alignment strategy documented',               article: 'IIGCC NZIF',  blocking: false, status: 'gap' },
];

const SEED_SFDR_CLASSES = [
  {
    id: 'art_6', label: 'Article 6', subtitle: 'No sustainability claims',
    description: 'Fund integrates sustainability risks into its investment decisions but does not promote environmental or social characteristics.',
    requirements: ['Sustainability risk policy', 'Principal adverse impact disclosure (optional)', 'No specific ESG targets'],
    pai_required: false, periodic_report: false,
  },
  {
    id: 'art_8', label: 'Article 8', subtitle: 'Promotes E/S characteristics',
    description: 'Fund promotes environmental or social characteristics and the companies in which investments are made follow good governance practices.',
    requirements: ['PAI statement (mandatory if AUM > €500M)', 'Periodic sustainability report', 'Pre-contractual disclosure template', 'Good governance policy'],
    pai_required: true, periodic_report: true,
  },
  {
    id: 'art_9', label: 'Article 9', subtitle: 'Sustainable investment objective',
    description: 'Fund has sustainable investment as its objective — DNSH principle must apply and taxonomy alignment must be disclosed.',
    requirements: ['Full taxonomy alignment disclosure', 'DNSH for all investments', 'EU Climate Benchmark or equivalent', 'Enhanced periodic + pre-contractual reports'],
    pai_required: true, periodic_report: true,
  },
];

const SEED_FRAMEWORKS = [
  {
    id: 'IORP_II',
    name: 'IORP II Directive',
    articles: 'Arts 25, 28, 38, 46',
    description: 'EU Directive 2016/2341 — prudential framework for occupational pension funds. Art. 28 mandates climate risk in Own Risk Assessment.',
    tags: ['Climate ORA', 'Art. 28', 'Funding'],
  },
  {
    id: 'EIOPA_ST22',
    name: 'EIOPA Stress Test 2022',
    articles: 'Instantaneous + LT scenarios',
    description: 'EIOPA 2022 occupational pension fund climate stress test — 2 instantaneous (hot-house / disorderly) + 2 long-term (net-zero / delayed) scenarios.',
    tags: ['Stress Test', 'NGFS', '4 Scenarios'],
  },
  {
    id: 'SFDR_FMP',
    name: 'SFDR — IORPs as FMPs',
    articles: 'Arts 6, 8, 9, RTS Annexes',
    description: 'Sustainable Finance Disclosure Regulation — IORPs above €500M AUM qualify as financial market participants and must disclose sustainability characteristics.',
    tags: ['SFDR', 'PAI', 'Periodic Report'],
  },
  {
    id: 'IIGCC_NZIF',
    name: 'IIGCC Net Zero Investment Framework v2',
    articles: 'Pillars 1-4',
    description: 'Asset owner framework for Paris alignment: portfolio coverage, decarbonisation, engagement, and real economy alignment targets by 2050.',
    tags: ['Net Zero', 'Paris', 'Asset Owner'],
  },
  {
    id: 'TCFD',
    name: 'TCFD Recommendations',
    articles: 'Governance / Strategy / Risk / Metrics',
    description: 'Task Force on Climate-related Financial Disclosures — 11 recommendations across 4 pillars. Basis for ISSB S2, CSRD ESRS E1, and SFDR integration.',
    tags: ['Disclosure', 'Governance', 'Scenario'],
  },
];

/* ── Tab 1: Stress Test ─────────────────────────────────────────────────── */
const IORP_TYPES = [
  { value: 'defined_benefit',  label: 'Defined Benefit' },
  { value: 'defined_contribution', label: 'Defined Contribution' },
  { value: 'hybrid',           label: 'Hybrid' },
  { value: 'collective_dc',    label: 'Collective DC' },
];

const SCENARIO_OPTIONS = [
  { id: 'net_zero_2050',    label: 'Net Zero 2050' },
  { id: 'below_2c',         label: 'Below 2°C' },
  { id: 'hot_house_world',  label: 'Hot-House World' },
  { id: 'current_policies', label: 'Current Policies' },
];

function StressTestTab({ onResult }) {
  const [form, setForm] = useState({
    fund_name: 'NL Pension Fund Alpha',
    iorp_type: 'defined_benefit',
    total_assets: '1000000000',
    technical_provisions: '900000000',
    liability_duration: '18',
    equity_pct: '40',
    sov_bonds_pct: '25',
    corp_ig_pct: '20',
    corp_hy_pct: '5',
    real_estate_pct: '7',
    infra_pct: '3',
    sfdr_class: 'art_8',
  });
  const [scenarios, setScenarios] = useState(['net_zero_2050', 'below_2c', 'hot_house_world', 'current_policies']);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const f = (k) => (v) => setForm(p => ({ ...p, [k]: v }));

  const toggleScenario = (id) => {
    setScenarios(prev =>
      prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]
    );
  };

  const runStress = async () => {
    setLoading(true);
    try {
      const payload = {
        fund: {
          fund_name: form.fund_name,
          iorp_type: form.iorp_type,
          total_assets_eur: parseFloat(form.total_assets),
          technical_provisions_eur: parseFloat(form.technical_provisions),
          liability_duration_years: parseFloat(form.liability_duration),
          equity_pct: parseFloat(form.equity_pct),
          sovereign_bonds_pct: parseFloat(form.sov_bonds_pct),
          corp_ig_pct: parseFloat(form.corp_ig_pct),
          corp_hy_pct: parseFloat(form.corp_hy_pct),
          real_estate_pct: parseFloat(form.real_estate_pct),
          infrastructure_pct: parseFloat(form.infra_pct),
          sfdr_classification: form.sfdr_class,
        },
        scenarios,
      };
      const res = await axios.post(`${BASE}/assess`, payload);
      setResult(res.data);
      onResult && onResult(res.data);
    } catch {
      // Fallback to seed data
      const seedResult = {
        pre_funding_ratio_pct: 111.1,
        worst_post_funding_ratio_pct: 87.3,
        ora_compliance_status: 'partial',
        sfdr_classification: form.sfdr_class,
        scenarios: SEED_SCENARIOS.filter(s => scenarios.includes(s.id)),
        asset_losses: SEED_ASSET_LOSSES.filter(d =>
          scenarios.some(s => SEED_SCENARIOS.find(x => x.id === s)?.label === d.scenario)
        ),
        recovery_plan_triggered: true,
      };
      setResult(seedResult);
      onResult && onResult(seedResult);
    } finally {
      setLoading(false);
    }
  };

  // Auto-run on mount with defaults
  useEffect(() => { runStress(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const scenarioData = result?.scenarios ?? SEED_SCENARIOS;
  const assetLossData = result?.asset_losses ?? SEED_ASSET_LOSSES;

  return (
    <div className="space-y-4">
      {/* Form */}
      <Section title="Fund Parameters">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="sm:col-span-2">
            <Inp label="Fund Name" value={form.fund_name} onChange={f('fund_name')} />
          </div>
          <Sel label="IORP Type" value={form.iorp_type} onChange={f('iorp_type')} options={IORP_TYPES} />
          <Sel label="SFDR Classification" value={form.sfdr_class} onChange={f('sfdr_class')}
            options={[{value:'art_6',label:'Article 6'},{value:'art_8',label:'Article 8'},{value:'art_9',label:'Article 9'}]} />
          <Inp label="Total Assets (EUR)" value={form.total_assets} onChange={f('total_assets')} type="number" />
          <Inp label="Technical Provisions (EUR)" value={form.technical_provisions} onChange={f('technical_provisions')} type="number" />
          <Inp label="Liability Duration (years)" value={form.liability_duration} onChange={f('liability_duration')} type="number" />
        </div>
      </Section>

      <Section title="Asset Allocation (%)">
        <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
          <Inp label="Equity %" value={form.equity_pct} onChange={f('equity_pct')} type="number" />
          <Inp label="Sovereign Bonds %" value={form.sov_bonds_pct} onChange={f('sov_bonds_pct')} type="number" />
          <Inp label="Corp IG %" value={form.corp_ig_pct} onChange={f('corp_ig_pct')} type="number" />
          <Inp label="Corp HY %" value={form.corp_hy_pct} onChange={f('corp_hy_pct')} type="number" />
          <Inp label="Real Estate %" value={form.real_estate_pct} onChange={f('real_estate_pct')} type="number" />
          <Inp label="Infrastructure %" value={form.infra_pct} onChange={f('infra_pct')} type="number" />
        </div>
        <p className="text-[10px] text-gray-400 mt-2">
          Total: {[form.equity_pct, form.sov_bonds_pct, form.corp_ig_pct, form.corp_hy_pct, form.real_estate_pct, form.infra_pct]
            .reduce((a, v) => a + (parseFloat(v) || 0), 0).toFixed(0)}%
          {' '}(remainder allocated to cash/other)
        </p>
      </Section>

      <Section title="Climate Scenarios">
        <div className="flex flex-wrap gap-3 mb-3">
          {SCENARIO_OPTIONS.map(s => (
            <label key={s.id} className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={scenarios.includes(s.id)}
                onChange={() => toggleScenario(s.id)}
                className="accent-emerald-500"
              />
              {s.label}
            </label>
          ))}
        </div>
        <Btn onClick={runStress} loading={loading}>Run Stress Test</Btn>
      </Section>

      {result && (
        <>
          {/* Funding Ratios Bar Chart */}
          <Section title="Funding Ratio: Pre vs Post-Stress by Scenario">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={scenarioData} margin={{ left: 10, right: 20, top: 4, bottom: 40 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
                <XAxis dataKey="label" tick={{ fontSize: 9 }} angle={-15} textAnchor="end" interval={0} />
                <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 130]} />
                <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
                <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
                <Bar dataKey="pre" name="Pre-Stress" fill="#111" radius={[3, 3, 0, 0]} />
                <Bar dataKey="post" name="Post-Stress" radius={[3, 3, 0, 0]}>
                  {scenarioData.map((d, i) => (
                    <Cell key={i} fill={d.post < 90 ? '#ef4444' : d.post < 100 ? '#f59e0b' : '#10b981'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>

          {/* Scenario Table */}
          <Section title="Scenario Funding Ratio Table">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-200">
                  {['Scenario', 'Pre-Stress FR', 'Post-Stress FR', 'Change (pp)', 'Recovery Plan'].map(h => (
                    <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {scenarioData.map((s, i) => {
                  const change = (s.post - s.pre).toFixed(1);
                  const trigger = s.post < 100;
                  const rowBg = s.post < 90 ? 'bg-red-50/40' : s.post < 100 ? 'bg-amber-50/30' : 'bg-emerald-50/20';
                  return (
                    <tr key={i} className={`border-b border-gray-100 hover:brightness-95 ${rowBg}`}>
                      <td className="py-1.5 px-2 text-gray-700 font-medium">{s.label}</td>
                      <td className="py-1.5 px-2 font-mono text-gray-600">{s.pre}%</td>
                      <td className="py-1.5 px-2 font-mono font-semibold">
                        <span className={s.post < 90 ? 'text-red-600' : s.post < 100 ? 'text-amber-600' : 'text-emerald-600'}>
                          {s.post}%
                        </span>
                      </td>
                      <td className="py-1.5 px-2 font-mono text-red-600">{change}pp</td>
                      <td className="py-1.5 px-2">
                        <Badge label={trigger ? 'TRIGGERED' : 'Not Required'} color={trigger ? 'red' : 'green'} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p className="text-[10px] text-gray-400 mt-2">
              Row shading: red = FR &lt; 90% (severe), amber = FR 90–100% (recovery plan required), green = FR &gt; 100% (adequate).
            </p>
          </Section>
        </>
      )}
    </div>
  );
}

/* ── Tab 2: ORA Checklist ───────────────────────────────────────────────── */
function OraChecklistTab({ checklistData }) {
  const [items, setItems] = useState(
    (checklistData?.length ? checklistData : SEED_ORA_CHECKLIST).map(i => ({ ...i }))
  );

  const toggle = (id) => {
    setItems(prev =>
      prev.map(i => i.id === id ? { ...i, status: i.status === 'met' ? 'gap' : 'met' } : i)
    );
  };

  const metCount = items.filter(i => i.status === 'met').length;
  const blockingGaps = items.filter(i => i.status === 'gap' && i.blocking).length;
  const pct = Math.round((metCount / items.length) * 100);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">ORA Completeness</span>
          <div className="flex items-center gap-3">
            <span className="text-xs font-mono text-gray-600">{metCount} / {items.length} met ({pct}%)</span>
            {blockingGaps > 0 && (
              <span className="px-2 py-0.5 rounded border text-[10px] font-semibold bg-red-50 text-red-700 border-red-200">
                {blockingGaps} blocking gap{blockingGaps > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all ${pct >= 80 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-500' : 'bg-red-500'}`}
            style={{ width: `${pct}%` }}
          />
        </div>
      </div>

      <Section title="Art. 28 ORA Requirements (toggle to update)">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['', 'Item ID', 'Requirement', 'Article', 'Blocking', 'Status'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map(item => (
              <tr key={item.id}
                className={`border-b border-gray-100 hover:bg-gray-50 ${item.status === 'gap' && item.blocking ? 'bg-red-50/30' : ''}`}
              >
                <td className="py-1.5 px-2">
                  <input
                    type="checkbox"
                    checked={item.status === 'met'}
                    onChange={() => toggle(item.id)}
                    className="accent-emerald-500"
                  />
                </td>
                <td className="py-1.5 px-2 font-mono text-gray-500">{item.id}</td>
                <td className="py-1.5 px-2 text-gray-700">{item.title}</td>
                <td className="py-1.5 px-2 text-gray-500 whitespace-nowrap">{item.article}</td>
                <td className="py-1.5 px-2">
                  {item.blocking
                    ? <Badge label="Blocking" color="red" />
                    : <Badge label="Advisory" color="gray" />}
                </td>
                <td className="py-1.5 px-2">
                  <Badge label={item.status === 'met' ? 'Met' : 'Gap'} color={item.status === 'met' ? 'green' : 'red'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 3: Funding Ratio ───────────────────────────────────────────────── */
const PIE_COLORS = ['#10b981', '#f59e0b', '#6366f1'];

function FundingRatioTab() {
  const timeSeries = useMemo(() => genFundingTimeSeries(), []);

  return (
    <div className="space-y-4">
      {/* Recovery plan alert */}
      <div className="bg-red-50 border border-red-200 rounded-lg p-3 flex items-start gap-2">
        <span className="text-red-500 text-xs mt-0.5">&#9888;</span>
        <div>
          <p className="text-xs font-semibold text-red-700">Recovery Plan Trigger — Hot-House World Scenario</p>
          <p className="text-[11px] text-red-600 mt-0.5">
            Post-stress funding ratio falls to 87.3% under the hot-house world scenario, breaching the 100% threshold.
            IORP II Art. 38 recovery plan must be activated within 3 months.
          </p>
        </div>
      </div>

      <Section title="Projected Funding Ratio by Scenario (2024–2050)">
        <ResponsiveContainer width="100%" height={280}>
          <AreaChart data={timeSeries} margin={{ left: 0, right: 20, top: 8, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="%" domain={[70, 125]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <ReferenceLine y={100} stroke="#111" strokeDasharray="4 2" label={{ value: '100%', position: 'insideRight', fontSize: 9 }} />
            <ReferenceLine y={90}  stroke="#ef4444" strokeDasharray="4 2" label={{ value: '90% trigger', position: 'insideRight', fontSize: 9, fill: '#ef4444' }} />
            <Area type="monotone" dataKey="net_zero"     name="Net Zero 2050"    stroke="#10b981" fill="#10b981" fillOpacity={0.08} strokeWidth={1.5} dot={false} />
            <Area type="monotone" dataKey="cur_policies" name="Current Policies" stroke="#6366f1" fill="#6366f1" fillOpacity={0.08} strokeWidth={1.5} dot={false} />
            <Area type="monotone" dataKey="below_2c"    name="Below 2°C"        stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.08} strokeWidth={1.5} dot={false} />
            <Area type="monotone" dataKey="hot_house"   name="Hot-House World"  stroke="#ef4444" fill="#ef4444" fillOpacity={0.08} strokeWidth={1.5} dot={false} />
          </AreaChart>
        </ResponsiveContainer>
      </Section>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Section title="Liability Stress Breakdown">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={SEED_LIABILITY_PIE}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
                label={({ name, value }) => `${name}: ${value}%`}
                labelLine={false}
              >
                {SEED_LIABILITY_PIE.map((_, i) => (
                  <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
            </PieChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Sponsor Covenant Buffer">
          <div className="space-y-3">
            {[
              { label: 'Sponsor Credit Rating', value: 'BBB+', color: 'text-amber-600' },
              { label: 'Covenant Buffer (base)', value: '€45M', color: 'text-gray-800' },
              { label: 'Buffer — Net Zero 2050', value: '€38M', color: 'text-emerald-600' },
              { label: 'Buffer — Below 2°C', value: '€22M', color: 'text-amber-600' },
              { label: 'Buffer — Hot-House World', value: '−€12M', color: 'text-red-600' },
              { label: 'Buffer — Current Policies', value: '€41M', color: 'text-emerald-600' },
            ].map(({ label, value, color }) => (
              <div key={label} className="flex justify-between items-center border-b border-gray-100 pb-2">
                <span className="text-xs text-gray-600">{label}</span>
                <span className={`text-xs font-mono font-semibold ${color}`}>{value}</span>
              </div>
            ))}
          </div>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 4: SFDR Classification ─────────────────────────────────────────── */
function SFDRClassificationTab({ sfdrData, currentClass = 'art_8' }) {
  const classes = sfdrData?.length ? sfdrData : SEED_SFDR_CLASSES;
  const [selected, setSelected] = useState(currentClass);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {classes.map(c => {
          const isSelected = selected === c.id;
          return (
            <button
              key={c.id}
              onClick={() => setSelected(c.id)}
              className={`text-left p-4 rounded-lg border transition-all ${
                isSelected
                  ? 'border-emerald-500 bg-emerald-50 shadow-sm'
                  : 'border-gray-200 bg-white hover:border-gray-400'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className={`font-bold text-sm ${isSelected ? 'text-emerald-700' : 'text-gray-800'}`}>{c.label}</span>
                {isSelected && (
                  <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500 text-white">Current</span>
                )}
              </div>
              <p className="text-[11px] text-gray-500 font-medium mb-2">{c.subtitle}</p>
              <p className="text-[11px] text-gray-600 mb-3">{c.description}</p>
              <div className="space-y-1.5">
                {c.requirements.map((r, i) => (
                  <div key={i} className="flex items-start gap-1.5 text-[11px] text-gray-600">
                    <span className="text-emerald-500 mt-0.5">&#10003;</span>
                    {r}
                  </div>
                ))}
              </div>
              <div className="flex gap-2 mt-3 flex-wrap">
                <Badge
                  label={c.pai_required ? 'PAI Required' : 'PAI Optional'}
                  color={c.pai_required ? 'green' : 'gray'}
                />
                <Badge
                  label={c.periodic_report ? 'Periodic Report' : 'No Periodic Report'}
                  color={c.periodic_report ? 'blue' : 'gray'}
                />
              </div>
            </button>
          );
        })}
      </div>

      <Section title="Disclosure Requirements Summary">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {['Requirement', 'Art. 6', 'Art. 8', 'Art. 9'].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ['Sustainability risk integration', '✓', '✓', '✓'],
              ['Principal adverse impact statement', 'Optional', 'Required (>€500M)', 'Required'],
              ['Pre-contractual disclosure template', '—', 'Annex II', 'Annex III'],
              ['Periodic sustainability report', '—', 'Required', 'Required'],
              ['EU Taxonomy alignment disclosure', '—', 'Partial', 'Full'],
              ['DNSH principle application', '—', 'Partial', 'All investments'],
            ].map(([req, ...vals]) => (
              <tr key={req} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 text-gray-700">{req}</td>
                {vals.map((v, i) => (
                  <td key={i} className={`py-1.5 px-2 font-mono ${v === '—' ? 'text-gray-300' : 'text-gray-700'}`}>{v}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 5: Framework Reference ─────────────────────────────────────────── */
function FrameworkReferenceTab({ frameworkData }) {
  const frameworks = frameworkData?.length ? frameworkData : SEED_FRAMEWORKS;

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      {frameworks.map(fw => (
        <div key={fw.id} className="bg-white border border-gray-200 rounded-lg p-4">
          <div className="flex items-start justify-between mb-1.5">
            <span className="font-semibold text-sm text-gray-800">{fw.name}</span>
            <span className="font-mono text-[10px] text-gray-400 bg-gray-50 border border-gray-200 px-1.5 py-0.5 rounded">{fw.id}</span>
          </div>
          <p className="text-[11px] text-emerald-700 font-medium mb-2">{fw.articles}</p>
          <p className="text-[11px] text-gray-600 mb-3">{fw.description}</p>
          <div className="flex flex-wrap gap-1.5">
            {fw.tags.map(t => (
              <span key={t} className="px-1.5 py-0.5 rounded border border-gray-200 text-[10px] text-gray-500 bg-gray-50">{t}</span>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

/* ── TABS config ────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'stress',     label: 'Stress Test' },
  { id: 'ora',        label: 'ORA Checklist' },
  { id: 'funding',    label: 'Funding Ratio' },
  { id: 'sfdr',       label: 'SFDR Classification' },
  { id: 'frameworks', label: 'Framework Reference' },
];

/* ── Root component ─────────────────────────────────────────────────────── */
export default function IORPPensionPage() {
  const [tab, setTab] = useState('stress');
  const [stressResult, setStressResult] = useState(null);
  const [oraChecklist, setOraChecklist] = useState(null);
  const [sfdrClasses, setSfdrClasses] = useState(null);
  const [frameworks, setFrameworks] = useState(null);

  // KPI values (derived from seed until API responds)
  const pre  = stressResult?.pre_funding_ratio_pct  ?? 111.1;
  const post = stressResult?.worst_post_funding_ratio_pct ?? 87.3;
  const ora  = stressResult?.ora_compliance_status  ?? 'partial';
  const sfdr = stressResult?.sfdr_classification    ?? 'art_8';

  const oraColor  = ora === 'compliant' ? 'text-emerald-600' : ora === 'partial' ? 'text-amber-600' : 'text-red-600';
  const oraLabel  = { compliant: 'Compliant', partial: 'Partial', non_compliant: 'Non-Compliant' }[ora] ?? ora;
  const sfdrLabel = { art_6: 'Art. 6', art_8: 'Art. 8', art_9: 'Art. 9' }[sfdr] ?? sfdr;

  useEffect(() => {
    (async () => {
      try {
        const [cl, sc, fw] = await Promise.all([
          axios.get(`${BASE}/ref/ora-checklist`).catch(() => null),
          axios.get(`${BASE}/ref/sfdr-classes`).catch(() => null),
          axios.get(`${BASE}/ref/frameworks`).catch(() => null),
        ]);
        setOraChecklist(cl?.data?.checklist || null);
        setSfdrClasses(sc?.data?.classes || null);
        setFrameworks(fw?.data?.frameworks || null);
      } catch { /* use seed */ }
    })();
  }, []);

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo pension fund — IORP II Art. 28 ORA climate stress test with EIOPA 2022 scenarios and seed fallback data." />

      {/* Page header */}
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">IORP II Pension Climate Risk</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            EIOPA Stress Test 2022 · Art. 28 ORA · ALM · Funding Ratio · SFDR FMP Classification
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['IORP II', 'Art. 28', 'EIOPA 2022', 'SFDR FMP', 'NZIF v2'].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard
          label="Pre-Stress Funding Ratio"
          value={`${pre}%`}
          sub="Based on technical provisions"
          color="text-emerald-600"
        />
        <KpiCard
          label="Worst-Case Post-Stress FR"
          value={`${post}%`}
          sub="Hot-house world scenario"
          color={post < 100 ? 'text-red-600' : post < 110 ? 'text-amber-600' : 'text-emerald-600'}
        />
        <KpiCard
          label="ORA Compliance Status"
          value={oraLabel}
          sub="Art. 28 IORP II assessment"
          color={oraColor}
        />
        <KpiCard
          label="SFDR Classification"
          value={sfdrLabel}
          sub="Financial market participant"
          color="text-gray-900"
        />
      </div>

      {/* Tab bar */}
      <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
              tab === t.id ? 'bg-white text-gray-900 shadow-sm border border-gray-200' : 'text-gray-500 hover:text-gray-700'
            }`}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'stress'     && <StressTestTab onResult={setStressResult} />}
      {tab === 'ora'        && <OraChecklistTab checklistData={oraChecklist} />}
      {tab === 'funding'    && <FundingRatioTab />}
      {tab === 'sfdr'       && <SFDRClassificationTab sfdrData={sfdrClasses} currentClass={sfdr} />}
      {tab === 'frameworks' && <FrameworkReferenceTab frameworkData={frameworks} />}

      {/* Footer */}
      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p>
          <span className="font-semibold text-gray-500">Regulatory basis:</span>{' '}
          IORP II Directive 2016/2341 Art. 28 (ORA) · EIOPA 2022 Occupational Pensions Climate Stress Test ·
          SFDR Regulation (EU) 2019/2088 Arts 6/8/9 · IIGCC Net Zero Investment Framework v2 · TCFD Recommendations
        </p>
        <p>
          <span className="font-semibold text-gray-500">Scenarios:</span>{' '}
          Net Zero 2050 · Below 2°C · Hot-House World (physical risk) · Current Policies — aligned with NGFS Phase 4
        </p>
      </div>
    </div>
  );
}
