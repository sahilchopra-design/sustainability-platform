/**
 * InfrastructureFinancePage.jsx  —  Route: /infrastructure-finance
 * Sprint 22 E51 — Equator Principles IV / IFC Performance Standards / OECD & Paris Alignment / DSCR Climate Stress / Blended Finance
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell,
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
const Row = ({ children }) => <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">{children}</div>;
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

function seed(i, s) { return Math.abs(Math.sin(i * 9301 + s * 49297) * 233280) % 233280 / 233280; }

const TABS = ['Equator Principles IV', 'IFC Performance Standards', 'OECD & Paris Alignment', 'DSCR Climate Stress', 'Blended Finance & Labels'];

const EP_PRINCIPLES = [
  'Assessment (ESIA)', 'Management & Monitoring', 'Stakeholder Engagement',
  'Grievance Mechanism', 'Independent Review', 'Covenants & Reporting',
  'Independent Monitoring', 'Transparency', 'Human Rights Due Diligence', 'ESAP Implementation',
];

const IFC_PS = [
  { id: 'PS1', name: 'Assessment & Management System', reqs: ['ESMS documentation', 'Risk assessment', 'Management programme'] },
  { id: 'PS2', name: 'Labour & Working Conditions', reqs: ['Human resources policy', 'Worker org rights', 'Non-discrimination'] },
  { id: 'PS3', name: 'Resource Efficiency', reqs: ['Energy efficiency', 'Greenhouse gas reductions', 'Water efficiency'] },
  { id: 'PS4', name: 'Community Health & Safety', reqs: ['Infrastructure safety', 'Emergency preparedness', 'Security personnel'] },
  { id: 'PS5', name: 'Land Acquisition', reqs: ['Land assessment', 'Negotiated settlement', 'Livelihood restoration'] },
  { id: 'PS6', name: 'Biodiversity Conservation', reqs: ['Habitat assessment', 'BBOP offsets', 'No-net-loss biodiversity'] },
  { id: 'PS7', name: 'Indigenous Peoples', reqs: ['FPIC documented', 'Cultural heritage assessment', 'Benefit sharing'] },
  { id: 'PS8', name: 'Cultural Heritage', reqs: ['Chance find procedure', 'Physical & non-physical heritage', 'Stakeholder consultation'] },
];

export default function InfrastructureFinancePage() {
  const [tab, setTab] = useState(0);

  // Tab 1
  const [projectType, setProjectType] = useState('greenfield');
  const [sector, setSector] = useState('energy');
  const [epCountry, setEpCountry] = useState('Indonesia');
  const [totalCost, setTotalCost] = useState('850000000');
  const [epResult, setEpResult] = useState(null);

  // Tab 2 — IFC PS scores (per PS, 0-100)
  const s2 = 98765;
  const [psScores] = useState(() => IFC_PS.map((_, i) => Math.round(45 + seed(i, s2) * 50)));

  // Tab 3
  const [oecdTier, setOecdTier] = useState('Tier 2');
  const [mitigAligned, setMitigAligned] = useState(true);
  const [adaptAligned, setAdaptAligned] = useState(false);
  const [govAligned, setGovAligned] = useState(true);

  // Tab 4
  const [baselineDSCR, setBaselineDSCR] = useState('1.45');
  const [dscrSector, setDscrSector] = useState('Renewable Energy');

  // Tab 5
  const [blendStructure, setBlendStructure] = useState('first_loss');

  const runEP = useCallback(async () => {
    try {
      const res = await axios.post(`${API}/api/v1/infrastructure/equator-principles`, {
        project_type: projectType, sector, country: epCountry, total_cost_usd: +totalCost,
      });
      setEpResult(res.data);
    } catch {
      const cost = +totalCost;
      const cat = cost > 500e6 ? 'A' : cost > 50e6 ? 'B' : 'C';
      const s = epCountry.length + sector.length;
      const scores = EP_PRINCIPLES.map((_, i) => Math.round(50 + seed(i, s) * 45));
      const passing = scores.filter(s => s >= 70).length;
      setEpResult({ category: cat, scores, passing, total: EP_PRINCIPLES.length, esap_required: cat !== 'C', compliant: passing >= 8 });
    }
  }, [projectType, sector, epCountry, totalCost]);

  const catColor = { A: 'red', B: 'yellow', C: 'emerald' };

  // Tab 2: composite
  const compositePS = Math.round(psScores.reduce((a, b) => a + b, 0) / psScores.length);
  const psBarData = IFC_PS.map((ps, i) => ({ name: ps.id, score: psScores[i] }));

  // Tab 3: PA sub-criteria
  const s3 = 11111;
  const paCriteria = [
    { name: 'Scope 1 GHG', score: Math.round(50 + seed(1, s3) * 45) },
    { name: 'Scope 2 GHG', score: Math.round(55 + seed(2, s3) * 40) },
    { name: 'Scope 3 GHG', score: Math.round(30 + seed(3, s3) * 55) },
    { name: 'Temp Trajectory', score: Math.round(40 + seed(4, s3) * 50) },
    { name: 'NDC Alignment', score: Math.round(45 + seed(5, s3) * 45) },
    { name: 'Adaptation Plan', score: Math.round(35 + seed(6, s3) * 55) },
    { name: 'Governance', score: Math.round(60 + seed(7, s3) * 35) },
  ];
  const paScore = Math.round(paCriteria.reduce((a, b) => a + b.score, 0) / paCriteria.length);
  const ghgReduction = Math.round(15000 + seed(8, s3) * 45000);

  // Tab 4: DSCR stress
  const baseline = +baselineDSCR;
  const dscrHaircuts = {
    'Renewable Energy': { phys: 0.08, trans: 0.06 },
    'Toll Road': { phys: 0.05, trans: 0.12 },
    'Port': { phys: 0.12, trans: 0.08 },
    'Airport': { phys: 0.06, trans: 0.15 },
    'Water': { phys: 0.10, trans: 0.04 },
  };
  const hc = dscrHaircuts[dscrSector] || { phys: 0.08, trans: 0.08 };
  const dscrPhys = +(baseline * (1 - hc.phys)).toFixed(3);
  const dscrTrans = +(baseline * (1 - hc.trans)).toFixed(3);
  const dscrComb = +(baseline * (1 - hc.phys - hc.trans + hc.phys * hc.trans)).toFixed(3);
  const covenantBreach = dscrComb < 1.0;
  const dscrBarData = [
    { scenario: 'Baseline', dscr: baseline },
    { scenario: 'Physical Stress', dscr: dscrPhys },
    { scenario: 'Transition Stress', dscr: dscrTrans },
    { scenario: 'Combined Stress', dscr: dscrComb },
  ];
  const dscrLineData = Array.from({ length: 9 }, (_, i) => {
    const cp = 40 + i * 20;
    const factor = 1 - (cp - 40) / 40 * hc.trans * 0.5;
    return { carbon_price: cp, dscr: +(baseline * factor).toFixed(3) };
  });

  // Tab 5: Blended finance
  const blendConfigs = {
    first_loss: { senior: 50, mezz: 15, first_loss: 10, equity: 15, grant: 5, mdb: 5 },
    guarantee: { senior: 60, mezz: 10, first_loss: 0, equity: 20, grant: 0, mdb: 10 },
    concessional: { senior: 45, mezz: 10, first_loss: 5, equity: 20, grant: 10, mdb: 10 },
    grant: { senior: 35, mezz: 10, first_loss: 0, equity: 15, grant: 30, mdb: 10 },
    equity_plus: { senior: 40, mezz: 10, first_loss: 5, equity: 30, grant: 5, mdb: 10 },
  };
  const cfg = blendConfigs[blendStructure] || blendConfigs.first_loss;
  const trancheData = [{ structure: blendStructure.replace('_', ' '), ...cfg }];
  const crowdIn = +((cfg.senior + cfg.mezz + cfg.equity) / (cfg.first_loss + cfg.grant + cfg.mdb)).toFixed(2);
  const privateMobilised = Math.round((cfg.senior + cfg.mezz + cfg.equity) / 100 * +totalCost);
  const additionality = Math.round(55 + seed(20, blendStructure.length) * 40);
  const blendedIRR = +(7.5 + seed(21, blendStructure.length) * 4.5).toFixed(1);
  const privateIRR = +(12 + seed(22, blendStructure.length) * 6).toFixed(1);

  const sdgChips = ['SDG 7', 'SDG 9', 'SDG 11', 'SDG 13', 'SDG 17'];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Infrastructure Finance — ESG & Climate</h1>
          <p className="text-sm text-gray-500 mt-1">Equator Principles IV · IFC Performance Standards · OECD Screening · Paris Alignment · DSCR Climate Stress · Blended Finance</p>
        </div>

        <div className="flex gap-1 mb-6 bg-white border border-gray-200 rounded-lg p-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors ${tab === i ? 'bg-emerald-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* ── TAB 1: Equator Principles IV ── */}
        {tab === 0 && (
          <div>
            <Section title="Project Parameters">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="Project Type" value={projectType} onChange={e => setProjectType(e.target.value)}>
                  {['greenfield', 'brownfield', 'expansion', 'acquisition'].map(t => <option key={t}>{t}</option>)}
                </Sel>
                <Sel label="Sector" value={sector} onChange={e => setSector(e.target.value)}>
                  {['energy', 'transport', 'water', 'mining', 'agriculture', 'manufacturing'].map(s => <option key={s}>{s}</option>)}
                </Sel>
                <Inp label="Host Country" value={epCountry} onChange={e => setEpCountry(e.target.value)} />
                <Inp label="Total Cost (USD)" type="number" value={totalCost} onChange={e => setTotalCost(e.target.value)} />
              </div>
              <Btn onClick={runEP}>Run EP IV Assessment</Btn>
            </Section>
            {epResult && (
              <>
                <Row>
                  <div className={`bg-${catColor[epResult.category] || 'gray'}-50 border border-${catColor[epResult.category] || 'gray'}-200 rounded-lg p-4 flex flex-col justify-center items-center`}>
                    <div className="text-xs text-gray-500 mb-1">EP Category</div>
                    <div className={`text-4xl font-black text-${catColor[epResult.category] || 'gray'}-700`}>{epResult.category}</div>
                    <div className="text-xs text-gray-400 mt-1">{epResult.category === 'A' ? 'High Impact' : epResult.category === 'B' ? 'Medium Impact' : 'Low Impact'}</div>
                  </div>
                  <KpiCard label="Principles Passing" value={`${epResult.passing}/${epResult.total}`} sub="≥70/100 threshold" color={epResult.compliant ? 'emerald' : 'red'} />
                  <KpiCard label="ESAP Required" value={epResult.esap_required ? 'Yes' : 'No'} sub="Environmental & Social Action Plan" color={epResult.esap_required ? 'yellow' : 'emerald'} />
                  <KpiCard label="EP Compliant" value={epResult.compliant ? 'Compliant' : 'Non-Compliant'} sub="overall assessment" color={epResult.compliant ? 'emerald' : 'red'} />
                </Row>
                <Section title="Principle-by-Principle Scores">
                  <div className="overflow-x-auto">
                    <table className="w-full text-xs border-collapse">
                      <thead>
                        <tr className="bg-gray-50">
                          {['#', 'Principle', 'Score', 'Status'].map(h => (
                            <th key={h} className="border border-gray-200 px-3 py-2 text-left font-semibold text-gray-600">{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {EP_PRINCIPLES.map((p, i) => {
                          const sc = epResult.scores[i];
                          return (
                            <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                              <td className="border border-gray-200 px-3 py-2 font-bold text-gray-500">EP{i + 1}</td>
                              <td className="border border-gray-200 px-3 py-2">{p}</td>
                              <td className="border border-gray-200 px-3 py-2 font-bold">{sc}/100</td>
                              <td className="border border-gray-200 px-3 py-2">
                                <span className={`px-2 py-0.5 rounded text-xs font-bold ${sc >= 70 ? 'bg-emerald-100 text-emerald-700' : sc >= 50 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                                  {sc >= 70 ? 'Pass' : sc >= 50 ? 'Partial' : 'Fail'}
                                </span>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </Section>
                <Section title="EP Compliance Summary">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {[
                      ['Monitoring Required', epResult.category !== 'C', true],
                      ['Grievance Mechanism', epResult.esap_required, true],
                      ['Independent Review', epResult.category === 'A', false],
                      ['ESAP Required', epResult.esap_required, false],
                    ].map(([label, present, required], i) => (
                      <div key={i} className={`p-3 rounded border ${present ? 'bg-emerald-50 border-emerald-200' : 'bg-gray-50 border-gray-200'}`}>
                        <div className="text-xs font-medium text-gray-600">{label}</div>
                        <div className={`text-sm font-bold mt-1 ${present ? 'text-emerald-700' : 'text-gray-400'}`}>{present ? 'Required' : 'Not Required'}</div>
                      </div>
                    ))}
                  </div>
                </Section>
              </>
            )}
          </div>
        )}

        {/* ── TAB 2: IFC Performance Standards ── */}
        {tab === 1 && (
          <div>
            <Section title="IFC Performance Standard Scores">
              <Row>
                <KpiCard label="Composite PS Score" value={`${compositePS}/100`} sub="all 8 standards" color={compositePS >= 70 ? 'emerald' : compositePS >= 50 ? 'yellow' : 'red'} />
                <KpiCard label="IFC Compliant" value={compositePS >= 70 ? 'Yes' : 'No'} sub="≥70 threshold" color={compositePS >= 70 ? 'emerald' : 'red'} />
                <KpiCard label="Standards Passing" value={`${psScores.filter(s => s >= 70).length}/8`} sub="≥70/100 pass" color="gray" />
              </Row>
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={psBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="score" name="PS Score">
                    {psBarData.map((d, i) => (
                      <Cell key={i} fill={d.score >= 70 ? '#059669' : d.score >= 50 ? '#ca8a04' : '#dc2626'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Performance Standard Details">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {IFC_PS.map((ps, i) => {
                  const sc = psScores[i];
                  const color = sc >= 70 ? 'emerald' : sc >= 50 ? 'yellow' : 'red';
                  return (
                    <div key={ps.id} className={`p-4 rounded-lg border bg-${color}-50 border-${color}-200`}>
                      <div className="flex items-center justify-between mb-2">
                        <span className={`text-xs font-bold text-${color}-700`}>{ps.id}</span>
                        <span className={`text-lg font-black text-${color}-700`}>{sc}</span>
                      </div>
                      <div className="text-xs font-semibold text-gray-700 mb-2">{ps.name}</div>
                      <div className="space-y-1">
                        {ps.reqs.map((r, j) => (
                          <div key={j} className="flex items-center gap-1 text-xs text-gray-600">
                            <span className={sc >= 70 ? 'text-emerald-500' : 'text-gray-400'}>✓</span>
                            {r}
                          </div>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </Section>
          </div>
        )}

        {/* ── TAB 3: OECD & Paris Alignment ── */}
        {tab === 2 && (
          <div>
            <Section title="OECD Common Approaches">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="OECD Tier" value={oecdTier} onChange={e => setOecdTier(e.target.value)}>
                  {['Tier 1', 'Tier 2', 'Tier 3'].map(t => <option key={t}>{t}</option>)}
                </Sel>
              </div>
              <Row>
                <KpiCard label="OECD Tier" value={oecdTier} sub="Common Approaches 2016" color={oecdTier === 'Tier 1' ? 'red' : oecdTier === 'Tier 2' ? 'yellow' : 'emerald'} />
                <KpiCard label="Env Screening" value={oecdTier === 'Tier 3' ? 'Screened Out' : 'Review Required'} sub="environmental category" color={oecdTier === 'Tier 3' ? 'emerald' : 'yellow'} />
                <KpiCard label="Notification Required" value={oecdTier === 'Tier 1' ? 'Yes' : 'No'} sub="export credit notification" color={oecdTier === 'Tier 1' ? 'red' : 'emerald'} />
                <KpiCard label="Independent Review" value={oecdTier === 'Tier 1' ? 'Required' : 'Optional'} sub="OECD review process" color={oecdTier === 'Tier 1' ? 'yellow' : 'emerald'} />
              </Row>
            </Section>
            <Section title="Paris Alignment Assessment">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                {[
                  ['Mitigation Aligned', mitigAligned, setMitigAligned],
                  ['Adaptation Aligned', adaptAligned, setAdaptAligned],
                  ['Governance Aligned', govAligned, setGovAligned],
                ].map(([lbl, val, setter]) => (
                  <div key={lbl} className="flex flex-col gap-1">
                    <label className="text-xs font-medium text-gray-600">{lbl}</label>
                    <button onClick={() => setter(!val)}
                      className={`px-3 py-2 rounded text-sm font-medium border ${val ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-700 border-gray-300'}`}>
                      {val ? 'Aligned' : 'Not Aligned'}
                    </button>
                  </div>
                ))}
              </div>
              <Row>
                <KpiCard label="PA Alignment Score" value={`${paScore}/100`} sub="composite sub-criteria" color={paScore >= 70 ? 'emerald' : paScore >= 50 ? 'yellow' : 'red'} />
                <KpiCard label="Mitigation" value={mitigAligned ? 'Aligned' : 'Gap'} sub="Paris Art. 2.1(a)" color={mitigAligned ? 'emerald' : 'red'} />
                <KpiCard label="Adaptation" value={adaptAligned ? 'Aligned' : 'Gap'} sub="Paris Art. 2.1(b)" color={adaptAligned ? 'emerald' : 'red'} />
                <KpiCard label="GHG Reduction" value={`${(ghgReduction / 1000).toFixed(0)}k tCO₂/yr`} sub="project contribution" color="emerald" />
              </Row>
              <Section title="Paris Alignment Sub-Criteria Scores">
                <ResponsiveContainer width="100%" height={240}>
                  <BarChart data={paCriteria}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                    <YAxis domain={[0, 100]} />
                    <Tooltip />
                    <Bar dataKey="score" name="Score">
                      {paCriteria.map((d, i) => (
                        <Cell key={i} fill={d.score >= 70 ? '#059669' : d.score >= 50 ? '#ca8a04' : '#dc2626'} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </Section>
            </Section>
          </div>
        )}

        {/* ── TAB 4: DSCR Climate Stress ── */}
        {tab === 3 && (
          <div>
            <Section title="DSCR Stress Parameters">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Inp label="Baseline DSCR" type="number" step="0.01" value={baselineDSCR} onChange={e => setBaselineDSCR(e.target.value)} />
                <Sel label="Sector (haircut profile)" value={dscrSector} onChange={e => setDscrSector(e.target.value)}>
                  {['Renewable Energy', 'Toll Road', 'Port', 'Airport', 'Water'].map(s => <option key={s}>{s}</option>)}
                </Sel>
              </div>
            </Section>
            {covenantBreach && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-bold">
                Covenant Breach Warning: Combined stress DSCR ({dscrComb}) falls below 1.0x — loan covenant breach likely. Immediate review required.
              </div>
            )}
            <Row>
              <KpiCard label="Baseline DSCR" value={baseline.toFixed(2) + 'x'} sub="pre-stress" color="emerald" />
              <KpiCard label="DSCR Physical Stress" value={dscrPhys.toFixed(3) + 'x'} sub={`-${(hc.phys * 100).toFixed(0)}% haircut`} color={dscrPhys >= 1.0 ? 'emerald' : 'red'} />
              <KpiCard label="DSCR Transition Stress" value={dscrTrans.toFixed(3) + 'x'} sub={`-${(hc.trans * 100).toFixed(0)}% haircut`} color={dscrTrans >= 1.0 ? 'emerald' : 'red'} />
              <KpiCard label="DSCR Combined Stress" value={dscrComb.toFixed(3) + 'x'} sub="phys + trans overlay" color={dscrComb >= 1.0 ? 'emerald' : 'red'} />
            </Row>
            <Section title="DSCR Across Scenarios">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={dscrBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="scenario" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, Math.max(2, baseline + 0.5)]} />
                  <Tooltip />
                  <Bar dataKey="dscr" name="DSCR">
                    {dscrBarData.map((d, i) => (
                      <Cell key={i} fill={d.dscr >= 1.0 ? '#059669' : '#dc2626'} />
                    ))}
                  </Bar>
                  <Line type="monotone" stroke="#dc2626" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="DSCR Combined vs Carbon Price Sensitivity">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={dscrLineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="carbon_price" label={{ value: 'Carbon Price ($/tCO₂)', position: 'insideBottom', offset: -2, fontSize: 11 }} />
                  <YAxis domain={[0.5, baseline + 0.3]} label={{ value: 'DSCR', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="dscr" stroke="#059669" strokeWidth={2} name="DSCR Combined" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 5: Blended Finance & Labels ── */}
        {tab === 4 && (
          <div>
            <Section title="Blended Finance Structure">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Sel label="Structure Type" value={blendStructure} onChange={e => setBlendStructure(e.target.value)}>
                  <option value="first_loss">First Loss Tranche</option>
                  <option value="guarantee">Guarantee</option>
                  <option value="concessional">Concessional Loan</option>
                  <option value="grant">Grant Co-financing</option>
                  <option value="equity_plus">Equity + Mezzanine</option>
                </Sel>
              </div>
              <Row>
                <KpiCard label="Crowding-In Ratio" value={`${crowdIn}x`} sub="private per DFI dollar" color={crowdIn >= 3 ? 'emerald' : crowdIn >= 1.5 ? 'yellow' : 'red'} />
                <KpiCard label="Private Finance Mobilised" value={`$${(privateMobilised / 1e6).toFixed(0)}M`} sub="senior + mezz + equity" color="emerald" />
                <KpiCard label="OECD Additionality" value={`${additionality}/100`} sub="additionality score" color={additionality >= 70 ? 'emerald' : 'yellow'} />
                <KpiCard label="Blended IRR" value={`${blendedIRR}%`} sub="vs private ${privateIRR}%" color="gray" />
              </Row>
            </Section>
            <Section title="Tranche Breakdown (% of Total Financing)">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={trancheData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="structure" />
                  <YAxis unit="%" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="senior" stackId="a" fill="#1e40af" name="Senior Debt" />
                  <Bar dataKey="mezz" stackId="a" fill="#0284c7" name="Mezzanine" />
                  <Bar dataKey="first_loss" stackId="a" fill="#dc2626" name="First Loss" />
                  <Bar dataKey="equity" stackId="a" fill="#059669" name="Equity" />
                  <Bar dataKey="grant" stackId="a" fill="#ca8a04" name="Grant" />
                  <Bar dataKey="mdb" stackId="a" fill="#7c3aed" name="MDB / DFI" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Climate Labels & SDG Alignment">
              <div className="flex flex-wrap gap-3 mb-4">
                {[
                  { label: 'CBI Certified', color: 'emerald', desc: 'Climate Bonds Initiative' },
                  { label: 'ICMA GBF Aligned', color: 'emerald', desc: 'Green Bond Framework' },
                  { label: 'SDG Labelled', color: 'blue', desc: 'Multi-SDG contribution' },
                ].map(b => (
                  <div key={b.label} className={`bg-${b.color}-50 border border-${b.color}-200 rounded-lg px-4 py-3`}>
                    <div className={`text-xs font-bold text-${b.color}-700`}>{b.label}</div>
                    <div className="text-xs text-gray-400 mt-0.5">{b.desc}</div>
                  </div>
                ))}
              </div>
              <div className="flex flex-wrap gap-2 mb-4">
                {sdgChips.map(sdg => (
                  <span key={sdg} className="bg-emerald-100 text-emerald-800 border border-emerald-200 rounded-full px-3 py-1 text-xs font-bold">{sdg}</span>
                ))}
              </div>
              <Row>
                <KpiCard label="Blended Project IRR" value={`${blendedIRR}%`} sub="risk-adjusted" color="emerald" />
                <KpiCard label="Private Sector IRR" value={`${privateIRR}%`} sub="hurdle rate" color="gray" />
                <KpiCard label="IRR Enhancement" value={`+${(privateIRR - blendedIRR).toFixed(1)}%`} sub="from concessional capital" color="emerald" />
              </Row>
            </Section>
            <div className="flex justify-end mt-4">
              <Btn onClick={() => alert('Infrastructure finance report exported (demo)')}>Export Report</Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
