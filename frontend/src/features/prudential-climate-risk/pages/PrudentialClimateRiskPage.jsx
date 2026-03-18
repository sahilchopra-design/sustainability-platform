/**
 * PrudentialClimateRiskPage.jsx
 * Route: /prudential-climate-risk
 * Concept: Prudential Climate Risk — BOE BES · ECB DFAST · NGFS v4 · ICAAP Pillar 2
 */
import React, { useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

const Section = ({ title, children }) => (
  <div className="mb-6">
    <h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, color = 'emerald' }) => (
  <div className={`bg-${color}-50 border border-${color}-200 rounded-lg p-4`}>
    <div className="text-xs text-gray-500 mb-1">{label}</div>
    <div className={`text-2xl font-bold text-${color}-700`}>{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
);
const Row = ({ children }) => (
  <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">{children}</div>
);
const Inp = ({ label, ...p }) => (
  <div className="flex flex-col gap-1">
    <label className="text-xs font-medium text-gray-600">{label}</label>
    <input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p} />
  </div>
);
const Sel = ({ label, children, ...p }) => (
  <div className="flex flex-col gap-1">
    <label className="text-xs font-medium text-gray-600">{label}</label>
    <select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select>
  </div>
);
const Btn = ({ children, ...p }) => (
  <button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>
);

function seeded(i, seed) {
  return Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;
}

const TABS = ['Scenario Overview', 'CET1 Stress Test', 'Segment Capital', 'ICAAP / Pillar 2', 'Regulatory Output'];

const NGFS_SCENARIOS = [
  { id: 'net_zero_2050', label: 'Net Zero 2050', category: 'orderly', temp: '1.5°C' },
  { id: 'below_2c', label: 'Below 2°C', category: 'orderly', temp: '1.8°C' },
  { id: 'delayed_transition', label: 'Delayed Transition', category: 'disorderly', temp: '1.8°C' },
  { id: 'divergent_net_zero', label: 'Divergent Net Zero', category: 'disorderly', temp: '1.5°C' },
  { id: 'current_policies', label: 'Current Policies', category: 'hot_house', temp: '3.0°C' },
  { id: 'ndcs', label: 'Nationally Determined', category: 'hot_house', temp: '2.5°C' },
];

const YEARS = [2025, 2027, 2030, 2035, 2040, 2045, 2050];

const SEGMENTS = [
  { segment: 'Residential Mortgage', transition_risk: 'medium', physical_risk: 'high', brown_share: 22, stranded: 1.4, rwa_uplift: 8, capital_add_on: 0.6 },
  { segment: 'Commercial RE', transition_risk: 'high', physical_risk: 'high', brown_share: 35, stranded: 3.2, rwa_uplift: 15, capital_add_on: 1.4 },
  { segment: 'Corporate Lending', transition_risk: 'high', physical_risk: 'medium', brown_share: 28, stranded: 2.8, rwa_uplift: 12, capital_add_on: 1.1 },
  { segment: 'Project Finance', transition_risk: 'very_high', physical_risk: 'medium', brown_share: 45, stranded: 5.1, rwa_uplift: 22, capital_add_on: 2.0 },
  { segment: 'Retail Auto', transition_risk: 'high', physical_risk: 'low', brown_share: 60, stranded: 4.2, rwa_uplift: 18, capital_add_on: 1.7 },
  { segment: 'Trade Finance', transition_risk: 'medium', physical_risk: 'medium', brown_share: 18, stranded: 0.9, rwa_uplift: 6, capital_add_on: 0.5 },
  { segment: 'Sovereign Bonds', transition_risk: 'low', physical_risk: 'high', brown_share: 8, stranded: 0.3, rwa_uplift: 3, capital_add_on: 0.2 },
  { segment: 'Infrastructure', transition_risk: 'high', physical_risk: 'high', brown_share: 32, stranded: 2.5, rwa_uplift: 14, capital_add_on: 1.2 },
];

const seed = 77;

