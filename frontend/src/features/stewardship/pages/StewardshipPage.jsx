/**
 * StewardshipPage.jsx
 * Route: /stewardship
 * Badge: GFANZ·E6
 *
 * Tab 1 — Portfolio Engagement   POST /api/v1/stewardship/portfolio
 * Tab 2 — Engagement Log         POST /api/v1/stewardship/engagement
 * Tab 3 — Proxy Votes            POST /api/v1/stewardship/proxy-votes
 * Tab 4 — Escalation Ladder      GET  /api/v1/stewardship/ref/escalation-framework
 * Tab 5 — Initiatives            (seed data, NZAMI/CA100+/UNPRI/NZIF/GFANZ)
 */
import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Legend, Cell,
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

/* ── Seed data generators ───────────────────────────────────────────────── */
function genPortfolioData() {
  const rng = mkRng(101);
  const companies = [
    'TotalEnergies SE', 'Volkswagen AG', 'HSBC Holdings', 'Shell plc',
    'Rio Tinto Group', 'Glencore plc', 'ArcelorMittal', 'Anglo American',
    'BHP Group', 'Unilever plc', 'Nestle SA', 'BP plc',
  ];
  const types = ['collaborative', 'direct', 'escalation'];
  const statuses = ['active', 'escalated', 'completed'];
  return companies.map(c => ({
    company: c,
    type: types[Math.floor(rng() * 3)],
    status: statuses[Math.floor(rng() * 3)],
    esgRisk: Math.round(30 + rng() * 65),
    engagements: Math.ceil(rng() * 12),
    lastContact: `2026-0${Math.ceil(rng() * 2)}-${String(Math.ceil(rng() * 28)).padStart(2, '0')}`,
  }));
}

function genEngagementLog() {
  const rng = mkRng(202);
  const cats = ['climate', 'governance', 'biodiversity', 'human-rights'];
  const actions = ['Schedule follow-up call', 'Send formal letter', 'Escalate to CEO level', 'Review progress report', 'Join collaborative initiative'];
  const companies = ['TotalEnergies SE', 'Shell plc', 'BHP Group', 'Volkswagen AG', 'HSBC Holdings', 'Glencore plc'];
  return Array.from({ length: 12 }, (_, i) => ({
    id: i + 1,
    company: companies[Math.floor(rng() * companies.length)],
    category: cats[Math.floor(rng() * 4)],
    escalationLevel: Math.ceil(rng() * 6),
    nextAction: actions[Math.floor(rng() * actions.length)],
    date: `2026-0${Math.ceil(rng() * 3)}-${String(Math.ceil(rng() * 28)).padStart(2, '0')}`,
    notes: 'Discussed Scope 3 reduction commitments and net zero pathway alignment.',
  }));
}

function genProxyVotes() {
  const rng = mkRng(303);
  const resolutions = [
    'Climate Transition Plan Approval', 'Board Director Re-election (Climate)',
    'Executive Pay ESG Linkage', 'Say-on-Climate Vote', 'Nature Risk Disclosure',
    'Supply Chain Due Diligence', 'Deforestation-Free Policy', 'TCFD Reporting',
    'Science-Based Target Adoption', 'Renewable Energy Transition',
  ];
  const rationales = [
    'Insufficient Paris alignment', 'Strong climate governance', 'Inadequate Scope 3 targets',
    'Good TCFD disclosure', 'Supports net zero commitment', 'Board lacks climate expertise',
  ];
  return resolutions.map((r, i) => ({
    resolution: r,
    company: ['Shell plc', 'BHP Group', 'TotalEnergies', 'Anglo American', 'Volkswagen AG'][Math.floor(rng() * 5)],
    vote: rng() > 0.4 ? 'For' : 'Against',
    mgmtRec: rng() > 0.5 ? 'For' : 'Against',
    rationale: rationales[Math.floor(rng() * rationales.length)],
    year: 2025 + Math.floor(rng() * 2),
  }));
}

