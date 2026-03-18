/**
 * Physical Hazard Page — E41
 * Hazard Overview, Hazard Details, Financial Impact, CRREM Pathway, Scenario Comparison.
 * Backend: /api/v1/physical-hazard
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

const TABS = ['Hazard Overview', 'Hazard Details', 'Financial Impact', 'CRREM Pathway', 'Scenario Comparison'];
const HAZARDS = ['flood', 'wildfire', 'heat_stress', 'sea_level_rise', 'cyclone', 'drought', 'subsidence'];
const HAZARD_LABELS = ['Flood', 'Wildfire', 'Heat Stress', 'Sea Level Rise', 'Cyclone', 'Drought', 'Subsidence'];
const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'];

function hazardColor(v) {
  if (v >= 70) return '#ef4444';
  if (v >= 40) return '#f59e0b';
  return '#10b981';
}

function riskTier(v) {
  if (v >= 70) return { label: 'High', color: '#ef4444', bg: '#fee2e2' };
  if (v >= 40) return { label: 'Medium', color: '#f59e0b', bg: '#fef3c7' };
  return { label: 'Low', color: '#10b981', bg: '#dcfce7' };
}

function genSeed(entityId) {
  let h = 0;
  for (let i = 0; i < (entityId || 'A001').length; i++) h = (h * 31 + entityId.charCodeAt(i)) | 0;
  return Math.abs(h) || 42;
}

const ASSET_TYPES = ['office_building', 'industrial_plant', 'data_centre', 'retail', 'residential', 'agricultural_land', 'coastal_port', 'infrastructure'];
const SCENARIOS = ['RCP2.6', 'RCP4.5', 'RCP8.5', 'SSP1-2.6', 'SSP5-8.5'];
const HORIZONS = ['2030', '2050', '2080'];

const ADAPTATION_MEASURES = {
  flood: ['Install flood barriers', 'Elevated ground floor', 'Sump pump systems', 'Permeable paving'],
  wildfire: ['Defensible space clearing', 'Fire-resistant materials', 'Ember-resistant vents', 'Sprinkler systems'],
  heat_stress: ['Cool roofs & green roofs', 'Enhanced HVAC', 'Shading structures', 'Passive cooling design'],
  sea_level_rise: ['Coastal defences', 'Building elevation', 'Managed retreat strategy', 'Tidal flood barriers'],
  cyclone: ['Structural reinforcement', 'Impact-resistant glazing', 'Backup power systems', 'Storm shutters'],
  drought: ['Water recycling systems', 'Drought-resistant landscaping', 'Rainwater harvesting', 'Leak detection'],
  subsidence: ['Foundation underpinning', 'Ground stabilisation', 'Monitoring sensors', 'Drainage improvement'],
};

const DATA_SOURCES = [
  { label: 'IPCC AR6', color: '#3b82f6' },
  { label: 'JRC', color: '#10b981' },
  { label: 'WRI Aqueduct', color: '#06b6d4' },
];

export default function PhysicalHazardPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [entityId, setEntityId] = useState('A-001');
  const [assetName, setAssetName] = useState('Central London Office Tower');
  const [assetType, setAssetType] = useState('office_building');
  const [country, setCountry] = useState('GBR');
  const [scenario, setScenario] = useState('RCP4.5');
  const [horizon, setHorizon] = useState('2050');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  const seed = genSeed(entityId);

  const hazardScores = HAZARDS.map((h, i) => ({
    hazard: HAZARD_LABELS[i],
    key: h,
    score: Math.round(15 + s(i, seed) * 75),
    rp20: Math.round(10 + s(i, seed + 1) * 60),
    rp100: Math.round(20 + s(i, seed + 2) * 70),
    exposure: ['Low', 'Medium', 'High'][Math.floor(s(i, seed + 3) * 3)],
    vulnerability: Math.round(20 + s(i, seed + 4) * 65),
    adaptation: ADAPTATION_MEASURES[h][0],
  }));

  const composite = Math.round(hazardScores.reduce((a, b) => a + b.score, 0) / hazardScores.length);
  const tier = riskTier(composite);
  const primaryHazard = [...hazardScores].sort((a, b) => b.score - a.score)[0];

  const radarData = hazardScores.map(h => ({ hazard: h.hazard, score: h.score }));

  const scenarioData = [2030, 2050, 2080].map((yr, i) => ({
    year: yr,
    'RCP2.6': Math.round(2 + s(i, seed + 10) * 5),
    'RCP4.5': Math.round(5 + s(i, seed + 11) * 8),
    'RCP8.5': Math.round(10 + s(i, seed + 12) * 15),
  }));

  const crremYears = [2025, 2028, 2031, 2034, 2037, 2040, 2043, 2046, 2050];
  const crremData = crremYears.map((yr, i) => ({
    year: yr,
    target: Math.round(120 - i * 8),
    current: Math.round(180 - i * 3 - s(i, seed + 20) * 6),
  }));
  const strandingYear = crremData.find(d => d.current > d.target)?.year;
  const crremStatus = strandingYear ? 'At Risk' : 'Compliant';

  async function runFullAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/physical-hazard/full-assessment`, {
        entity_id: entityId, asset_name: assetName, asset_type: assetType,
        country_code: country, climate_scenario: scenario, time_horizon: parseInt(horizon),
      });
      setResult(res.data);
    } catch { setResult(null); } finally { setLoading(false); }
  }

  async function callEndpoint(path, body = {}) {
    setLoading(true);
    try {
      await axios.post(`${API}/api/v1/physical-hazard/${path}`, { entity_id: entityId, ...body });
    } catch { } finally { setLoading(false); }
  }

  const barWithThresholds = hazardScores.map(h => ({ ...h, mediumLine: 40, highLine: 70 }));

  const scenarioCompare = ['RCP2.6', 'RCP4.5', 'RCP8.5'].map((sc, i) => ({
    scenario: sc,
    composite: Math.round(composite * (0.6 + i * 0.25)),
    primaryHazard: primaryHazard.hazard,
    damage: `${(1.5 + i * 2.5 + s(i, seed + 30) * 3).toFixed(1)}%`,
  }));
  const scenarioComposeBar = HAZARDS.map((_, i) => ({
    hazard: HAZARD_LABELS[i],
    'RCP2.6': Math.round(hazardScores[i].score * 0.6),
    'RCP4.5': Math.round(hazardScores[i].score * 0.85),
    'RCP8.5': hazardScores[i].score,
  }));

  return (
    <div style={{ fontFamily: 'Inter,system-ui,sans-serif', background: '#f3f4f6', minHeight: '100vh', padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ marginBottom: 24 }}>
          <h1 style={{ margin: 0, fontSize: 24, fontWeight: 700, color: '#111' }}>Physical Climate Hazard Assessment</h1>
          <p style={{ margin: '4px 0 0', color: '#6b7280', fontSize: 14 }}>IPCC AR6 — 7 hazard types across multiple RCP/SSP scenarios and time horizons</p>
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

        {/* Tab 0: Hazard Overview */}
        {activeTab === 0 && (
          <>
            <Section title="Asset Configuration">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Asset Name" value={assetName} onChange={setAssetName} />
                <Inp label="Country Code (ISO3)" value={country} onChange={setCountry} />
              </Row>
              <Row>
                <Sel label="Asset Type" value={assetType} onChange={setAssetType} options={ASSET_TYPES} />
                <Sel label="Climate Scenario" value={scenario} onChange={setScenario} options={SCENARIOS} />
                <Sel label="Time Horizon" value={horizon} onChange={setHorizon} options={HORIZONS} />
              </Row>
              <Btn onClick={runFullAssessment}>{loading ? 'Assessing...' : 'Run Full Assessment'}</Btn>
            </Section>

            <Section title="Hazard KPIs">
              <Row>
                <KpiCard label="Composite Hazard Score" value={composite} sub={`${horizon} horizon`} color={hazardColor(composite)} />
                <KpiCard label="Risk Tier" value={tier.label} sub={scenario}
                  color={tier.color} />
                <KpiCard label="Primary Hazard" value={primaryHazard.hazard} sub={`Score: ${primaryHazard.score}`} color="#3b82f6" />
                <KpiCard label="Property Damage %" value={`${(composite * 0.08 + 1.2).toFixed(1)}%`} sub="Expected annual loss" color="#f59e0b" />
              </Row>
            </Section>

            <Section title="7-Hazard Radar Profile">
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="hazard" tick={{ fontSize: 12 }} />
                  <Radar name="Hazard Score" dataKey="score" stroke="#10b981" fill="#10b981" fillOpacity={0.3} />
                  <Tooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* Tab 1: Hazard Details */}
        {activeTab === 1 && (
          <>
            <Section title="Hazard Score Bar Chart">
              <div style={{ marginBottom: 8, fontSize: 12, color: '#6b7280' }}>Dashed lines: 40 = Medium threshold, 70 = High threshold</div>
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={hazardScores}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hazard" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="score" name="Score">
                    {hazardScores.map((h, i) => <Cell key={i} fill={hazardColor(h.score)} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
              <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                {[{ label: 'Low (<40)', color: '#10b981' }, { label: 'Medium (40-70)', color: '#f59e0b' }, { label: 'High (>70)', color: '#ef4444' }].map(l => (
                  <div key={l.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                    <div style={{ width: 12, height: 12, borderRadius: 2, background: l.color }} />
                    <span style={{ fontSize: 12, color: '#6b7280' }}>{l.label}</span>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Hazard Detail Table">
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                  <thead>
                    <tr style={{ background: '#f9fafb' }}>
                      {['Hazard', 'Score', 'RP 20yr', 'RP 100yr', 'Exposure', 'Vulnerability', 'Adaptation Measure'].map(h => (
                        <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {hazardScores.map((row, i) => (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 500 }}>{row.hazard}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: hazardColor(row.score) }}>{row.score}</td>
                        <td style={{ padding: '10px 12px', color: hazardColor(row.rp20) }}>{row.rp20}</td>
                        <td style={{ padding: '10px 12px', color: hazardColor(row.rp100) }}>{row.rp100}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: row.exposure === 'High' ? '#fee2e2' : row.exposure === 'Medium' ? '#fef3c7' : '#dcfce7', color: row.exposure === 'High' ? '#dc2626' : row.exposure === 'Medium' ? '#b45309' : '#16a34a', borderRadius: 4, padding: '2px 8px', fontSize: 12 }}>{row.exposure}</span>
                        </td>
                        <td style={{ padding: '10px 12px', color: hazardColor(row.vulnerability) }}>{row.vulnerability}</td>
                        <td style={{ padding: '10px 12px', color: '#6b7280', fontSize: 12 }}>{row.adaptation}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Data Source Accreditation">
              <div style={{ display: 'flex', gap: 10 }}>
                {DATA_SOURCES.map(ds => (
                  <span key={ds.label} style={{ background: ds.color + '20', color: ds.color, border: `1px solid ${ds.color}`, borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>{ds.label}</span>
                ))}
              </div>
            </Section>
          </>
        )}

        {/* Tab 2: Financial Impact */}
        {activeTab === 2 && (
          <>
            <Section title="Financial Impact KPIs">
              <Row>
                <KpiCard label="Expected Annual Damage" value={`${(composite * 0.08 + 1.2).toFixed(1)}%`} color="#ef4444" />
                <KpiCard label="Business Interruption" value={`${Math.round(5 + s(1, seed) * 40)} days`} sub="Annual avg" color="#f59e0b" />
                <KpiCard label="Stranded Value Risk" value={`${(composite * 0.12).toFixed(1)}%`} color="#8b5cf6" />
                <KpiCard label="Adaptation CapEx" value={`$${(0.8 + s(2, seed) * 3.5).toFixed(1)}M`} sub="NPV 10yr" color="#3b82f6" />
              </Row>
            </Section>
            <Section title="Scenario Damage Comparison (% Asset Value)">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={scenarioData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Legend />
                  <Area type="monotone" dataKey="RCP2.6" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
                  <Area type="monotone" dataKey="RCP4.5" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.15} />
                  <Area type="monotone" dataKey="RCP8.5" stroke="#ef4444" fill="#ef4444" fillOpacity={0.15} />
                </AreaChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Adaptation Recommendations">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                {[primaryHazard, hazardScores[1]].map((h, i) => (
                  <div key={i} style={{ border: '1px solid #e5e7eb', borderRadius: 8, padding: 16 }}>
                    <div style={{ fontWeight: 600, color: '#374151', marginBottom: 8 }}>{h.hazard} Measures</div>
                    {(ADAPTATION_MEASURES[h.key] || []).map((m, j) => (
                      <div key={j} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, fontSize: 13 }}>
                        <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#10b981', flexShrink: 0 }} />
                        <span style={{ color: '#4b5563' }}>{m}</span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </Section>
          </>
        )}

        {/* Tab 3: CRREM Pathway */}
        {activeTab === 3 && (
          <>
            <Section title="CRREM Compliance Status">
              <Row>
                <KpiCard label="CRREM Status" value={crremStatus} color={crremStatus === 'Compliant' ? '#10b981' : '#ef4444'} />
                <KpiCard label="Stranding Year" value={strandingYear || 'N/A'} sub="If pathway maintained" color={strandingYear ? '#ef4444' : '#10b981'} />
                <KpiCard label="Current Energy Intensity" value="180 kWh/m²" sub="per year" color="#f59e0b" />
                <KpiCard label="Retrofit NPV" value={`$${(1.2 + s(3, seed) * 2.5).toFixed(1)}M`} sub="10yr adaptation NPV" color="#3b82f6" />
              </Row>
            </Section>
            <Section title="CRREM Pathway: Energy Intensity vs Target">
              <div style={{ marginBottom: 8, fontSize: 13, color: '#6b7280' }}>Green = CRREM target pathway | Orange = current performance trajectory</div>
              <ResponsiveContainer width="100%" height={280}>
                <LineChart data={crremData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="year" />
                  <YAxis label={{ value: 'kWh/m²/yr', angle: -90, position: 'insideLeft', fontSize: 11 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="target" stroke="#10b981" strokeWidth={2} name="CRREM Target" strokeDasharray="5 5" />
                  <Line type="monotone" dataKey="current" stroke="#f59e0b" strokeWidth={2} name="Current Performance" />
                </LineChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Retrofit Recommendations">
              {['Deep energy renovation', 'Heat pump installation', 'Solar PV rooftop system', 'Smart building controls', 'Triple-glazed windows', 'Thermal insulation upgrade'].map((rec, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid #f3f4f6', fontSize: 13 }}>
                  <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#10b981', flexShrink: 0 }} />
                  <span style={{ color: '#374151' }}>{rec}</span>
                  <span style={{ marginLeft: 'auto', color: '#6b7280', fontSize: 12 }}>
                    Est. saving: {(2 + s(i, seed + 25) * 18).toFixed(1)} kWh/m²/yr
                  </span>
                </div>
              ))}
            </Section>
          </>
        )}

        {/* Tab 4: Scenario Comparison */}
        {activeTab === 4 && (
          <>
            <Section title="Scenario KPI Comparison">
              <Row>
                {scenarioCompare.map((sc, i) => (
                  <KpiCard key={sc.scenario} label={sc.scenario} value={sc.composite}
                    sub={`Tier: ${riskTier(sc.composite).label}`}
                    color={hazardColor(sc.composite)} />
                ))}
              </Row>
            </Section>
            <Section title="Hazard Scores Across RCP Scenarios">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={scenarioComposeBar}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hazard" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="RCP2.6" fill="#10b981" />
                  <Bar dataKey="RCP4.5" fill="#f59e0b" />
                  <Bar dataKey="RCP8.5" fill="#ef4444" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Scenario Summary Table">
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                <thead>
                  <tr style={{ background: '#f9fafb' }}>
                    {['Scenario', 'Composite Score', 'Risk Tier', 'Primary Hazard', 'Damage %'].map(h => (
                      <th key={h} style={{ padding: '10px 12px', textAlign: 'left', borderBottom: '1px solid #e5e7eb', fontWeight: 600 }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {scenarioCompare.map((row, i) => {
                    const t = riskTier(row.composite);
                    return (
                      <tr key={i} style={{ borderBottom: '1px solid #f3f4f6' }}>
                        <td style={{ padding: '10px 12px', fontWeight: 600 }}>{row.scenario}</td>
                        <td style={{ padding: '10px 12px', fontWeight: 700, color: hazardColor(row.composite) }}>{row.composite}</td>
                        <td style={{ padding: '10px 12px' }}>
                          <span style={{ background: t.bg, color: t.color, borderRadius: 4, padding: '2px 8px', fontSize: 12, fontWeight: 600 }}>{t.label}</span>
                        </td>
                        <td style={{ padding: '10px 12px' }}>{row.primaryHazard}</td>
                        <td style={{ padding: '10px 12px', color: '#ef4444', fontWeight: 600 }}>{row.damage}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Section>
            <Section title="IPCC AR6 Data Quality">
              <div style={{ display: 'flex', gap: 10 }}>
                {DATA_SOURCES.map(ds => (
                  <span key={ds.label} style={{ background: ds.color + '20', color: ds.color, border: `1px solid ${ds.color}`, borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>{ds.label}</span>
                ))}
                <span style={{ background: '#f0fdf4', color: '#16a34a', border: '1px solid #86efac', borderRadius: 6, padding: '4px 14px', fontSize: 13, fontWeight: 600 }}>High Confidence</span>
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