export default function PrudentialClimateRiskPage() {
  const [tab, setTab] = useState(0);
  const [selectedScenarios, setSelectedScenarios] = useState(['net_zero_2050', 'delayed_transition', 'current_policies']);
  const [institutionType, setInstitutionType] = useState('commercial_bank');
  const [besRound, setBesRound] = useState('2025');
  const [cstRound, setCstRound] = useState('2024');
  const [running, setRunning] = useState(false);

  const tempData = useMemo(() => YEARS.map((yr, i) => {
    const row = { year: yr };
    NGFS_SCENARIOS.forEach((s, si) => {
      const base = s.category === 'orderly' ? 1.5 : s.category === 'disorderly' ? 1.9 : 2.8;
      row[s.id] = +(base + seeded(i * 7 + si * 3, seed) * 0.4 * (yr >= 2040 ? 1.2 : 1)).toFixed(2);
    });
    return row;
  }), []);

  const carbonData = useMemo(() => YEARS.map((yr, i) => {
    const row = { year: yr };
    NGFS_SCENARIOS.forEach((s, si) => {
      const base = s.category === 'orderly' ? 120 + i * 40 : s.category === 'disorderly' ? 80 + i * 30 : 40 + i * 5;
      row[s.id] = Math.round(base + seeded(i * 5 + si * 9, seed) * 30);
    });
    return row;
  }), []);

  const cet1Data = useMemo(() => [
    { scenario: 'Net Zero 2050', baseline: 14.2, stressed: 12.8, depletion: 1.4 },
    { scenario: 'Delayed Transition', baseline: 14.2, stressed: 11.9, depletion: 2.3 },
    { scenario: 'Current Policies', baseline: 14.2, stressed: 10.7, depletion: 3.5 },
  ], []);

  const lossTable = useMemo(() => [
    { category: 'Credit Risk — Transition', net_zero: 0.8, delayed: 1.6, hot_house: 2.9 },
    { category: 'Credit Risk — Physical', net_zero: 0.4, delayed: 0.6, hot_house: 1.8 },
    { category: 'Market Risk', net_zero: 0.2, delayed: 0.4, hot_house: 0.7 },
    { category: 'Op Risk', net_zero: 0.05, delayed: 0.08, hot_house: 0.15 },
  ], []);

  const segCapData = useMemo(() => SEGMENTS.map(s => ({ segment: s.segment.split(' ')[0], capital_add_on: s.capital_add_on })), []);

  const SCENARIO_COLORS = { net_zero_2050: '#059669', below_2c: '#10b981', delayed_transition: '#f59e0b', divergent_net_zero: '#84cc16', current_policies: '#ef4444', ndcs: '#f97316' };

  function scenarioBadge(cat) {
    const map = { orderly: 'bg-emerald-100 text-emerald-700', disorderly: 'bg-amber-100 text-amber-700', hot_house: 'bg-red-100 text-red-700' };
    return <span className={`text-xs px-2 py-0.5 rounded font-medium ${map[cat]}`}>{cat.replace('_', ' ')}</span>;
  }

  function riskBadge(level) {
    const map = { very_high: 'bg-red-100 text-red-700', high: 'bg-amber-100 text-amber-700', medium: 'bg-yellow-100 text-yellow-700', low: 'bg-emerald-100 text-emerald-700' };
    return <span className={`text-xs px-2 py-0.5 rounded font-medium ${map[level] || 'bg-gray-100 text-gray-500'}`}>{level.replace('_', ' ')}</span>;
  }

  async function runStress() {
    setRunning(true);
    try {
      await axios.post(`${API}/api/v1/prudential-climate/stress`, { institution_type: institutionType, scenarios: selectedScenarios });
    } catch {}
    setRunning(false);
  }

  function toggleScenario(id) {
    setSelectedScenarios(prev => prev.includes(id) ? prev.filter(s => s !== id) : [...prev, id]);
  }

  const activeScenarios = NGFS_SCENARIOS.filter(s => selectedScenarios.includes(s.id));

  return (
    <div className="p-6 bg-white min-h-screen text-black">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-black">Prudential Climate Risk</h1>
        <p className="text-sm text-gray-500 mt-1">BOE BES · ECB DFAST · NGFS v4 · ICAAP Pillar 2</p>
      </div>

      <div className="flex gap-2 mb-6 border-b border-gray-200 overflow-x-auto">
        {TABS.map((t, i) => (
          <button key={t} onClick={() => setTab(i)}
            className={`px-4 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${tab === i ? 'border-emerald-600 text-emerald-700' : 'border-transparent text-gray-500 hover:text-black'}`}>
            {t}
          </button>
        ))}
      </div>

      {tab === 0 && (
        <div>
          <Section title="NGFS v4 Scenario Selector">
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
              {NGFS_SCENARIOS.map(s => (
                <label key={s.id} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${selectedScenarios.includes(s.id) ? 'border-emerald-400 bg-emerald-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}>
                  <input type="checkbox" checked={selectedScenarios.includes(s.id)} onChange={() => toggleScenario(s.id)} className="accent-emerald-600" />
                  <div>
                    <div className="text-sm font-medium text-black">{s.label}</div>
                    <div className="flex items-center gap-2 mt-1">{scenarioBadge(s.category)}<span className="text-xs text-gray-400">{s.temp}</span></div>
                  </div>
                </label>
              ))}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <Sel label="Institution Type" value={institutionType} onChange={e => setInstitutionType(e.target.value)}>
                <option value="commercial_bank">Commercial Bank</option>
                <option value="investment_bank">Investment Bank</option>
                <option value="insurance">Insurance</option>
                <option value="asset_manager">Asset Manager</option>
              </Sel>
            </div>
            <Btn onClick={runStress} disabled={running}>{running ? 'Running...' : 'Run Stress Test'}</Btn>
          </Section>

          <Section title="Temperature Trajectory (°C) to 2050">
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={tempData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis domain={[1, 4]} />
                <Tooltip />
                <Legend />
                {activeScenarios.map(s => (
                  <Line key={s.id} type="monotone" dataKey={s.id} stroke={SCENARIO_COLORS[s.id]} name={s.label} dot={false} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Carbon Price Trajectory (USD/tCO2e)">
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={carbonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip />
                <Legend />
                {activeScenarios.map(s => (
                  <Line key={s.id} type="monotone" dataKey={s.id} stroke={SCENARIO_COLORS[s.id]} name={s.label} dot={false} strokeWidth={2} />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}

      {tab === 1 && (
        <div>
          <Section title="CET1 Stress Test Settings">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <Sel label="BOE BES Round" value={besRound} onChange={e => setBesRound(e.target.value)}>
                <option value="2025">BES 2025</option>
                <option value="2023">BES 2023</option>
                <option value="2021">BES 2021</option>
              </Sel>
              <Sel label="ECB CST Round" value={cstRound} onChange={e => setCstRound(e.target.value)}>
                <option value="2024">CST 2024</option>
                <option value="2022">CST 2022</option>
              </Sel>
            </div>
          </Section>

          <Section title="CET1 Ratio — Baseline vs Stressed">
            <Row>
              <KpiCard label="Baseline CET1" value="14.2%" sub="Pre-stress" color="emerald" />
              <KpiCard label="Max CET1 Depletion" value="-3.5 ppts" sub="Current Policies scenario" color="red" />
              <KpiCard label="Worst Scenario" value="Current Policies" sub="10.7% stressed CET1" color="red" />
              <KpiCard label="CET1 Min Threshold" value="10.5%" sub={cet1Data[2].stressed < 10.5 ? 'BREACH' : 'No breach'} color={cet1Data[2].stressed < 10.5 ? 'red' : 'emerald'} />
            </Row>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={cet1Data} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="scenario" tick={{ fontSize: 11 }} />
                <YAxis domain={[8, 16]} />
                <Tooltip />
                <Legend />
                <ReferenceLine y={10.5} stroke="#ef4444" strokeDasharray="5 5" label={{ value: 'Min 10.5%', position: 'right', fontSize: 11, fill: '#ef4444' }} />
                <Bar dataKey="baseline" fill="#d1fae5" name="Baseline CET1 %" radius={[4, 4, 0, 0]} />
                <Bar dataKey="stressed" fill="#059669" name="Stressed CET1 %" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Credit & Market Risk Losses (% RWA)">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <th className="px-3 py-2 text-left">Risk Category</th>
                  <th className="px-3 py-2 text-right">Net Zero</th>
                  <th className="px-3 py-2 text-right">Delayed Transition</th>
                  <th className="px-3 py-2 text-right">Current Policies</th>
                </tr>
              </thead>
              <tbody>
                {lossTable.map((r, i) => (
                  <tr key={r.category} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-3 py-2 font-medium">{r.category}</td>
                    <td className="px-3 py-2 text-right text-emerald-700">{r.net_zero}%</td>
                    <td className="px-3 py-2 text-right text-amber-700">{r.delayed}%</td>
                    <td className="px-3 py-2 text-right text-red-700">{r.hot_house}%</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>
        </div>
      )}

      {tab === 2 && (
        <div>
          <Section title="Loan Segment Climate Risk Overlays">
            <div className="overflow-x-auto mb-4">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                    <th className="px-3 py-2 text-left">Segment</th>
                    <th className="px-3 py-2 text-left">Transition Risk</th>
                    <th className="px-3 py-2 text-left">Physical Risk</th>
                    <th className="px-3 py-2 text-right">Brown Share %</th>
                    <th className="px-3 py-2 text-right">Stranded Exp (£bn)</th>
                    <th className="px-3 py-2 text-right">RWA Uplift %</th>
                    <th className="px-3 py-2 text-right">Capital Add-On %</th>
                  </tr>
                </thead>
                <tbody>
                  {SEGMENTS.map((s, i) => (
                    <tr key={s.segment} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 font-medium">{s.segment}</td>
                      <td className="px-3 py-2">{riskBadge(s.transition_risk)}</td>
                      <td className="px-3 py-2">{riskBadge(s.physical_risk)}</td>
                      <td className="px-3 py-2 text-right">{s.brown_share}%</td>
                      <td className="px-3 py-2 text-right">£{s.stranded}bn</td>
                      <td className="px-3 py-2 text-right text-amber-700">+{s.rwa_uplift}%</td>
                      <td className="px-3 py-2 text-right font-semibold text-red-700">+{s.capital_add_on}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>

          <Section title="Capital Add-On by Segment (%)">
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={segCapData} layout="vertical" margin={{ left: 20 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="segment" type="category" width={100} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="capital_add_on" fill="#f59e0b" radius={[0, 4, 4, 0]} name="Capital Add-On %" />
              </BarChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}

      {tab === 3 && (
        <div>
          <Section title="ICAAP Pillar 2 Climate Assessment">
            <Row>
              <KpiCard label="Pillar 2a Add-On" value="1.8%" sub="Firm-specific capital req." color="amber" />
              <KpiCard label="Pillar 2b Buffer" value="0.7%" sub="Forward-looking buffer" color="amber" />
              <KpiCard label="SREP Finding" value="Needs Improvement" sub="EBA SREP score: 3" color="amber" />
              <KpiCard label="Climate SRP 43.1" value="Material" sub="Basel supervisory review" color="red" />
            </Row>
          </Section>

          <Section title="Basel SRP 43.1 Climate Risk Categorisation">
            {[
              { category: 'Credit Risk', categorisation: 'material', explanation: 'Transition risk exposures exceed 5% of RWA in 2+ sectors.' },
              { category: 'Market Risk', categorisation: 'potentially_material', explanation: 'Carbon-intensive equity positions subject to repricing.' },
              { category: 'Liquidity Risk', categorisation: 'potentially_material', explanation: 'Green bond market liquidity under stress scenarios.' },
              { category: 'Operational Risk', categorisation: 'immaterial', explanation: 'Physical risk impacts on operations limited to 1 geography.' },
              { category: 'Reputational Risk', categorisation: 'potentially_material', explanation: 'ESG rating divergence flagged in media monitoring.' },
            ].map((r, i) => (
              <div key={r.category} className={`flex items-start gap-3 p-3 rounded-lg mb-2 ${r.categorisation === 'material' ? 'bg-red-50' : r.categorisation === 'potentially_material' ? 'bg-amber-50' : 'bg-gray-50'}`}>
                <div className="flex-1">
                  <div className="font-medium text-sm">{r.category}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{r.explanation}</div>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded font-medium flex-shrink-0 ${r.categorisation === 'material' ? 'bg-red-100 text-red-700' : r.categorisation === 'potentially_material' ? 'bg-amber-100 text-amber-700' : 'bg-gray-100 text-gray-500'}`}>{r.categorisation.replace('_', ' ')}</span>
              </div>
            ))}
          </Section>

          <Section title="EBA SREP Climate Scores (1-4)">
            {[
              { area: 'Governance & Strategy', score: 3 },
              { area: 'Risk Management', score: 3 },
              { area: 'Capital Adequacy', score: 2 },
              { area: 'Liquidity Adequacy', score: 2 },
            ].map(r => (
              <div key={r.area} className="flex items-center gap-3 mb-2">
                <span className="text-sm font-medium w-48">{r.area}</span>
                <div className="flex gap-1">
                  {[1, 2, 3, 4].map(n => (
                    <div key={n} className={`w-8 h-8 rounded flex items-center justify-center text-sm font-bold ${n <= r.score ? (r.score >= 3 ? 'bg-amber-400 text-white' : 'bg-emerald-500 text-white') : 'bg-gray-100 text-gray-300'}`}>{n}</div>
                  ))}
                </div>
                <span className={`text-xs ml-2 ${r.score >= 3 ? 'text-amber-600' : 'text-emerald-600'}`}>{r.score >= 3 ? 'Supervisory concern' : 'Acceptable'}</span>
              </div>
            ))}
          </Section>
        </div>
      )}

      {tab === 4 && (
        <div>
          <Section title="Total Climate Capital Requirements">
            <Row>
              <KpiCard label="Total Climate Capital Buffer" value="2.5%" sub="% of RWA (P2a + P2b)" color="red" />
              <KpiCard label="Total Climate RWA Uplift" value="+11.8%" sub="Across all segments" color="amber" />
              <KpiCard label="Short-Term Horizon" value="0.6%" sub="0–3 years" color="emerald" />
              <KpiCard label="Long-Term Horizon" value="3.2%" sub="10–30 years" color="red" />
            </Row>
          </Section>

          <Section title="Regulatory Framework Capital Requirements Comparison">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={[
                { framework: 'BOE BES 2025', capital_req: 2.1 },
                { framework: 'ECB DFAST 2024', capital_req: 1.9 },
                { framework: 'ICAAP Pillar 2a', capital_req: 1.8 },
                { framework: 'Pillar 2b Buffer', capital_req: 0.7 },
                { framework: 'Basel SRP 43.1', capital_req: 2.5 },
              ]} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="framework" tick={{ fontSize: 10 }} />
                <YAxis />
                <Tooltip />
                <Bar dataKey="capital_req" fill="#059669" radius={[4, 4, 0, 0]} name="Capital Req %" />
              </BarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="Regulatory Findings Summary">
            {[
              { finding: 'CET1 buffer insufficient under Current Policies scenario', severity: 'high', action: 'Increase capital buffer by Q4 2025' },
              { finding: 'Brown share in Retail Auto exceeds 50% — EPC D/E dominant', severity: 'high', action: 'Green lending strategy required' },
              { finding: 'Pillar 2b climate buffer not yet formalised in ICAAP', severity: 'medium', action: 'Update ICAAP by next supervisory review' },
              { finding: 'TCFD scenario analysis not aligned to NGFS v4', severity: 'medium', action: 'Upgrade to NGFS v4 scenarios' },
            ].map((f, i) => (
              <div key={i} className={`p-3 rounded-lg mb-2 ${f.severity === 'high' ? 'bg-red-50 border border-red-200' : 'bg-amber-50 border border-amber-200'}`}>
                <div className="font-medium text-sm text-black">{f.finding}</div>
                <div className="text-xs text-gray-500 mt-0.5">Action: {f.action}</div>
              </div>
            ))}
          </Section>

          <Section title="Export">
            <div className="flex gap-3">
              <Btn onClick={() => alert('Regulatory report export initiated')}>Export Regulatory Report</Btn>
              <Btn onClick={() => alert('ICAAP disclosure package initiated')}>ICAAP Disclosure Package</Btn>
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}
