import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';

const Section = ({title,children})=>(<div className="mb-6"><h2 className="text-lg font-semibold text-black mb-3 border-b border-emerald-200 pb-1">{title}</h2>{children}</div>);
const KpiCard = ({label,value,sub})=>(<div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm"><div className="text-xs text-gray-500 mb-1">{label}</div><div className="text-2xl font-bold text-black">{value}</div>{sub&&<div className="text-xs text-emerald-600 mt-1">{sub}</div>}</div>);
const Row = ({children})=>(<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">{children}</div>);
const Inp = ({label,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><input className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}/></div>);
const Sel = ({label,children,...p})=>(<div className="flex flex-col gap-1"><label className="text-xs text-gray-600">{label}</label><select className="border border-gray-300 rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-400" {...p}>{children}</select></div>);
const Btn = ({children,...p})=>(<button className="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded text-sm font-medium transition-colors" {...p}>{children}</button>);

const seed = 42;
const rng = (i, s = seed) => Math.abs(Math.sin(i * 9301 + s * 49297) * 233280) % 233280 / 233280;

const TABS = ['EU AI Act Classification', 'NIST AI RMF', 'Algorithmic Bias Detection', 'Explainability Scoring', 'AI Liability Assessment'];

const USE_CASES = ['credit scoring','recruitment','biometric identification','law enforcement','critical infrastructure','medical diagnosis','education assessment','border control','judicial decision','safety component','GPAI model','other'];

const RISK_COLORS = { Prohibited: 'bg-red-100 text-red-800 border-red-300', 'High-Risk': 'bg-orange-100 text-orange-800 border-orange-300', Limited: 'bg-yellow-100 text-yellow-800 border-yellow-300', Minimal: 'bg-green-100 text-green-800 border-green-300' };

function classifyRisk(useCase, autoDecision) {
  if (['biometric identification','law enforcement','border control'].includes(useCase)) return autoDecision ? 'Prohibited' : 'High-Risk';
  if (['credit scoring','recruitment','medical diagnosis','education assessment','judicial decision','safety component'].includes(useCase)) return 'High-Risk';
  if (['GPAI model'].includes(useCase)) return 'Limited';
  return 'Minimal';
}

const ANNEX_III = [
  { id: 'A1', description: 'Biometric identification and categorisation of natural persons', applicable: false },
  { id: 'A2', description: 'Management and operation of critical infrastructure', applicable: false },
  { id: 'A3', description: 'Education and vocational training', applicable: false },
  { id: 'A4', description: 'Employment, workers management and access to self-employment', applicable: false },
  { id: 'A5', description: 'Access to and enjoyment of essential private services and public benefits', applicable: false },
  { id: 'A6', description: 'Law enforcement and administration of justice', applicable: false },
  { id: 'A7', description: 'Migration, asylum and border control management', applicable: false },
  { id: 'A8', description: 'Administration of justice and democratic processes', applicable: false },
];

const PROTECTED_ATTRS = ['age','gender','race/ethnicity','disability','religion','nationality'];

const XAI_METHODS = ['SHAP','LIME','Attention Weights','Gradient-based','Counterfactual','Anchors'];

const HARM_SCENARIOS = ['physical harm','property damage','psychological harm','fundamental rights violation','financial harm','reputational harm'];

// ── Tab 1: EU AI Act Classification ──────────────────────────────────────────
function Tab1() {
  const [systemName, setSystemName] = useState('LoanScoreAI v3');
  const [useCase, setUseCase] = useState('credit scoring');
  const [autoDecision, setAutoDecision] = useState(true);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const annexData = ANNEX_III.map((item, i) => ({
    ...item,
    applicable: rng(i, seed + 1) > 0.6,
  }));

  const handleClassify = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/ai-risk/classify-system', { system_name: systemName, use_case: useCase, automated_decision: autoDecision });
      setResult(res.data);
    } catch {
      setResult({ risk_category: classifyRisk(useCase, autoDecision), gpai_threshold: rng(0, seed + 2) * 100, annex_iii_applicable: Math.floor(rng(1, seed + 3) * 4) });
    }
    setLoading(false);
  }, [systemName, useCase, autoDecision]);

  const riskCat = result?.risk_category || classifyRisk(useCase, autoDecision);

  return (
    <div>
      <Section title="System Details">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <Inp label="AI System Name" value={systemName} onChange={e => setSystemName(e.target.value)} />
          <Sel label="Use Case Category" value={useCase} onChange={e => setUseCase(e.target.value)}>
            {USE_CASES.map(u => <option key={u} value={u}>{u}</option>)}
          </Sel>
          <div className="flex flex-col gap-1">
            <label className="text-xs text-gray-600">Automated Decision-Making</label>
            <div className="flex items-center gap-2 mt-2">
              <input type="checkbox" checked={autoDecision} onChange={e => setAutoDecision(e.target.checked)} className="w-4 h-4 accent-emerald-600" />
              <span className="text-sm">{autoDecision ? 'Yes — Art. 22 GDPR applicable' : 'No — human oversight retained'}</span>
            </div>
          </div>
        </div>
        <Btn onClick={handleClassify} disabled={loading}>{loading ? 'Classifying…' : 'Classify System'}</Btn>
      </Section>

      <Section title="Risk Classification">
        <Row>
          <KpiCard label="Risk Category" value={riskCat} sub={`EU AI Act Art. 6 / Annex III`} />
          <KpiCard label="GPAI Threshold" value={`${(result?.gpai_threshold || rng(0, seed + 2) * 100).toFixed(1)} FLOP`} sub="10²⁵ FLOPs general-purpose threshold" />
          <KpiCard label="Annex III Items" value={`${result?.annex_iii_applicable || 3} / ${ANNEX_III.length}`} sub="High-risk use cases applicable" />
          <KpiCard label="Conformity Assessment" value={autoDecision ? 'Required' : 'Voluntary'} sub="Art. 43 notified body" />
        </Row>
        <div className="flex gap-2 mb-4">
          {Object.entries(RISK_COLORS).map(([cat, cls]) => (
            <span key={cat} className={`px-3 py-1 text-sm font-semibold rounded border ${cls} ${riskCat === cat ? 'ring-2 ring-offset-1 ring-emerald-500' : 'opacity-50'}`}>{cat}</span>
          ))}
        </div>
      </Section>

      <Section title="Annex III Checklist">
        <div className="overflow-auto">
          <table className="min-w-full text-sm border border-gray-200 rounded">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">ID</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">High-Risk Category</th>
                <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">Applicable</th>
              </tr>
            </thead>
            <tbody>
              {annexData.map(item => (
                <tr key={item.id} className="border-t border-gray-100">
                  <td className="px-3 py-2 font-mono text-xs">{item.id}</td>
                  <td className="px-3 py-2">{item.description}</td>
                  <td className="px-3 py-2">
                    <span className={`px-2 py-0.5 rounded text-xs font-medium ${item.applicable ? 'bg-orange-100 text-orange-700' : 'bg-gray-100 text-gray-500'}`}>
                      {item.applicable ? 'Yes' : 'No'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ── Tab 2: NIST AI RMF ────────────────────────────────────────────────────────
function Tab2() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const radarData = [
    { function: 'GOVERN', score: result?.govern || Math.round(rng(0, seed + 10) * 40 + 50) },
    { function: 'MAP', score: result?.map_score || Math.round(rng(1, seed + 10) * 40 + 40) },
    { function: 'MEASURE', score: result?.measure || Math.round(rng(2, seed + 10) * 40 + 45) },
    { function: 'MANAGE', score: result?.manage || Math.round(rng(3, seed + 10) * 40 + 35) },
  ];

  const gapData = [
    'AI Risk Policy','Accountability Roles','Risk Tolerance','Stakeholder Engagement','Risk Identification',
    'Risk Prioritisation','Testing Protocols','Performance Metrics','Monitoring Cadence','Incident Response',
  ].map((cat, i) => ({ category: cat, gap: Math.round(rng(i, seed + 11) * 50 + 10) }))
    .sort((a, b) => b.gap - a.gap).slice(0, 10);

  const overallScore = Math.round(radarData.reduce((s, d) => s + d.score, 0) / radarData.length);

  const handleAssess = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/ai-risk/assess-nist-rmf', {});
      setResult(res.data);
    } catch {
      setResult({ govern: 65, map_score: 55, measure: 60, manage: 48 });
    }
    setLoading(false);
  }, []);

  const actions = [
    'Establish AI Governance Committee with C-suite accountability (GOVERN GV.1)',
    'Conduct structured AI impact assessments for Annex III use cases (MAP MP.2)',
    'Implement automated bias and performance monitoring pipelines (MEASURE MG.2)',
    'Define incident escalation playbook and rollback procedures (MANAGE MR.3)',
    'Document AI system inventories with risk tier classification (GOVERN GV.2)',
  ];

  return (
    <div>
      <Section title="NIST AI RMF Assessment">
        <Btn onClick={handleAssess} disabled={loading}>{loading ? 'Assessing…' : 'Run RMF Assessment'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Overall RMF Score" value={`${overallScore}/100`} sub="NIST AI RMF 1.0 composite" />
        {radarData.map(d => <KpiCard key={d.function} label={`${d.function} Score`} value={d.score} sub="/100" />)}
      </Row>
      <Section title="4-Function Radar">
        <ResponsiveContainer width="100%" height={300}>
          <RadarChart data={radarData}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="function" tick={{ fontSize: 12 }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Radar name="Score" dataKey="score" stroke="#059669" fill="#059669" fillOpacity={0.3} />
            <Tooltip />
          </RadarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Top 10 Subcategory Gaps">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={gapData} layout="vertical" margin={{ left: 140, right: 20 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis type="number" domain={[0, 60]} />
            <YAxis type="category" dataKey="category" tick={{ fontSize: 11 }} />
            <Tooltip />
            <Bar dataKey="gap" fill="#f97316" name="Gap Score" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Recommended Actions">
        <ul className="space-y-2">
          {actions.map((a, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="mt-0.5 w-5 h-5 flex-shrink-0 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-xs font-bold">{i + 1}</span>
              {a}
            </li>
          ))}
        </ul>
      </Section>
    </div>
  );
}

// ── Tab 3: Algorithmic Bias Detection ─────────────────────────────────────────
function Tab3() {
  const [selected, setSelected] = useState(['gender', 'race/ethnicity']);
  const [modelType, setModelType] = useState('gradient boosting');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggle = (attr) => setSelected(s => s.includes(attr) ? s.filter(x => x !== attr) : [...s, attr]);

  const biasData = [
    { metric: 'Demographic Parity', value: result?.demographic_parity || +(rng(0, seed + 20) * 0.3 + 0.1).toFixed(3) },
    { metric: 'Equalised Odds', value: result?.equalised_odds || +(rng(1, seed + 20) * 0.25 + 0.05).toFixed(3) },
    { metric: 'Calibration', value: result?.calibration || +(rng(2, seed + 20) * 0.2 + 0.02).toFixed(3) },
    { metric: 'Counterfactual', value: result?.counterfactual || +(rng(3, seed + 20) * 0.35 + 0.08).toFixed(3) },
    { metric: 'Individual Fairness', value: result?.individual || +(rng(4, seed + 20) * 0.28 + 0.06).toFixed(3) },
    { metric: 'Statistical Parity', value: result?.statistical_parity || +(rng(5, seed + 20) * 0.32 + 0.07).toFixed(3) },
  ];

  const disparateImpact = result?.disparate_impact || +(0.6 + rng(6, seed + 20) * 0.3).toFixed(3);
  const gdprFlag = disparateImpact < 0.8;

  const mitigation = [
    'Apply pre-processing reweighing to equalise representation in training data',
    'Implement in-processing adversarial debiasing during model training',
    'Apply post-processing equalised odds calibration on model outputs',
    'Conduct regular fairness audits per GDPR Art. 22 recital 71',
    'Document bias testing in AI system transparency register (EU AI Act Art. 13)',
  ];

  const handleDetect = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/ai-risk/detect-bias', { protected_attributes: selected, model_type: modelType });
      setResult(res.data);
    } catch {
      setResult(null);
    }
    setLoading(false);
  }, [selected, modelType]);

  return (
    <div>
      <Section title="Configuration">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-gray-600 mb-2 block">Protected Attributes</label>
            <div className="flex flex-wrap gap-2">
              {PROTECTED_ATTRS.map(a => (
                <button key={a} onClick={() => toggle(a)} className={`px-3 py-1 rounded text-sm border ${selected.includes(a) ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-700 border-gray-300'}`}>{a}</button>
              ))}
            </div>
          </div>
          <Sel label="Model Type" value={modelType} onChange={e => setModelType(e.target.value)}>
            {['gradient boosting','logistic regression','neural network','random forest','SVM','ensemble'].map(m => <option key={m}>{m}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleDetect} disabled={loading}>{loading ? 'Detecting…' : 'Detect Bias'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Disparate Impact Ratio" value={disparateImpact.toFixed(3)} sub="Threshold: 0.8 (80% rule)" />
        <KpiCard label="GDPR Art. 22 Flag" value={gdprFlag ? 'FLAGGED' : 'Clear'} sub={gdprFlag ? 'Automated decision review required' : 'Below threshold'} />
        <KpiCard label="Protected Attributes" value={selected.length} sub="Under assessment" />
        <KpiCard label="Model Type" value={modelType} sub="Algorithm class" />
      </Row>
      <Section title="Fairness Metrics">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={biasData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="metric" tick={{ fontSize: 10 }} angle={-20} textAnchor="end" height={50} />
            <YAxis domain={[0, 0.5]} />
            <Tooltip />
            <Bar dataKey="value" fill="#6366f1" name="Bias Score (lower = fairer)" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Mitigation Steps">
        <ol className="space-y-2">
          {mitigation.map((m, i) => (
            <li key={i} className="flex items-start gap-2 text-sm">
              <span className="mt-0.5 w-5 h-5 flex-shrink-0 rounded-full bg-orange-100 text-orange-700 flex items-center justify-center text-xs font-bold">{i + 1}</span>
              {m}
            </li>
          ))}
        </ol>
      </Section>
    </div>
  );
}

// ── Tab 4: Explainability Scoring ─────────────────────────────────────────────
function Tab4() {
  const [selectedMethods, setSelectedMethods] = useState(['SHAP', 'LIME']);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggleMethod = (m) => setSelectedMethods(s => s.includes(m) ? s.filter(x => x !== m) : [...s, m]);

  const maturityLevel = result?.maturity || 3;
  const xaiComplianceData = [
    { requirement: 'Transparency', score: Math.round(rng(0, seed + 30) * 30 + 60) },
    { requirement: 'Right to Explanation', score: Math.round(rng(1, seed + 30) * 30 + 55) },
    { requirement: 'Human Oversight', score: Math.round(rng(2, seed + 30) * 25 + 65) },
    { requirement: 'Audit Trail', score: Math.round(rng(3, seed + 30) * 30 + 50) },
    { requirement: 'Documentation', score: Math.round(rng(4, seed + 30) * 35 + 45) },
    { requirement: 'Model Cards', score: Math.round(rng(5, seed + 30) * 30 + 40) },
  ];

  const handleScore = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/ai-risk/score-explainability', { methods: selectedMethods });
      setResult(res.data);
    } catch {
      setResult({ maturity: 3 });
    }
    setLoading(false);
  }, [selectedMethods]);

  const maturityLabels = ['', 'Ad hoc', 'Documented', 'Standardised', 'Managed', 'Optimised'];
  const maturityColors = ['', 'bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-emerald-500'];

  return (
    <div>
      <Section title="Explanation Methods">
        <div className="flex flex-wrap gap-2 mb-4">
          {XAI_METHODS.map(m => (
            <button key={m} onClick={() => toggleMethod(m)} className={`px-3 py-1 rounded text-sm border ${selectedMethods.includes(m) ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-white text-gray-700 border-gray-300'}`}>{m}</button>
          ))}
        </div>
        <Btn onClick={handleScore} disabled={loading}>{loading ? 'Scoring…' : 'Score Explainability'}</Btn>
      </Section>
      <Row>
        <KpiCard label="XAI Maturity Level" value={`${maturityLevel} / 5`} sub={maturityLabels[maturityLevel]} />
        <KpiCard label="Active Methods" value={selectedMethods.length} sub="Explanation techniques deployed" />
        <KpiCard label="Right-to-Explanation" value={maturityLevel >= 3 ? 'Ready' : 'Not Ready'} sub="EU AI Act Annex XII" />
        <KpiCard label="GDPR Art. 22 Compliance" value={maturityLevel >= 4 ? 'Compliant' : 'Partial'} sub="Recital 71 explainability" />
      </Row>
      <Section title="XAI Maturity Ladder">
        <div className="flex items-end gap-2 h-20 mb-2">
          {[1,2,3,4,5].map(lvl => (
            <div key={lvl} className="flex-1 flex flex-col items-center gap-1">
              <div className={`w-full rounded-t ${maturityColors[lvl]} ${lvl <= maturityLevel ? 'opacity-100' : 'opacity-20'}`} style={{ height: `${lvl * 16}px` }} />
              <span className="text-xs text-gray-500">{lvl}</span>
            </div>
          ))}
        </div>
        <div className="text-xs text-gray-500 text-center">Current level: <strong>{maturityLevel}</strong> — {maturityLabels[maturityLevel]}</div>
      </Section>
      <Section title="EU AI Act Annex XII Compliance">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={xaiComplianceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="requirement" tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 100]} />
            <Tooltip />
            <Bar dataKey="score" fill="#059669" name="Compliance Score" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

// ── Tab 5: AI Liability Assessment ────────────────────────────────────────────
function Tab5() {
  const [harmScenario, setHarmScenario] = useState('physical harm');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const damageData = [
    { category: 'Physical harm', exposure: Math.round(rng(0, seed + 40) * 800 + 200) },
    { category: 'Property damage', exposure: Math.round(rng(1, seed + 40) * 600 + 100) },
    { category: 'Psychological harm', exposure: Math.round(rng(2, seed + 40) * 400 + 80) },
    { category: 'Fundamental rights', exposure: Math.round(rng(3, seed + 40) * 700 + 150) },
  ];

  const liabilityTimeline = [
    { year: 2024, exposure: 1.2 }, { year: 2025, exposure: 2.1 },
    { year: 2026, exposure: 3.8 }, { year: 2027, exposure: 5.5 },
  ];

  const enforcementTable = [
    { date: 'May 2024', event: 'EU AI Act enters into force', article: 'Art. 1-4' },
    { date: 'Aug 2025', event: 'Prohibited AI systems — full prohibition', article: 'Art. 5' },
    { date: 'Aug 2026', event: 'High-risk AI obligations apply', article: 'Art. 6-51' },
    { date: 'Aug 2027', event: 'All remaining provisions in force', article: 'Art. 52-99' },
  ];

  const handleCalc = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.post('/api/v1/ai-risk/calculate-liability', { harm_scenario: harmScenario });
      setResult(res.data);
    } catch {
      setResult(null);
    }
    setLoading(false);
  }, [harmScenario]);

  const totalExposure = damageData.reduce((s, d) => s + d.exposure, 0);
  const doGap = Math.round(rng(7, seed + 40) * 500 + 200);

  return (
    <div>
      <Section title="Configuration">
        <div className="flex gap-4 mb-4">
          <Sel label="Harm Scenario" value={harmScenario} onChange={e => setHarmScenario(e.target.value)}>
            {HARM_SCENARIOS.map(s => <option key={s} value={s}>{s}</option>)}
          </Sel>
        </div>
        <Btn onClick={handleCalc} disabled={loading}>{loading ? 'Calculating…' : 'Calculate Liability'}</Btn>
      </Section>
      <Row>
        <KpiCard label="Total Exposure" value={`€${totalExposure.toLocaleString()}k`} sub="Aggregate damage categories" />
        <KpiCard label="D&O Insurance Gap" value={`€${doGap}k`} sub="vs. current policy limit" />
        <KpiCard label="Liability Directive" value="2024/2853" sub="EU AI Liability Directive" />
        <KpiCard label="Max Penalty (Art. 99)" value="€35M / 7% revenue" sub="Prohibited AI violations" />
      </Row>
      <Section title="Damage Category Exposure (€k)">
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={damageData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="category" tick={{ fontSize: 11 }} />
            <YAxis />
            <Tooltip formatter={v => `€${v}k`} />
            <Bar dataKey="exposure" fill="#ef4444" name="Exposure (€k)" />
          </BarChart>
        </ResponsiveContainer>
      </Section>
      <Section title="EU AI Liability Directive Exposure Trend (€M)">
        <ResponsiveContainer width="100%" height={200}>
          <LineChart data={liabilityTimeline}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" />
            <YAxis />
            <Tooltip formatter={v => `€${v}M`} />
            <Line type="monotone" dataKey="exposure" stroke="#7c3aed" strokeWidth={2} name="Exposure" dot />
          </LineChart>
        </ResponsiveContainer>
      </Section>
      <Section title="Enforcement Timeline">
        <table className="min-w-full text-sm border border-gray-200 rounded">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">Date</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">Event</th>
              <th className="px-3 py-2 text-left text-xs font-medium text-gray-600">Article</th>
            </tr>
          </thead>
          <tbody>
            {enforcementTable.map((row, i) => (
              <tr key={i} className="border-t border-gray-100">
                <td className="px-3 py-2 font-mono text-xs text-gray-600">{row.date}</td>
                <td className="px-3 py-2">{row.event}</td>
                <td className="px-3 py-2 font-mono text-xs text-emerald-700">{row.article}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AIRiskPage() {
  const [activeTab, setActiveTab] = useState(0);
  const tabComponents = [Tab1, Tab2, Tab3, Tab4, Tab5];
  const ActiveComp = tabComponents[activeTab];

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">AI & ML Risk Finance</h1>
          <p className="text-sm text-gray-500 mt-1">EU AI Act 2024/1689 · NIST AI RMF 1.0 · Algorithmic Bias Detection · GDPR Art 22 · EU AI Liability Directive · E76</p>
        </div>
        <div className="flex flex-wrap gap-2 mb-6 border-b border-gray-200 pb-2">
          {TABS.map((tab, i) => (
            <button key={i} onClick={() => setActiveTab(i)} className={`px-4 py-2 rounded-t text-sm font-medium transition-colors ${activeTab === i ? 'bg-emerald-600 text-white' : 'bg-white text-gray-600 hover:bg-emerald-50 border border-gray-200'}`}>{tab}</button>
          ))}
        </div>
        <ActiveComp />
      </div>
    </div>
  );
}
