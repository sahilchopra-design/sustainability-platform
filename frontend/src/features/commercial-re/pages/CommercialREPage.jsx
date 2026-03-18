/**
 * CommercialREPage.jsx  —  Route: /commercial-re
 * Sprint 22 E50 — CRREM 2.0 / EPC & EPBD / GRESB / REFI & NABERS / Retrofit & Green Lease
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, Cell,
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

const TABS = ['CRREM 2.0', 'EPC & EPBD 2024', 'GRESB Real Estate', 'REFI & NABERS', 'Retrofit & Green Lease'];

// CRREM approximate pathway data (kgCO₂/m²/yr) by asset type
const CRREM_PATHWAYS = {
  office:     [35, 30, 26, 22, 18, 14],
  retail:     [40, 35, 30, 25, 21, 17],
  logistics:  [28, 24, 20, 17, 14, 11],
  hotel:      [50, 43, 37, 31, 25, 19],
  industrial: [30, 26, 22, 18, 15, 12],
};

const EPC_RATINGS = ['A', 'B', 'C', 'D', 'E', 'F', 'G'];
const EPC_THRESHOLDS = { UK: [0, 50, 75, 100, 125, 150, 200], DE: [0, 30, 50, 75, 100, 130, 160], FR: [0, 50, 90, 150, 230, 330, 450] };
const EPC_COLORS = ['#059669', '#16a34a', '#84cc16', '#ca8a04', '#ea580c', '#dc2626', '#9f1239'];

const GREEN_LEASE_CLAUSES = [
  'Metering & monitoring data sharing', 'Energy efficiency obligations', 'Sub-metering per floor',
  'Water efficiency targets', 'Waste reduction & reporting', 'EPC upgrade commitment',
  'Green fit-out standards', 'Cooling & heating efficiency', 'Renewable energy procurement',
  'Biodiversity & wellbeing provisions', 'Carbon reduction targets', 'GRESB data provision',
];

export default function CommercialREPage() {
  const [tab, setTab] = useState(0);

  // Tab 1
  const [assetType, setAssetType] = useState('office');
  const [country, setCountry] = useState('UK');
  const [energyIntensity, setEnergyIntensity] = useState('185');
  const [co2Intensity, setCo2Intensity] = useState('38');
  const [crremResult, setCrremResult] = useState(null);

  // Tab 2
  const [epcCountry, setEpcCountry] = useState('UK');
  const [buildingType, setBuildingType] = useState('office');
  const [primaryEnergy, setPrimaryEnergy] = useState('165');

  // Tab 3
  const [mgmtScore, setMgmtScore] = useState('22');
  const [perfScore, setPerfScore] = useState('54');
  const [peerGroup, setPeerGroup] = useState('Office Europe');

  // Tab 4
  const [naberType, setNaberType] = useState('office');
  const [naberStars, setNaberStars] = useState(3);

  // Tab 5
  const [leaseClauses, setLeaseClauses] = useState(new Set(['Metering & monitoring data sharing', 'Energy efficiency obligations', 'EPC upgrade commitment', 'Carbon reduction targets']));

  const runCRREM = useCallback(async () => {
    try {
      const res = await axios.post(`${API}/api/v1/commercial-re/crrem`, {
        asset_type: assetType, country, energy_intensity: +energyIntensity, co2_intensity: +co2Intensity,
      });
      setCrremResult(res.data);
    } catch {
      const pathway = CRREM_PATHWAYS[assetType] || CRREM_PATHWAYS.office;
      const current = +co2Intensity;
      let strandingYear = 2045;
      for (let i = 0; i < pathway.length; i++) {
        const yr = 2025 + i * 5;
        if (current > pathway[i] * (1 + i * 0.02)) { strandingYear = yr; break; }
      }
      const gap = +(current - pathway[0]).toFixed(1);
      setCrremResult({ stranding_year: strandingYear, overconsumption_gap: gap, risk: gap > 10 ? 'High' : gap > 0 ? 'Medium' : 'Low' });
    }
  }, [assetType, country, energyIntensity, co2Intensity]);

  const crremPathwayData = Array.from({ length: 6 }, (_, i) => {
    const yr = 2025 + i * 5;
    const path = CRREM_PATHWAYS[assetType] || CRREM_PATHWAYS.office;
    return {
      year: yr,
      pathway: path[i],
      asset: Math.max(5, +co2Intensity - i * 1.5),
    };
  });

  const strandColor = crremResult ? (crremResult.stranding_year < 2030 ? 'red' : crremResult.stranding_year < 2040 ? 'yellow' : 'emerald') : 'gray';

  // Tab 2: EPC
  const thresholds = EPC_THRESHOLDS[epcCountry] || EPC_THRESHOLDS.UK;
  let epcRating = 'G';
  for (let i = 0; i < thresholds.length - 1; i++) {
    if (+primaryEnergy <= thresholds[i + 1]) { epcRating = EPC_RATINGS[i]; break; }
  }
  const epcIdx = EPC_RATINGS.indexOf(epcRating);
  const epcColor = EPC_COLORS[epcIdx] || '#9f1239';
  const epbdRequired = epcIdx >= 4; // E or worse
  const epcBarData = EPC_RATINGS.map((r, i) => ({
    rating: r, energy: thresholds[i + 1] || 250, current: r === epcRating,
  }));

  // Tab 3: GRESB
  const mgmt = Math.min(30, Math.max(0, +mgmtScore));
  const perf = Math.min(70, Math.max(0, +perfScore));
  const total = mgmt + perf;
  const stars = total >= 90 ? 5 : total >= 75 ? 4 : total >= 60 ? 3 : total >= 45 ? 2 : 1;
  const peerPct = Math.round(30 + seed(1, total) * 60);
  const gresb5 = [
    { area: 'Energy', score: Math.round(perf * 0.28) },
    { area: 'GHG', score: Math.round(perf * 0.24) },
    { area: 'Water', score: Math.round(perf * 0.18) },
    { area: 'Waste', score: Math.round(perf * 0.16) },
    { area: 'Land', score: Math.round(perf * 0.14) },
  ];
  const dataCoverage = Math.round(55 + seed(2, total) * 40);

  // Tab 4: REFI & NABERS
  const physRisk = Math.round(30 + seed(3, 5555) * 55);
  const transRisk = Math.round(25 + seed(4, 5555) * 60);
  const composite = Math.round((physRisk * 0.5 + transRisk * 0.5));
  const refiTier = composite >= 80 ? 5 : composite >= 65 ? 4 : composite >= 50 ? 3 : composite >= 35 ? 2 : 1;
  const tierColors = { 1: 'emerald', 2: 'green', 3: 'yellow', 4: 'orange', 5: 'red' };
  const nabersPeerAvg = 3.5;
  const nabersDiff = +(naberStars - nabersPeerAvg).toFixed(1);
  const nabersBarData = [
    { label: 'Asset NABERS', value: naberStars },
    { label: 'Peer Average', value: nabersPeerAvg },
  ];

  // Tab 5: Retrofit
  const retrofitMeasures = [
    { measure: 'LED Lighting Upgrade', capex: 18, energySaving: 15, npv: 42, irr: 28, priority: 'High' },
    { measure: 'BMS Controls Upgrade', capex: 35, energySaving: 12, npv: 38, irr: 22, priority: 'High' },
    { measure: 'HVAC Modernisation', capex: 120, energySaving: 25, npv: 95, irr: 18, priority: 'High' },
    { measure: 'Building Fabric Insulation', capex: 85, energySaving: 20, npv: 65, irr: 15, priority: 'Medium' },
    { measure: 'Solar PV Rooftop', capex: 60, energySaving: 18, npv: 72, irr: 19, priority: 'High' },
    { measure: 'Heat Pump Installation', capex: 95, energySaving: 22, npv: 55, irr: 13, priority: 'Medium' },
    { measure: 'EV Charging Points', capex: 45, energySaving: 2, npv: 18, irr: 8, priority: 'Low' },
    { measure: 'Green Roof', capex: 40, energySaving: 4, npv: 12, irr: 7, priority: 'Low' },
  ].sort((a, b) => b.irr - a.irr);

  const totalRetrofitCapex = retrofitMeasures.reduce((s, m) => s + m.capex, 0);
  const leaseScore = Math.round((leaseClauses.size / GREEN_LEASE_CLAUSES.length) * 100);
  const leaseGrade = leaseScore >= 80 ? 'A' : leaseScore >= 65 ? 'B' : leaseScore >= 50 ? 'C' : leaseScore >= 35 ? 'D' : 'F';
  const greenPremium = +(leaseClauses.size * 0.4).toFixed(1);
  const brownDiscount = +(Math.max(0, 12 - leaseClauses.size) * 0.5).toFixed(1);

  const toggleClause = c => setLeaseClauses(prev => {
    const n = new Set(prev); n.has(c) ? n.delete(c) : n.add(c); return n;
  });

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Commercial Real Estate Climate Risk</h1>
          <p className="text-sm text-gray-500 mt-1">CRREM 2.0 · EPC & EPBD 2024 · GRESB · REFI & NABERS · Retrofit & Green Lease</p>
        </div>

        <div className="flex gap-1 mb-6 bg-white border border-gray-200 rounded-lg p-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors ${tab === i ? 'bg-emerald-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* ── TAB 1: CRREM 2.0 ── */}
        {tab === 0 && (
          <div>
            <Section title="Asset Parameters">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Sel label="Asset Type" value={assetType} onChange={e => setAssetType(e.target.value)}>
                  {['office', 'retail', 'logistics', 'hotel', 'industrial'].map(t => <option key={t}>{t}</option>)}
                </Sel>
                <Sel label="Country" value={country} onChange={e => setCountry(e.target.value)}>
                  {['UK', 'DE', 'FR', 'NL', 'US', 'AU'].map(c => <option key={c}>{c}</option>)}
                </Sel>
                <Inp label="Energy Intensity (kWh/m²/yr)" type="number" value={energyIntensity} onChange={e => setEnergyIntensity(e.target.value)} />
                <Inp label="CO₂ Intensity (kgCO₂/m²/yr)" type="number" value={co2Intensity} onChange={e => setCo2Intensity(e.target.value)} />
                <div className="flex items-end"><Btn onClick={runCRREM}>Run CRREM Assessment</Btn></div>
              </div>
            </Section>
            {crremResult && (
              <Row>
                <div className={`bg-${strandColor}-50 border border-${strandColor}-200 rounded-lg p-4`}>
                  <div className="text-xs text-gray-500 mb-1">Stranding Year</div>
                  <div className={`text-3xl font-black text-${strandColor}-700`}>{crremResult.stranding_year}</div>
                </div>
                <KpiCard label="Stranding Risk" value={crremResult.risk} sub={`CRREM 2.0 — ${assetType}`} color={crremResult.risk === 'High' ? 'red' : crremResult.risk === 'Medium' ? 'yellow' : 'emerald'} />
                <KpiCard label="Overconsumption Gap" value={`${crremResult.overconsumption_gap} kgCO₂`} sub="vs 2025 pathway target" color={crremResult.overconsumption_gap > 0 ? 'red' : 'emerald'} />
                <KpiCard label="CRREM Pathway" value={`${(CRREM_PATHWAYS[assetType] || CRREM_PATHWAYS.office)[0]} kg`} sub="2025 target intensity" color="gray" />
              </Row>
            )}
            <Section title="CRREM Pathway 2025–2050 vs Asset Trajectory">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={crremPathwayData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis unit=" kg" />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="pathway" stroke="#dc2626" strokeWidth={2} name="CRREM Pathway" />
                  <Line type="monotone" dataKey="asset" stroke="#059669" strokeWidth={2} strokeDasharray="5 3" name="Asset Trajectory" />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 2: EPC & EPBD 2024 ── */}
        {tab === 1 && (
          <div>
            <Section title="Building Parameters">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="Country" value={epcCountry} onChange={e => setEpcCountry(e.target.value)}>
                  {['UK', 'DE', 'FR'].map(c => <option key={c}>{c}</option>)}
                </Sel>
                <Sel label="Building Type" value={buildingType} onChange={e => setBuildingType(e.target.value)}>
                  {['office', 'retail', 'logistics', 'hotel', 'industrial'].map(t => <option key={t}>{t}</option>)}
                </Sel>
                <Inp label="Primary Energy (kWh/m²/yr)" type="number" value={primaryEnergy} onChange={e => setPrimaryEnergy(e.target.value)} />
              </div>
            </Section>
            <Row>
              <div className="rounded-lg p-4 border flex flex-col justify-center items-center" style={{ background: epcColor + '22', borderColor: epcColor }}>
                <div className="text-xs text-gray-500 mb-1">EPC Rating</div>
                <div className="text-5xl font-black" style={{ color: epcColor }}>{epcRating}</div>
              </div>
              <KpiCard label="Primary Energy" value={`${primaryEnergy} kWh/m²`} sub="declared consumption" color="gray" />
              <KpiCard label="EPBD 2030 Target" value="EPC C or better" sub="minimum requirement" color="emerald" />
              <KpiCard label="Renovation Required" value={epbdRequired ? 'YES' : 'No'} sub={epbdRequired ? 'EPBD Art.9 obligation' : 'Compliant 2030'} color={epbdRequired ? 'red' : 'emerald'} />
            </Row>
            {epbdRequired && (
              <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 font-medium">
                Warning: Building rated {epcRating} — EPBD 2024 requires renovation to EPC C minimum by 2030. Renovation obligation applies under Article 9(3).
              </div>
            )}
            <Section title="EPC Scale with Asset Position">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={epcBarData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" unit=" kWh" />
                  <YAxis dataKey="rating" type="category" width={30} />
                  <Tooltip />
                  <Bar dataKey="energy" name="Threshold (kWh/m²/yr)">
                    {epcBarData.map((d, i) => (
                      <Cell key={i} fill={d.current ? epcColor : EPC_COLORS[i] + '88'} />
                    ))}
                  </Bar>
                  <ReferenceLine x={+primaryEnergy} stroke="#000" strokeWidth={2} strokeDasharray="4 2" label={{ value: 'This asset', position: 'top', fontSize: 10 }} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="EPBD Renovation Obligations Checklist">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {['Thermal insulation upgrade', 'HVAC efficiency improvement', 'Renewable energy integration', 'Smart building systems', 'EV charging readiness', 'Digital energy monitoring'].map((c, i) => (
                  <div key={i} className={`flex items-center gap-2 p-2 rounded border ${epbdRequired ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50'}`}>
                    <span className={`text-xs ${epbdRequired ? 'text-red-600' : 'text-gray-400'}`}>{epbdRequired ? '✗' : '✓'}</span>
                    <span className="text-xs text-gray-700">{c}</span>
                  </div>
                ))}
              </div>
            </Section>
          </div>
        )}

        {/* ── TAB 3: GRESB Real Estate ── */}
        {tab === 2 && (
          <div>
            <Section title="GRESB Scores">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Inp label="Management Score (0–30)" type="number" min="0" max="30" value={mgmtScore} onChange={e => setMgmtScore(e.target.value)} />
                <Inp label="Performance Score (0–70)" type="number" min="0" max="70" value={perfScore} onChange={e => setPerfScore(e.target.value)} />
                <Sel label="Peer Group" value={peerGroup} onChange={e => setPeerGroup(e.target.value)}>
                  {['Office Europe', 'Retail Europe', 'Industrial Europe', 'Office Global', 'Diversified'].map(g => <option key={g}>{g}</option>)}
                </Sel>
              </div>
              <Row>
                <KpiCard label="Total GRESB Score" value={`${total}/100`} sub="Management + Performance" color={total >= 75 ? 'emerald' : total >= 55 ? 'yellow' : 'red'} />
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex flex-col justify-center">
                  <div className="text-xs text-gray-500 mb-2">Star Rating</div>
                  <div className="flex gap-1">
                    {Array.from({ length: 5 }, (_, i) => (
                      <span key={i} className={`text-2xl ${i < stars ? 'text-yellow-400' : 'text-gray-200'}`}>★</span>
                    ))}
                  </div>
                  <div className="text-xs text-gray-400 mt-1">{stars} Star{stars !== 1 ? 's' : ''}</div>
                </div>
                <KpiCard label="Peer Percentile" value={`${peerPct}th`} sub={peerGroup} color="gray" />
                <KpiCard label="Data Coverage" value={`${dataCoverage}%`} sub="weighted average" color={dataCoverage >= 80 ? 'emerald' : 'yellow'} />
              </Row>
            </Section>
            <Section title="GRESB Performance Areas Breakdown">
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={gresb5}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="area" tick={{ fontSize: 12 }} />
                  <PolarRadiusAxis domain={[0, 25]} tick={{ fontSize: 9 }} />
                  <Radar name="GRESB Score" dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.3} />
                  <Legend />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Management Criteria Scores">
              <div className="overflow-x-auto">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {['Criteria', 'Score', 'Max', 'Status'].map(h => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left font-semibold text-gray-600">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {[
                      ['Leadership & Strategy', mgmt * 0.35, 10.5],
                      ['Policies', mgmt * 0.25, 7.5],
                      ['Reporting', mgmt * 0.22, 6.6],
                      ['Risks & Opportunities', mgmt * 0.18, 5.4],
                    ].map(([c, sc, mx], i) => (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="border border-gray-200 px-3 py-2 font-medium">{c}</td>
                        <td className="border border-gray-200 px-3 py-2">{sc.toFixed(1)}</td>
                        <td className="border border-gray-200 px-3 py-2">{mx.toFixed(1)}</td>
                        <td className="border border-gray-200 px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${sc / mx >= 0.7 ? 'bg-emerald-100 text-emerald-700' : sc / mx >= 0.5 ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
                            {(sc / mx * 100).toFixed(0)}%
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
          </div>
        )}

        {/* ── TAB 4: REFI & NABERS ── */}
        {tab === 3 && (
          <div>
            <Section title="REFI Climate Risk Assessment">
              <Row>
                <KpiCard label="Physical Risk Score" value={`${physRisk}/100`} sub="flood, heat, subsidence" color={physRisk >= 65 ? 'red' : physRisk >= 45 ? 'yellow' : 'emerald'} />
                <KpiCard label="Transition Risk Score" value={`${transRisk}/100`} sub="EPC, carbon, regulation" color={transRisk >= 65 ? 'red' : transRisk >= 45 ? 'yellow' : 'emerald'} />
                <KpiCard label="Composite Risk Score" value={`${composite}/100`} sub="equally weighted" color={composite >= 65 ? 'red' : composite >= 45 ? 'yellow' : 'emerald'} />
                <KpiCard label="REFI Risk Tier" value={`Tier ${refiTier}`} sub={['Minimal', 'Low', 'Medium', 'Elevated', 'Critical'][refiTier - 1]} color={tierColors[refiTier] || 'gray'} />
              </Row>
            </Section>
            <Section title="NABERS Rating">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Sel label="Asset Type" value={naberType} onChange={e => setNaberType(e.target.value)}>
                  {['office', 'retail', 'hotel', 'industrial'].map(t => <option key={t}>{t}</option>)}
                </Sel>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-gray-600">Energy Stars (1–6)</label>
                  <div className="flex gap-1 mt-1">
                    {Array.from({ length: 6 }, (_, i) => (
                      <button key={i} onClick={() => setNaberStars(i + 1)}
                        className={`text-2xl transition-colors ${i < naberStars ? 'text-yellow-400' : 'text-gray-200 hover:text-yellow-200'}`}>★</button>
                    ))}
                  </div>
                  <div className="text-xs text-gray-400">{naberStars} Star{naberStars !== 1 ? 's' : ''} Energy</div>
                </div>
              </div>
              <Row>
                <KpiCard label="NABERS Energy" value={`${naberStars} ★`} sub={naberType} color={naberStars >= 5 ? 'emerald' : naberStars >= 4 ? 'green' : naberStars >= 3 ? 'yellow' : 'red'} />
                <KpiCard label="NABERS Water" value={`${Math.min(6, naberStars + 1)} ★`} sub="water efficiency" color="emerald" />
                <KpiCard label="NABERS Indoor" value={`${Math.max(1, naberStars - 1)} ★`} sub="indoor environment" color="gray" />
                <KpiCard label="vs Peer Avg" value={`${nabersDiff >= 0 ? '+' : ''}${nabersDiff}`} sub="stars above/below avg" color={nabersDiff >= 0 ? 'emerald' : 'red'} />
              </Row>
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={nabersBarData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="label" />
                  <YAxis domain={[0, 6]} ticks={[0, 1, 2, 3, 4, 5, 6]} />
                  <Tooltip />
                  <Bar dataKey="value" name="NABERS Stars">
                    {nabersBarData.map((d, i) => (
                      <Cell key={i} fill={i === 0 ? '#059669' : '#d1fae5'} />
                    ))}
                  </Bar>
                  <ReferenceLine y={nabersPeerAvg} stroke="#ca8a04" strokeDasharray="4 2" label={{ value: 'Peer Avg', position: 'right', fontSize: 10 }} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 5: Retrofit & Green Lease ── */}
        {tab === 4 && (
          <div>
            <Section title="Retrofit Measures — Ranked by IRR">
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-xs border-collapse">
                  <thead>
                    <tr className="bg-gray-50">
                      {['Measure', 'Capex (£/m²)', 'Energy Saving %', 'NPV (£/m²)', 'IRR %', 'Priority'].map(h => (
                        <th key={h} className="border border-gray-200 px-3 py-2 text-left font-semibold text-gray-600">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {retrofitMeasures.map((m, i) => (
                      <tr key={i} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                        <td className="border border-gray-200 px-3 py-2 font-medium">{m.measure}</td>
                        <td className="border border-gray-200 px-3 py-2">£{m.capex}</td>
                        <td className="border border-gray-200 px-3 py-2">{m.energySaving}%</td>
                        <td className="border border-gray-200 px-3 py-2">£{m.npv}</td>
                        <td className="border border-gray-200 px-3 py-2 font-bold">{m.irr}%</td>
                        <td className="border border-gray-200 px-3 py-2">
                          <span className={`px-2 py-0.5 rounded text-xs font-bold ${m.priority === 'High' ? 'bg-emerald-100 text-emerald-700' : m.priority === 'Medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'}`}>{m.priority}</span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Row>
                <KpiCard label="Total Retrofit Capex" value={`£${totalRetrofitCapex}/m²`} sub="full programme" color="gray" />
                <KpiCard label="CRREM Year Improvement" value="+6 yrs" sub="stranding deferred" color="emerald" />
              </Row>
            </Section>
            <Section title="Green Lease Clause Checklist">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 mb-4">
                {GREEN_LEASE_CLAUSES.map(c => (
                  <label key={c} className="flex items-center gap-2 cursor-pointer p-2 rounded border border-gray-200 hover:bg-gray-50">
                    <input type="checkbox" checked={leaseClauses.has(c)} onChange={() => toggleClause(c)} className="accent-emerald-600" />
                    <span className={`text-xs ${leaseClauses.has(c) ? 'text-emerald-700 font-medium' : 'text-gray-600'}`}>{c}</span>
                  </label>
                ))}
              </div>
              <Row>
                <KpiCard label="Green Lease Score" value={`${leaseScore}/100`} sub={`${leaseClauses.size}/${GREEN_LEASE_CLAUSES.length} clauses`} color={leaseScore >= 70 ? 'emerald' : leaseScore >= 50 ? 'yellow' : 'red'} />
                <KpiCard label="Green Lease Grade" value={leaseGrade} sub="performance grade" color={['A', 'B'].includes(leaseGrade) ? 'emerald' : leaseGrade === 'C' ? 'yellow' : 'red'} />
                <KpiCard label="Green Premium" value={`+${greenPremium}%`} sub="rental uplift estimate" color="emerald" />
                <KpiCard label="Brown Discount" value={`-${brownDiscount}%`} sub="absent-clause penalty" color={+brownDiscount > 0 ? 'red' : 'emerald'} />
              </Row>
            </Section>
            <div className="flex justify-end mt-4">
              <Btn onClick={() => alert('Commercial RE report exported (demo)')}>Export Report</Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
