/**
 * CDPPage.jsx
 * Route: /cdp-scoring
 *
 * CDP Climate & Water Scoring
 *
 * Tab 1 — Climate Scoring    POST /api/v1/cdp/climate/assess
 * Tab 2 — Water Scoring      POST /api/v1/cdp/water/assess
 * Tab 3 — Score Breakdown    (derived from assessment)
 * Tab 4 — Activity Groups    (seed data — 12 activity groups)
 * Tab 5 — Comparison         (seed data — current vs sector vs A-list)
 */
import React, { useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111' };

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
    amber:  'bg-amber-50  text-amber-700  border-amber-200',
    red:    'bg-red-50    text-red-700    border-red-200',
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return (
    <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>
  );
}

function Inp({ label, value, onChange, type = 'text' }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-gray-400 bg-white"
      />
    </div>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider font-medium">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-gray-400 bg-white"
      >
        {options.map(o => <option key={o} value={o}>{o}</option>)}
      </select>
    </div>
  );
}

function Btn({ children, onClick, loading }) {
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className="px-4 py-2 bg-black text-white text-xs font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors"
    >
      {loading ? 'Running…' : children}
    </button>
  );
}

/* ── Seed data ──────────────────────────────────────────────────────────── */
const CLIMATE_MODULES = [
  'Governance', 'Risks & Opps', 'Business Strategy', 'Targets & Initiatives',
  'Emissions Methodology', 'Scope 1', 'Scope 2', 'Scope 3',
  'Energy', 'Carbon Pricing', 'Engagement', 'Verification',
  'Sequestration', 'Stranded Assets', 'TCFD Alignment',
];

const WATER_MODULES = [
  'Water Security', 'Governance', 'Business Impact', 'Accounting',
  'Risk', 'Opportunity', 'Watershed', 'Supply Chain', 'Verification',
];

const ACTIVITY_GROUPS = [
  { name: 'Power Generation', ghg: 512, risk: 'High' },
  { name: 'Oil & Gas',        ghg: 845, risk: 'Critical' },
  { name: 'Coal',             ghg: 1240, risk: 'Critical' },
  { name: 'Cement',           ghg: 620, risk: 'High' },
  { name: 'Steel',            ghg: 780, risk: 'High' },
  { name: 'Chemicals',        ghg: 430, risk: 'Medium' },
  { name: 'Transport',        ghg: 290, risk: 'Medium' },
  { name: 'Buildings',        ghg: 180, risk: 'Medium' },
  { name: 'Agriculture',      ghg: 340, risk: 'High' },
  { name: 'Finance',          ghg: 95,  risk: 'Low' },
  { name: 'Services',         ghg: 45,  risk: 'Low' },
  { name: 'Retail',           ghg: 65,  risk: 'Low' },
];

const GRADE_COLOR = {
  'A':  'text-emerald-600', 'A-': 'text-emerald-500',
  'B':  'text-blue-600',    'B-': 'text-blue-500',
  'C':  'text-amber-600',   'D':  'text-red-500',  'D-': 'text-red-600',
};
const RISK_COLOR = {
  'Critical': 'red', 'High': 'amber', 'Medium': 'gray', 'Low': 'green',
};

function letterGrade(score) {
  if (score >= 90) return 'A';
  if (score >= 80) return 'A-';
  if (score >= 70) return 'B';
  if (score >= 60) return 'B-';
  if (score >= 50) return 'C';
  if (score >= 35) return 'D';
  return 'D-';
}

function genClimateData() {
  const rng = mkRng(7777);
  const weights = [8,7,7,8,6,7,6,5,5,5,4,4,4,3,6];
  const scores = CLIMATE_MODULES.map((m, i) => ({
    module: m,
    score: Math.round(55 + rng() * 35),
    weight: weights[i],
    full: 100,
  }));
  scores.forEach(s => { s.contribution = parseFloat(((s.score * s.weight) / 100).toFixed(1)); });
  const total = scores.reduce((a, b) => a + b.contribution, 0) / scores.reduce((a, b) => a + b.weight, 0) * 100;
  return { scores, total: Math.round(total) };
}

function genWaterData() {
  const rng = mkRng(8888);
  return WATER_MODULES.map(m => ({ module: m, score: Math.round(45 + rng() * 45) }));
}

function genComparisonData() {
  const rng = mkRng(9999);
  return CLIMATE_MODULES.slice(0, 8).map(m => ({
    module: m.length > 10 ? m.slice(0, 10) : m,
    current: Math.round(55 + rng() * 30),
    sectorMedian: Math.round(45 + rng() * 25),
    aListAvg: Math.round(82 + rng() * 12),
  }));
}

