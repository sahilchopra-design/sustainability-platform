/**
 * AviationClimatePage.jsx  —  Route: /aviation-climate
 * Sprint 22 E49 — CORSIA Phase 2 / SAF Mandates / EU ETS Aviation / IATA NZC / Fleet Profile
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine,
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

const TABS = ['CORSIA Phase 2', 'SAF Mandates', 'EU ETS Aviation', 'IATA Net Zero', 'Fleet Profile & Summary'];
const CORSIA_SCHEMES = ['VERRA VCS', 'Gold Standard', 'CAR', 'ACR', 'Plan Vivo', 'SOCIALCARBON', 'REDD+ VCS', 'ART TREES'];

export default function AviationClimatePage() {
  const [tab, setTab] = useState(0);

  // Tab 1
  const [icaoCode, setIcaoCode] = useState('BAW');
  const [baselineCO2, setBaselineCO2] = useState('5800000');
  const [actualCO2, setActualCO2] = useState('6400000');
  const [eligibleRoutes, setEligibleRoutes] = useState('78');
  const [corsiaResult, setCorsiaResult] = useState(null);
  const [checkedSchemes, setCheckedSchemes] = useState(new Set(['VERRA VCS', 'Gold Standard']));

  // Tab 2
  const [jurisdiction, setJurisdiction] = useState('EU ReFuelEU');
  const [currentSAF, setCurrentSAF] = useState('2.5');
  const [safPathway, setSafPathway] = useState('HEFA');
  const [lifetimeCI, setLifetimeCI] = useState('38');

  // Tab 3
  const [intraEEACO2, setIntraEEACO2] = useState('4200000');
  const [etsYear, setEtsYear] = useState('2025');
  const [corsiaExempt, setCorsiaExempt] = useState(false);

  // Tab 4
  const [fleetIntensity, setFleetIntensity] = useState('85');

  const runCORSIA = useCallback(async () => {
    try {
      const res = await axios.post(`${API}/api/v1/aviation/corsia-phase2`, {
        icao_code: icaoCode, baseline_tco2: +baselineCO2, actual_tco2: +actualCO2,
        eligible_routes_pct: +eligibleRoutes,
      });
      setCorsiaResult(res.data);
    } catch {
      const baseline = +baselineCO2;
      const actual = +actualCO2;
      const elig = +eligibleRoutes / 100;
      const growth = ((actual - baseline) / baseline * 100).toFixed(2);
      const obligation = Math.round(Math.max(0, actual - baseline) * elig);
      const cost = Math.round(obligation * 4.5);
      setCorsiaResult({ obligation, cost, growth_factor: growth, phase: 'Phase 2 (Mandatory)' });
    }
  }, [icaoCode, baselineCO2, actualCO2, eligibleRoutes]);

  const toggleScheme = s => setCheckedSchemes(prev => {
    const n = new Set(prev);
    n.has(s) ? n.delete(s) : n.add(s);
    return n;
  });

  // CORSIA regional BarChart
  const corsiaRegions = ['North America', 'Europe', 'Asia-Pacific', 'Middle East', 'Latin America', 'Africa'].map((r, i) => ({
    region: r,
    baseline: Math.round((+baselineCO2 / 6) * (0.8 + seed(i, 111) * 0.4)),
    actual: Math.round((+actualCO2 / 6) * (0.8 + seed(i + 10, 111) * 0.4)),
  }));

  // Tab 2: SAF mandates
  const safMandateData = Array.from({ length: 6 }, (_, i) => {
    const yr = 2025 + i * 5;
    return {
      year: yr,
      EU: yr <= 2025 ? 2 : yr <= 2030 ? 6 : yr <= 2035 ? 20 : yr <= 2040 ? 34 : yr <= 2045 ? 42 : 70,
      US: yr <= 2025 ? 3 : yr <= 2030 ? 10 : yr <= 2035 ? 15 : yr <= 2040 ? 20 : yr <= 2045 ? 25 : 35,
      UK: yr <= 2025 ? 2 : yr <= 2030 ? 10 : yr <= 2035 ? 22 : yr <= 2040 ? 38 : yr <= 2045 ? 52 : 75,
    };
  });
  const targetMap = { 'EU ReFuelEU': 6, 'US IRA': 10, 'UK SAF mandate': 10 };
  const safTarget2030 = targetMap[jurisdiction] || 6;
  const safGap = +(safTarget2030 - +currentSAF).toFixed(1);
  const safPenalty = safGap > 0 ? Math.round(safGap * 0.01 * 2e8 * 0.5) : 0;
  const jetFuelLCI = 89;
  const safCI = +lifetimeCI;
  const ira45Z = safCI < jetFuelLCI ? ((jetFuelLCI - safCI) / jetFuelLCI * 1.75).toFixed(2) : '0.00';
  const totalCredit = Math.round(+ira45Z * 8e6 * 3.785 / 1000);

  // Tab 3: EU ETS Aviation
  const co2Val = +intraEEACO2;
  const freeAllocPct = { 2024: 0.85, 2025: 0.75, 2026: 0.60, 2027: 0.45, 2028: 0.30, 2029: 0.15, 2030: 0 }[+etsYear] ?? 0;
  const freeAlloc = Math.round(co2Val * freeAllocPct);
  const surrenderGap = co2Val - freeAlloc;
  const euaCost = Math.round(surrenderGap * 65);
  const etsTimelineData = [2024, 2025, 2026, 2027, 2028, 2029].map(y => ({
    year: String(y),
    free: Math.round(co2Val * ({ 2024: 0.85, 2025: 0.75, 2026: 0.60, 2027: 0.45, 2028: 0.30, 2029: 0.15 }[y] ?? 0)),
    obligation: Math.round(co2Val * ({ 2024: 0.15, 2025: 0.25, 2026: 0.40, 2027: 0.55, 2028: 0.70, 2029: 0.85 }[y] ?? 0)),
  }));

  // Tab 4: IATA NZC
  const nzcData = Array.from({ length: 7 }, (_, i) => {
    const yr = 2020 + i * 5;
    const total = 100;
    const eff = Math.round(total * (0.1 + i * 0.06));
    const saf = Math.round(total * (0.02 + i * 0.09));
    const removal = Math.round(total * (i * 0.025));
    const offset = total - eff - saf - removal;
    return { year: yr, efficiency: eff, saf, carbon_removal: removal, offset: Math.max(0, offset) };
  });
  const alignScore = Math.round(30 + seed(99, +fleetIntensity) * 55);
  const effGap = +(seed(10, +fleetIntensity) * 20 + 5).toFixed(1);
  const safGapIATA = +(seed(11, +fleetIntensity) * 25 + 10).toFixed(1);
  const offsetGap = +(seed(12, +fleetIntensity) * 15 + 5).toFixed(1);

  const fleetTable = [
    { type: 'B737-800', count: 45, age: 12, stranding_year: 2033, stranded_value: 1.2 },
    { type: 'A320-200', count: 38, age: 10, stranding_year: 2035, stranded_value: 0.9 },
    { type: 'B777-300', count: 12, age: 8, stranding_year: 2038, stranded_value: 2.1 },
    { type: 'A350-900', count: 15, age: 3, stranding_year: 2045, stranded_value: 0.3 },
    { type: 'B787-9', count: 18, age: 5, stranding_year: 2042, stranded_value: 0.4 },
  ];
  const totalStranded = fleetTable.reduce((s, f) => s + f.stranded_value, 0).toFixed(1);

  // Tab 5: Fleet profile
  const s5 = 54321;
  const intensityData = [
    { type: 'A220', co2: 68 }, { type: 'A320neo', co2: 72 }, { type: 'B737 MAX', co2: 74 },
    { type: 'A350', co2: 55 }, { type: 'B787', co2: 60 }, { type: 'B777', co2: 88 },
    { type: 'A380', co2: 95 }, { type: 'B737-800', co2: 92 },
  ];
  const safCompat = [
    { name: 'SAF Compatible', value: 78 }, { name: 'Not Compatible', value: 22 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Aviation Climate Risk</h1>
          <p className="text-sm text-gray-500 mt-1">CORSIA Phase 2 · SAF Mandates (IRA/ReFuelEU/UK) · EU ETS Aviation · IATA Net Zero 2050 · Fleet Transition</p>
        </div>

        <div className="flex gap-1 mb-6 bg-white border border-gray-200 rounded-lg p-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors ${tab === i ? 'bg-emerald-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* ── TAB 1: CORSIA Phase 2 ── */}
        {tab === 0 && (
          <div>
            <Section title="Operator & Emissions Data">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Inp label="ICAO Operator Code" value={icaoCode} onChange={e => setIcaoCode(e.target.value)} />
                <Inp label="Baseline tCO₂ (2019 basis)" type="number" value={baselineCO2} onChange={e => setBaselineCO2(e.target.value)} />
                <Inp label="Actual tCO₂ (reporting year)" type="number" value={actualCO2} onChange={e => setActualCO2(e.target.value)} />
                <Inp label="Eligible Routes (%)" type="number" value={eligibleRoutes} onChange={e => setEligibleRoutes(e.target.value)} />
              </div>
              <div className="flex items-center gap-4 mb-4">
                <div className="bg-emerald-100 border border-emerald-300 rounded px-3 py-1 text-xs font-bold text-emerald-800">CORSIA Phase 2 — MANDATORY (2024–2026)</div>
                <Btn onClick={runCORSIA}>Calculate CORSIA Obligation</Btn>
              </div>
            </Section>
            {corsiaResult && (
              <Row>
                <KpiCard label="Offsetting Obligation" value={`${(corsiaResult.obligation / 1000).toFixed(0)}k tCO₂`} sub="required offsets" color="red" />
                <KpiCard label="Offset Cost (USD)" value={`$${(corsiaResult.cost / 1e6).toFixed(1)}M`} sub="@ $4.50/tCO₂" color="red" />
                <KpiCard label="Traffic Growth Factor" value={`${corsiaResult.growth_factor}%`} sub="vs baseline" color="gray" />
                <KpiCard label="Phase Status" value="Phase 2" sub="Mandatory 2024–2026" color="emerald" />
              </Row>
            )}
            <Section title="Eligible Schemes (CORSIA Approved)">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-4">
                {CORSIA_SCHEMES.map(s => (
                  <label key={s} className="flex items-center gap-2 cursor-pointer">
                    <input type="checkbox" checked={checkedSchemes.has(s)} onChange={() => toggleScheme(s)} className="accent-emerald-600" />
                    <span className="text-xs text-gray-700">{s}</span>
                  </label>
                ))}
              </div>
              <div className="text-xs text-gray-500">{checkedSchemes.size} of {CORSIA_SCHEMES.length} eligible schemes used</div>
            </Section>
            <Section title="Baseline vs Actual Emissions by Route Region">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={corsiaRegions}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="region" tick={{ fontSize: 10 }} />
                  <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={v => `${(v / 1e6).toFixed(2)}M tCO₂`} />
                  <Legend />
                  <Bar dataKey="baseline" fill="#d1fae5" name="Baseline (2019)" />
                  <Bar dataKey="actual" fill="#059669" name="Actual" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 2: SAF Mandates ── */}
        {tab === 1 && (
          <div>
            <Section title="SAF Mandate Parameters">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="Jurisdiction" value={jurisdiction} onChange={e => setJurisdiction(e.target.value)}>
                  <option>EU ReFuelEU</option>
                  <option>US IRA</option>
                  <option>UK SAF mandate</option>
                </Sel>
                <Inp label="Current SAF Blend %" type="number" value={currentSAF} onChange={e => setCurrentSAF(e.target.value)} />
              </div>
              <Row>
                <KpiCard label="2030 SAF Target" value={`${safTarget2030}%`} sub={jurisdiction} color="emerald" />
                <KpiCard label="Compliance Gap (2030)" value={`${safGap}%`} sub="blend shortfall" color={safGap > 0 ? 'red' : 'emerald'} />
                <KpiCard label="Est. Penalty (2030)" value={`$${(safPenalty / 1e6).toFixed(1)}M`} sub="non-compliance cost" color={safPenalty > 0 ? 'red' : 'emerald'} />
              </Row>
            </Section>
            <Section title="SAF Mandate Trajectories 2025–2050 (EU / US / UK)">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={safMandateData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis unit="%" />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="EU" fill="#059669" name="EU ReFuelEU" />
                  <Bar dataKey="US" fill="#0284c7" name="US IRA" />
                  <Bar dataKey="UK" fill="#7c3aed" name="UK SAF Mandate" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="IRA Section 45Z SAF Tax Credit">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="SAF Pathway" value={safPathway} onChange={e => setSafPathway(e.target.value)}>
                  {['HEFA', 'ATJ-IsoOH', 'FT-SPK', 'SIP', 'PtL'].map(p => <option key={p}>{p}</option>)}
                </Sel>
                <Inp label="Lifecycle CI (gCO₂eq/MJ)" type="number" value={lifetimeCI} onChange={e => setLifetimeCI(e.target.value)} />
              </div>
              <Row>
                <KpiCard label="Jet Fuel CI (reference)" value="89 gCO₂/MJ" sub="conventional" color="gray" />
                <KpiCard label="SAF CI (lifecycle)" value={`${lifetimeCI} gCO₂/MJ`} sub="this pathway" color="gray" />
                <KpiCard label="45Z Credit (USD/gge)" value={`$${ira45Z}`} sub="max $1.75/gge" color="emerald" />
                <KpiCard label="Total Annual Credit" value={`$${(totalCredit / 1e6).toFixed(1)}M`} sub="est. fleet volume" color="emerald" />
              </Row>
            </Section>
          </div>
        )}

        {/* ── TAB 3: EU ETS Aviation ── */}
        {tab === 2 && (
          <div>
            <Section title="EU ETS Aviation Parameters">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Inp label="Intra-EEA CO₂ (tCO₂)" type="number" value={intraEEACO2} onChange={e => setIntraEEACO2(e.target.value)} />
                <Sel label="Reporting Year" value={etsYear} onChange={e => setEtsYear(e.target.value)}>
                  {[2024, 2025, 2026, 2027, 2028, 2029].map(y => <option key={y}>{y}</option>)}
                </Sel>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-gray-600">Art. 10 CORSIA Exemption</label>
                  <button onClick={() => setCorsiaExempt(!corsiaExempt)}
                    className={`px-3 py-2 rounded text-sm font-medium border ${corsiaExempt ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-700 border-gray-300'}`}>
                    {corsiaExempt ? 'Exemption ON' : 'Exemption OFF'}
                  </button>
                </div>
              </div>
              <Row>
                <KpiCard label="Free Allocation (EUAs)" value={freeAlloc.toLocaleString()} sub={`${Math.round(freeAllocPct * 100)}% free in ${etsYear}`} color="emerald" />
                <KpiCard label="Surrender Gap (EUAs)" value={surrenderGap.toLocaleString()} sub="must surrender" color={surrenderGap > 0 ? 'red' : 'emerald'} />
                <KpiCard label="Surrender Cost" value={`€${(euaCost / 1e6).toFixed(1)}M`} sub="@ €65/EUA" color={euaCost > 0 ? 'red' : 'emerald'} />
                <KpiCard label="CORSIA Interaction" value={corsiaExempt ? 'Exempt (Art.10)' : 'Full ETS applies'} sub="intra-EEA" color={corsiaExempt ? 'emerald' : 'gray'} />
              </Row>
            </Section>
            <Section title="Free Allocation Phase-Down vs ETS Obligation (2024–2029)">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={etsTimelineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={v => `${(v / 1e6).toFixed(1)}M`} />
                  <Tooltip formatter={v => `${(v / 1e6).toFixed(2)}M tCO₂`} />
                  <Legend />
                  <Bar dataKey="free" stackId="a" fill="#d1fae5" name="Free Allowances" />
                  <Bar dataKey="obligation" stackId="a" fill="#059669" name="Must Surrender" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 4: IATA Net Zero ── */}
        {tab === 3 && (
          <div>
            <Section title="IATA Net Zero Carbon 2050 Pathway">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Inp label="Current Fleet CO₂ Intensity (g/pkm)" type="number" value={fleetIntensity} onChange={e => setFleetIntensity(e.target.value)} />
              </div>
              <Row>
                <KpiCard label="NZC Alignment Score" value={`${alignScore}/100`} sub="IATA benchmark" color={alignScore >= 70 ? 'emerald' : alignScore >= 50 ? 'yellow' : 'red'} />
                <KpiCard label="Efficiency Gap" value={`${effGap}%`} sub="vs IATA trajectory" color="red" />
                <KpiCard label="SAF Gap" value={`${safGapIATA}%`} sub="blend required" color="red" />
                <KpiCard label="Offset Gap" value={`${offsetGap} MtCO₂`} sub="residual offsets needed" color="red" />
              </Row>
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={nzcData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis unit="%" />
                  <Tooltip />
                  <Legend />
                  <Area type="monotone" dataKey="efficiency" stackId="1" stroke="#059669" fill="#d1fae5" name="Technology & Efficiency" />
                  <Area type="monotone" dataKey="saf" stackId="1" stroke="#0284c7" fill="#bfdbfe" name="SAF" />
                  <Area type="monotone" dataKey="carbon_removal" stackId="1" stroke="#7c3aed" fill="#ede9fe" name="Carbon Removal" />
                  <Area type="monotone" dataKey="offset" stackId="1" stroke="#ca8a04" fill="#fef9c3" name="Offset (residual)" />
                </AreaChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Aircraft Stranding Risk">
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {['Aircraft Type', 'Count', 'Avg Age (yr)', 'Stranding Year', 'Stranded Value ($B)', 'Risk'].map(h => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left font-semibold text-gray-600">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {fleetTable.map((f, i) => (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="border border-gray-200 px-3 py-2 font-medium">{f.type}</td>
                        <td className="border border-gray-200 px-3 py-2">{f.count}</td>
                        <td className="border border-gray-200 px-3 py-2">{f.age}</td>
                        <td className="border border-gray-200 px-3 py-2">{f.stranding_year}</td>
                        <td className="border border-gray-200 px-3 py-2">${f.stranded_value}B</td>
                        <td className="border border-gray-200 px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${f.stranding_year < 2035 ? 'bg-red-100 text-red-700' : f.stranding_year < 2040 ? 'bg-yellow-100 text-yellow-700' : 'bg-emerald-100 text-emerald-700'}`}>
                            {f.stranding_year < 2035 ? 'High' : f.stranding_year < 2040 ? 'Medium' : 'Low'}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="mt-3">
                <KpiCard label="Total Stranded Value" value={`$${totalStranded}B`} sub="early retirement costs" color="red" />
              </div>
            </Section>
          </div>
        )}

        {/* ── TAB 5: Fleet Profile & Summary ── */}
        {tab === 4 && (
          <div>
            <Section title="CO₂ Intensity by Aircraft Type">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={intensityData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="type" tick={{ fontSize: 11 }} />
                  <YAxis domain={[50, 100]} unit=" g/pkm" />
                  <Tooltip />
                  <ReferenceLine y={75} stroke="#dc2626" strokeDasharray="4 2" label={{ value: 'Industry avg', position: 'right', fontSize: 10 }} />
                  <Bar dataKey="co2" name="CO₂ Intensity (g/pkm)">
                    {intensityData.map((d, i) => (
                      <Cell key={i} fill={d.co2 < 75 ? '#059669' : d.co2 < 85 ? '#ca8a04' : '#dc2626'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <Section title="SAF Compatibility">
                <ResponsiveContainer width="100%" height={220}>
                  <PieChart>
                    <Pie data={safCompat} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={d => `${d.name}: ${d.value}%`}>
                      <Cell fill="#059669" />
                      <Cell fill="#dc2626" />
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </Section>
              <Section title="Fleet Summary KPIs">
                <div className="grid grid-cols-2 gap-3">
                  <KpiCard label="High Emission Aircraft" value="28%" sub=">85 g CO₂/pkm" color="red" />
                  <KpiCard label="Hydrogen-Ready" value="0" sub="no H₂ models yet" color="gray" />
                  <KpiCard label="Total Transition Cost" value="$4.2B" sub="fleet modernisation" color="gray" />
                  <KpiCard label="SAF Compatible" value="78%" sub="of fleet by seat" color="emerald" />
                </div>
              </Section>
            </div>
            <Section title="Framework Compliance Summary">
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {['Framework', 'Status', 'Key Gap', 'Priority'].map(h => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left font-semibold text-gray-600">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['CORSIA Phase 2', 'Partial', 'Offset procurement needed', 'High'],
                      ['EU ReFuelEU SAF', 'Non-Compliant', 'SAF blend 2.5% vs 6% (2030)', 'High'],
                      ['EU ETS Aviation', 'Compliant', 'Free allocation declining', 'Medium'],
                      ['IATA NZC 2050', 'Behind', 'Efficiency -12% vs pathway', 'High'],
                      ['UK SAF Mandate', 'Partial', 'Procurement partnerships needed', 'Medium'],
                    ].map(([fw, st, gap, pri], i) => (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="border border-gray-200 px-3 py-2 font-medium">{fw}</td>
                        <td className="border border-gray-200 px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${st === 'Compliant' ? 'bg-emerald-100 text-emerald-700' : st === 'Partial' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>{st}</span>
                        </td>
                        <td className="border border-gray-200 px-3 py-2 text-gray-600">{gap}</td>
                        <td className="border border-gray-200 px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${pri === 'High' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{pri}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <div className="flex justify-end mt-4">
              <Btn onClick={() => alert('Aviation climate report exported (demo)')}>Export Report</Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