/* ── Tab 1: Portfolio Engagement ───────────────────────────────────────── */
const PORTFOLIO_SEED = genPortfolioData();

function PortfolioEngagement() {
  const [data, setData] = useState(PORTFOLIO_SEED);
  const [loading, setLoading] = useState(false);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    setLoading(true);
    axios.post(`${BASE}/stewardship/portfolio`, { portfolio_id: 'DEMO_001' })
      .then(r => { if (r.data?.companies?.length) setData(r.data.companies); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const filtered = filter === 'all' ? data : data.filter(d => d.status === filter);

  const typeColor = t => ({ collaborative: 'blue', direct: 'green', escalation: 'red' }[t] || 'gray');
  const statusColor = s => ({ active: 'green', escalated: 'red', completed: 'gray' }[s] || 'gray');

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Engaged Companies" value={data.length} sub="Active stewardship" color="text-emerald-600" />
        <KpiCard label="Active Escalations" value={data.filter(d => d.status === 'escalated').length} sub="Requiring action" color="text-amber-600" />
        <KpiCard label="Collaborative" value={data.filter(d => d.type === 'collaborative').length} sub="Joint initiatives" />
        <KpiCard label="Avg ESG Risk" value={Math.round(data.reduce((a, b) => a + b.esgRisk, 0) / data.length)} sub="0-100 scale" color="text-red-600" />
      </div>

      <Section title="Portfolio Company Engagement Status">
        <div className="flex gap-2 mb-3">
          {['all', 'active', 'escalated', 'completed'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              className={`px-3 py-1 text-xs rounded-full border transition-colors ${filter === f ? 'bg-black text-white border-black' : 'border-gray-200 text-gray-600 hover:border-gray-400'}`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
        {loading && <p className="text-xs text-gray-400 py-4 text-center">Loading engagement data…</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['Company', 'Engagement Type', 'Status', 'ESG Risk', 'Engagements', 'Last Contact'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((row, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-2 font-medium text-gray-800">{row.company}</td>
                  <td className="py-2 px-2"><Badge label={row.type} color={typeColor(row.type)} /></td>
                  <td className="py-2 px-2"><Badge label={row.status} color={statusColor(row.status)} /></td>
                  <td className="py-2 px-2">
                    <div className="flex items-center gap-2">
                      <div className="w-16 bg-gray-100 rounded-full h-1.5">
                        <div className={`h-1.5 rounded-full ${row.esgRisk > 70 ? 'bg-red-500' : row.esgRisk > 50 ? 'bg-amber-500' : 'bg-emerald-500'}`} style={{ width: `${row.esgRisk}%` }} />
                      </div>
                      <span className="font-mono">{row.esgRisk}</span>
                    </div>
                  </td>
                  <td className="py-2 px-2 font-mono text-center">{row.engagements}</td>
                  <td className="py-2 px-2 text-gray-500 font-mono">{row.lastContact}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 2: Engagement Log ──────────────────────────────────────────────── */
const LOG_SEED = genEngagementLog();

function EngagementLog() {
  const [form, setForm] = useState({ company: 'Shell plc', category: 'climate', level: '3', action: 'Schedule follow-up call' });
  const [log, setLog] = useState(LOG_SEED);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/stewardship/engagement`, form);
      if (r.data?.entries?.length) setLog(r.data.entries);
    } catch {}
    setLoading(false);
  };

  const catColor = c => ({ climate: 'blue', governance: 'gray', biodiversity: 'green', 'human-rights': 'red' }[c] || 'gray');

  return (
    <div className="space-y-4">
      <Section title="Log New Engagement">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
          <Inp label="Company" value={form.company} onChange={v => setForm(f => ({ ...f, company: v }))} />
          <Sel label="Issue Category" value={form.category} onChange={v => setForm(f => ({ ...f, category: v }))} options={[
            { value: 'climate', label: 'Climate' },
            { value: 'governance', label: 'Governance' },
            { value: 'biodiversity', label: 'Biodiversity' },
            { value: 'human-rights', label: 'Human Rights' },
          ]} />
          <Sel label="Escalation Level" value={form.level} onChange={v => setForm(f => ({ ...f, level: v }))} options={[1,2,3,4,5,6].map(n => ({ value: String(n), label: `Level ${n}` }))} />
          <Inp label="Next Action" value={form.action} onChange={v => setForm(f => ({ ...f, action: v }))} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Logging…' : 'Log Engagement'}</Btn>
      </Section>

      <Section title="Engagement History">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['#', 'Company', 'Category', 'Level', 'Next Action', 'Date'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {log.map(row => (
                <tr key={row.id} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-2 font-mono text-gray-400">{row.id}</td>
                  <td className="py-2 px-2 font-medium text-gray-800">{row.company}</td>
                  <td className="py-2 px-2"><Badge label={row.category} color={catColor(row.category)} /></td>
                  <td className="py-2 px-2">
                    <span className={`font-mono font-bold ${row.escalationLevel >= 5 ? 'text-red-600' : row.escalationLevel >= 3 ? 'text-amber-600' : 'text-emerald-600'}`}>
                      L{row.escalationLevel}
                    </span>
                  </td>
                  <td className="py-2 px-2 text-gray-600">{row.nextAction}</td>
                  <td className="py-2 px-2 font-mono text-gray-500">{row.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 3: Proxy Votes ─────────────────────────────────────────────────── */
const VOTES_SEED = genProxyVotes();

function ProxyVotes() {
  const [votes, setVotes] = useState(VOTES_SEED);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setLoading(true);
    axios.post(`${BASE}/stewardship/proxy-votes`, { portfolio_id: 'DEMO_001', year: 2025 })
      .then(r => { if (r.data?.votes?.length) setVotes(r.data.votes); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const forCount = votes.filter(v => v.vote === 'For').length;
  const againstCount = votes.length - forCount;
  const withMgmt = votes.filter(v => v.vote === v.mgmtRec).length;

  const chartData = [
    { name: 'For Management', value: withMgmt, fill: '#10b981' },
    { name: 'Against Management', value: votes.length - withMgmt, fill: '#ef4444' },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Votes Cast" value={votes.length} sub="This proxy season" />
        <KpiCard label="For Resolutions" value={forCount} sub="Votes in favour" color="text-emerald-600" />
        <KpiCard label="Against Mgmt" value={votes.length - withMgmt} sub="Dissenting votes" color="text-red-600" />
        <KpiCard label="Mgmt Alignment" value={`${Math.round((withMgmt / votes.length) * 100)}%`} sub="With management rec." />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Section title="Vote Distribution">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={chartData} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                {chartData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Voting Summary by Category">
          <div className="space-y-2">
            {['climate', 'governance', 'social'].map(cat => {
              const catVotes = votes.filter((_, i) => i % 3 === ['climate', 'governance', 'social'].indexOf(cat));
              const catFor = catVotes.filter(v => v.vote === 'For').length;
              const pct = catVotes.length ? Math.round((catFor / catVotes.length) * 100) : 0;
              return (
                <div key={cat} className="flex items-center gap-3">
                  <span className="text-xs text-gray-600 w-24 capitalize">{cat}</span>
                  <div className="flex-1 bg-gray-100 rounded-full h-2">
                    <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${pct}%` }} />
                  </div>
                  <span className="text-xs font-mono text-gray-600 w-10 text-right">{pct}%</span>
                </div>
              );
            })}
          </div>
        </Section>
      </div>

      <Section title="Proxy Voting Record">
        {loading && <p className="text-xs text-gray-400 py-2 text-center">Loading votes…</p>}
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['Resolution', 'Company', 'Vote', 'Mgmt Rec.', 'Rationale', 'Year'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {votes.map((row, i) => (
                <tr key={i} className={`border-b border-gray-100 hover:bg-gray-50 ${row.vote !== row.mgmtRec ? 'bg-amber-50/20' : ''}`}>
                  <td className="py-2 px-2 text-gray-800">{row.resolution}</td>
                  <td className="py-2 px-2 text-gray-600">{row.company}</td>
                  <td className="py-2 px-2"><Badge label={row.vote} color={row.vote === 'For' ? 'green' : 'red'} /></td>
                  <td className="py-2 px-2"><Badge label={row.mgmtRec} color={row.mgmtRec === 'For' ? 'green' : 'amber'} /></td>
                  <td className="py-2 px-2 text-gray-500 max-w-[200px] truncate">{row.rationale}</td>
                  <td className="py-2 px-2 font-mono text-gray-500">{row.year}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 4: Escalation Ladder ───────────────────────────────────────────── */
const STEPS = [
  { level: 1, label: 'Monitor', desc: 'Track ESG metrics and flag concerns via regular screening', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  { level: 2, label: 'Dialogue', desc: 'Initiate informal discussion with investor relations team', color: 'bg-emerald-100 text-emerald-800 border-emerald-200' },
  { level: 3, label: 'Letter', desc: 'Send formal engagement letter to board / senior management', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  { level: 4, label: 'Meeting', desc: 'Schedule board-level meeting; escalate to Chair if required', color: 'bg-amber-100 text-amber-800 border-amber-200' },
  { level: 5, label: 'Collective', desc: 'Join or lead collaborative engagement (CA100+, NZAMI)', color: 'bg-orange-100 text-orange-800 border-orange-200' },
  { level: 6, label: 'Divest', desc: 'Last resort — reduce/exit position and public communication', color: 'bg-red-100 text-red-800 border-red-200' },
];

const rng303 = mkRng(404);
const ENTITY_PROGRESS = ['TotalEnergies SE', 'Volkswagen AG', 'Glencore plc', 'BHP Group'].map(e => ({
  company: e,
  level: Math.ceil(rng303() * 6),
}));

function EscalationLadder() {
  const [framework, setFramework] = useState(null);

  useEffect(() => {
    axios.get(`${BASE}/stewardship/ref/escalation-framework`)
      .then(r => { if (r.data) setFramework(r.data); })
      .catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <Section title="GFANZ E6 Escalation Framework — 6-Step Ladder">
        <div className="space-y-3">
          {STEPS.map(step => (
            <div key={step.level} className={`flex items-start gap-3 p-3 rounded-lg border ${step.color}`}>
              <div className="w-8 h-8 rounded-full bg-white/70 flex items-center justify-center font-bold text-sm shrink-0 shadow-sm">
                {step.level}
              </div>
              <div>
                <p className="font-semibold text-sm">{step.label}</p>
                <p className="text-xs mt-0.5 opacity-80">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section title="Portfolio Escalation Positions">
        <div className="space-y-3">
          {ENTITY_PROGRESS.map(e => (
            <div key={e.company} className="flex items-center gap-3">
              <span className="text-xs text-gray-700 font-medium w-40 truncate">{e.company}</span>
              <div className="flex gap-1 flex-1">
                {STEPS.map(s => (
                  <div
                    key={s.level}
                    className={`flex-1 h-5 rounded text-[9px] font-bold flex items-center justify-center transition-all ${e.level >= s.level ? (s.level <= 2 ? 'bg-emerald-500 text-white' : s.level <= 4 ? 'bg-amber-500 text-white' : 'bg-red-500 text-white') : 'bg-gray-100 text-gray-400'}`}
                  >
                    {s.level}
                  </div>
                ))}
              </div>
              <Badge label={STEPS[e.level - 1]?.label} color={e.level <= 2 ? 'green' : e.level <= 4 ? 'amber' : 'red'} />
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 5: Initiatives ─────────────────────────────────────────────────── */
const INITIATIVES = [
  {
    name: 'Net Zero Asset Managers Initiative',
    abbr: 'NZAMI',
    description: 'Commitment to support investing aligned with net zero by 2050 or sooner; interim targets set.',
    members: 325,
    aum: '$57.5T',
    status: 'Active Member',
    commitment: 'High',
    color: 'bg-emerald-50 border-emerald-200',
  },
  {
    name: 'Climate Action 100+',
    abbr: 'CA100+',
    description: 'Investor-led initiative ensuring the world\'s largest GHG emitters take necessary climate action.',
    members: 700,
    aum: '$68T',
    status: 'Lead Investor',
    commitment: 'High',
    color: 'bg-blue-50 border-blue-200',
  },
  {
    name: 'UN Principles for Responsible Investment',
    abbr: 'UNPRI',
    description: 'Six principles for incorporating ESG into investment analysis and ownership practices.',
    members: 5300,
    aum: '$121T',
    status: 'Signatory',
    commitment: 'Medium',
    color: 'bg-purple-50 border-purple-200',
  },
  {
    name: 'Net Zero Investment Framework',
    abbr: 'NZIF',
    description: 'Paris Aligned Investment Initiative framework for investors to set net zero targets and act.',
    members: 90,
    aum: '$33T',
    status: 'Aligned',
    commitment: 'High',
    color: 'bg-teal-50 border-teal-200',
  },
  {
    name: 'Glasgow Financial Alliance for Net Zero',
    abbr: 'GFANZ',
    description: 'Coalition of leading financial institutions committed to accelerating net zero transition.',
    members: 650,
    aum: '$150T',
    status: 'Member',
    commitment: 'High',
    color: 'bg-amber-50 border-amber-200',
  },
];

function Initiatives() {
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="GFANZ Alignment" value="87%" sub="E6 criteria met" color="text-emerald-600" />
        <KpiCard label="Initiatives" value={INITIATIVES.length} sub="Collaborative programs" />
        <KpiCard label="Lead Engagements" value="3" sub="Investor-led roles" color="text-blue-600" />
        <KpiCard label="Coverage AUM" value="$150T" sub="Combined AUM in GFANZ" />
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {INITIATIVES.map(ini => (
          <div key={ini.abbr} className={`rounded-lg border p-4 ${ini.color}`}>
            <div className="flex items-start justify-between mb-2">
              <div>
                <p className="text-xs font-mono font-bold text-gray-700">{ini.abbr}</p>
                <p className="text-sm font-semibold text-gray-900 mt-0.5 leading-tight">{ini.name}</p>
              </div>
              <Badge label={ini.status} color={ini.commitment === 'High' ? 'green' : 'amber'} />
            </div>
            <p className="text-xs text-gray-600 mb-3 leading-relaxed">{ini.description}</p>
            <div className="flex gap-4 text-xs text-gray-600">
              <span><span className="font-semibold text-gray-900">{ini.members.toLocaleString()}</span> members</span>
              <span><span className="font-semibold text-gray-900">{ini.aum}</span> AUM</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'portfolio', label: 'Portfolio Engagement' },
  { id: 'log', label: 'Engagement Log' },
  { id: 'votes', label: 'Proxy Votes' },
  { id: 'ladder', label: 'Escalation Ladder' },
  { id: 'initiatives', label: 'Initiatives' },
];

export default function StewardshipPage() {
  const [tab, setTab] = useState('portfolio');

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <DemoBanner />
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">Stewardship & Engagement</h1>
          <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">GFANZ·E6</span>
        </div>
        <p className="text-xs text-gray-500">Portfolio engagement, escalation ladder, proxy voting and collaborative stewardship initiatives.</p>
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

      {tab === 'portfolio'    && <PortfolioEngagement />}
      {tab === 'log'          && <EngagementLog />}
      {tab === 'votes'        && <ProxyVotes />}
      {tab === 'ladder'       && <EscalationLadder />}
      {tab === 'initiatives'  && <Initiatives />}
    </div>
  );
}
