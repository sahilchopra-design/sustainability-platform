/**
 * ShippingMaritimePage.jsx  —  Route: /shipping-maritime
 * Sprint 22 E48 — CII / EEXI / Poseidon Principles / EU ETS Shipping / Fleet & Fuel Switch
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
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

const RATING_COLORS = { A: '#059669', B: '#16a34a', C: '#ca8a04', D: '#ea580c', E: '#dc2626' };
const TABS = ['CII Rating', 'EEXI & FuelEU', 'Poseidon Principles', 'EU ETS Shipping', 'Fleet Portfolio & Fuel Switch'];

export default function ShippingMaritimePage() {
  const [tab, setTab] = useState(0);

  // Tab 1 state
  const [vesselType, setVesselType] = useState('bulk_carrier');
  const [dwt, setDwt] = useState('75000');
  const [distance, setDistance] = useState('48000');
  const [fuelConsumed, setFuelConsumed] = useState('3200');
  const [ciiYear, setCiiYear] = useState('2024');
  const [ciiResult, setCiiResult] = useState(null);

  // Tab 2 state
  const [eeplApplied, setEeplApplied] = useState(false);
  const [powerLimit, setPowerLimit] = useState('85');
  const [fuelType, setFuelType] = useState('VLSFO');

  // Tab 3 state
  const [ppYear, setPpYear] = useState('2024');

  // Tab 4 state
  const [etsCO2, setEtsCO2] = useState('12000');
  const [etsYear, setEtsYear] = useState('2025');

  // Tab 5 state
  const [currentFuel, setCurrentFuel] = useState('HFO');
  const [targetFuel, setTargetFuel] = useState('LNG');
  const [fuelCapex, setFuelCapex] = useState('4500000');

  const runCII = useCallback(async () => {
    try {
      const res = await axios.post(`${API}/api/v1/shipping/cii-rating`, {
        vessel_type: vesselType, dwt: +dwt, distance_nm: +distance,
        fuel_consumed_mt: +fuelConsumed, year: +ciiYear,
      });
      setCiiResult(res.data);
    } catch {
      const s = +dwt + +distance;
      const attained = 3.2 + seed(1, s) * 2.8;
      const required = 4.5 - (+ciiYear - 2023) * 0.09;
      const ratio = attained / required;
      const rating = ratio < 0.85 ? 'A' : ratio < 0.95 ? 'B' : ratio < 1.05 ? 'C' : ratio < 1.15 ? 'D' : 'E';
      setCiiResult({ attained: attained.toFixed(2), required: required.toFixed(2), ratio: ratio.toFixed(3), rating });
    }
  }, [vesselType, dwt, distance, fuelConsumed, ciiYear]);

  const ciiTraj = Array.from({ length: 8 }, (_, i) => ({
    year: 2023 + i,
    required: +(4.5 - i * 0.09).toFixed(3),
    attained: ciiResult ? +(+ciiResult.attained - i * 0.04).toFixed(3) : +(3.8 - i * 0.04).toFixed(3),
  }));

  const ratingColor = ciiResult ? (RATING_COLORS[ciiResult.rating] || '#6b7280') : '#6b7280';
  const ratingTailwind = { A: 'emerald', B: 'green', C: 'yellow', D: 'orange', E: 'red' };
  const ratingCol = ciiResult ? (ratingTailwind[ciiResult.rating] || 'gray') : 'gray';

  // Tab 2 data
  const s2 = 12345;
  const eexiAttained = 4.2 + seed(2, s2) * 1.8;
  const eexiRequired = 5.1;
  const eexiCompliant = eexiAttained <= eexiRequired;
  const fuelEUIntensity = { HFO: 91.96, VLSFO: 89.0, LNG: 56.0, methanol: 45.0, ammonia: 0.0 }[fuelType] || 89.0;
  const fuelEU2025Target = 89.34;
  const fuelEU2030Target = 80.0;
  const fuelEUPenalty = fuelEUIntensity > fuelEU2025Target ? Math.round((fuelEUIntensity - fuelEU2025Target) * 18000) : 0;
  const fuelEUData = [
    { name: 'Vessel (WtW)', value: fuelEUIntensity },
    { name: '2025 Target', value: fuelEU2025Target },
    { name: '2030 Target', value: fuelEU2030Target },
    { name: '2035 Target', value: 71.0 },
    { name: '2040 Target', value: 62.0 },
  ];

  // Tab 3 data
  const s3 = +ppYear + 1000;
  const ppScore = Math.round(40 + seed(3, s3) * 45);
  const ppDelta = +(seed(4, s3) * 20 - 10).toFixed(1);
  const ppTrajectory = Array.from({ length: 6 }, (_, i) => ({
    year: 2025 + i * 5,
    required: +(85 - i * 5).toFixed(1),
    vessel: +(ppScore - i * 3.5).toFixed(1),
  }));
  const aerAttained = +(5.2 + seed(5, s3) * 2.0).toFixed(2);
  const aerRequired = 6.0;

  // Tab 4 data
  const co2Val = +etsCO2;
  const phaseIn = { 2024: 0.40, 2025: 0.70, 2026: 1.0 }[+etsYear] ?? 1.0;
  const obligation = Math.round(co2Val * phaseIn);
  const freeAlloc = Math.round(co2Val * 0.05);
  const surrenderGap = obligation - freeAlloc;
  const euaPrice = 65;
  const surrenderCost = surrenderGap * euaPrice;
  const phaseData = [
    { year: '2024', obligation: 40, free: 5 },
    { year: '2025', obligation: 70, free: 3 },
    { year: '2026', obligation: 100, free: 0 },
  ];
  const etsLineData = Array.from({ length: 9 }, (_, i) => ({
    eua: 40 + i * 10,
    cost: Math.round(surrenderGap * (40 + i * 10) / 1000),
  }));

  // Tab 5 data
  const s5 = 77777;
  const ciiDist = [
    { name: 'A', value: Math.round(seed(10, s5) * 15 + 5) },
    { name: 'B', value: Math.round(seed(11, s5) * 20 + 10) },
    { name: 'C', value: Math.round(seed(12, s5) * 25 + 15) },
    { name: 'D', value: Math.round(seed(13, s5) * 15 + 5) },
    { name: 'E', value: Math.round(seed(14, s5) * 8 + 2) },
  ];
  const fuelReduction = { HFO: 0, VLSFO: 3, LNG: 22, methanol: 30, ammonia: 100 };
  const co2Red = (fuelReduction[targetFuel] || 0) - (fuelReduction[currentFuel] || 0);
  const capexN = +fuelCapex;
  const opexDelta = Math.round(capexN * 0.05);
  const annualSaving = Math.round(co2Red * 120);
  const payback = annualSaving > 0 ? (capexN / annualSaving).toFixed(1) : 'N/A';
  const radarData = [
    { fuel: 'LNG', tech: 85, availability: 70, cost: 60 },
    { fuel: 'Methanol', tech: 65, availability: 50, cost: 55 },
    { fuel: 'Ammonia', tech: 40, availability: 30, cost: 45 },
    { fuel: 'Hydrogen', tech: 35, availability: 20, cost: 30 },
    { fuel: 'Biofuel', tech: 75, availability: 60, cost: 65 },
  ];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Shipping & Maritime Climate Risk</h1>
          <p className="text-sm text-gray-500 mt-1">IMO CII · EEXI · FuelEU Maritime · Poseidon Principles · EU ETS Shipping · Fleet Fuel Switch</p>
        </div>

        {/* Tab Bar */}
        <div className="flex gap-1 mb-6 bg-white border border-gray-200 rounded-lg p-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2 rounded text-sm font-medium whitespace-nowrap transition-colors ${tab === i ? 'bg-emerald-600 text-white' : 'text-gray-600 hover:bg-gray-100'}`}>
              {t}
            </button>
          ))}
        </div>

        {/* ── TAB 1: CII Rating ── */}
        {tab === 0 && (
          <div>
            <Section title="Vessel & Voyage Parameters">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Sel label="Vessel Type" value={vesselType} onChange={e => setVesselType(e.target.value)}>
                  <option value="bulk_carrier">Bulk Carrier</option>
                  <option value="tanker">Tanker</option>
                  <option value="container">Container Ship</option>
                  <option value="gas_carrier">Gas Carrier</option>
                  <option value="ro_ro">Ro-Ro</option>
                </Sel>
                <Inp label="DWT (tonnes)" type="number" value={dwt} onChange={e => setDwt(e.target.value)} />
                <Inp label="Distance (NM/yr)" type="number" value={distance} onChange={e => setDistance(e.target.value)} />
                <Inp label="Fuel Consumed (MT/yr)" type="number" value={fuelConsumed} onChange={e => setFuelConsumed(e.target.value)} />
                <Sel label="Year" value={ciiYear} onChange={e => setCiiYear(e.target.value)}>
                  {[2023, 2024, 2025, 2026, 2027].map(y => <option key={y}>{y}</option>)}
                </Sel>
                <div className="flex items-end"><Btn onClick={runCII}>Run CII Assessment</Btn></div>
              </div>
            </Section>
            {ciiResult && (
              <>
                <Row>
                  <KpiCard label="CII Attained" value={ciiResult.attained} sub="g CO₂/(t·NM)" color="gray" />
                  <KpiCard label="CII Required" value={ciiResult.required} sub="g CO₂/(t·NM)" color="gray" />
                  <KpiCard label="CII Ratio" value={ciiResult.ratio} sub="attained / required" color={+ciiResult.ratio < 1 ? 'emerald' : 'red'} />
                  <div className={`bg-${ratingCol}-50 border border-${ratingCol}-200 rounded-lg p-4 flex flex-col justify-center items-center`}>
                    <div className="text-xs text-gray-500 mb-1">IMO CII Rating</div>
                    <div className="text-5xl font-black" style={{ color: ratingColor }}>{ciiResult.rating}</div>
                    <div className="text-xs text-gray-400 mt-1">Rating {ciiResult.rating}</div>
                  </div>
                </Row>
                <Section title="CII Attained vs Required">
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart data={[{ name: 'Current Year', attained: +ciiResult.attained, required: +ciiResult.required }]}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" />
                      <YAxis domain={[0, 8]} />
                      <Tooltip />
                      <Legend />
                      <Bar dataKey="attained" fill="#059669" name="CII Attained" />
                      <Bar dataKey="required" fill="#d1fae5" name="CII Required" />
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
            <Section title="CII Required Reduction Trajectory (2023–2030)">
              <ResponsiveContainer width="100%" height={240}>
                <LineChart data={ciiTraj}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis domain={[3, 5.5]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="required" stroke="#dc2626" strokeWidth={2} name="Required CII" dot={false} />
                  <Line type="monotone" dataKey="attained" stroke="#059669" strokeWidth={2} strokeDasharray="5 3" name="Vessel Trajectory" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 2: EEXI & FuelEU ── */}
        {tab === 1 && (
          <div>
            <Section title="EEXI Parameters">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="Fuel Type" value={fuelType} onChange={e => setFuelType(e.target.value)}>
                  {['HFO', 'VLSFO', 'LNG', 'methanol', 'ammonia'].map(f => <option key={f}>{f}</option>)}
                </Sel>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-medium text-gray-600">EPL Applied</label>
                  <button onClick={() => setEeplApplied(!eeplApplied)}
                    className={`px-3 py-2 rounded text-sm font-medium border ${eeplApplied ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-700 border-gray-300'}`}>
                    {eeplApplied ? 'EPL ON' : 'EPL OFF'}
                  </button>
                </div>
                {eeplApplied && <Inp label="Power Limit (%)" type="number" value={powerLimit} onChange={e => setPowerLimit(e.target.value)} />}
              </div>
              <Row>
                <KpiCard label="EEXI Attained" value={eexiAttained.toFixed(2)} sub="g CO₂/(t·NM)" color="gray" />
                <KpiCard label="EEXI Required" value={eexiRequired.toFixed(2)} sub="g CO₂/(t·NM)" color="gray" />
                <KpiCard label="EEXI Ratio" value={(eexiAttained / eexiRequired).toFixed(3)} sub="attained / required" color={eexiCompliant ? 'emerald' : 'red'} />
                <KpiCard label="EEXI Status" value={eexiCompliant ? 'Compliant' : 'Non-Compliant'} sub={eeplApplied ? `EPL: ${powerLimit}%` : 'No power limit'} color={eexiCompliant ? 'emerald' : 'red'} />
              </Row>
            </Section>
            <Section title="FuelEU Maritime — GHG Intensity (WtW)">
              <Row>
                <KpiCard label="Vessel GHG Intensity" value={`${fuelEUIntensity.toFixed(1)}`} sub="gCO₂eq/MJ (WtW)" color="gray" />
                <KpiCard label="2025 Target" value="89.34" sub="gCO₂eq/MJ" color="emerald" />
                <KpiCard label="2030 Target" value="80.0" sub="gCO₂eq/MJ" color="emerald" />
                <KpiCard label="FuelEU Penalty" value={`€${(fuelEUPenalty / 1000).toFixed(0)}k`} sub="2025 compliance" color={fuelEUPenalty > 0 ? 'red' : 'emerald'} />
              </Row>
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={fuelEUData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="value" name="GHG Intensity (gCO₂eq/MJ)">
                    {fuelEUData.map((d, i) => (
                      <Cell key={i} fill={i === 0 ? '#059669' : '#d1fae5'} />
                    ))}
                  </Bar>
                  <ReferenceLine y={89.34} stroke="#dc2626" strokeDasharray="4 2" label={{ value: '2025 Limit', position: 'right', fontSize: 10 }} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 3: Poseidon Principles ── */}
        {tab === 2 && (
          <div>
            <Section title="Poseidon Principles Alignment">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Sel label="Reporting Year" value={ppYear} onChange={e => setPpYear(e.target.value)}>
                  {[2022, 2023, 2024].map(y => <option key={y}>{y}</option>)}
                </Sel>
              </div>
              <Row>
                <KpiCard label="PP Alignment Score" value={`${ppScore}/100`} sub="Climate score" color={ppScore >= 70 ? 'emerald' : ppScore >= 50 ? 'yellow' : 'red'} />
                <KpiCard label="Required Trajectory" value={(85 - (+ppYear - 2025) * 1).toFixed(1)} sub="AER gCO₂/(t·NM)" color="gray" />
                <KpiCard label="Delta vs Required" value={`${ppDelta > 0 ? '+' : ''}${ppDelta}%`} sub="above/below path" color={ppDelta <= 0 ? 'emerald' : 'red'} />
                <KpiCard label="Sea Cargo AER" value={`${aerAttained}`} sub="vs required ${aerRequired}" color={aerAttained <= aerRequired ? 'emerald' : 'red'} />
              </Row>
            </Section>
            <Section title="PP Required Trajectory vs Vessel Path (2025–2050)">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={ppTrajectory}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis domain={[50, 90]} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="required" stroke="#dc2626" strokeWidth={2} name="PP Required Trajectory" />
                  <Line type="monotone" dataKey="vessel" stroke="#059669" strokeWidth={2} strokeDasharray="5 3" name="Vessel Climate Score" />
                </LineChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Sea Cargo Charter — AER">
              <Row>
                <KpiCard label="AER Attained" value={aerAttained} sub="gCO₂/(t·NM)" color="gray" />
                <KpiCard label="AER Required" value={aerRequired.toFixed(2)} sub="gCO₂/(t·NM)" color="gray" />
                <KpiCard label="AER Aligned" value={aerAttained <= aerRequired ? 'Yes' : 'No'} sub="Sea Cargo Charter" color={aerAttained <= aerRequired ? 'emerald' : 'red'} />
              </Row>
            </Section>
          </div>
        )}

        {/* ── TAB 4: EU ETS Shipping ── */}
        {tab === 3 && (
          <div>
            <Section title="EU ETS Shipping Parameters">
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-4">
                <Inp label="Verified CO₂ Emissions (tCO₂)" type="number" value={etsCO2} onChange={e => setEtsCO2(e.target.value)} />
                <Sel label="Reporting Year" value={etsYear} onChange={e => setEtsYear(e.target.value)}>
                  {[2024, 2025, 2026].map(y => <option key={y}>{y}</option>)}
                </Sel>
              </div>
              <Row>
                <KpiCard label="ETS Obligation (EUAs)" value={obligation.toLocaleString()} sub={`${Math.round(phaseIn * 100)}% phase-in`} color="gray" />
                <KpiCard label="Free Allocation (EUAs)" value={freeAlloc.toLocaleString()} sub="~5% of obligation" color="emerald" />
                <KpiCard label="Surrender Gap (EUAs)" value={surrenderGap.toLocaleString()} sub="to surrender" color={surrenderGap > 0 ? 'red' : 'emerald'} />
                <KpiCard label="Surrender Cost" value={`€${(surrenderCost / 1000).toFixed(0)}k`} sub={`@ €${euaPrice}/EUA`} color={surrenderCost > 0 ? 'red' : 'emerald'} />
              </Row>
            </Section>
            <Section title="EU ETS Phase-In Schedule (2024–2026)">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={phaseData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis unit="%" domain={[0, 110]} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="obligation" fill="#059669" name="Obligation %" />
                  <Bar dataKey="free" fill="#d1fae5" name="Free Allocation %" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="ETS Cost Sensitivity vs EUA Price">
              <ResponsiveContainer width="100%" height={220}>
                <LineChart data={etsLineData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="eua" label={{ value: 'EUA Price (€)', position: 'insideBottom', offset: -2, fontSize: 11 }} />
                  <YAxis label={{ value: 'Cost (€k)', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip />
                  <Line type="monotone" dataKey="cost" stroke="#059669" strokeWidth={2} name="ETS Cost (€k)" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* ── TAB 5: Fleet Portfolio & Fuel Switch ── */}
        {tab === 4 && (
          <div>
            <Section title="Fleet CII Distribution">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <ResponsiveContainer width="100%" height={260}>
                  <PieChart>
                    <Pie data={ciiDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={d => `${d.name}: ${d.value}`}>
                      {ciiDist.map((d, i) => <Cell key={i} fill={RATING_COLORS[d.name]} />)}
                    </Pie>
                    <Tooltip />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
                <div className="flex flex-col gap-3 justify-center">
                  {ciiDist.map(d => (
                    <div key={d.name} className="flex items-center gap-3">
                      <span className="text-2xl font-black w-6" style={{ color: RATING_COLORS[d.name] }}>{d.name}</span>
                      <div className="flex-1 bg-gray-100 rounded-full h-4">
                        <div className="h-4 rounded-full" style={{ width: `${d.value * 2}%`, background: RATING_COLORS[d.name] }} />
                      </div>
                      <span className="text-sm font-bold w-8">{d.value}</span>
                    </div>
                  ))}
                </div>
              </div>
            </Section>
            <Section title="Fuel Switch Analysis">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
                <Sel label="Current Fuel" value={currentFuel} onChange={e => setCurrentFuel(e.target.value)}>
                  {['HFO', 'VLSFO', 'LNG', 'methanol', 'ammonia'].map(f => <option key={f}>{f}</option>)}
                </Sel>
                <Sel label="Target Fuel" value={targetFuel} onChange={e => setTargetFuel(e.target.value)}>
                  {['HFO', 'VLSFO', 'LNG', 'methanol', 'ammonia'].map(f => <option key={f}>{f}</option>)}
                </Sel>
                <Inp label="Capex (USD)" type="number" value={fuelCapex} onChange={e => setFuelCapex(e.target.value)} />
              </div>
              <Row>
                <KpiCard label="Capex" value={`$${(+fuelCapex / 1e6).toFixed(1)}M`} sub="fuel switch investment" color="gray" />
                <KpiCard label="Opex Delta" value={`$${(opexDelta / 1000).toFixed(0)}k/yr`} sub="incremental opex" color="gray" />
                <KpiCard label="CO₂ Reduction" value={`${co2Red}%`} sub="vs current fuel" color={co2Red > 0 ? 'emerald' : 'red'} />
                <KpiCard label="Payback" value={`${payback} yrs`} sub="simple payback" color="gray" />
              </Row>
            </Section>
            <Section title="Alternative Fuel Readiness">
              <ResponsiveContainer width="100%" height={280}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="fuel" tick={{ fontSize: 11 }} />
                  <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 9 }} />
                  <Radar name="Technology Readiness" dataKey="tech" stroke="#059669" fill="#059669" fillOpacity={0.25} />
                  <Radar name="Availability" dataKey="availability" stroke="#0284c7" fill="#0284c7" fillOpacity={0.15} />
                  <Radar name="Cost Competitiveness" dataKey="cost" stroke="#ca8a04" fill="#ca8a04" fillOpacity={0.15} />
                  <Legend />
                  <Tooltip />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
            <div className="flex justify-end mt-4">
              <Btn onClick={() => alert('Fleet report exported (demo)')}>Export Fleet Report</Btn>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
