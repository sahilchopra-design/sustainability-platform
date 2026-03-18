/**
 * CarbonCreditQualityPage.jsx
 * Route: /carbon-credit-quality
 * Tabs: Project Scoring | Portfolio Analysis | CCP Eligibility | CORSIA & Article 6 | Reference
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  PieChart, Pie, Cell,
  ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || '';
const TT = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111', fontSize: 11 };
const EMERALD = '#10b981';
const TABS = ['Project Scoring', 'Portfolio Analysis', 'CCP Eligibility', 'CORSIA & Article 6', 'Reference'];

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
  const cls = { green: 'bg-emerald-50 text-emerald-700 border-emerald-200', amber: 'bg-amber-50 text-amber-700 border-amber-200', red: 'bg-red-50 text-red-700 border-red-200', blue: 'bg-blue-50 text-blue-700 border-blue-200', yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200', gray: 'bg-gray-50 text-gray-600 border-gray-200' }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-2 py-0.5 rounded border text-xs font-medium ${cls}`}>{label}</span>;
};

const METHODOLOGIES = ['REDD+ (VM0007)', 'AMS-II.D Solar PV', 'ACM0002 Grid electricity', 'VM0010 REDD IFM', 'VM0033 Rice cultivation', 'ACM0006 Biogas', 'VM0042 WASH', 'AR-AM0014 Reforestation', 'VM0031 Cookstoves', 'AMS-III.D Methane recovery'];
const STANDARDS = ['vcs', 'gold_standard', 'cdm', 'art6_itmo', 'ccp'];
const TIER_COLORS = { A: '#10b981', B: '#f59e0b', C: '#f97316', D: '#ef4444' };

function tierColor(tier) {
  return { A: 'green', B: 'yellow', C: 'amber', D: 'red' }[tier] || 'gray';
}

function buildProjectScore(name, standard, methodology, projectType, vintage, volume) {
  const r = rng([name, standard, methodology, projectType, vintage, volume].join('').split('').reduce((a, c) => a + c.charCodeAt(0), 53));
  const add = Math.round(40 + r() * 55);
  const perm = Math.round(30 + r() * 65);
  const cobens = Math.round(30 + r() * 65);
  const overall = Math.round((add * 0.4 + perm * 0.35 + cobens * 0.25));
  const tier = overall >= 80 ? 'A' : overall >= 65 ? 'B' : overall >= 50 ? 'C' : 'D';
  const corsia = standard !== 'cdm' && overall >= 60;
  const ccp = overall >= 75 && standard !== 'cdm';
  const art6 = standard === 'art6_itmo';
  const priceMin = projectType === 'removal' ? 80 : 8;
  const priceMax = projectType === 'removal' ? 300 : 35;
  const priceMid = Math.round(priceMin + r() * (priceMax - priceMin));
  return {
    overall, tier, add, perm, cobens, corsia, ccp, art6,
    price: { min: priceMin, mid: priceMid, max: priceMax },
    issues: [
      overall < 70 ? 'Additionality baseline requires regulatory approval update' : null,
      perm < 60 ? 'Permanence buffer contribution below programme minimum' : null,
      cobens < 60 ? 'Co-benefits not independently verified' : null,
    ].filter(Boolean),
  };
}

/* ── Tab 1: Project Scoring ──────────────────────────────────────────────── */
function ProjectScoringTab() {
  const [name, setName] = useState('Amazon Rainforest REDD+');
  const [standard, setStandard] = useState('vcs');
  const [methodology, setMethodology] = useState('REDD+ (VM0007)');
  const [projectType, setProjectType] = useState('avoidance');
  const [vintage, setVintage] = useState('2023');
  const [volume, setVolume] = useState('50000');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const score = async () => {
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/api/v1/carbon-credit-quality/score-project`, { project_name: name, standard, methodology, project_type: projectType, vintage_year: parseInt(vintage), volume_tco2e: parseInt(volume) });
      setResult(data);
    } catch {
      setResult(buildProjectScore(name, standard, methodology, projectType, vintage, volume));
    } finally { setLoading(false); }
  };

  const d = result || buildProjectScore(name, standard, methodology, projectType, vintage, volume);

  return (
    <div>
      <Section title="Project Configuration">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Inp label="Project Name" value={name} onChange={e => setName(e.target.value)} />
          <Sel label="Standard" value={standard} onChange={e => setStandard(e.target.value)}>
            {STANDARDS.map(s => <option key={s} value={s}>{s.toUpperCase().replace('_', ' ')}</option>)}
          </Sel>
          <Sel label="Methodology" value={methodology} onChange={e => setMethodology(e.target.value)}>
            {METHODOLOGIES.map(m => <option key={m}>{m}</option>)}
          </Sel>
          <Sel label="Project Type" value={projectType} onChange={e => setProjectType(e.target.value)}>
            <option value="avoidance">Avoidance</option>
            <option value="removal">Removal</option>
            <option value="reduction">Reduction</option>
          </Sel>
          <Inp label="Vintage Year" value={vintage} onChange={e => setVintage(e.target.value)} type="number" />
          <Inp label="Volume (tCO2e)" value={volume} onChange={e => setVolume(e.target.value)} type="number" />
        </div>
        <Btn onClick={score} disabled={loading}>{loading ? 'Scoring...' : 'Score Project'}</Btn>
      </Section>

      <div className="flex items-center gap-4 mb-6">
        <div className="bg-white border border-gray-200 rounded-lg p-5 flex items-center gap-5">
          <div>
            <div className="text-xs text-gray-500 mb-1">Quality Tier</div>
            <div className={`text-5xl font-black`} style={{ color: TIER_COLORS[d.tier] }}>{d.tier}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500 mb-1">Overall Quality Score</div>
            <div className="text-4xl font-bold text-black">{d.overall}<span className="text-base text-gray-400">/100</span></div>
          </div>
        </div>
        <div className="flex gap-3">
          <div className="flex flex-col items-center bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <div className="text-xs text-gray-500 mb-1">CCP Label</div>
            <Badge label={d.ccp ? 'YES' : 'NO'} color={d.ccp ? 'green' : 'red'} />
          </div>
          <div className="flex flex-col items-center bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <div className="text-xs text-gray-500 mb-1">CORSIA Eligible</div>
            <Badge label={d.corsia ? 'YES' : 'NO'} color={d.corsia ? 'green' : 'red'} />
          </div>
          <div className="flex flex-col items-center bg-gray-50 border border-gray-200 rounded-lg px-4 py-3">
            <div className="text-xs text-gray-500 mb-1">Article 6 ITMO</div>
            <Badge label={d.art6 ? 'YES' : 'NO'} color={d.art6 ? 'blue' : 'gray'} />
          </div>
        </div>
      </div>

      <Row>
        <KpiCard label="Additionality Score" value={`${d.add}/100`} sub="regulatory + financial test" accent={d.add >= 70} />
        <KpiCard label="Permanence Risk Score" value={`${d.perm}/100`} sub="buffer & reversal risk" accent={d.perm >= 70} />
        <KpiCard label="Co-Benefits Score" value={`${d.cobens}/100`} sub="SDG / biodiversity" accent={d.cobens >= 70} />
        <KpiCard label="Price Range Estimate" value={`$${d.price.mid}/t`} sub={`$${d.price.min}–$${d.price.max} USD/tCO2e`} />
      </Row>

      {d.issues && d.issues.length > 0 && (
        <Section title="Quality Issues">
          <ul className="space-y-1.5">
            {d.issues.map((iss, i) => <li key={i} className="flex items-start gap-2 text-xs text-gray-600"><span className="text-amber-400 mt-0.5">&#9679;</span>{iss}</li>)}
          </ul>
        </Section>
      )}
    </div>
  );
}

/* ── Tab 2: Portfolio Analysis ───────────────────────────────────────────── */
function PortfolioAnalysisTab() {
  const [loading, setLoading] = useState(false);
  const [ran, setRan] = useState(false);

  const r = rng(2025 * 7 + 11);
  const PROJECTS = ['Borneo REDD+', 'Chilean Wind Farm', 'Kenya Cookstoves', 'NZ Reforestation', 'Brazil Solar PV'].map((name, i) => {
    const std = ['vcs', 'gold_standard', 'cdm', 'art6_itmo', 'ccp'][i];
    const type = ['avoidance', 'reduction', 'reduction', 'removal', 'reduction'][i];
    const d = buildProjectScore(name, std, METHODOLOGIES[i], type, '2023', String(Math.round(10000 + r() * 90000)));
    return { name, standard: std.toUpperCase().replace('_', ' '), type, tier: d.tier, score: d.overall, volume: Math.round(10000 + r() * 90000), ccp: d.ccp, corsia: d.corsia };
  });

  const tierDist = ['A','B','C','D'].map(t => ({ tier: t, count: PROJECTS.filter(p => p.tier === t).length }));
  const stdDist = Object.entries(PROJECTS.reduce((acc, p) => { acc[p.standard] = (acc[p.standard] || 0) + 1; return acc; }, {})).map(([name, value]) => ({ name, value }));
  const avgScore = Math.round(PROJECTS.reduce((a, p) => a + p.score, 0) / PROJECTS.length);
  const totalVol = PROJECTS.reduce((a, p) => a + p.volume, 0);
  const pctCcp = Math.round(PROJECTS.filter(p => p.ccp).length / PROJECTS.length * 100);
  const pctCorsia = Math.round(PROJECTS.filter(p => p.corsia).length / PROJECTS.length * 100);
  const PIE_COLORS = [EMERALD, '#6366f1', '#f59e0b', '#ef4444', '#6b7280'];

  const run = async () => {
    setLoading(true);
    try { await axios.post(`${API}/api/v1/carbon-credit-quality/score-portfolio`, { projects: PROJECTS }); }
    catch { } finally { setLoading(false); setRan(true); }
  };

  return (
    <div>
      <Section title="Portfolio Scoring">
        <Btn onClick={run} disabled={loading}>{loading ? 'Analysing...' : 'Analyse Portfolio (5 Projects)'}</Btn>
      </Section>

      <Row>
        <KpiCard label="Avg Quality Score" value={`${avgScore}/100`} accent={avgScore >= 65} />
        <KpiCard label="Total Volume" value={`${(totalVol/1000).toFixed(0)}k tCO2e`} sub="across all projects" />
        <KpiCard label="CCP Labelled" value={`${pctCcp}%`} sub="ICVCM certified" accent={pctCcp >= 50} />
        <KpiCard label="CORSIA Eligible" value={`${pctCorsia}%`} sub="ICAO approved" accent={pctCorsia >= 60} />
      </Row>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="Quality Tier Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={tierDist}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="tier" tick={{ fontSize: 12 }} />
              <YAxis allowDecimals={false} tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={TT} />
              <Bar dataKey="count" name="Projects" radius={[3,3,0,0]}>
                {tierDist.map((entry, i) => <Cell key={i} fill={TIER_COLORS[entry.tier] || EMERALD} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Portfolio by Standard">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie data={stdDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={75} label={({ name }) => name} labelLine={false}>
                {stdDist.map((_, i) => <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />)}
              </Pie>
              <Tooltip contentStyle={TT} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="Project Portfolio">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              {['Project','Standard','Type','Tier','Score','Volume (tCO2e)','CCP','CORSIA'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {PROJECTS.map((p, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-2 font-medium text-gray-800">{p.name}</td>
                <td className="py-2 text-gray-600">{p.standard}</td>
                <td className="py-2 text-gray-600 capitalize">{p.type}</td>
                <td className="py-2"><span className="font-bold" style={{ color: TIER_COLORS[p.tier] }}>{p.tier}</span></td>
                <td className="py-2 text-gray-700">{p.score}</td>
                <td className="py-2 text-gray-600">{p.volume.toLocaleString()}</td>
                <td className="py-2"><Badge label={p.ccp ? 'Yes' : 'No'} color={p.ccp ? 'green' : 'gray'} /></td>
                <td className="py-2"><Badge label={p.corsia ? 'Yes' : 'No'} color={p.corsia ? 'green' : 'gray'} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 3: CCP Eligibility ──────────────────────────────────────────────── */
const ICVCM_CRITERIA = [
  { id: 'CCP-01', name: 'Effective governance', description: 'Programme has robust governance including independent oversight' },
  { id: 'CCP-02', name: 'Tracking system', description: 'Unique serial number registry prevents double issuance' },
  { id: 'CCP-03', name: 'Transparent reporting', description: 'Publicly accessible methodology and project documentation' },
  { id: 'CCP-04', name: 'Robust independent third-party validation and verification', description: 'Accredited VVB assessment' },
  { id: 'CCP-05', name: 'Additionality', description: 'Emissions reductions are beyond business-as-usual' },
  { id: 'CCP-06', name: 'Permanence', description: 'Buffer pool or equivalent reversal mechanism in place' },
  { id: 'CCP-07', name: 'Robust quantification', description: 'Conservative baselines and uncertainty assessment' },
  { id: 'CCP-08', name: 'No double counting', description: 'No use in multiple registries or by multiple parties' },
  { id: 'CCP-09', name: 'Sustainable development safeguards', description: 'FPIC, human rights, biodiversity co-benefits' },
  { id: 'CCP-10', name: 'No net harm', description: 'Net emissions removals contribute to, not undermine, NDCs' },
];

function CCPEligibilityTab() {
  const [standard, setStandard] = useState('vcs');
  const [methodology, setMethodology] = useState('REDD+ (VM0007)');
  const [projectType, setProjectType] = useState('avoidance');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const check = async () => {
    setLoading(true);
    const r = rng([standard, methodology, projectType].join('').split('').reduce((a, c) => a + c.charCodeAt(0), 61));
    try {
      const { data } = await axios.post(`${API}/api/v1/carbon-credit-quality/check-ccp-eligibility`, { standard, methodology, project_type: projectType });
      setResult(data);
    } catch {
      const criteria = ICVCM_CRITERIA.map(c => ({
        ...c,
        status: r() > 0.25 ? 'pass' : r() > 0.5 ? 'partial' : 'fail',
        notes: r() > 0.6 ? 'Meets requirement' : 'Evidence review required',
      }));
      const eligible = criteria.filter(c => c.status === 'pass').length >= 8;
      setResult({ criteria, eligible, justification: eligible ? 'Majority of ICVCM Core Carbon Principles met under assessment.' : 'Insufficient criteria met; additionality and permanence evidence gaps remain.' });
    } finally { setLoading(false); }
  };

  const statusColor = { pass: 'green', partial: 'amber', fail: 'red' };

  return (
    <div>
      <Section title="CCP Eligibility Check">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Sel label="Standard" value={standard} onChange={e => setStandard(e.target.value)}>
            {STANDARDS.map(s => <option key={s} value={s}>{s.toUpperCase().replace('_', ' ')}</option>)}
          </Sel>
          <Sel label="Methodology" value={methodology} onChange={e => setMethodology(e.target.value)}>
            {METHODOLOGIES.map(m => <option key={m}>{m}</option>)}
          </Sel>
          <Sel label="Project Type" value={projectType} onChange={e => setProjectType(e.target.value)}>
            <option value="avoidance">Avoidance</option>
            <option value="removal">Removal</option>
            <option value="reduction">Reduction</option>
          </Sel>
        </div>
        <Btn onClick={check} disabled={loading}>{loading ? 'Checking...' : 'Check CCP Eligibility'}</Btn>
      </Section>

      {result && (
        <>
          <div className="flex items-center gap-4 mb-4">
            <div className={`px-5 py-3 rounded-lg border ${result.eligible ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
              <div className="text-xs text-gray-500 mb-1">CCP Label Eligible</div>
              <div className={`text-2xl font-bold ${result.eligible ? 'text-emerald-600' : 'text-red-600'}`}>{result.eligible ? 'YES' : 'NO'}</div>
            </div>
            <div className="text-sm text-gray-600 flex-1">{result.justification}</div>
          </div>

          <Section title="ICVCM 10 Core Carbon Principles Assessment">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100">
                  {['ID','Criterion','Status','Notes'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
                </tr>
              </thead>
              <tbody>
                {result.criteria.map((c, i) => (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-2 font-mono text-gray-500">{c.id}</td>
                    <td className="py-2 text-gray-700 font-medium">{c.name}</td>
                    <td className="py-2"><Badge label={c.status.toUpperCase()} color={statusColor[c.status] || 'gray'} /></td>
                    <td className="py-2 text-gray-500">{c.notes}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>
        </>
      )}
    </div>
  );
}

/* ── Tab 4: CORSIA & Article 6 ───────────────────────────────────────────── */
function CORSIAArticle6Tab() {
  const corsiaData = [
    { programme: 'Verra VCS', phase: 'Pilot + First + Second', vintages: '2016–2020 (Pilot)', eligible: true },
    { programme: 'Gold Standard', phase: 'Pilot + First + Second', vintages: '2016–2020 (Pilot)', eligible: true },
    { programme: 'CAR Climate Action Reserve', phase: 'Pilot', vintages: '2016–2020', eligible: true },
    { programme: 'ACR American Carbon Registry', phase: 'Pilot', vintages: '2016–2020', eligible: true },
    { programme: 'CDM', phase: 'Not approved', vintages: 'N/A', eligible: false },
    { programme: 'Art 6.4 ITMO', phase: 'Pilot (pending)', vintages: 'TBD', eligible: null },
  ];

  const buyerGuide = [
    { framework: 'SBTi (VCMI Platinum)', acceptable: ['Art 6.4 ITMOs with CA', 'CCP-labelled removal credits'], notes: 'Beyond value chain mitigation only for "beyond" claims' },
    { framework: 'VCMI Core', acceptable: ['High-quality VCS/GS credits', 'CCP-labelled credits'], notes: 'Minimum 20% removal credits recommended' },
    { framework: 'GCP (Gold Standard)', acceptable: ['Gold Standard CERs/VERs', 'CCP-labelled'], notes: 'Additionality proof required' },
    { framework: 'CORSIA (Airlines)', acceptable: ['CORSIA-eligible units only'], notes: 'See ICAO approved programme list' },
  ];

  return (
    <div>
      <Section title="CORSIA Approved Programmes">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              {['Programme','Phase Coverage','Eligible Vintages','CORSIA Eligible'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {corsiaData.map((row, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-2 font-medium text-gray-800">{row.programme}</td>
                <td className="py-2 text-gray-600">{row.phase}</td>
                <td className="py-2 text-gray-600">{row.vintages}</td>
                <td className="py-2">
                  {row.eligible === null ? <Badge label="PENDING" color="blue" /> : <Badge label={row.eligible ? 'YES' : 'NO'} color={row.eligible ? 'green' : 'red'} />}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Article 6 ITMOs — Key Requirements">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-xs font-semibold text-blue-700 mb-2">Corresponding Adjustment</div>
            <p className="text-xs text-blue-800">Host country must apply a corresponding adjustment (CA) in its NDC accounting per Art 6.2 CMA decision 3/CMA.3. Without CA, credit cannot be used for international claims.</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-xs font-semibold text-blue-700 mb-2">Authorisation Status</div>
            <p className="text-xs text-blue-800">Each ITMO must carry a specific authorisation letter from the host country government designating the buyer entity or programme for the intended use (NDC, other international mitigation).</p>
          </div>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <div className="text-xs font-semibold text-blue-700 mb-2">Art 6.4 Mechanism</div>
            <p className="text-xs text-blue-800">UNFCCC-supervised mechanism replacing CDM. Operative rules adopted at CMA.5 (Dec 2023). First projects expected to register 2025. Includes A6.4ERs for both mitigation contribution and authorised purposes.</p>
          </div>
        </div>
      </Section>

      <Section title="Buyer's Guide — Which Credits for Which Claim?">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              {['Framework / Claim Type','Acceptable Credits','Notes'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {buyerGuide.map((row, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-2 font-semibold text-gray-800">{row.framework}</td>
                <td className="py-2 text-gray-600">{row.acceptable.join('; ')}</td>
                <td className="py-2 text-gray-500">{row.notes}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 5: Reference ────────────────────────────────────────────────────── */
function ReferenceTab() {
  const standards = [
    { name: 'VCS (Verra)', governance: 'Verra Board', additionality: 'Strong', permanence: 'Buffer pool 10-100yr', rating: 'A' },
    { name: 'Gold Standard', governance: 'GS Foundation', additionality: 'Strong + SDG', permanence: 'Registry buffer', rating: 'A' },
    { name: 'CDM', governance: 'UNFCCC CDM EB', additionality: 'Variable', permanence: 'tCER/lCER', rating: 'C' },
    { name: 'Art 6 ITMO', governance: 'UNFCCC/Host Govt', additionality: 'NDC aligned', permanence: 'CA required', rating: 'A' },
    { name: 'CCP (ICVCM)', governance: 'ICVCM', additionality: 'Very strong', permanence: 'Buffer + oversight', rating: 'A' },
  ];

  const prices = [
    { type: 'Tech removal (DAC)', min: 400, max: 1200, note: 'Direct air capture — high cost, high permanence' },
    { type: 'Tech removal (BECCS)', min: 80, max: 300, note: 'Bioenergy with CCS' },
    { type: 'Nature-based removal', min: 15, max: 80, note: 'Reforestation, soil carbon' },
    { type: 'Nature-based avoidance', min: 4, max: 35, note: 'REDD+, conservation' },
    { type: 'Energy / industrial reduction', min: 3, max: 20, note: 'Renewable energy, cookstoves' },
  ];

  return (
    <div>
      <Section title="Standards Comparison">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              {['Standard','Governance','Additionality','Permanence','Tier'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {standards.map((s, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-2 font-semibold text-gray-800">{s.name}</td>
                <td className="py-2 text-gray-600">{s.governance}</td>
                <td className="py-2 text-gray-600">{s.additionality}</td>
                <td className="py-2 text-gray-600">{s.permanence}</td>
                <td className="py-2"><span className="font-bold" style={{ color: TIER_COLORS[s.rating] }}>{s.rating}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="Price Benchmarks by Credit Type (USD/tCO2e)">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              {['Credit Type','Range (Low)','Range (High)','Notes'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {prices.map((p, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-2 font-medium text-gray-800">{p.type}</td>
                <td className="py-2 text-gray-600">${p.min}</td>
                <td className="py-2 text-gray-600">${p.max}</td>
                <td className="py-2 text-gray-500">{p.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      <Section title="ICVCM Core Carbon Principles — Summary">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {ICVCM_CRITERIA.map((c, i) => (
            <div key={i} className="flex gap-2 bg-gray-50 rounded p-2.5">
              <span className="font-mono text-xs text-emerald-600 w-16 flex-shrink-0">{c.id}</span>
              <div>
                <div className="text-xs font-semibold text-gray-700">{c.name}</div>
                <div className="text-xs text-gray-500">{c.description}</div>
              </div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────────── */
function CarbonCreditQualityPage() {
  const [tab, setTab] = useState(0);
  const tabContent = [<ProjectScoringTab />, <PortfolioAnalysisTab />, <CCPEligibilityTab />, <CORSIAArticle6Tab />, <ReferenceTab />];

  return (
    <div className="min-h-screen bg-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Carbon Credit Quality Assessment</h1>
          <p className="text-sm text-gray-500 mt-1">ICVCM CCP · CORSIA · Article 6 ITMOs · VCS · Gold Standard</p>
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

export default CarbonCreditQualityPage;
