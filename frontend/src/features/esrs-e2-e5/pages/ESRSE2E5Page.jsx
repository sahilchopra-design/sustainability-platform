/**
 * ESRSE2E5Page.jsx
 * Route: /esrs-e2-e5
 * Tabs: Overview | E2 Pollution | E3 Water & Marine | E4 Biodiversity | E5 Circular Economy
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  AreaChart, Area, PieChart, Pie, Cell,
  ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || '';
const TT = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111', fontSize: 11 };
const EMERALD = '#10b981';
const TABS = ['Overview', 'E2 Pollution', 'E3 Water & Marine', 'E4 Biodiversity', 'E5 Circular Economy'];

const rng = (seed) => { let s = seed; return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }; };

const Section = ({ title, children }) => (
  <div className="mb-6">
    {title && <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{title}</div>}
    {children}
  </div>
);

const KpiCard = ({ label, value, sub, accent }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <div className="text-xs text-gray-500 mb-1">{label}</div>
    <div className={`text-2xl font-bold ${accent ? 'text-emerald-600' : 'text-black'}`}>{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
);

const Row = ({ children }) => (
  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">{children}</div>
);

const Inp = ({ label, ...p }) => (
  <div className="mb-3">
    <label className="block text-xs text-gray-500 mb-1">{label}</label>
    <input className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400" {...p} />
  </div>
);

const Sel = ({ label, children, ...p }) => (
  <div className="mb-3">
    <label className="block text-xs text-gray-500 mb-1">{label}</label>
    <select className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400" {...p}>{children}</select>
  </div>
);

const Btn = ({ children, ...p }) => (
  <button className="bg-black text-white text-sm px-4 py-2 rounded hover:bg-gray-800 transition-colors" {...p}>{children}</button>
);

const Badge = ({ label, color }) => {
  const cls = { green: 'bg-emerald-50 text-emerald-700 border-emerald-200', amber: 'bg-amber-50 text-amber-700 border-amber-200', red: 'bg-red-50 text-red-700 border-red-200', blue: 'bg-blue-50 text-blue-700 border-blue-200', gray: 'bg-gray-50 text-gray-600 border-gray-200' }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-2 py-0.5 rounded border text-xs font-medium ${cls}`}>{label}</span>;
};

const StatusDot = ({ pct }) => {
  const color = pct >= 75 ? 'bg-emerald-500' : pct >= 50 ? 'bg-amber-400' : 'bg-red-400';
  return <span className={`inline-block w-2 h-2 rounded-full mr-1.5 ${color}`} />;
};

/* ── Seed-based mock data ─────────────────────────────────────────────────── */
function buildOverviewData(entity) {
  const r = rng(entity.split('').reduce((a, c) => a + c.charCodeAt(0), 42));
  const e2 = Math.round(40 + r() * 55);
  const e3 = Math.round(40 + r() * 55);
  const e4 = Math.round(35 + r() * 55);
  const e5 = Math.round(40 + r() * 55);
  const overall = Math.round((e2 + e3 + e4 + e5) / 4);
  const gaps = [
    { topic: 'E2 Pollution', gap: 'Air pollutant intensity metrics missing', severity: e2 < 60 ? 'High' : 'Medium' },
    { topic: 'E3 Water', gap: 'Water stress area disclosure incomplete', severity: e3 < 60 ? 'High' : 'Low' },
    { topic: 'E4 Biodiversity', gap: 'ENCORE dependency mapping not completed', severity: e4 < 60 ? 'High' : 'Medium' },
    { topic: 'E5 Circular Economy', gap: 'Recycled content % not quantified', severity: e5 < 60 ? 'High' : 'Low' },
  ];
  const material = [e2, e3, e4, e5].filter(v => v < 70).length;
  return { e2, e3, e4, e5, overall, gaps, material };
}