/* ── Tab 1: Climate Scoring ─────────────────────────────────────────────── */
function ClimateScoring() {
  const [company, setCompany] = useState('Apex Energy Corp');
  const [sector, setSector] = useState('Power Generation');
  const [revenue, setRevenue] = useState('2500');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seedData = useMemo(() => genClimateData(), []);
  const data = result || seedData;

  const radarData = data.scores.map(s => ({ subject: s.module.slice(0, 8), score: s.score, full: 100 }));

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/cdp/climate/assess`, {
        company_name: company, sector, annual_revenue_musd: parseFloat(revenue),
      });
      setResult(res.data);
    } catch { setResult(seedData); }
    finally { setLoading(false); }
  }

  const grade = letterGrade(data.total);

  return (
    <div className="space-y-4">
      <Section title="Entity Parameters">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
          <Inp label="Company Name" value={company} onChange={setCompany} />
          <Sel label="Sector" value={sector} onChange={setSector} options={ACTIVITY_GROUPS.map(a => a.name)} />
          <Inp label="Annual Revenue (M USD)" value={revenue} onChange={setRevenue} type="number" />
          <div className="flex items-end">
            <Btn onClick={handleRun} loading={loading}>Run CDP Climate Assessment</Btn>
          </div>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Climate Score" value={grade} sub="CDP letter grade"
          color={GRADE_COLOR[grade] || 'text-gray-700'} />
        <KpiCard label="Disclosure %" value={`${data.total ?? 62}%`} sub="Overall disclosure level"
          color={data.total >= 70 ? 'text-emerald-600' : data.total >= 50 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Awareness %" value={`${Math.min(100, (data.total ?? 62) + 8)}%`} sub="Awareness level" color="text-blue-600" />
        <KpiCard label="Management %" value={`${Math.max(0, (data.total ?? 62) - 12)}%`} sub="Management level" color="text-gray-700" />
      </div>

      <Section title="CDP Module Radar — 15 Climate Modules">
        <ResponsiveContainer width="100%" height={340}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="rgba(0,0,0,0.08)" />
            <PolarAngleAxis dataKey="subject" tick={{ fontSize: 9, fill: '#6b7280' }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 8 }} />
            <Radar name="Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.25} strokeWidth={1.5} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 2: Water Scoring ───────────────────────────────────────────────── */
function WaterScoring() {
  const [company, setCompany] = useState('Apex Energy Corp');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const seedData = useMemo(() => genWaterData(), []);
  const data = result || seedData;

  async function handleRun() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/cdp/water/assess`, { company_name: company });
      setResult(res.data?.modules || null);
    } catch { setResult(seedData); }
    finally { setLoading(false); }
  }

  const avg = Math.round(data.reduce((a, b) => a + b.score, 0) / data.length);
  const grade = letterGrade(avg);

  return (
    <div className="space-y-4">
      <Section title="Entity Parameters">
        <div className="flex gap-3 items-end flex-wrap">
          <div className="w-64"><Inp label="Company Name" value={company} onChange={setCompany} /></div>
          <Btn onClick={handleRun} loading={loading}>Run CDP Water Assessment</Btn>
        </div>
      </Section>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Water Score" value={grade} sub="CDP water letter grade"
          color={GRADE_COLOR[grade] || 'text-gray-700'} />
        <KpiCard label="Avg Module Score" value={`${avg}/100`} sub="9 water modules"
          color={avg >= 70 ? 'text-emerald-600' : avg >= 50 ? 'text-amber-600' : 'text-red-600'} />
        <KpiCard label="Top Module" value={data.reduce((a, b) => a.score > b.score ? a : b).module.slice(0, 10)}
          sub="Highest scoring" color="text-emerald-600" />
        <KpiCard label="Gap Module" value={data.reduce((a, b) => a.score < b.score ? a : b).module.slice(0, 10)}
          sub="Lowest scoring" color="text-red-600" />
      </div>

      <Section title="Water Module Scores — 9 Modules">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={data} margin={{ left: 10, right: 20, top: 4, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="module" tick={{ fontSize: 9 }} angle={-35} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Bar dataKey="score" name="Score" radius={[3, 3, 0, 0]}>
              {data.map((d, i) => (
                <Cell key={i} fill={d.score >= 70 ? '#10b981' : d.score >= 50 ? '#f59e0b' : '#ef4444'} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 3: Score Breakdown ─────────────────────────────────────────────── */
function ScoreBreakdown() {
  const data = useMemo(() => genClimateData(), []);
  const sorted = [...data.scores].sort((a, b) => b.contribution - a.contribution);

  return (
    <Section title="Module Score Breakdown — Sorted by Weighted Contribution">
      <table className="w-full text-xs">
        <thead>
          <tr className="border-b border-gray-200">
            {['Module', 'Score (0-100)', 'Weight (%)', 'Weighted Contribution', 'Grade'].map(h => (
              <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {sorted.map((row, i) => {
            const grade = letterGrade(row.score);
            return (
              <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2 font-medium text-gray-700">{row.module}</td>
                <td className="py-1.5 px-2 font-mono">
                  <div className="flex items-center gap-2">
                    <span>{row.score}</span>
                    <div className="w-20 bg-gray-100 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-emerald-500" style={{ width: `${row.score}%` }} />
                    </div>
                  </div>
                </td>
                <td className="py-1.5 px-2 font-mono text-gray-500">{row.weight}%</td>
                <td className="py-1.5 px-2 font-mono font-semibold">{row.contribution}</td>
                <td className="py-1.5 px-2">
                  <span className={`font-bold font-mono ${GRADE_COLOR[grade] || 'text-gray-600'}`}>{grade}</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
      <p className="text-[10px] text-gray-400 mt-3">
        Weighted contribution = (score × weight) / 100. Sorted descending by contribution.
      </p>
    </Section>
  );
}

/* ── Tab 4: Activity Groups ─────────────────────────────────────────────── */
function ActivityGroups() {
  return (
    <div className="space-y-4">
      <Section title="12 CDP Activity Groups — GHG Intensity & Risk Level">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {ACTIVITY_GROUPS.map((ag, i) => (
            <div key={i} className="border border-gray-200 rounded-lg p-3 bg-white hover:shadow-sm transition-shadow">
              <p className="text-xs font-semibold text-gray-800 mb-2">{ag.name}</p>
              <div className="space-y-1.5">
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-gray-500">GHG Intensity</span>
                  <span className="text-[10px] font-mono font-semibold text-gray-700">{ag.ghg} tCO2e/M€</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-[10px] text-gray-500">Risk Level</span>
                  <Badge label={ag.risk} color={RISK_COLOR[ag.risk]} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 5: Comparison ──────────────────────────────────────────────────── */
function Comparison() {
  const data = useMemo(() => genComparisonData(), []);

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <KpiCard label="vs. Sector Median" value="+8.4 pts" sub="Current entity outperforms" color="text-emerald-600" />
        <KpiCard label="vs. A-List Avg" value="-19.2 pts" sub="Gap to A-list average" color="text-red-600" />
        <KpiCard label="Global Percentile" value="62nd" sub="Among disclosed companies" color="text-blue-600" />
      </div>

      <Section title="CDP Score Comparison: Current Entity vs Sector Median vs Global A-List Average">
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ left: 10, right: 20, top: 4, bottom: 50 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="module" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} domain={[0, 100]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="current" name="Current Entity" fill="#111" radius={[2, 2, 0, 0]} />
            <Bar dataKey="sectorMedian" name="Sector Median" fill="#9ca3af" radius={[2, 2, 0, 0]} />
            <Bar dataKey="aListAvg" name="A-List Average" fill="#10b981" radius={[2, 2, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>

        <div className="mt-4 grid grid-cols-3 gap-3">
          {data.slice(0, 3).map((d, i) => (
            <div key={i} className="bg-gray-50 rounded p-2 text-xs">
              <p className="font-medium text-gray-700 mb-1">{d.module}</p>
              <div className="space-y-0.5">
                <div className="flex justify-between">
                  <span className="text-gray-500">Current</span>
                  <span className="font-mono font-semibold">{d.current}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">Sector</span>
                  <span className="font-mono text-gray-500">{d.sectorMedian}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">A-List</span>
                  <span className="font-mono text-emerald-600">{d.aListAvg}</span>
                </div>
                <div className={`text-[10px] font-semibold mt-1 ${d.current >= d.sectorMedian ? 'text-emerald-600' : 'text-red-600'}`}>
                  {d.current >= d.sectorMedian ? '+' : ''}{d.current - d.sectorMedian} vs sector
                </div>
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── TABS ───────────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'climate',    label: 'Climate Scoring' },
  { id: 'water',      label: 'Water Scoring' },
  { id: 'breakdown',  label: 'Score Breakdown' },
  { id: 'activity',   label: 'Activity Groups' },
  { id: 'comparison', label: 'Comparison' },
];

/* ── Root ───────────────────────────────────────────────────────────────── */
export default function CDPPage() {
  const [tab, setTab] = useState('climate');

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <DemoBanner message="Demo entity — CDP Climate & Water scoring with seed fallback data. Seed defaults: Apex Energy Corp, Power Generation, B- grade." />

      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">CDP Climate & Water Scoring</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            CDP Questionnaire 2023 · Climate Change + Water Security · 15 climate modules · 9 water modules
          </p>
        </div>
        <div className="flex gap-1.5 flex-wrap">
          {['CDP 2023', 'A-List', 'TCFD Aligned', 'Paris Aligned'].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

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

      {tab === 'climate'    && <ClimateScoring />}
      {tab === 'water'      && <WaterScoring />}
      {tab === 'breakdown'  && <ScoreBreakdown />}
      {tab === 'activity'   && <ActivityGroups />}
      {tab === 'comparison' && <Comparison />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">Scoring basis:</span> CDP Climate Change Questionnaire 2023 · CDP Water Security Questionnaire 2023 · Letter grades A/A-/B/B-/C/D/D- · A-list = score &ge;90</p>
        <p><span className="font-semibold text-gray-500">Modules:</span> 15 climate modules · 9 water security modules · Activity group GHG intensities are indicative sector averages (tCO2e per M€ revenue)</p>
      </div>
    </div>
  );
}
