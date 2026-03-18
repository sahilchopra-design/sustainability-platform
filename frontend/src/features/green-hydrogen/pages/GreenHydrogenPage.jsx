/**
 * Green Hydrogen Page — E43
 * Project Overview, EU Classification, LCOH Economics, Scenario Analysis, Cross-Framework.
 * Backend: /api/v1/green-hydrogen
 */
import React, { useState } from 'react';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import axios from 'axios';

const API = 'http://localhost:8001';
const s = (i, seed) => Math.abs(Math.sin(i * 9301 + seed * 49297) * 233280) % 233280 / 233280;

const Section = ({ title, children }) => (
  <div style={{ background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, padding: 24, marginBottom: 20 }}>
    <h3 style={{ margin: '0 0 16px', fontSize: 16, fontWeight: 600, color: '#111' }}>{title}</h3>
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, color = '#10b981' }) => (
  <div style={{ background: '#f9fafb', border: '1px solid #e5e7eb', borderRadius: 8, padding: 16, textAlign: 'center' }}>
    <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: 12, color: '#6b7280', marginTop: 4 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 2 }}>{sub}</div>}
  </div>
);
const Row = ({ children, gap = 12 }) => (
  <div style={{ display: 'grid', gridTemplateColumns: `repeat(${React.Children.count(children)},1fr)`, gap }}>
    {children}
  </div>
);
const Inp = ({ label, value, onChange, type = 'text' }) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#374151', marginBottom: 4 }}>{label}</label>
    <input type={type} value={value} onChange={e => onChange(e.target.value)}
      style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 14, boxSizing: 'border-box' }} />
  </div>
);
const Sel = ({ label, value, onChange, options }) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: '#374151', marginBottom: 4 }}>{label}</label>
    <select value={value} onChange={e => onChange(e.target.value)}
      style={{ width: '100%', padding: '8px 12px', border: '1px solid #d1d5db', borderRadius: 6, fontSize: 14, background: '#fff' }}>
      {options.map(o => <option key={o.value || o} value={o.value || o}>{o.label || o}</option>)}
    </select>
  </div>
);
const Btn = ({ children, onClick, color = '#10b981' }) => (
  <button onClick={onClick} style={{ background: color, color: '#fff', border: 'none', borderRadius: 6, padding: '10px 20px', fontSize: 14, fontWeight: 600, cursor: 'pointer' }}>
    {children}
  </button>
);

const TABS = ['Project Overview', 'EU Classification', 'LCOH Economics', 'Scenario Analysis', 'Cross-Framework'];
const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

const H2_PATHWAYS = [
  { pathway: 'Green (Electrolysis)', colour: 'green', colorHex: '#10b981', bg: '#dcfce7', carbonIntensity: 0.9, rfnboEligible: true, lcoh: '3.5–6.0' },
  { pathway: 'Blue (SMR+CCS)', colour: 'blue', colorHex: '#3b82f6', bg: '#dbeafe', carbonIntensity: 2.8, rfnboEligible: false, lcoh: '1.8–3.0' },
  { pathway: 'Turquoise (Pyrolysis)', colour: 'turquoise', colorHex: '#06b6d4', bg: '#cffafe', carbonIntensity: 1.5, rfnboEligible: false, lcoh: '2.0–4.0' },
  { pathway: 'Pink (Nuclear)', colour: 'pink', colorHex: '#ec4899', bg: '#fce7f3', carbonIntensity: 0.6, rfnboEligible: true, lcoh: '4.5–8.0' },
  { pathway: 'Grey (SMR)', colour: 'grey', colorHex: '#6b7280', bg: '#f3f4f6', carbonIntensity: 10.0, rfnboEligible: false, lcoh: '1.0–2.0' },
];

const ELECTROLYSER_PARAMS = [
  { tech: 'PEM', capex: 1200, efficiency: 67, lifetime: 20, degradation: 1.5 },
  { tech: 'ALK', capex: 800, efficiency: 70, lifetime: 25, degradation: 0.8 },
  { tech: 'SOEC', capex: 2500, efficiency: 82, lifetime: 15, degradation: 2.0 },
  { tech: 'AEM', capex: 600, efficiency: 65, lifetime: 10, degradation: 1.8 },
];