/* ── Tab 1: Overview ─────────────────────────────────────────────────────── */
function OverviewTab() {
  const [entity, setEntity] = useState('Acme Industries AG');
  const [period, setPeriod] = useState('2024');
  const [nace, setNace] = useState('C24');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/esrs-e2-e5/assess`, { entity_name: entity, reporting_period: period, nace_sector: nace });
      setResult(data);
    } catch {
      setResult(buildOverviewData(entity));
    } finally { setLoading(false); }
  };

  const d = result || buildOverviewData(entity);
  const radarData = [
    { topic: 'E2 Pollution', score: d.e2 },
    { topic: 'E3 Water', score: d.e3 },
    { topic: 'E4 Biodiversity', score: d.e4 },
    { topic: 'E5 Circular', score: d.e5 },
  ];

  return (
    <div>
      <Section title="Entity Configuration">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} />
          <Inp label="Reporting Period" value={period} onChange={e => setPeriod(e.target.value)} />
          <Sel label="NACE Sector" value={nace} onChange={e => setNace(e.target.value)}>
            {['B05','B08','C10','C13','C17','C19','C20','C21','C22','C23','C24','C25','D35','E36','E37','F41','G46','H49','I55','J62'].map(s => <option key={s}>{s}</option>)}
          </Sel>
        </div>
        <div className="flex gap-3 mt-2">
          <Btn onClick={run} disabled={loading}>{loading ? 'Running...' : 'Run Assessment'}</Btn>
          <Btn onClick={run} style={{ background: '#fff', color: '#000', border: '1px solid #e5e7eb' }}>Materiality Screen</Btn>
        </div>
      </Section>

      <div className="flex items-center gap-3 mb-4">
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg px-5 py-3 flex-1 text-center">
          <div className="text-xs text-gray-500 mb-1">Overall ESRS E2–E5 Compliance</div>
          <div className="text-4xl font-bold text-emerald-600">{d.overall}%</div>
        </div>
        <div className="bg-gray-50 border border-gray-200 rounded-lg px-5 py-3 text-center">
          <div className="text-xs text-gray-500 mb-1">Material Topics</div>
          <div className="text-3xl font-bold text-black">{d.material} / 4</div>
          <div className="text-xs text-gray-400 mt-1">requiring disclosure</div>
        </div>
      </div>

      <Row>
        <KpiCard label="E2 Pollution Compliance" value={`${d.e2}%`} sub="ESRS E2-1 to E2-6" accent={d.e2 >= 75} />
        <KpiCard label="E3 Water Compliance" value={`${d.e3}%`} sub="ESRS E3-1 to E3-5" accent={d.e3 >= 75} />
        <KpiCard label="E4 Biodiversity Compliance" value={`${d.e4}%`} sub="ESRS E4-1 to E4-6" accent={d.e4 >= 75} />
        <KpiCard label="E5 Circular Economy" value={`${d.e5}%`} sub="ESRS E5-1 to E5-6" accent={d.e5 >= 75} />
      </Row>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="Topic Compliance Radar">
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart data={radarData}>
              <PolarGrid />
              <PolarAngleAxis dataKey="topic" tick={{ fontSize: 11 }} />
              <PolarRadiusAxis domain={[0, 100]} tick={{ fontSize: 10 }} />
              <Radar name="Compliance %" dataKey="score" stroke={EMERALD} fill={EMERALD} fillOpacity={0.25} />
              <Tooltip contentStyle={TT} />
            </RadarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Disclosure Gaps Summary">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-1.5 text-gray-500 font-medium">Topic</th>
                <th className="text-left py-1.5 text-gray-500 font-medium">Gap</th>
                <th className="text-left py-1.5 text-gray-500 font-medium">Severity</th>
              </tr>
            </thead>
            <tbody>
              {d.gaps.map((g, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-1.5 text-gray-700 font-medium">{g.topic}</td>
                  <td className="py-1.5 text-gray-600 max-w-xs">{g.gap}</td>
                  <td className="py-1.5">
                    <Badge label={g.severity} color={g.severity === 'High' ? 'red' : g.severity === 'Medium' ? 'amber' : 'green'} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 2: E2 Pollution ─────────────────────────────────────────────────── */
function E2PollutionTab() {
  const [entity, setEntity] = useState('Acme Industries AG');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/esrs-e2-e5/assess-e2`, { entity_name: entity });
      setResult(data);
    } catch { setResult(null); } finally { setLoading(false); }
  };

  const r = rng(entity.split('').reduce((a, c) => a + c.charCodeAt(0), 7));
  const compliance = Math.round(45 + r() * 50);
  const airData = [
    { name: 'NOx', value: Math.round(200 + r() * 800), unit: 't/yr' },
    { name: 'SOx', value: Math.round(50 + r() * 400), unit: 't/yr' },
    { name: 'PM2.5', value: Math.round(10 + r() * 100), unit: 't/yr' },
    { name: 'NMVOC', value: Math.round(30 + r() * 200), unit: 't/yr' },
  ];
  const waterPollutants = [
    { substance: 'Nitrogen (total)', conc: `${(r() * 15 + 2).toFixed(1)} mg/L`, limit: '10 mg/L', status: r() > 0.5 ? 'Compliant' : 'Exceeds' },
    { substance: 'Phosphorus (total)', conc: `${(r() * 2 + 0.5).toFixed(2)} mg/L`, limit: '1 mg/L', status: r() > 0.5 ? 'Compliant' : 'Exceeds' },
    { substance: 'Heavy Metals (Cd)', conc: `${(r() * 0.05).toFixed(3)} mg/L`, limit: '0.01 mg/L', status: r() > 0.6 ? 'Compliant' : 'Exceeds' },
  ];
  const disclosures = ['E2-1','E2-2','E2-3','E2-4','E2-5','E2-6'].map(d => ({ d, pct: Math.round(40 + r() * 60) }));
  const gaps = [
    'E2-2: Pollutant emission intensity not reported per unit of production',
    'E2-4: Substances of very high concern (SVHC) inventory incomplete',
    'E2-6: Financial effects of pollution incidents not quantified',
  ].slice(0, compliance < 70 ? 3 : 1);

  return (
    <div>
      <Section title="Assessment Input">
        <div className="flex gap-4 items-end">
          <div className="flex-1"><Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} /></div>
          <div className="mb-3"><Btn onClick={run} disabled={loading}>{loading ? 'Running...' : 'Assess E2 Pollution'}</Btn></div>
        </div>
      </Section>

      <Row>
        <KpiCard label="E2 Compliance" value={`${compliance}%`} sub="across E2-1 to E2-6" accent={compliance >= 75} />
        <KpiCard label="Air Pollutants Disclosed" value={`${airData.length}/4`} sub="NOx · SOx · PM2.5 · NMVOC" />
        <KpiCard label="Water Pollutants" value={`${waterPollutants.length}`} sub="substances tracked" />
        <KpiCard label="Open Gaps" value={gaps.length} sub="requiring remediation" />
      </Row>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="Air Pollutant Emissions (t/yr)">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={airData} margin={{ left: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={TT} />
              <Bar dataKey="value" fill={EMERALD} radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Water Pollutants">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                {['Substance','Concentration','ELV Limit','Status'].map(h => <th key={h} className="text-left py-1.5 text-gray-500 font-medium">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {waterPollutants.map((w, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-2 text-gray-700">{w.substance}</td>
                  <td className="py-2 text-gray-600">{w.conc}</td>
                  <td className="py-2 text-gray-500">{w.limit}</td>
                  <td className="py-2"><Badge label={w.status} color={w.status === 'Compliant' ? 'green' : 'red'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>

      <Section title="Disclosure Completeness — E2-1 to E2-6">
        <div className="space-y-2">
          {disclosures.map(({ d: disc, pct }) => (
            <div key={disc} className="flex items-center gap-3">
              <span className="text-xs font-mono text-gray-600 w-12">{disc}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full transition-all" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
            </div>
          ))}
        </div>
      </Section>

      {gaps.length > 0 && (
        <Section title="Compliance Gaps">
          <ul className="space-y-1.5">
            {gaps.map((g, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                <span className="mt-0.5 text-red-400">&#9679;</span>{g}
              </li>
            ))}
          </ul>
        </Section>
      )}
    </div>
  );
}

/* ── Tab 3: E3 Water & Marine ─────────────────────────────────────────────── */
function E3WaterTab() {
  const [entity, setEntity] = useState('Acme Industries AG');
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try { await axios.post(`${API}/api/v1/esrs-e2-e5/assess-e3`, { entity_name: entity }); }
    catch { } finally { setLoading(false); }
  };

  const r = rng(entity.split('').reduce((a, c) => a + c.charCodeAt(0), 13));
  const withdrawal = Math.round(500000 + r() * 2000000);
  const discharge = Math.round(withdrawal * (0.5 + r() * 0.3));
  const consumption = withdrawal - discharge;
  const stressPct = Math.round(20 + r() * 60);
  const trend = Array.from({ length: 6 }, (_, i) => ({
    year: 2019 + i,
    withdrawal: Math.round(withdrawal * (0.85 + r() * 0.3)),
    consumption: Math.round(consumption * (0.8 + r() * 0.4)),
  }));
  const watersheds = [
    { name: 'Rhine Basin — Germany', operations: 3, tier: 'High' },
    { name: 'Po Valley — Italy', operations: 2, tier: 'High' },
    { name: 'Thames Basin — UK', operations: 1, tier: 'Medium' },
    { name: 'Mississippi — USA', operations: 4, tier: 'Low' },
  ];
  const disclosures = ['E3-1','E3-2','E3-3','E3-4','E3-5'].map(d => ({ d, pct: Math.round(40 + r() * 55) }));

  return (
    <div>
      <Section title="Assessment Input">
        <div className="flex gap-4 items-end">
          <div className="flex-1"><Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} /></div>
          <div className="mb-3"><Btn onClick={run} disabled={loading}>{loading ? 'Running...' : 'Assess E3 Water'}</Btn></div>
        </div>
      </Section>

      <Row>
        <KpiCard label="Water Withdrawal" value={`${(withdrawal / 1000).toFixed(0)}k m3`} sub="total annual" />
        <KpiCard label="Water Discharge" value={`${(discharge / 1000).toFixed(0)}k m3`} sub="to water bodies" />
        <KpiCard label="Water Consumption" value={`${(consumption / 1000).toFixed(0)}k m3`} sub="net consumption" />
        <KpiCard label="Water Stress Exposure" value={`${stressPct}%`} sub="operations in high-stress areas" accent={stressPct > 50} />
      </Row>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="Withdrawal vs Consumption Trend (6 years)">
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={trend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TT} formatter={(v) => [`${(v/1000).toFixed(0)}k m3`]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Area type="monotone" dataKey="withdrawal" stroke="#6366f1" fill="#ede9fe" name="Withdrawal" />
              <Area type="monotone" dataKey="consumption" stroke={EMERALD} fill="#d1fae5" name="Consumption" />
            </AreaChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Operations by Watershed Stress Tier">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                {['Watershed','Operations','Stress Tier'].map(h => <th key={h} className="text-left py-1.5 text-gray-500 font-medium">{h}</th>)}
              </tr>
            </thead>
            <tbody>
              {watersheds.map((w, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-2 text-gray-700">{w.name}</td>
                  <td className="py-2 text-gray-600 text-center">{w.operations}</td>
                  <td className="py-2"><Badge label={w.tier} color={w.tier === 'High' ? 'red' : w.tier === 'Medium' ? 'amber' : 'green'} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>

      <Section title="Disclosure Completeness — E3-1 to E3-5">
        <div className="space-y-2">
          {disclosures.map(({ d: disc, pct }) => (
            <div key={disc} className="flex items-center gap-3">
              <span className="text-xs font-mono text-gray-600 w-12">{disc}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 4: E4 Biodiversity ──────────────────────────────────────────────── */
function E4BiodiversityTab() {
  const [entity, setEntity] = useState('Acme Industries AG');
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try { await axios.post(`${API}/api/v1/esrs-e2-e5/assess-e4`, { entity_name: entity }); }
    catch { } finally { setLoading(false); }
  };

  const r = rng(entity.split('').reduce((a, c) => a + c.charCodeAt(0), 19));
  const sensitivePct = Math.round(10 + r() * 45);
  const landChange = Math.round(50 + r() * 500);
  const speciesAffected = Math.round(5 + r() * 40);
  const ecoServices = Math.round(4 + r() * 8);
  const encoreDeps = ['Water regulation', 'Soil quality', 'Climate regulation', 'Flood regulation', 'Pollination', 'Erosion control'].slice(0, Math.round(3 + r() * 3));
  const disclosures = ['E4-1','E4-2','E4-3','E4-4','E4-5','E4-6'].map(d => ({ d, pct: Math.round(30 + r() * 60) }));

  return (
    <div>
      <Section title="Assessment Input">
        <div className="flex gap-4 items-end">
          <div className="flex-1"><Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} /></div>
          <div className="mb-3"><Btn onClick={run} disabled={loading}>{loading ? 'Running...' : 'Assess E4 Biodiversity'}</Btn></div>
        </div>
      </Section>

      <Row>
        <KpiCard label="Operations in Sensitive Areas" value={`${sensitivePct}%`} sub="Natura 2000 / KBA / WHS" accent={sensitivePct > 30} />
        <KpiCard label="Land Use Change" value={`${landChange} ha`} sub="since 2015 baseline" />
        <KpiCard label="Species Affected" value={speciesAffected} sub="IUCN Red List species" />
        <KpiCard label="Ecosystem Service Deps" value={ecoServices} sub="ENCORE-identified dependencies" accent />
      </Row>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="ENCORE Ecosystem Services Dependencies">
          <div className="flex flex-wrap gap-2 pt-1">
            {encoreDeps.map((dep, i) => (
              <span key={i} className="px-3 py-1 bg-emerald-50 text-emerald-700 border border-emerald-200 rounded-full text-xs font-medium">{dep}</span>
            ))}
          </div>
          <div className="mt-4 text-xs text-gray-500 bg-gray-50 rounded p-3">
            ENCORE (Exploring Natural Capital Opportunities, Risks and Exposure) framework used per TNFD LEAP methodology and ESRS E4-3 requirements.
          </div>
        </Section>

        <Section title="SBTN / TNFD Cross-Reference">
          <table className="w-full text-xs">
            <tbody>
              {[
                ['SBTN Step 1', 'Scoping', 'Align with E4-2 IRO assessment'],
                ['SBTN Step 2', 'Locate', 'Map to E4-3 site disclosure'],
                ['TNFD LEAP-L1', 'Locate interface', 'E4-4 area metrics'],
                ['TNFD LEAP-E1', 'Env. conditions', 'E4-5 sensitive areas'],
              ].map(([fw, step, note], i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-2 font-mono text-xs text-gray-500 w-28">{fw}</td>
                  <td className="py-2 text-gray-700 font-medium">{step}</td>
                  <td className="py-2 text-gray-500">{note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      </div>

      <Section title="Disclosure Completeness — E4-1 to E4-6">
        <div className="space-y-2">
          {disclosures.map(({ d: disc, pct }) => (
            <div key={disc} className="flex items-center gap-3">
              <span className="text-xs font-mono text-gray-600 w-12">{disc}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Tab 5: E5 Circular Economy ──────────────────────────────────────────── */
function E5CircularTab() {
  const [entity, setEntity] = useState('Acme Industries AG');
  const [loading, setLoading] = useState(false);

  const run = async () => {
    setLoading(true);
    try { await axios.post(`${API}/api/v1/esrs-e2-e5/assess-e5`, { entity_name: entity }); }
    catch { } finally { setLoading(false); }
  };

  const r = rng(entity.split('').reduce((a, c) => a + c.charCodeAt(0), 23));
  const inflows = Math.round(10000 + r() * 90000);
  const recycledContent = Math.round(10 + r() * 50);
  const waste = Math.round(1000 + r() * 9000);
  const circularityRate = Math.round(15 + r() * 55);
  const wasteDestination = [
    { name: 'Recycling', value: Math.round(r() * 40 + 20) },
    { name: 'Reuse', value: Math.round(r() * 20 + 5) },
    { name: 'Recovery', value: Math.round(r() * 15 + 5) },
    { name: 'Incineration', value: Math.round(r() * 20 + 10) },
    { name: 'Landfill', value: Math.round(r() * 25 + 10) },
  ];
  const flowData = [
    { cat: 'Renewable', inflow: Math.round(r() * inflows * 0.3), outflow: Math.round(r() * inflows * 0.25) },
    { cat: 'Non-renewable', inflow: Math.round(r() * inflows * 0.5), outflow: Math.round(r() * inflows * 0.4) },
    { cat: 'Recycled', inflow: Math.round(r() * inflows * 0.2), outflow: Math.round(r() * inflows * 0.18) },
  ];
  const disclosures = ['E5-1','E5-2','E5-3','E5-4','E5-5','E5-6'].map(d => ({ d, pct: Math.round(35 + r() * 55) }));
  const PIE_COLORS = [EMERALD, '#6366f1', '#f59e0b', '#ef4444', '#6b7280'];

  return (
    <div>
      <Section title="Assessment Input">
        <div className="flex gap-4 items-end">
          <div className="flex-1"><Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} /></div>
          <div className="mb-3"><Btn onClick={run} disabled={loading}>{loading ? 'Running...' : 'Assess E5 Circular'}</Btn></div>
        </div>
      </Section>

      <Row>
        <KpiCard label="Material Inflows" value={`${(inflows/1000).toFixed(0)}k t`} sub="total annual input" />
        <KpiCard label="Recycled Content" value={`${recycledContent}%`} sub="of total material inputs" accent={recycledContent > 30} />
        <KpiCard label="Waste Generated" value={`${(waste/1000).toFixed(1)}k t`} sub="total waste" />
        <KpiCard label="Circularity Rate" value={`${circularityRate}%`} sub="circular material use" accent={circularityRate > 40} />
      </Row>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="Waste Destination">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={wasteDestination} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label={({ name, value }) => `${name}: ${value}%`} labelLine={false}>
                {wasteDestination.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={TT} formatter={(v) => [`${v}%`]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Resource Inflows vs Outflows by Category">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={flowData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="cat" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TT} formatter={(v) => [`${(v/1000).toFixed(1)}k t`]} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="inflow" fill={EMERALD} name="Inflow" radius={[3,3,0,0]} />
              <Bar dataKey="outflow" fill="#6366f1" name="Outflow" radius={[3,3,0,0]} />
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="Disclosure Completeness — E5-1 to E5-6">
        <div className="space-y-2">
          {disclosures.map(({ d: disc, pct }) => (
            <div key={disc} className="flex items-center gap-3">
              <span className="text-xs font-mono text-gray-600 w-12">{disc}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-2">
                <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${pct}%` }} />
              </div>
              <span className="text-xs text-gray-500 w-8 text-right">{pct}%</span>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────────── */
function ESRSE2E5Page() {
  const [tab, setTab] = useState(0);
  const tabContent = [<OverviewTab />, <E2PollutionTab />, <E3WaterTab />, <E4BiodiversityTab />, <E5CircularTab />];

  return (
    <div className="min-h-screen bg-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">ESRS E2–E5 Environmental Disclosures</h1>
          <p className="text-sm text-gray-500 mt-1">Pollution · Water & Marine · Biodiversity · Circular Economy — ESRS 2024 compliance</p>
        </div>

        <div className="flex gap-0 border-b border-gray-200 mb-6 overflow-x-auto">
          {TABS.map((t, i) => (
            <button
              key={i}
              onClick={() => setTab(i)}
              className={`px-4 py-2.5 text-sm whitespace-nowrap transition-colors ${tab === i ? 'border-b-2 border-emerald-500 text-black font-semibold' : 'text-gray-500 hover:text-gray-700'}`}
            >
              {t}
            </button>
          ))}
        </div>

        <div>{tabContent[tab]}</div>
      </div>
    </div>
  );
}

export default ESRSE2E5Page;
