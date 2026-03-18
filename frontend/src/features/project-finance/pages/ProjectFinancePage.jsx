/**
 * ProjectFinancePage.jsx
 * Route: /project-finance
 *
 * Project Finance & Blended Finance hub.
 * Tabs:
 *   1. Project Finance  — DSCR / LLCR / IRR / PPA modelling for renewable projects
 *   2. Blended Finance  — DFI / MDB concessional tranche structuring
 *   3. Green Bonds      — ICMA GBP / EU GBS alignment calculator
 *   4. DSCR Sensitivity — Sensitivity waterfall & covenant headroom
 */
import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell,
} from 'recharts';
import {
  Zap, Layers, Leaf, BarChart2, RefreshCw, Info, TrendingUp,
} from 'lucide-react';
import DemoBanner from '../../../components/shared/DemoBanner';
import ProjectFinancePanel from '../ProjectFinancePanel';
import { BlendedFinancePanel } from '../BlendedFinancePanel';

// ── Seed RNG ──────────────────────────────────────────────────────────────
function seededRand(seed) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 4294967296; };
}

// ── Primitives ────────────────────────────────────────────────────────────
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

function KpiCard({ label, value, sub, accent }) {
  const accentCls = accent === 'green' ? 'text-emerald-600' : accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="text-[10px] font-semibold uppercase tracking-wider text-gray-400 mb-1">{label}</div>
      <div className={`text-2xl font-bold font-mono ${accentCls}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

const TABS = [
  { id: 'pf', label: 'Project Finance', icon: Zap },
  { id: 'blended', label: 'Blended Finance', icon: Layers },
  { id: 'green_bonds', label: 'Green Bond Alignment', icon: Leaf },
  { id: 'sensitivity', label: 'DSCR Sensitivity', icon: BarChart2 },
];

// ── Green Bond Alignment Tab ───────────────────────────────────────────────
const GB_PRINCIPLES = [
  { id: 'use_of_proceeds', label: 'Use of Proceeds', weight: 0.30, icma: true, eugbs: true },
  { id: 'project_evaluation', label: 'Project Evaluation & Selection', weight: 0.20, icma: true, eugbs: true },
  { id: 'management_proceeds', label: 'Management of Proceeds', weight: 0.20, icma: true, eugbs: true },
  { id: 'reporting', label: 'Reporting & Disclosure', weight: 0.15, icma: true, eugbs: true },
  { id: 'taxonomy_alignment', label: 'EU Taxonomy Alignment', weight: 0.10, icma: false, eugbs: true },
  { id: 'dnsh', label: 'Do No Significant Harm (DNSH)', weight: 0.05, icma: false, eugbs: true },
];

function GreenBondTab() {
  const [scores, setScores] = useState({ use_of_proceeds: 85, project_evaluation: 70, management_proceeds: 90, reporting: 65, taxonomy_alignment: 55, dnsh: 60 });
  const [framework, setFramework] = useState('EUGBS');

  const applicablePrinciples = GB_PRINCIPLES.filter(p => framework === 'ICMA' ? p.icma : p.eugbs);
  const totalWeight = applicablePrinciples.reduce((s, p) => s + p.weight, 0);
  const overallScore = applicablePrinciples.reduce((s, p) => s + (scores[p.id] || 0) * (p.weight / totalWeight), 0);
  const compliant = overallScore >= 75;

  const barData = applicablePrinciples.map(p => ({
    name: p.label.replace('EU Taxonomy Alignment', 'EU Taxonomy').replace('Do No Significant Harm (DNSH)', 'DNSH'),
    score: scores[p.id] || 0,
    threshold: 75,
  }));

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        {['ICMA', 'EUGBS'].map(f => (
          <button key={f} onClick={() => setFramework(f)}
            className={`px-4 py-2 rounded-lg text-xs font-semibold border transition-colors ${framework === f ? 'bg-black text-white border-black' : 'bg-white text-gray-600 border-gray-300 hover:bg-gray-50'}`}>
            {f === 'ICMA' ? 'ICMA GBP 2021' : 'EU GBS (Reg 2023/2631)'}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard label="Overall Score" value={`${overallScore.toFixed(0)}/100`} accent={compliant ? 'green' : 'amber'} />
        <KpiCard label="Status" value={compliant ? 'ALIGNED' : 'PARTIAL'} accent={compliant ? 'green' : 'amber'} sub={`${framework} framework`} />
        <KpiCard label="Principles Assessed" value={`${applicablePrinciples.length}`} sub="of 6 total" />
        <KpiCard label="Gap to Threshold" value={compliant ? '0 pts' : `${(75 - overallScore).toFixed(0)} pts`} accent={compliant ? 'green' : 'red'} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="Principle Scores" subtitle="Adjust sliders to reflect self-assessment">
          <div className="space-y-4">
            {applicablePrinciples.map(p => (
              <div key={p.id}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="text-gray-700 font-medium">{p.label}</span>
                  <span className={`font-mono font-bold ${scores[p.id] >= 75 ? 'text-emerald-600' : 'text-amber-600'}`}>{scores[p.id]}</span>
                </div>
                <input type="range" min="0" max="100" value={scores[p.id] || 0}
                  onChange={e => setScores(prev => ({ ...prev, [p.id]: parseInt(e.target.value) }))}
                  className="w-full h-1.5 accent-black" />
                <div className="text-[10px] text-gray-400">Weight: {(p.weight * 100).toFixed(0)}%</div>
              </div>
            ))}
          </div>
        </Section>

        <Section title="Score vs. Threshold (75)" subtitle="ICMA / EU GBS alignment assessment">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={barData} layout="vertical" barSize={16}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 10 }} width={120} />
              <Tooltip />
              <ReferenceLine x={75} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '75 threshold', fontSize: 9, fill: '#ef4444' }} />
              <Bar dataKey="score" radius={[0, 4, 4, 0]} name="Score">
                {barData.map((d, i) => <Cell key={i} fill={d.score >= 75 ? '#059669' : d.score >= 50 ? '#f59e0b' : '#ef4444'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ── DSCR Sensitivity Tab ──────────────────────────────────────────────────
function DSCRSensitivityTab() {
  const rng = useMemo(() => seededRand(73001), []);
  const baseRevenue = 28_000_000;
  const baseOpex = 8_500_000;
  const baseDebtService = 14_200_000;
  const baseDSCR = (baseRevenue - baseOpex) / baseDebtService;

  const sensitivityFactors = [
    { name: 'P90 Energy Yield', delta: -0.15, revImpact: -0.15, opexImpact: 0 },
    { name: '+20% Opex', delta: 0, revImpact: 0, opexImpact: 0.20 },
    { name: 'PPA Price -10%', delta: -0.10, revImpact: -0.10, opexImpact: 0 },
    { name: 'Interest Rate +100bps', delta: 0, revImpact: 0, opexImpact: 0, dsImpact: 0.08 },
    { name: 'Curtailment +5%', delta: -0.05, revImpact: -0.05, opexImpact: 0 },
    { name: 'Merchant Price -15%', delta: -0.15, revImpact: -0.10, opexImpact: 0 },
  ];

  const waterfallData = [
    { name: 'Base Case', dscr: +baseDSCR.toFixed(2), fill: '#059669' },
    ...sensitivityFactors.map(f => {
      const rev = baseRevenue * (1 + (f.revImpact || 0));
      const opex = baseOpex * (1 + (f.opexImpact || 0));
      const ds = baseDebtService * (1 + (f.dsImpact || 0));
      const dscr = (rev - opex) / ds;
      return { name: f.name, dscr: +dscr.toFixed(2), fill: dscr >= 1.15 ? '#059669' : dscr >= 1.05 ? '#f59e0b' : '#ef4444' };
    }),
  ];

  const years = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12, 15, 18, 20];
  const profileData = years.map((yr, i) => {
    const degradation = 1 - yr * 0.005;
    const debtAmort = 1 - (yr / 20) * 0.6;
    const dscr = (baseRevenue * degradation - baseOpex) / (baseDebtService * debtAmort);
    return { year: `Y${yr}`, dscr: +dscr.toFixed(2), covenant: 1.15 };
  });

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <KpiCard label="Base DSCR" value={baseDSCR.toFixed(2) + 'x'} accent={baseDSCR >= 1.15 ? 'green' : 'amber'} />
        <KpiCard label="Covenant Threshold" value="1.15x" sub="Senior lender floor" />
        <KpiCard label="Headroom" value={`${((baseDSCR - 1.15)).toFixed(2)}x`} accent={baseDSCR - 1.15 >= 0.1 ? 'green' : 'amber'} sub="to covenant breach" />
        <KpiCard label="P90 Stressed DSCR" value={`${(waterfallData[1]?.dscr || 0)}x`} accent={(waterfallData[1]?.dscr || 0) >= 1.15 ? 'green' : 'red'} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="DSCR Sensitivity Waterfall" subtitle="Each bar shows DSCR under single-factor stress">
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={waterfallData} barSize={24}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" height={50} />
              <YAxis domain={[0.8, 2.2]} tickFormatter={v => `${v}x`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={v => `${v}x`} />
              <ReferenceLine y={1.15} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '1.15x covenant', fontSize: 9, fill: '#ef4444' }} />
              <Bar dataKey="dscr" radius={[4, 4, 0, 0]}>
                {waterfallData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="DSCR Profile Over Project Life" subtitle="Base case debt amortisation schedule Y1–Y20">
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={profileData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="year" tick={{ fontSize: 10 }} />
              <YAxis domain={[0.8, 2.5]} tickFormatter={v => `${v}x`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={v => `${v}x`} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <ReferenceLine y={1.15} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Covenant', fontSize: 9, fill: '#ef4444' }} />
              <Line type="monotone" dataKey="dscr" stroke="#0284c7" name="DSCR" strokeWidth={2} dot={{ r: 2 }} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════════════════════════════
export default function ProjectFinancePage() {
  const [activeTab, setActiveTab] = useState('pf');

  return (
    <div className="min-h-screen bg-white">
      <DemoBanner message="DSCR, IRR, and Green Bond scores display deterministic sample data. Load a real project via the Project Finance tab to see live calculations." />
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">Project Finance</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              DSCR · LLCR · IRR · PPA Risk · Blended Finance · Green Bond Alignment
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">DSCR · LLCR</span>
            <span className="text-[10px] font-bold px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">GREEN BOND</span>
          </div>
        </div>

        <div className="flex gap-1 mt-4 overflow-x-auto">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${active ? 'bg-black text-white' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'pf' && <ProjectFinancePanel powerPlantId="demo-001" powerPlantName="Demo Wind Farm" />}
        {activeTab === 'blended' && <BlendedFinancePanel />}
        {activeTab === 'green_bonds' && <GreenBondTab />}
        {activeTab === 'sensitivity' && <DSCRSensitivityTab />}
      </div>
    </div>
  );
}