const RFNBO_CRITERIA = [
  { criterion: 'Additionality', key: 'additionality', desc: 'New renewable capacity attributed to electrolyser (3yr rule or direct connection)' },
  { criterion: 'Temporal Correlation', key: 'temporal', desc: 'Hourly matching of renewable electricity to hydrogen production' },
  { criterion: 'Geographical Correlation', key: 'geo', desc: 'Renewable source in same or adjacent bidding zone' },
  { criterion: 'Carbon Intensity < 3.38 kgCO2e/kgH2', key: 'carbon', desc: 'Full lifecycle GHG intensity below EU RFNBO threshold' },
  { criterion: 'Bioenergy Restriction', key: 'bio', desc: 'No co-firing with bioenergy feedstocks prohibited under RED III' },
];

const SUBSIDY_VALUES = [
  { scheme: 'EU H2 Bank', value: 0.80 },
  { scheme: 'IRA 45V (US)', value: 3.00 },
  { scheme: 'UK Ren H2', value: 1.20 },
  { scheme: 'Japan GX', value: 0.50 },
  { scheme: 'None', value: 0.00 },
];

const SCENARIO_TABLE = [
  { scenario: '2025 Base', year: 2025, capex: 1200, elec: 65, cf: 35, lcoh: 5.20, parity: false },
  { scenario: '2028 Progress', year: 2028, capex: 900, elec: 55, cf: 40, lcoh: 4.10, parity: false },
  { scenario: '2030 NZE', year: 2030, capex: 700, elec: 45, cf: 45, lcoh: 3.20, parity: false },
  { scenario: '2033 Accelerated', year: 2033, capex: 500, elec: 35, cf: 50, lcoh: 2.40, parity: false },
  { scenario: '2037 Optimistic', year: 2037, capex: 400, elec: 28, cf: 55, lcoh: 1.90, parity: true },
  { scenario: '2040 BNEF', year: 2040, capex: 300, elec: 22, cf: 60, lcoh: 1.50, parity: true },
];

const POLICY_TIMELINE = [
  { year: 2024, event: 'EU H2 Bank First Auction Results (3.2 GW allocated)', region: 'EU' },
  { year: 2025, event: 'IRA 45V Final Rule effective — $3/kgH2 max credit', region: 'US' },
  { year: 2026, event: 'EU H2 Bank Second Auction (target 6 GW)', region: 'EU' },
  { year: 2027, event: 'EU RFNBO delegated act full enforcement', region: 'EU' },
  { year: 2028, event: 'Japan GX Strategy — 3 Mt/yr domestic target', region: 'JP' },
  { year: 2030, event: 'EU 10 Mt domestic + 10 Mt import H2 target', region: 'EU' },
];

const CROSS_FW_RADAR = [
  { framework: 'EU Taxonomy CCM', score: 85 },
  { framework: 'SFDR Art 9', score: 78 },
  { framework: 'GFANZ', score: 72 },
  { framework: 'IRA 45V', score: 90 },
  { framework: 'Japan GX', score: 65 },
];

function genSeed(entityId) {
  let h = 0;
  for (let i = 0; i < (entityId || 'P001').length; i++) h = (h * 31 + entityId.charCodeAt(i)) | 0;
  return Math.abs(h) || 42;
}

function lcohColor(v) {
  const f = parseFloat(v);
  if (f <= 2) return '#10b981';
  if (f <= 4) return '#f59e0b';
  return '#ef4444';
}

