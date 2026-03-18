/**
 * BiodiversityFinanceV2Page.jsx
 * Route: /biodiversity-finance-v2
 * Concept: Biodiversity Finance v2 — TNFD LEAP · PBAF · ENCORE · GBF COP15
 */
import React, { useState, useMemo } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  LineChart, Line, AreaChart, Area, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
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

const TABS = ['TNFD LEAP', 'ENCORE Services', 'PBAF & MSA', 'GBF / BNG', 'BFFI & Reporting'];
const COLORS = ['#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5', '#f59e0b', '#ef4444'];

const ENCORE_SERVICES = [
  'Water regulation', 'Climate regulation', 'Flood & storm regulation', 'Air quality',
  'Soil quality', 'Disease & pest control', 'Pollination', 'Noise & visual',
  'Genetic material', 'Nursery population', 'Biomass', 'Freshwater',
  'Ground water', 'Surface water', 'Fibres & materials', 'Renewable energy',
  'Medicinal resources', 'Ornamental resources', 'Carbon sequestration',
  'Coastal protection', 'Erosion control', 'Mass consolidation', 'Dilution',
];

export default function BiodiversityFinanceV2Page() {
  const [tab, setTab] = useState(0);
  const [entity, setEntity] = useState('Alpha Investments SA');
  const [sector, setSector] = useState('banking');
  const [location, setLocation] = useState('Western Europe');
  const [leapData, setLeapData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [method, setMethod] = useState('outstanding_amount');
  const [preHabitat, setPreHabitat] = useState(12);
  const [postHabitat, setPostHabitat] = useState(18);
  const [habitatType, setHabitatType] = useState('lowland_meadow');
  const seed = 42;

  const encoreData = useMemo(() => ENCORE_SERVICES.map((s, i) => ({
    service: s,
    dependency: +(seeded(i, seed) * 5).toFixed(2),
    impact: +(seeded(i + 100, seed) * 5).toFixed(2),
    level: ['very_high', 'high', 'medium', 'low', 'very_low'][Math.floor(seeded(i + 7, seed) * 5)],
  })), []);

  const radarData = useMemo(() => encoreData.slice(0, 8).map(s => ({
    service: s.service.split(' ')[0],
    dependency: s.dependency,
    impact: s.impact,
  })), [encoreData]);

  const leapSteps = useMemo(() => [
    { step: 'Locate', score: +(seeded(0, seed) * 40 + 55).toFixed(1) },
    { step: 'Evaluate', score: +(seeded(1, seed) * 40 + 50).toFixed(1) },
    { step: 'Assess', score: +(seeded(2, seed) * 40 + 45).toFixed(1) },
    { step: 'Prepare', score: +(seeded(3, seed) * 40 + 40).toFixed(1) },
  ], []);

  const compositeLeap = useMemo(() => +(leapSteps.reduce((a, b) => a + b.score, 0) / 4).toFixed(1), [leapSteps]);

  const msaTime = useMemo(() => Array.from({ length: 5 }, (_, i) => ({
    year: 2021 + i,
    msa: +(seeded(i + 20, seed) * 0.08 + 0.10).toFixed(4),
  })), []);

  const pbafPie = useMemo(() => [
    { name: 'Outstanding Amount', value: +(seeded(10, seed) * 40 + 40).toFixed(1) },
    { name: 'Equity Ownership', value: +(seeded(11, seed) * 30 + 20).toFixed(1) },
    { name: 'Enterprise Value', value: +(seeded(12, seed) * 20 + 10).toFixed(1) },
  ], []);

  const gbfScores = useMemo(() => [
    { goal: 'Goal A — Ecosystem Integrity', score: +(seeded(30, seed) * 40 + 50).toFixed(0) },
    { goal: 'Goal B — Sustainable Use', score: +(seeded(31, seed) * 40 + 45).toFixed(0) },
    { goal: 'Goal C — Fair & Equitable Sharing', score: +(seeded(32, seed) * 40 + 40).toFixed(0) },
    { goal: 'Goal D — Adequate Means of Impl.', score: +(seeded(33, seed) * 40 + 35).toFixed(0) },
  ], []);

  const netGainPct = useMemo(() => (((postHabitat - preHabitat) / preHabitat) * 100).toFixed(1), [preHabitat, postHabitat]);
  const creditRequired = parseFloat(netGainPct) < 10;

  const bngData = useMemo(() => [
    { name: 'Pre-Development', units: parseFloat(preHabitat) },
    { name: 'Post-Development', units: parseFloat(postHabitat) },
  ], [preHabitat, postHabitat]);

  const frameworks = [
    { name: 'ESRS E4', status: 'Aligned', ref: 'E4-5 Biodiversity & ecosystems', color: 'emerald' },
    { name: 'GRI 304', status: 'Aligned', ref: 'GRI 304-1 Sites near protected areas', color: 'emerald' },
    { name: 'EU Taxonomy DNSH', status: 'Partial', ref: 'Art. 17 Do No Significant Harm', color: 'amber' },
    { name: 'SBTN', status: 'In Progress', ref: 'Step 3 — Set targets', color: 'blue' },
  ];

  const disclosureGaps = [
    'MSA footprint not geo-referenced to IBAT data',
    'PBAF attribution for unlisted equity missing',
    'GBF Target 15 financial disclosure absent',
    'TNFD Assess step incomplete (no IPBES linkage)',
  ];

  function levelBadge(level) {
    const map = {
      very_high: 'bg-red-100 text-red-700',
      high: 'bg-amber-100 text-amber-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700',
      very_low: 'bg-gray-100 text-gray-500',
    };
    return <span className={`text-xs px-2 py-0.5 rounded font-medium ${map[level] || 'bg-gray-100 text-gray-500'}`}>{level.replace('_', ' ')}</span>;
  }

  async function runLeap() {
    setLoading(true);
    try {
      const r = await axios.post(`${API}/api/v1/biodiversity/leap`, { entity, sector, location });
      setLeapData(r.data);
    } catch {
      setLeapData({ composite: compositeLeap, steps: leapSteps });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="p-6 bg-white min-h-screen text-black">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-black">Biodiversity Finance v2</h1>
        <p className="text-sm text-gray-500 mt-1">TNFD LEAP · PBAF · ENCORE · GBF COP15 Alignment</p>
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
          <Section title="TNFD LEAP Assessment">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} />
              <Sel label="Sector" value={sector} onChange={e => setSector(e.target.value)}>
                <option value="banking">Banking</option>
                <option value="insurance">Insurance</option>
                <option value="asset_management">Asset Management</option>
                <option value="corporate">Corporate</option>
              </Sel>
              <Inp label="Location / Region" value={location} onChange={e => setLocation(e.target.value)} />
            </div>
            <Btn onClick={runLeap} disabled={loading}>{loading ? 'Running...' : 'Run LEAP Assessment'}</Btn>
          </Section>

          <Section title="LEAP Composite Score">
            <Row>
              <KpiCard label="Composite LEAP Score" value={`${compositeLeap}/100`} sub="All 4 steps weighted equally" color="emerald" />
              <KpiCard label="Locate" value={`${leapSteps[0].score}`} sub="Footprint mapping" color="blue" />
              <KpiCard label="Evaluate" value={`${leapSteps[1].score}`} sub="Dependency & impact" color="blue" />
              <KpiCard label="Assess" value={`${leapSteps[2].score}`} sub="Material risk identification" color="blue" />
            </Row>
          </Section>

          <Section title="LEAP Step Completeness">
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={leapSteps} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="step" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar dataKey="score" fill="#059669" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="4-Step Progress">
            {leapSteps.map((s, i) => (
              <div key={s.step} className="flex items-center gap-3 mb-2">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${s.score >= 70 ? 'bg-emerald-100 text-emerald-700' : s.score >= 50 ? 'bg-amber-100 text-amber-700' : 'bg-red-100 text-red-700'}`}>{i + 1}</div>
                <span className="text-sm font-medium w-20">{s.step}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${s.score}%` }} />
                </div>
                <span className="text-sm font-semibold text-gray-700 w-12 text-right">{s.score}%</span>
              </div>
            ))}
          </Section>
        </div>
      )}

      {tab === 1 && (
        <div>
          <Section title="Ecosystem Service Dependency vs Impact (Top 8)">
            <ResponsiveContainer width="100%" height={320}>
              <RadarChart data={radarData}>
                <PolarGrid />
                <PolarAngleAxis dataKey="service" tick={{ fontSize: 11 }} />
                <PolarRadiusAxis domain={[0, 5]} tick={{ fontSize: 9 }} />
                <Radar name="Dependency" dataKey="dependency" stroke="#059669" fill="#059669" fillOpacity={0.3} />
                <Radar name="Impact" dataKey="impact" stroke="#f59e0b" fill="#f59e0b" fillOpacity={0.3} />
                <Legend />
                <Tooltip />
              </RadarChart>
            </ResponsiveContainer>
          </Section>

          <Section title="All 23 ENCORE Ecosystem Services">
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                    <th className="px-3 py-2 text-left">Service</th>
                    <th className="px-3 py-2 text-right">Dependency</th>
                    <th className="px-3 py-2 text-right">Impact</th>
                    <th className="px-3 py-2 text-left">Level</th>
                    <th className="px-3 py-2 text-left">Materiality</th>
                  </tr>
                </thead>
                <tbody>
                  {encoreData.map((s, i) => (
                    <tr key={s.service} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                      <td className="px-3 py-2 font-medium">{s.service}</td>
                      <td className="px-3 py-2 text-right">{s.dependency.toFixed(2)}</td>
                      <td className="px-3 py-2 text-right">{s.impact.toFixed(2)}</td>
                      <td className="px-3 py-2">{levelBadge(s.level)}</td>
                      <td className="px-3 py-2">
                        {s.level === 'very_high' || s.level === 'high'
                          ? <span className="text-xs bg-red-50 text-red-700 border border-red-200 px-2 py-0.5 rounded">Material</span>
                          : <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded">Monitor</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Section>
        </div>
      )}

      {tab === 2 && (
        <div>
          <Section title="PBAF Attribution Settings">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <Sel label="Attribution Method" value={method} onChange={e => setMethod(e.target.value)}>
                <option value="outstanding_amount">Outstanding Amount</option>
                <option value="equity_ownership">Equity Ownership</option>
                <option value="enterprise_value">Enterprise Value</option>
              </Sel>
              <KpiCard label="PBAF Attribution Factor" value="0.342" sub={method.replace('_', ' ')} color="emerald" />
              <KpiCard label="MSA Footprint" value="4,820 km²" sub="Mean Species Abundance" color="blue" />
              <KpiCard label="MSA Loss Fraction" value="12.4%" sub="vs. pristine baseline" color="amber" />
            </div>
          </Section>

          <Section title="Portfolio Attribution by Method">
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pbafPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={({ name, value }) => `${name}: ${value}%`}>
                  {pbafPie.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </Section>

          <Section title="MSA Footprint Over Time (km²)">
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={msaTime}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="year" />
                <YAxis />
                <Tooltip formatter={v => v.toFixed(4)} />
                <Area type="monotone" dataKey="msa" stroke="#059669" fill="#d1fae5" name="MSA" />
              </AreaChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}

      {tab === 3 && (
        <div>
          <Section title="GBF 30×30 Alignment Scorecard">
            <Row>
              {gbfScores.map(g => (
                <KpiCard key={g.goal} label={g.goal.split('—')[0].trim()} value={`${g.score}%`} sub={g.goal.split('—')[1]?.trim()} color="emerald" />
              ))}
            </Row>
            <div className="mt-2">
              <span className="text-sm font-medium text-gray-700">COP15 Contribution: </span>
              <span className="text-emerald-700 font-bold text-lg">{+(seeded(50, seed) * 20 + 55).toFixed(1)}%</span>
              <span className="text-xs text-gray-400 ml-2">vs 30×30 target</span>
            </div>
          </Section>

          <Section title="BNG Calculator">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
              <Inp label="Pre-Development Units" type="number" value={preHabitat} onChange={e => setPreHabitat(parseFloat(e.target.value) || 0)} />
              <Inp label="Post-Development Units" type="number" value={postHabitat} onChange={e => setPostHabitat(parseFloat(e.target.value) || 0)} />
              <Sel label="Habitat Type" value={habitatType} onChange={e => setHabitatType(e.target.value)}>
                <option value="lowland_meadow">Lowland Meadow</option>
                <option value="woodland">Woodland</option>
                <option value="wetland">Wetland</option>
                <option value="heathland">Heathland</option>
              </Sel>
              <div className="flex flex-col justify-end">
                <KpiCard label="Net Gain %" value={`${netGainPct}%`} sub={creditRequired ? 'Credits required' : 'No credits needed'} color={parseFloat(netGainPct) >= 10 ? 'emerald' : 'red'} />
              </div>
            </div>
          </Section>

          <Section title="BNG Habitat Units Before / After">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={bngData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="units" radius={[4, 4, 0, 0]}>
                  <Cell fill="#f59e0b" />
                  <Cell fill="#059669" />
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Section>
        </div>
      )}

      {tab === 4 && (
        <div>
          <Section title="BFFI Score">
            <Row>
              <KpiCard label="BFFI Score" value="0.48 PDF/m²/yr" sub="Potentially Disappeared Fraction" color="emerald" />
              <KpiCard label="Biodiversity Footprint" value="2,340 km² MSA" sub="Absolute impact" color="blue" />
              <KpiCard label="Intensity Score" value="12.4 MSA·km²/M€" sub="Per million EUR invested" color="amber" />
              <KpiCard label="SBTN Alignment" value="Developing" sub="Science Based Targets for Nature" color="amber" />
            </Row>
          </Section>

          <Section title="Cross-Framework Alignment">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-gray-50 text-xs text-gray-500 uppercase">
                  <th className="px-3 py-2 text-left">Framework</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Reference</th>
                </tr>
              </thead>
              <tbody>
                {frameworks.map((f, i) => (
                  <tr key={f.name} className={i % 2 === 0 ? 'bg-white' : 'bg-gray-50'}>
                    <td className="px-3 py-2 font-semibold">{f.name}</td>
                    <td className="px-3 py-2">
                      <span className={`text-xs px-2 py-0.5 rounded font-medium bg-${f.color}-100 text-${f.color}-700`}>{f.status}</span>
                    </td>
                    <td className="px-3 py-2 text-gray-500">{f.ref}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          <Section title="Disclosure Gaps">
            <ul className="space-y-2">
              {disclosureGaps.map((g, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-700">
                  <span className="mt-0.5 w-4 h-4 rounded-full bg-amber-100 text-amber-700 text-xs flex items-center justify-center font-bold flex-shrink-0">!</span>
                  {g}
                </li>
              ))}
            </ul>
          </Section>

          <Section title="Report Export">
            <div className="flex gap-3">
              <Btn onClick={() => alert('TNFD/PBAF report export initiated')}>Download TNFD Report</Btn>
              <Btn onClick={() => alert('GBF alignment export initiated')}>Export GBF Scorecard</Btn>
            </div>
          </Section>
        </div>
      )}
    </div>
  );
}
