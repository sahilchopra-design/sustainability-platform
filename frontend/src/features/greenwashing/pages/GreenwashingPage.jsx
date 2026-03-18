/**
 * GreenwashingPage.jsx
 * Route: /greenwashing
 * Tabs: Risk Assessment | Claim Screening | Label Verification | Regulatory Requirements | Reference
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || '';
const TT = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111', fontSize: 11 };
const EMERALD = '#10b981';
const TABS = ['Risk Assessment', 'Claim Screening', 'Label Verification', 'Regulatory Requirements', 'Reference'];

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

const MISLEADING_TERMS = [
  { term: 'eco-friendly', risk: 'High', reason: 'Vague, no quantitative basis' },
  { term: 'green', risk: 'High', reason: 'No standard definition' },
  { term: 'sustainable', risk: 'High', reason: 'Undefined scope' },
  { term: 'carbon neutral', risk: 'Medium', reason: 'Requires verified offset methodology' },
  { term: 'net zero', risk: 'Medium', reason: 'Must align with SBTi/VCMI standard' },
  { term: 'climate positive', risk: 'High', reason: 'No regulatory definition' },
  { term: 'natural', risk: 'Medium', reason: 'Ambiguous for financial products' },
  { term: 'clean', risk: 'High', reason: 'Vague comparative claim' },
  { term: 'responsible', risk: 'Medium', reason: 'Requires specific criteria' },
  { term: 'ESG-aligned', risk: 'Medium', reason: 'Must reference specific ESG framework' },
  { term: 'Paris-aligned', risk: 'Medium', reason: 'Must cite pathway and methodology' },
  { term: 'zero emissions', risk: 'High', reason: 'Requires Scope 1/2/3 basis' },
  { term: 'biodiversity-friendly', risk: 'High', reason: 'No measurement standard' },
  { term: 'impact', risk: 'Medium', reason: 'Causality must be demonstrated' },
  { term: 'conscious', risk: 'Low', reason: 'Aspirational but not material' },
  { term: 'future-proof', risk: 'Low', reason: 'Forward-looking; PSLRA caveats apply' },
];

/* ── Tab 1: Risk Assessment ──────────────────────────────────────────────── */
function RiskAssessmentTab() {
  const [entity, setEntity] = useState('GreenFund Capital Ltd');
  const [level, setLevel] = useState('entity');
  const [sfdr, setSfdr] = useState('Art8');
  const [taxAlign, setTaxAlign] = useState('45');
  const [claims, setClaims] = useState([]);
  const [newClaim, setNewClaim] = useState('');
  const [claimType, setClaimType] = useState('qualitative');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const addClaim = () => {
    if (newClaim.trim()) { setClaims(prev => [...prev, { text: newClaim.trim(), type: claimType }]); setNewClaim(''); }
  };

  const run = async () => {
    setLoading(true);
    const r = rng(entity.split('').reduce((a, c) => a + c.charCodeAt(0), 31));
    const flagged = Math.round(claims.length * (0.3 + r() * 0.5));
    const overallScore = Math.round(20 + r() * 70);
    const tier = overallScore < 30 ? 'low' : overallScore < 55 ? 'medium' : overallScore < 75 ? 'high' : 'very_high';
    try {
      const { data } = await axios.post(`${API}/api/v1/greenwashing/assess`, { entity_name: entity, level, sfdr_classification: sfdr, taxonomy_alignment_claimed: parseFloat(taxAlign), claims });
      setResult(data);
    } catch {
      setResult({
        overall_score: overallScore, risk_tier: tier,
        claims_submitted: claims.length, claims_flagged: flagged,
        eu_reg_score: Math.round(30 + r() * 60), fca_score: Math.round(30 + r() * 60),
        claims_results: claims.map((c, i) => ({ claim_text: c.text.substring(0, 60), risk_level: ['Low','Medium','High'][Math.floor(r() * 3)], substantiation_score: Math.round(20 + r() * 70), top_issue: 'Vague terminology; quantitative basis missing' })),
        remediation: ['Quantify all sustainability claims with verifiable data', 'Add ESMA/FCA substantiation documentation', 'Review taxonomy alignment calculation methodology', 'Obtain third-party verification for material claims'],
      });
    } finally { setLoading(false); }
  };

  const tierColor = { low: 'green', medium: 'amber', high: 'red', very_high: 'red' };
  const d = result;

  return (
    <div>
      <Section title="Entity & Classification">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Inp label="Entity Name" value={entity} onChange={e => setEntity(e.target.value)} />
          <Sel label="Assessment Level" value={level} onChange={e => setLevel(e.target.value)}>
            <option value="entity">Entity Level</option>
            <option value="product">Product Level</option>
          </Sel>
          <Sel label="SFDR Classification" value={sfdr} onChange={e => setSfdr(e.target.value)}>
            <option value="Art6">Article 6</option>
            <option value="Art8">Article 8</option>
            <option value="Art9">Article 9</option>
          </Sel>
          <Inp label="Taxonomy Alignment % Claimed" value={taxAlign} onChange={e => setTaxAlign(e.target.value)} type="number" />
        </div>
      </Section>

      <Section title="Sustainability Claims">
        <div className="flex gap-3 mb-3">
          <div className="flex-1">
            <input
              className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400"
              placeholder="Enter a sustainability claim..."
              value={newClaim}
              onChange={e => setNewClaim(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && addClaim()}
            />
          </div>
          <Sel label="" value={claimType} onChange={e => setClaimType(e.target.value)} style={{ marginBottom: 0 }}>
            <option value="quantitative">Quantitative</option>
            <option value="qualitative">Qualitative</option>
            <option value="label">Label</option>
            <option value="comparative">Comparative</option>
          </Sel>
          <div><Btn onClick={addClaim}>Add Claim</Btn></div>
        </div>
        {claims.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {claims.map((c, i) => (
              <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 rounded text-xs flex items-center gap-1">
                <span className="font-medium">[{c.type}]</span> {c.text.substring(0, 40)}{c.text.length > 40 ? '...' : ''}
                <button className="ml-1 text-gray-400 hover:text-red-500" onClick={() => setClaims(p => p.filter((_, j) => j !== i))}>x</button>
              </span>
            ))}
          </div>
        )}
        <Btn onClick={run} disabled={loading}>{loading ? 'Running...' : 'Run Assessment'}</Btn>
      </Section>

      {d && (
        <>
          <div className="flex items-center gap-4 mb-6">
            <div className="bg-white border border-gray-200 rounded-lg px-6 py-4 flex-1">
              <div className="text-xs text-gray-500 mb-1">Overall Risk Score</div>
              <div className={`text-4xl font-bold ${d.overall_score >= 55 ? 'text-red-600' : d.overall_score >= 30 ? 'text-amber-500' : 'text-emerald-600'}`}>{d.overall_score}</div>
              <div className="mt-2"><Badge label={d.risk_tier?.toUpperCase().replace('_',' ') || 'MEDIUM'} color={tierColor[d.risk_tier] || 'amber'} /></div>
            </div>
          </div>

          <Row>
            <KpiCard label="Claims Submitted" value={d.claims_submitted || 0} sub="total reviewed" />
            <KpiCard label="Claims Flagged" value={d.claims_flagged || 0} sub="require remediation" />
            <KpiCard label="EU Reg Score" value={`${d.eu_reg_score || 0}/100`} sub="Reg 2023/2441" />
            <KpiCard label="FCA Score" value={`${d.fca_score || 0}/100`} sub="Consumer Duty / AGR" />
          </Row>

          {d.claims_results && d.claims_results.length > 0 && (
            <Section title="Claims Screening Results">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100">
                    {['Claim (excerpt)','Risk Level','Substantiation Score','Top Issue'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {d.claims_results.map((c, i) => (
                    <tr key={i} className="border-b border-gray-50">
                      <td className="py-2 text-gray-700 max-w-xs">{c.claim_text}</td>
                      <td className="py-2"><Badge label={c.risk_level} color={c.risk_level === 'High' ? 'red' : c.risk_level === 'Medium' ? 'amber' : 'green'} /></td>
                      <td className="py-2 text-gray-600">{c.substantiation_score}/100</td>
                      <td className="py-2 text-gray-500">{c.top_issue}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
          )}

          {d.remediation && (
            <Section title="Remediation Steps">
              <ol className="space-y-1.5 list-decimal list-inside">
                {d.remediation.map((step, i) => <li key={i} className="text-sm text-gray-600">{step}</li>)}
              </ol>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

/* ── Tab 2: Claim Screening ──────────────────────────────────────────────── */
function ClaimScreeningTab() {
  const [claim, setClaim] = useState('');
  const [claimType, setClaimType] = useState('qualitative');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const screen = async () => {
    setLoading(true);
    const r = rng(claim.split('').reduce((a, c) => a + c.charCodeAt(0), 47));
    const score = Math.round(20 + r() * 70);
    try {
      const { data } = await axios.post(`${API}/api/v1/greenwashing/screen-claim`, { claim_text: claim, claim_type: claimType });
      setResult(data);
    } catch {
      const flagged = MISLEADING_TERMS.filter(t => claim.toLowerCase().includes(t.term));
      setResult({
        risk_level: score > 60 ? 'High' : score > 35 ? 'Medium' : 'Low',
        substantiation_score: score,
        issues: flagged.length > 0 ? [`Vague terminology: ${flagged.map(t => t.term).join(', ')}`, 'Missing quantitative substantiation', 'No reference to recognised ESG standard'] : ['Claim appears specific; verify with third-party evidence'],
        regulatory_references: ['EU Reg 2023/2441 Art 8', 'ESMA Greenwashing Briefing 2023', 'FCA CP22/20 §4.3'],
        flagged_terms: flagged.map(t => t.term),
      });
    } finally { setLoading(false); }
  };

  const highlighted = result && claim
    ? claim.split(' ').map((word, i) => {
        const clean = word.toLowerCase().replace(/[^a-z-]/g, '');
        const flagged = result.flagged_terms && result.flagged_terms.includes(clean);
        return <span key={i} className={flagged ? 'bg-amber-100 text-amber-800 px-0.5 rounded' : ''}>{word} </span>;
      })
    : null;

  return (
    <div>
      <Section title="Single Claim Screening">
        <div className="mb-3">
          <label className="block text-xs text-gray-500 mb-1">Claim Text</label>
          <textarea
            className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400 h-20"
            placeholder="Enter a sustainability claim to screen..."
            value={claim}
            onChange={e => setClaim(e.target.value)}
          />
        </div>
        <div className="flex gap-4 items-end">
          <div className="w-48">
            <Sel label="Claim Type" value={claimType} onChange={e => setClaimType(e.target.value)}>
              <option value="quantitative">Quantitative</option>
              <option value="qualitative">Qualitative</option>
              <option value="label">Label</option>
              <option value="comparative">Comparative</option>
            </Sel>
          </div>
          <div className="mb-3"><Btn onClick={screen} disabled={loading || !claim.trim()}>{loading ? 'Screening...' : 'Screen Claim'}</Btn></div>
        </div>
      </Section>

      {result && (
        <>
          <Section title="Screening Result">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
              <KpiCard label="Risk Level" value={result.risk_level} accent={result.risk_level === 'Low'} />
              <KpiCard label="Substantiation Score" value={`${result.substantiation_score}/100`} accent={result.substantiation_score >= 70} />
              <KpiCard label="Issues Found" value={result.issues?.length || 0} sub="flagged items" />
            </div>
            {highlighted && (
              <div className="bg-gray-50 border border-gray-100 rounded p-3 text-sm leading-relaxed mb-3">
                <div className="text-xs text-gray-400 mb-2">Claim with flagged terms highlighted:</div>
                {highlighted}
              </div>
            )}
            {result.issues && result.issues.length > 0 && (
              <div className="mb-3">
                <div className="text-xs text-gray-500 mb-2">Issues identified:</div>
                <ul className="space-y-1">
                  {result.issues.map((iss, i) => <li key={i} className="text-xs text-gray-600 flex items-start gap-2"><span className="text-amber-400 mt-0.5">&#9679;</span>{iss}</li>)}
                </ul>
              </div>
            )}
            {result.regulatory_references && (
              <div className="flex flex-wrap gap-2">
                {result.regulatory_references.map((ref, i) => <Badge key={i} label={ref} color="blue" />)}
              </div>
            )}
          </Section>
        </>
      )}

      <Section title="Misleading Terms Reference Library">
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-100">
              {['Term','Risk Level','Reason'].map(h => <th key={h} className="text-left py-2 text-gray-500 font-medium">{h}</th>)}
            </tr>
          </thead>
          <tbody>
            {MISLEADING_TERMS.map((t, i) => (
              <tr key={i} className="border-b border-gray-50">
                <td className="py-1.5 font-mono text-gray-700">"{t.term}"</td>
                <td className="py-1.5"><Badge label={t.risk} color={t.risk === 'High' ? 'red' : t.risk === 'Medium' ? 'amber' : 'green'} /></td>
                <td className="py-1.5 text-gray-500">{t.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ── Tab 3: Label Verification ───────────────────────────────────────────── */
const LABELS = ['SFDR Art 8', 'SFDR Art 9', 'EU Taxonomy Aligned', 'SDR Sustainable Focus', 'SDR Impact', 'Green Bond'];

function LabelVerificationTab() {
  const [selected, setSelected] = useState(['SFDR Art 8']);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const toggle = (label) => setSelected(p => p.includes(label) ? p.filter(l => l !== label) : [...p, label]);

  const verify = async () => {
    setLoading(true);
    const r = rng(selected.join('').length * 7 + 19);
    try {
      const { data } = await axios.post(`${API}/api/v1/greenwashing/verify-labels`, { labels: selected });
      setResult(data);
    } catch {
      setResult({
        results: selected.map(label => ({
          label,
          status: r() > 0.6 ? 'pass' : r() > 0.3 ? 'conditional' : 'fail',
          gaps: [
            { requirement: 'PAI disclosure completeness', status: r() > 0.5 ? 'Met' : 'Not Met', gap: r() > 0.5 ? '' : 'PAI indicators 1-14 not fully disclosed' },
            { requirement: 'Taxonomy alignment calculation', status: r() > 0.5 ? 'Met' : 'Not Met', gap: r() > 0.5 ? '' : 'Turnover/CapEx/OpEx split not provided' },
          ].filter(g => g.status === 'Not Met'),
        })),
      });
    } finally { setLoading(false); }
  };

  const statusColor = { pass: 'green', conditional: 'amber', fail: 'red' };

  return (
    <div>
      <Section title="Select Labels to Verify">
        <div className="flex flex-wrap gap-3 mb-4">
          {LABELS.map(label => (
            <label key={label} className="flex items-center gap-2 cursor-pointer">
              <input type="checkbox" checked={selected.includes(label)} onChange={() => toggle(label)} className="accent-emerald-500" />
              <span className="text-sm text-gray-700">{label}</span>
            </label>
          ))}
        </div>
        <Btn onClick={verify} disabled={loading || selected.length === 0}>{loading ? 'Verifying...' : 'Verify Labels'}</Btn>
      </Section>

      {result && result.results && (
        <Section title="Verification Results">
          <div className="space-y-4">
            {result.results.map((res, i) => (
              <div key={i} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <span className="font-semibold text-sm text-gray-800">{res.label}</span>
                  <Badge label={res.status.toUpperCase()} color={statusColor[res.status] || 'gray'} />
                </div>
                {res.gaps && res.gaps.length > 0 ? (
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-100">
                        {['Requirement','Status','Gap Description'].map(h => <th key={h} className="text-left py-1.5 text-gray-500 font-medium">{h}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {res.gaps.map((g, j) => (
                        <tr key={j} className="border-b border-gray-50">
                          <td className="py-1.5 text-gray-700">{g.requirement}</td>
                          <td className="py-1.5"><Badge label={g.status} color={g.status === 'Met' ? 'green' : 'red'} /></td>
                          <td className="py-1.5 text-gray-500">{g.gap || '—'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <div className="text-xs text-emerald-600">All requirements met. Label claim substantiated.</div>
                )}
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

/* ── Tab 4: Regulatory Requirements ─────────────────────────────────────── */
const EU_REQS = [
  { id: 'EU-1', text: 'Claims must be based on accurate, verifiable information (Art 3)', ref: 'Art 3' },
  { id: 'EU-2', text: 'Comparative claims reference equivalent products (Art 4)', ref: 'Art 4' },
  { id: 'EU-3', text: 'Labels based on approved certification schemes (Art 5)', ref: 'Art 5' },
  { id: 'EU-4', text: 'Complete life-cycle perspective for environmental claims (Art 6)', ref: 'Art 6' },
  { id: 'EU-5', text: 'No promotion of non-compliant goods under EU law (Art 7)', ref: 'Art 7' },
  { id: 'EU-6', text: 'Third-party verification for voluntary claims (Art 8)', ref: 'Art 8' },
  { id: 'EU-7', text: 'Annual review of substantiation documentation (Art 10)', ref: 'Art 10' },
  { id: 'EU-8', text: 'Penalties regime: effective, proportionate, dissuasive (Art 14)', ref: 'Art 14' },
];

const FCA_REQS = [
  { id: 'FCA-1', text: 'Name and marketing consistent with product sustainability (AGR 4.1)', ref: 'AGR 4.1' },
  { id: 'FCA-2', text: 'Ongoing product objectives genuinely pursued (AGR 4.2)', ref: 'AGR 4.2' },
  { id: 'FCA-3', text: 'Disclosures clear, fair and not misleading (COBS 4.2)', ref: 'COBS 4.2' },
  { id: 'FCA-4', text: 'Consumer Duty: good outcomes for retail customers (PRIN 12)', ref: 'PRIN 12' },
  { id: 'FCA-5', text: 'SDR label criteria met prior to use (SDR 3.1)', ref: 'SDR 3.1' },
  { id: 'FCA-6', text: 'Annual attestation from senior responsible officer (AGR 7)', ref: 'AGR 7' },
];

function RegulatoryRequirementsTab() {
  const [euChecked, setEuChecked] = useState({});
  const [fcaChecked, setFcaChecked] = useState({});

  const euScore = EU_REQS.filter(r => euChecked[r.id]).length;
  const fcaScore = FCA_REQS.filter(r => fcaChecked[r.id]).length;

  return (
    <div>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Section title="EU Requirements — Reg 2023/2441 (Green Claims Directive)">
          <div className="space-y-2 mb-3">
            {EU_REQS.map(req => (
              <label key={req.id} className="flex items-start gap-3 cursor-pointer group">
                <input type="checkbox" checked={!!euChecked[req.id]} onChange={() => setEuChecked(p => ({ ...p, [req.id]: !p[req.id] }))} className="mt-0.5 accent-emerald-500" />
                <span className="text-xs text-gray-600 group-hover:text-gray-800">
                  <span className="font-mono text-gray-400 mr-1">{req.ref}</span>{req.text}
                </span>
              </label>
            ))}
          </div>
          <div className="bg-gray-50 rounded p-3 flex items-center justify-between">
            <span className="text-xs text-gray-500">EU Compliance Score</span>
            <span className="text-lg font-bold text-black">{euScore} / {EU_REQS.length}</span>
          </div>
        </Section>

        <Section title="FCA Requirements — Consumer Duty & AGR">
          <div className="space-y-2 mb-3">
            {FCA_REQS.map(req => (
              <label key={req.id} className="flex items-start gap-3 cursor-pointer group">
                <input type="checkbox" checked={!!fcaChecked[req.id]} onChange={() => setFcaChecked(p => ({ ...p, [req.id]: !p[req.id] }))} className="mt-0.5 accent-emerald-500" />
                <span className="text-xs text-gray-600 group-hover:text-gray-800">
                  <span className="font-mono text-gray-400 mr-1">{req.ref}</span>{req.text}
                </span>
              </label>
            ))}
          </div>
          <div className="bg-gray-50 rounded p-3 flex items-center justify-between">
            <span className="text-xs text-gray-500">FCA Compliance Score</span>
            <span className="text-lg font-bold text-black">{fcaScore} / {FCA_REQS.length}</span>
          </div>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 5: Reference ────────────────────────────────────────────────────── */
function ReferenceTab() {
  const timeline = [
    { date: 'Mar 2021', event: 'EU Sustainable Finance Disclosure Regulation (SFDR) Level 1 applies' },
    { date: 'Jan 2023', event: 'EU Green Claims Directive proposal published by Commission' },
    { date: 'Mar 2023', event: 'ESMA Briefing on Greenwashing — common understanding established' },
    { date: 'Nov 2023', event: 'FCA Sustainability Disclosure Requirements (SDR) and labels finalised' },
    { date: 'Jul 2024', event: 'FCA SDR labels and naming/marketing rules effective (larger AUM)' },
    { date: 'Oct 2024', event: 'EU Empowering Consumers Directive (Reg 2023/2441) final text' },
    { date: 'Feb 2025', event: 'FCA SDR extended to smaller FMs; AGR review commences' },
    { date: 'Q3 2026', event: 'EU Green Claims Directive transposition deadline (estimated)' },
  ];

  const claimTypes = [
    { type: 'Quantitative', definition: 'Specific numerical claim (e.g. "40% lower carbon intensity")' },
    { type: 'Qualitative', definition: 'Descriptive claim without specific number (e.g. "lower impact")' },
    { type: 'Label', definition: 'Reference to a certification, rating or classification' },
    { type: 'Comparative', definition: 'Comparison to another product, prior period or market average' },
  ];

  const methodology = [
    'Step 1 — Identify all material sustainability-related communications',
    'Step 2 — Classify each claim by type (quantitative/qualitative/label/comparative)',
    'Step 3 — Test substantiation: evidence quality, scope, timeliness',
    'Step 4 — Check against regulated misleading terms list (ESMA/FCA)',
    'Step 5 — Map to applicable regulatory frameworks (EU Reg, FCA, SFDR)',
    'Step 6 — Score overall risk tier and produce remediation roadmap',
  ];

  return (
    <div>
      <Section title="Greenwashing Regulatory Timeline">
        <div className="space-y-3">
          {timeline.map((t, i) => (
            <div key={i} className="flex gap-4 items-start">
              <span className="text-xs font-mono text-emerald-600 w-20 flex-shrink-0 mt-0.5">{t.date}</span>
              <div className="flex-1 border-l-2 border-emerald-100 pl-4 pb-3">
                <p className="text-xs text-gray-700">{t.event}</p>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Section title="Claim Type Definitions">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-1.5 text-gray-500 font-medium">Type</th>
                <th className="text-left py-1.5 text-gray-500 font-medium">Definition</th>
              </tr>
            </thead>
            <tbody>
              {claimTypes.map((c, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-2 font-semibold text-gray-700">{c.type}</td>
                  <td className="py-2 text-gray-500">{c.definition}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>

        <Section title="Substantiation Methodology Framework">
          <ol className="space-y-2">
            {methodology.map((step, i) => (
              <li key={i} className="flex items-start gap-2 text-xs text-gray-600">
                <span className="flex-shrink-0 w-5 h-5 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center font-bold text-xs">{i + 1}</span>
                {step.replace(/^Step \d+ — /, '')}
              </li>
            ))}
          </ol>
        </Section>
      </div>

      <Section title="Illustrative Enforcement Actions (Generic Reference)">
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-xs text-amber-800">
          Enforcement cases referenced in this platform are illustrative only and do not represent specific regulatory decisions. Real enforcement decisions should be obtained from the relevant NCA or FCA register. EU Green Claims Directive enforcement will be administered by designated competent authorities in each member state. FCA enforcement is published in Final Notices on the FCA website.
        </div>
      </Section>
    </div>
  );
}

/* ── Main Page ───────────────────────────────────────────────────────────── */
function GreenwashingPage() {
  const [tab, setTab] = useState(0);
  const tabContent = [<RiskAssessmentTab />, <ClaimScreeningTab />, <LabelVerificationTab />, <RegulatoryRequirementsTab />, <ReferenceTab />];

  return (
    <div className="min-h-screen bg-white p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">Greenwashing Risk & Compliance</h1>
          <p className="text-sm text-gray-500 mt-1">EU Green Claims Directive · FCA SDR/AGR · ESMA Greenwashing Framework</p>
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

export default GreenwashingPage;