export default function GreenHydrogenPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [entityId, setEntityId] = useState('P-001');
  const [projectName, setProjectName] = useState('Nordic Green H2 Project');
  const [country, setCountry] = useState('NOR');
  const [pathway, setPathway] = useState('green_electrolysis');
  const [electrolyser, setElectrolyser] = useState('PEM');
  const [capacity, setCapacity] = useState('200');
  const [capFactor, setCapFactor] = useState('45');
  const [elecCost, setElecCost] = useState('38');
  const [capex, setCapex] = useState('1200');
  const [subsidy, setSubsidy] = useState('eu_h2_bank');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const seed = genSeed(entityId);

  // Compute LCOH
  const cap = parseFloat(capacity) || 200;
  const cf = parseFloat(capFactor) / 100 || 0.45;
  const elec = parseFloat(elecCost) || 38;
  const cpx = parseFloat(capex) || 1200;
  const techParams = ELECTROLYSER_PARAMS.find(e => e.tech === electrolyser) || ELECTROLYSER_PARAMS[0];
  const annualOutput = cap * cf * 8760 * 0.02; // 20 kgH2/kWh × MWh → t H2
  const capexAnnual = (cpx * cap * 1000) / (techParams.lifetime * annualOutput * 1000);
  const elecComponent = elec / 1000 / (techParams.efficiency / 100) * 33.3;
  const oAndM = capexAnnual * 0.04;
  const transport = 0.35;
  const lcohPreSubsidy = capexAnnual + elecComponent + oAndM + transport;
  const subsidyVal = SUBSIDY_VALUES.find(sv => sv.scheme.toLowerCase().includes(subsidy.split('_')[0])) || { value: 0 };
  const lcohNet = Math.max(0, lcohPreSubsidy - subsidyVal.value);
  const carbonIntensity = (elec * 0.25 / (techParams.efficiency / 100) * 3.6).toFixed(2);

  const selectedPathway = H2_PATHWAYS.find(p => p.colour === pathway.split('_')[0]) || H2_PATHWAYS[0];
  const rfnboPass = RFNBO_CRITERIA.map((c, i) => ({ ...c, pass: i !== 2 || pathway === 'green_electrolysis' }));

  const lcohWaterfall = [
    { name: 'Capital Recovery', value: parseFloat(capexAnnual.toFixed(2)), fill: '#3b82f6' },
    { name: 'Electricity', value: parseFloat(elecComponent.toFixed(2)), fill: '#10b981' },
    { name: 'O&M', value: parseFloat(oAndM.toFixed(2)), fill: '#f59e0b' },
    { name: 'Transport', value: transport, fill: '#8b5cf6' },
  ];

  const scenarioLine = SCENARIO_TABLE.map(sc => ({
    year: sc.year,
    LCOH: sc.lcoh,
    'Grey Parity': 1.5,
  }));

  const subsidyBar = SUBSIDY_VALUES.map(sv => ({
    scheme: sv.scheme,
    'Pre-Subsidy': parseFloat(lcohPreSubsidy.toFixed(2)),
    'Net LCOH': parseFloat(Math.max(0, lcohPreSubsidy - sv.value).toFixed(2)),
    'Subsidy Value': sv.value,
  }));

  async function runFullAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/green-hydrogen/full-assessment`, {
        entity_id: entityId, project_name: projectName, country_code: country,
        production_pathway: pathway, electrolysis_technology: electrolyser,
        capacity_mw: parseFloat(capacity), capacity_factor_pct: parseFloat(capFactor),
        electricity_cost_usd_mwh: parseFloat(elecCost), capex_per_kw: parseFloat(capex),
        subsidy_scheme: subsidy,
      });
      setResult(res.data);
    } catch { setResult(null); } finally { setLoading(false); }
  }

  async function callEndpoint(path, body = {}) {
    setLoading(true);
    try {
      await axios.post(`${API}/api/v1/green-hydrogen/${path}`, { entity_id: entityId, ...body });
    } catch { } finally { setLoading(false); }
  }

  const h2ColorBadge = () => {
    const p = H2_PATHWAYS.find(hp => hp.colour === pathway.split('_')[0]) || H2_PATHWAYS[0];
    return <span style={{ background: p.bg, color: p.colorHex, border: `1px solid ${p.colorHex}`, borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 700 }}>{p.colour.charAt(0).toUpperCase() + p.colour.slice(1)} H2</span>;
  };

  return (
    <div style={{ fontFamily: 'Inter,system-ui,sans-serif', background: '#f3f4f6', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#111' }}>Green Hydrogen Assessment</h1>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>LCOH analysis, EU RFNBO compliance, subsidy schemes and cross-framework alignment</p>
        </div>

        <div style={{ display: 'flex', gap: 0, borderBottom: '1px solid #e5e7eb', marginBottom: 24, background: '#fff', borderRadius: '8px 8px 0 0', padding: '0 16px' }}>
          {TABS.map((tab, i) => (
            <button key={tab} onClick={() => setActiveTab(i)} style={{
              background: 'none', border: 'none', borderBottom: activeTab === i ? '3px solid #10b981' : '3px solid transparent',
              padding: '14px 18px', fontSize: 14, fontWeight: activeTab === i ? 600 : 400,
              color: activeTab === i ? '#10b981' : '#6b7280', cursor: 'pointer', whiteSpace: 'nowrap',
            }}>{tab}</button>
          ))}
        </div>

        {/* Tab 0: Project Overview */}
        {activeTab === 0 && (
          <>
            <Section title="Project Configuration">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Project Name" value={projectName} onChange={setProjectName} />
                <Inp label="Country Code (ISO3)" value={country} onChange={setCountry} />
              </Row>
              <Row>
                <Sel label="Production Pathway" value={pathway} onChange={setPathway}
                  options={['green_electrolysis', 'blue_smr_ccs', 'turquoise_pyrolysis', 'pink_nuclear', 'grey_smr']} />
                <Sel label="Electrolysis Technology" value={electrolyser} onChange={setElectrolyser}
                  options={['PEM', 'ALK', 'SOEC', 'AEM']} />
                <Inp label="Capacity (MW)" value={capacity} onChange={setCapacity} type="number" />
              </Row>
              <Row>
                <Inp label="Capacity Factor (%)" value={capFactor} onChange={setCapFactor} type="number" />
                <Inp label="Electricity Cost ($/MWh)" value={elecCost} onChange={setElecCost} type="number" />
                <Inp label="CapEx per kW ($/kW)" value={capex} onChange={setCapex} type="number" />
                <Sel label="Subsidy Scheme" value={subsidy} onChange={setSubsidy}
                  options={['eu_h2_bank', 'ira_45v_us', 'uk_ren_hydrogen', 'japan_gx', 'none']} />
              </Row>
              <Btn onClick={runFullAssessment}>{loading ? 'Assessing...' : 'Run Full Assessment'}</Btn>
            </Section>
            <Section title="Project KPIs">
              <Row>
                <KpiCard label="LCOH (pre-subsidy)" value={`$${lcohPreSubsidy.toFixed(2)}/kgH2`} color={lcohColor(lcohPreSubsidy)} />
                <KpiCard label="Net LCOH (after subsidy)" value={`$${lcohNet.toFixed(2)}/kgH2`} sub={`${subsidy.replace(/_/g, ' ')}`} color={lcohColor(lcohNet)} />
                <KpiCard label="Carbon Intensity" value={`${carbonIntensity} kgCO2e/kgH2`} color={parseFloat(carbonIntensity) <= 3.38 ? '#10b981' : '#ef4444'} />
                <KpiCard label="EU Delegated Act" value={parseFloat(carbonIntensity) <= 3.38 && pathway === 'green_electrolysis' ? 'Compliant' : 'Non-Compliant'}
                  color={parseFloat(carbonIntensity) <= 3.38 && pathway === 'green_electrolysis' ? '#10b981' : '#ef4444'} />
              </Row>
            </Section>
            <Section title="Classification Badges">
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {h2ColorBadge()}
                <span style={{ background: '#f0fdf4', color: '#16a34a', border: '1px solid #86efac', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600 }}>GFANZ: Solution Finance</span>
                {parseFloat(carbonIntensity) <= 3.38 && (
                  <span style={{ background: '#dbeafe', color: '#1d4ed8', border: '1px solid #93c5fd', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600 }}>EU RFNBO Eligible</span>
                )}
                {lcohNet <= 2 && (
                  <span style={{ background: '#f0fdf4', color: '#16a34a', border: '1px solid #86efac', borderRadius: 20, padding: '4px 16px', fontSize: 13, fontWeight: 600 }}>Grey H2 Parity Achieved</span>
                )}
              </div>
            </Section>
          </>
        )}

        {/* Tab 1: EU Classification */}
        {activeTab === 1 && (
          <>
            <Section title="EU RFNBO Criteria Assessment">
              <div style={{ marginBottom: 12 }}>
                <Btn onClick={() => callEndpoint('eu-rfnbo-compliance', { pathway, technology: electrolyser, carbon_intensity: parseFloat(carbonIntensity) })}>
                  {loading ? 'Checking...' : 'Check RFNBO Compliance'}
                </Btn>
              </div>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Criterion', 'Status', 'Description'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {rfnboPass.map((row, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.criterion}</td>
                      <td style={{ padding: '10px 12px' }}>
                        <span style={{ background: row.pass ? '#dcfce7' : '#fee2e2', color: row.pass ? '#16a34a' : '#dc2626', borderRadius: 4, padding: '2px 10px', fontSize: 12, fontWeight: 700 }}>
                          {row.pass ? 'Pass' : 'Fail'}
                        </span>
                      </td>
                      <td style={{ padding: '10px 12px', color: '#6b7280' }}>{row.desc}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Carbon Intensity vs EU Threshold (3.38 kgCO2e/kgH2)">
              <div style={{ display: 'flex', alignItems: 'center', gap: 24, marginBottom: 16 }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 13, fontWeight: 500 }}>Carbon Intensity</span>
                    <span style={{ fontWeight: 700, color: parseFloat(carbonIntensity) <= 3.38 ? '#10b981' : '#ef4444' }}>
                      {carbonIntensity} / 3.38 kgCO2e/kgH2
                    </span>
                  </div>
                  <div style={{ height: 16, background: '#e5e7eb', borderRadius: 8, overflow: 'hidden', position: 'relative' }}>
                    <div style={{ height: '100%', width: `${Math.min(100, parseFloat(carbonIntensity) / 10 * 100)}%`, background: parseFloat(carbonIntensity) <= 3.38 ? '#10b981' : '#ef4444', borderRadius: 8 }} />
                    <div style={{ position: 'absolute', top: 0, left: `${3.38 / 10 * 100}%`, height: '100%', width: 2, background: '#374151' }} />
                  </div>
                  <div style={{ fontSize: 11, color: '#9ca3af', marginTop: 4 }}>Threshold at 3.38 shown by marker</div>
                </div>
              </div>
            </Section>
            <Section title="EU Taxonomy & Compliance Badges">
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ background: '#dbeafe', color: '#1d4ed8', border: '1px solid #93c5fd', borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>EU Taxonomy CCM 3.10</span>
                {parseFloat(carbonIntensity) <= 3.38 && (
                  <span style={{ background: '#dcfce7', color: '#16a34a', border: '1px solid #86efac', borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>RFNBO Compliant</span>
                )}
                <span style={{ background: '#fef3c7', color: '#b45309', border: '1px solid #fcd34d', borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>Delegated Act (EU) 2023/1184</span>
                <span style={{ background: '#f3f4f6', color: '#374151', border: '1px solid #d1d5db', borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>RED III Art 22a</span>
              </div>
            </Section>
          </>
        )}

        {/* Tab 2: LCOH Economics */}
        {activeTab === 2 && (
          <>
            <Section title="LCOH Waterfall Breakdown">
              <div style={{ marginBottom: 12 }}>
                <Btn onClick={() => callEndpoint('calculate-lcoh', { capacity_mw: parseFloat(capacity), capacity_factor: parseFloat(capFactor) / 100, electricity_cost: parseFloat(elecCost), capex_per_kw: parseFloat(capex) })}>
                  {loading ? 'Calculating...' : 'Calculate LCOH'}
                </Btn>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={lcohWaterfall}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" />
                  <YAxis label={{ value: '$/kgH2', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip formatter={v => `$${parseFloat(v).toFixed(2)}/kgH2`} />
                  <Bar dataKey="value" name="LCOH Component">
                    {lcohWaterfall.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="LCOH Economics KPIs">
              <Row>
                <KpiCard label="LCOH Pre-Subsidy" value={`$${lcohPreSubsidy.toFixed(2)}`} sub="$/kgH2" color={lcohColor(lcohPreSubsidy)} />
                <KpiCard label="Subsidy Value" value={`$${subsidyVal.value.toFixed(2)}`} sub="$/kgH2" color="#3b82f6" />
                <KpiCard label="Net LCOH" value={`$${lcohNet.toFixed(2)}`} sub="$/kgH2" color={lcohColor(lcohNet)} />
                <KpiCard label="Grey H2 Parity ($1.50)" value={lcohNet <= 2 ? 'Achieved' : 'Not Yet'} color={lcohNet <= 2 ? '#10b981' : '#f59e0b'} />
              </Row>
            </Section>
            <Section title="Electrolyser Technology Parameters">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Technology', 'CapEx ($/kW)', 'Efficiency (%)', 'Lifetime (yr)', 'Degradation (%/yr)'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {ELECTROLYSER_PARAMS.map((row, i) => (
                    <tr key={i} style={{ background: row.tech === electrolyser ? '#f0fdf4' : '#fff', borderBottom: '1px solid #f3f4f6' }}>
                      <td style={{ padding: '10px 12px', fontWeight: row.tech === electrolyser ? 700 : 500, color: row.tech === electrolyser ? '#10b981' : '#374151' }}>{row.tech}</td>
                      <td style={{ padding: '10px 12px' }}>{row.capex.toLocaleString()}</td>
                      <td style={{ padding: '10px 12px' }}>{row.efficiency}</td>
                      <td style={{ padding: '10px 12px' }}>{row.lifetime}</td>
                      <td style={{ padding: '10px 12px' }}>{row.degradation}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 3: Scenario Analysis */}
        {activeTab === 3 && (
          <>
            <Section title="LCOH Trajectory — 2025 to 2040">
              <div style={{ marginBottom: 12 }}>
                <Btn onClick={() => callEndpoint('scenario-analysis', { pathway, technology: electrolyser })}>
                  {loading ? 'Running Scenarios...' : 'Run Scenario Analysis'}
                </Btn>
              </div>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={scenarioLine}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis label={{ value: '$/kgH2', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip formatter={v => `$${v}/kgH2`} />
                  <Legend />
                  <Line type="monotone" dataKey="LCOH" stroke="#10b981" strokeWidth={2} dot={{ r: 4 }} />
                  <Line type="monotone" dataKey="Grey Parity" stroke="#ef4444" strokeWidth={1} strokeDasharray="5 5" />
                </LineChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Scenario Table">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Scenario', 'Year', 'Electrolyser CapEx ($/kW)', 'Electricity ($/MWh)', 'Capacity Factor (%)', 'LCOH ($/kgH2)', 'Parity'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {SCENARIO_TABLE.map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6', background: row.parity ? '#f0fdf4' : '#fff' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.scenario}</td>
                        <td style={{ padding: '10px 12px' }}>{row.year}</td>
                        <td style={{ padding: '10px 12px' }}>{row.capex}</td>
                        <td style={{ padding: '10px 12px' }}>{row.elec}</td>
                        <td style={{ padding: '10px 12px' }}>{row.cf}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: lcohColor(row.lcoh) }}>${row.lcoh}</td>
                        <td style={{ padding: '10px 12px' }}>
                          {row.parity ? (
                            <span style={{ color: '#10b981', fontWeight: 700 }}>Yes</span>
                          ) : (
                            <span style={{ color: '#9ca3af' }}>No</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Subsidy Scheme Comparison">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={subsidyBar}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="scheme" tick={{ fontSize: 11 }} />
                  <YAxis label={{ value: '$/kgH2', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip formatter={v => `$${parseFloat(v).toFixed(2)}/kgH2`} />
                  <Legend />
                  <Bar dataKey="Pre-Subsidy" fill="#ef4444" />
                  <Bar dataKey="Net LCOH" fill="#10b981" />
                  <Bar dataKey="Subsidy Value" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* Tab 4: Cross-Framework */}
        {activeTab === 4 && (
          <>
            <Section title="Framework Alignment Overview">
              <Row>
                {[
                  { fw: 'EU Taxonomy CCM 3.10', status: 'Aligned', color: '#10b981' },
                  { fw: 'SFDR Art 9', status: 'Eligible', color: '#3b82f6' },
                  { fw: 'GFANZ Solution Finance', status: 'Category 1', color: '#8b5cf6' },
                  { fw: 'IRA 45V (US)', status: pathway === 'green_electrolysis' ? 'Eligible' : 'Review', color: pathway === 'green_electrolysis' ? '#10b981' : '#f59e0b' },
                ].map(item => (
                  <KpiCard key={item.fw} label={item.fw} value={item.status} color={item.color} />
                ))}
              </Row>
              <div style={{ marginTop: 12, display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                <KpiCard label="Singapore GTT" value="Eligible" color="#06b6d4" />
                <KpiCard label="Japan GX League" value="Qualifying" color="#f59e0b" />
              </div>
            </Section>
            <Section title="H2 Pathway Reference Table">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Pathway', 'Colour', 'Carbon Intensity (kgCO2e/kgH2)', 'EU RFNBO Eligible', 'Typical LCOH ($/kgH2)'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {H2_PATHWAYS.map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.pathway}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: row.bg, color: row.colorHex, borderRadius: 4, padding: '2px 10px', fontSize: 12, fontWeight: 700 }}>{row.colour.charAt(0).toUpperCase() + row.colour.slice(1)}</span>
                        </td>
                        <td style={{ padding: '10px 12px', color: row.carbonIntensity <= 3.38 ? '#10b981' : '#ef4444', fontWeight: 600 }}>{row.carbonIntensity}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: row.rfnboEligible ? '#dcfce7' : '#fee2e2', color: row.rfnboEligible ? '#16a34a' : '#dc2626', borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>
                            {row.rfnboEligible ? 'Yes' : 'No'}
                          </span>
                        </td>
                        <td style={{ padding: '10px 12px', color: '#374151' }}>{row.lcoh}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Policy Timeline">
              {POLICY_TIMELINE.map((ev, i) => (
                <div key={i} style={{ display: 'flex', gap: 16, padding: '10px 0', borderBottom: '1px solid #f3f4f6', alignItems: 'flex-start' }}>
                  <div style={{ minWidth: 42, fontWeight: 700, color: '#10b981', fontSize: 14 }}>{ev.year}</div>
                  <span style={{ background: ev.region === 'EU' ? '#dbeafe' : ev.region === 'US' ? '#fef3c7' : '#f3e8ff', color: ev.region === 'EU' ? '#1d4ed8' : ev.region === 'US' ? '#b45309' : '#7c3aed', borderRadius: 4, padding: '1px 8px', fontSize: 11, fontWeight: 600, flexShrink: 0, marginTop: 1 }}>{ev.region}</span>
                  <span style={{ fontSize: 13, color: '#4b5563' }}>{ev.event}</span>
                </div>
              ))}
            </Section>
            <Section title="Framework Alignment Radar">
              <ResponsiveContainer width="100%" height={300}>
                <RadarChart data={CROSS_FW_RADAR}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="framework" tick={{ fontSize: 11 }} />
                  <Radar name="Alignment Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.28} />
                  <Tooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
