/**
 * SFDRProductReportingPage.jsx
 * Route: /sfdr-product-reporting
 * E22 — SFDR Product Periodic Reporting (RTS 2022/1288, Annex III + V)
 * Tabs:
 *   1. Periodic Report Generator   — completeness score, section gaps
 *   2. Product PAI                 — 14 PAI indicators table + BarChart
 *   3. Sustainable Investment Verification — 4-criteria checklist
 *   4. Taxonomy Disclosure         — 6-objective stacked BarChart
 *   5. Reference                   — Annex III/V comparison, PAI list, website requirements
 */
import React, { useState } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const EM = '#10b981';

// ── Primitives ────────────────────────────────────────────────────────────
function Section({ title, subtitle, children, action }) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 mb-4">
      {(title || action) && (
        <div className="flex items-start justify-between mb-4">
          <div>
            {title && <h3 className="text-sm font-semibold text-gray-900">{title}</h3>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {action}
        </div>
      )}
      {children}
    </div>
  );
}

function KpiCard({ label, value, sub, accent, badge }) {
  const accentCls = accent === 'green' ? 'text-emerald-600' : accent === 'red' ? 'text-red-600' : accent === 'amber' ? 'text-amber-600' : 'text-gray-900';
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-4">
      <div className="flex items-start justify-between mb-1">
        <span className="text-[10px] font-semibold uppercase tracking-wider text-gray-400">{label}</span>
        {badge && <span className="text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">{badge}</span>}
      </div>
      <div className={`text-2xl font-bold font-mono ${accentCls}`}>{value}</div>
      {sub && <div className="text-[11px] text-gray-400 mt-1">{sub}</div>}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center gap-2 mb-3">
      <label className="text-xs font-medium text-gray-600 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'text', min, max, step, placeholder }) {
  return (
    <input type={type} value={value} min={min} max={max} step={step} placeholder={placeholder}
      onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, children, loading }) {
  return (
    <button onClick={onClick} disabled={loading}
      className={`px-4 py-2 rounded-lg text-xs font-semibold bg-black text-white hover:bg-gray-800 transition-colors ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}>
      {loading ? 'Running…' : children}
    </button>
  );
}

// ── Static seed data ───────────────────────────────────────────────────────
const PAI_INDICATORS = [
  { id: 'PAI-1',  name: 'GHG emissions',                    unit: 'tCO₂e/MEUR', fund: 148, bm: 220, mandatory: true },
  { id: 'PAI-2',  name: 'Carbon footprint',                 unit: 'tCO₂e/MEUR', fund: 82, bm: 135, mandatory: true },
  { id: 'PAI-3',  name: 'GHG intensity investee companies', unit: 'tCO₂e/MEUR', fund: 210, bm: 310, mandatory: true },
  { id: 'PAI-4',  name: 'Fossil fuel sector exposure',      unit: '%',           fund: 6.2, bm: 11.4, mandatory: true },
  { id: 'PAI-5',  name: 'Non-renewable energy consumption', unit: '%',           fund: 68, bm: 78, mandatory: true },
  { id: 'PAI-6',  name: 'Energy consumption intensity',     unit: 'MWh/MEUR',   fund: 42, bm: 65, mandatory: true },
  { id: 'PAI-7',  name: 'Activities affecting biodiversity', unit: '%',          fund: 2.1, bm: 4.8, mandatory: true },
  { id: 'PAI-8',  name: 'Emissions to water',               unit: 'tonnes/MEUR', fund: 0.8, bm: 1.4, mandatory: true },
  { id: 'PAI-9',  name: 'Hazardous waste ratio',            unit: '%',           fund: 1.2, bm: 2.3, mandatory: true },
  { id: 'PAI-10', name: 'UNGC/OECD violations',             unit: '%',           fund: 3.1, bm: 7.2, mandatory: true },
  { id: 'PAI-11', name: 'Lack of grievance mechanisms',     unit: '%',           fund: 8.4, bm: 15.6, mandatory: true },
  { id: 'PAI-12', name: 'Unadjusted gender pay gap',        unit: '%',           fund: 14.2, bm: 21.8, mandatory: true },
  { id: 'PAI-13', name: 'Board gender diversity',           unit: '% female',    fund: 38, bm: 29, mandatory: true },
  { id: 'PAI-14', name: 'Exposure to controversial weapons', unit: '%',          fund: 0.0, bm: 1.1, mandatory: true },
];

const TOP5_PAI = PAI_INDICATORS.slice(0, 5).map(p => ({ name: p.id, fund: p.fund, benchmark: p.bm }));

const TAXONOMY_DATA = [
  { objective: 'CCM', eligible: 62, aligned: 28 },
  { objective: 'CCA', eligible: 44, aligned: 15 },
  { objective: 'WTR', eligible: 31, aligned: 8 },
  { objective: 'CE',  eligible: 28, aligned: 6 },
  { objective: 'PPC', eligible: 18, aligned: 4 },
  { objective: 'BIO', eligible: 12, aligned: 2 },
];

const INVESTEES_CHECK = [
  { name: 'WindCo Nordic AS',    dnsh: true,  social: true,  governance: true,  additionality: true  },
  { name: 'SolarPV España SL',   dnsh: true,  social: true,  governance: false, additionality: true  },
  { name: 'EV Fleet GmbH',       dnsh: true,  social: false, governance: true,  additionality: true  },
  { name: 'GreenBond Fund II',   dnsh: false, social: true,  governance: true,  additionality: false },
  { name: 'Circular Plastics BV', dnsh: true, social: true,  governance: true,  additionality: true  },
];

const ANNEX_COMPARISON = [
  { section: 'Cover page / summary', annex3: true, annex5: true },
  { section: 'Investment strategy & ESG integration', annex3: true, annex5: true },
  { section: 'Environmental/social characteristics promotion', annex3: true, annex5: false },
  { section: 'Sustainable investment objective', annex3: false, annex5: true },
  { section: 'PAI statement (product-level)', annex3: true, annex5: true },
  { section: 'EU Taxonomy alignment %', annex3: true, annex5: true },
  { section: 'Sustainable investment % achieved', annex3: true, annex5: true },
  { section: 'Best efforts confirmation (Art 8 only)', annex3: true, annex5: false },
  { section: 'Taxonomy-aligned economic activities list', annex3: false, annex5: true },
  { section: 'Website disclosures cross-reference', annex3: true, annex5: true },
];

const REPORT_SECTIONS = [
  'Executive Summary', 'Investment Strategy', 'E/S Characteristics', 'Sustainable Investments',
  'PAI Statement', 'Taxonomy Alignment', 'Monitoring Methodology', 'Data Sources', 'Limitations', 'Due Diligence',
];

// ── Component ─────────────────────────────────────────────────────────────
export default function SFDRProductReportingPage() {
  const [tab, setTab] = useState(0);

  // Tab 0
  const [productName, setProductName] = useState('Evergreen ESG UCITS Fund');
  const [sfdrArticle, setSfdrArticle] = useState('8');
  const [reportPeriod, setReportPeriod] = useState('2024');
  const [sustainPct, setSustainPct] = useState(42);
  const [taxPct, setTaxPct] = useState(18);
  const [reportResult, setReportResult] = useState(null);
  const [reportLoading, setReportLoading] = useState(false);
  const [reportError, setReportError] = useState('');

  // Tab 1
  const [paiLoading, setPaiLoading] = useState(false);
  const [paiResult, setPaiResult] = useState(null);
  const [paiError, setPaiError] = useState('');

  // Tab 2
  const [siLoading, setSiLoading] = useState(false);
  const [siResult, setSiResult] = useState(null);
  const [siError, setSiError] = useState('');

  // Tab 3
  const [taxLoading, setTaxLoading] = useState(false);
  const [taxResult, setTaxResult] = useState(null);
  const [taxError, setTaxError] = useState('');

  const completedSections = Math.round(REPORT_SECTIONS.length * (sfdrArticle === '9' ? 0.95 : 0.8));
  const reportScore = Math.round((completedSections / REPORT_SECTIONS.length) * 100);
  const verifiedCount = INVESTEES_CHECK.filter(i => i.dnsh && i.social && i.governance && i.additionality).length;
  const paiCoverage = 78;

  async function runReport() {
    setReportLoading(true); setReportError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/sfdr-product-reporting/generate-report`, {
        product_name: productName, sfdr_article: sfdrArticle, period: reportPeriod,
        sustainable_investment_pct: sustainPct, taxonomy_alignment_pct: taxPct,
      });
      setReportResult(data);
    } catch {
      setReportError('API unavailable — showing seed data.');
      const gaps = sfdrArticle === '9' ? ['Taxonomy-aligned activities list', 'DNSH verification evidence'] : ['Best efforts methodology'];
      setReportResult({ completeness_score: reportScore, section_gaps: gaps, download_ready: reportScore >= 80 });
    } finally { setReportLoading(false); }
  }

  async function runPai() {
    setPaiLoading(true); setPaiError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/sfdr-product-reporting/calculate-pai`, { product_name: productName });
      setPaiResult(data);
    } catch {
      setPaiError('API unavailable — showing seed data.');
      setPaiResult({ coverage_pct: paiCoverage, indicators: PAI_INDICATORS });
    } finally { setPaiLoading(false); }
  }

  async function runSI() {
    setSiLoading(true); setSiError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/sfdr-product-reporting/verify-sustainable-investment`, { product_name: productName });
      setSiResult(data);
    } catch {
      setSiError('API unavailable — showing seed data.');
      setSiResult({ verified_count: verifiedCount, total: INVESTEES_CHECK.length, verified_pct: Math.round(verifiedCount / INVESTEES_CHECK.length * 100) });
    } finally { setSiLoading(false); }
  }

  async function runTax() {
    setTaxLoading(true); setTaxError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/sfdr-product-reporting/taxonomy-disclosure`, { product_name: productName });
      setTaxResult(data);
    } catch {
      setTaxError('API unavailable — showing seed data.');
      setTaxResult({ data: TAXONOMY_DATA });
    } finally { setTaxLoading(false); }
  }

  const TABS = ['Periodic Report Generator', 'Product PAI', 'Sustainable Investment Verification', 'Taxonomy Disclosure', 'Reference'];

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="bg-black text-white px-6 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-base font-bold tracking-tight">SFDR Product Periodic Reporting</h1>
          <p className="text-xs text-gray-400 mt-0.5">RTS (EU) 2022/1288 · Annex III (Art 8) · Annex V (Art 9)</p>
        </div>
        <span className="text-[10px] font-bold px-2 py-1 rounded border border-emerald-500 text-emerald-400">E22</span>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 px-6 py-4">
        <KpiCard label="Report Completeness" value={`${reportScore}%`} sub="Periodic report" accent={reportScore >= 80 ? 'green' : 'amber'} />
        <KpiCard label="Sustainable Investment" value={`${sustainPct}%`} sub={`Art ${sfdrArticle} target`} accent="green" badge={`Art ${sfdrArticle}`} />
        <KpiCard label="Taxonomy Aligned" value={`${taxPct}%`} sub="CCM objective" accent="green" />
        <KpiCard label="PAI Coverage" value={`${paiCoverage}%`} sub="14 mandatory indicators" accent={paiCoverage >= 70 ? 'green' : 'amber'} />
      </div>

      <div className="px-6 border-b border-gray-200 bg-white">
        <div className="flex gap-1 overflow-x-auto">
          {TABS.map((t, i) => (
            <button key={i} onClick={() => setTab(i)}
              className={`px-4 py-2.5 text-xs font-semibold whitespace-nowrap border-b-2 transition-colors ${tab === i ? 'border-emerald-500 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
            >{t}</button>
          ))}
        </div>
      </div>

      <div className="px-6 py-4">

        {/* ── Tab 0: Report Generator ── */}
        {tab === 0 && (
          <>
            <Section title="Product Configuration" subtitle="Configure SFDR product for periodic reporting (Annex III / V)">
              <Row label="Product / Fund Name"><Inp value={productName} onChange={setProductName} type="text" /></Row>
              <Row label="SFDR Article">
                <div className="flex gap-4">
                  {['8', '9'].map(a => (
                    <label key={a} className="flex items-center gap-2 cursor-pointer">
                      <input type="radio" name="article" value={a} checked={sfdrArticle === a} onChange={() => setSfdrArticle(a)} className="accent-emerald-500" />
                      <span className={`text-xs font-semibold px-2 py-0.5 rounded ${sfdrArticle === a ? 'bg-emerald-100 text-emerald-700' : 'text-gray-600'}`}>Article {a}</span>
                    </label>
                  ))}
                </div>
              </Row>
              <Row label="Reporting Period">
                <Sel value={reportPeriod} onChange={setReportPeriod} options={[{ value: '2023', label: '2023' }, { value: '2024', label: '2024' }]} />
              </Row>
              <Row label={`Sustainable Investment % (target: ${sfdrArticle === '9' ? '100' : 'min 1'}%)`}>
                <div className="flex items-center gap-3">
                  <input type="range" min={0} max={100} value={sustainPct} onChange={e => setSustainPct(+e.target.value)} className="flex-1 accent-emerald-500" />
                  <span className="text-sm font-mono w-12 text-right">{sustainPct}%</span>
                </div>
              </Row>
              <Row label="Taxonomy Alignment %">
                <div className="flex items-center gap-3">
                  <input type="range" min={0} max={100} value={taxPct} onChange={e => setTaxPct(+e.target.value)} className="flex-1 accent-emerald-500" />
                  <span className="text-sm font-mono w-12 text-right">{taxPct}%</span>
                </div>
              </Row>
              <Btn onClick={runReport} loading={reportLoading}>Generate Report</Btn>
            </Section>
            {reportError && <div className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded p-3 mb-3">{reportError}</div>}
            {reportResult && (
              <Section title="Report Assessment">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className={`text-3xl font-bold font-mono ${reportResult.completeness_score >= 80 ? 'text-emerald-600' : 'text-amber-600'}`}>{reportResult.completeness_score}%</div>
                    <div className="text-xs text-gray-500 mt-1">Completeness Score</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className={`text-2xl font-bold ${reportResult.download_ready ? 'text-emerald-600' : 'text-amber-600'}`}>{reportResult.download_ready ? 'Ready' : 'Incomplete'}</div>
                    <div className="text-xs text-gray-500 mt-1">Download Status</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-3xl font-bold font-mono text-red-600">{reportResult.section_gaps?.length || 0}</div>
                    <div className="text-xs text-gray-500 mt-1">Section Gaps</div>
                  </div>
                </div>
                {reportResult.section_gaps?.length > 0 && (
                  <div>
                    <div className="text-xs font-semibold text-gray-700 mb-2">Gaps Identified</div>
                    {reportResult.section_gaps.map(g => (
                      <div key={g} className="flex items-center gap-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded px-3 py-1.5 mb-1">
                        <span className="w-2 h-2 rounded-full bg-red-500 shrink-0"></span>{g}
                      </div>
                    ))}
                  </div>
                )}
              </Section>
            )}
          </>
        )}

        {/* ── Tab 1: Product PAI ── */}
        {tab === 1 && (
          <>
            <Section title="Product-Level PAI Indicators" subtitle="14 mandatory principal adverse impact indicators (Annex I Table 1)">
              <Btn onClick={runPai} loading={paiLoading}>Calculate PAI</Btn>
              {paiError && <div className="text-xs text-amber-600 mt-2">{paiError}</div>}
              <div className="flex items-center gap-2 mt-3">
                <span className="text-xs text-gray-500">Coverage:</span>
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div className="bg-emerald-500 h-2 rounded-full" style={{ width: `${paiCoverage}%` }} />
                </div>
                <span className={`text-xs font-bold ${paiCoverage >= 70 ? 'text-emerald-600' : 'text-amber-600'}`}>{paiCoverage}%</span>
              </div>
            </Section>
            <Section title="Fund vs Benchmark — Top 5 PAI Indicators">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={TOP5_PAI} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 10 }} />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar dataKey="fund" name="Fund" fill={EM} radius={[4, 4, 0, 0]} />
                  <Bar dataKey="benchmark" name="Benchmark" fill="#d1d5db" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="All 14 PAI Indicators">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">ID</th>
                  <th className="text-left py-2 text-gray-500">Indicator</th>
                  <th className="text-right py-2 text-gray-500">Unit</th>
                  <th className="text-right py-2 text-gray-500">Fund</th>
                  <th className="text-right py-2 text-gray-500">Benchmark</th>
                  <th className="text-center py-2 text-gray-500">vs BM</th>
                </tr></thead>
                <tbody>
                  {PAI_INDICATORS.map(p => {
                    const better = p.id === 'PAI-13' ? p.fund > p.bm : p.fund < p.bm;
                    return (
                      <tr key={p.id} className="border-b border-gray-100 hover:bg-gray-50">
                        <td className="py-1.5 font-bold text-emerald-700">{p.id}</td>
                        <td className="py-1.5">{p.name}</td>
                        <td className="py-1.5 text-right text-gray-400">{p.unit}</td>
                        <td className="py-1.5 text-right font-mono">{p.fund}</td>
                        <td className="py-1.5 text-right font-mono text-gray-400">{p.bm}</td>
                        <td className={`py-1.5 text-center font-bold ${better ? 'text-emerald-600' : 'text-red-600'}`}>{better ? '↓ Better' : '↑ Worse'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* ── Tab 2: Sustainable Investment Verification ── */}
        {tab === 2 && (
          <>
            <Section title="Sustainable Investment Criteria Verification" subtitle="SFDR Art 2(17): Do Not Significantly Harm, Social Good, Good Governance, Additionality">
              <Btn onClick={runSI} loading={siLoading}>Verify Sustainable Investments</Btn>
              {siError && <div className="text-xs text-amber-600 mt-2">{siError}</div>}
            </Section>
            {siResult && (
              <Section title="Verification Summary">
                <div className="grid grid-cols-3 gap-4 mb-4">
                  <div className="text-center p-4 rounded-xl bg-emerald-50">
                    <div className="text-3xl font-bold font-mono text-emerald-600">{siResult.verified_count}/{siResult.total}</div>
                    <div className="text-xs text-gray-500 mt-1">Investees Verified</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className="text-3xl font-bold font-mono text-gray-700">{siResult.verified_pct}%</div>
                    <div className="text-xs text-gray-500 mt-1">Verified vs Claimed</div>
                  </div>
                  <div className="text-center p-4 rounded-xl bg-gray-50">
                    <div className={`text-xl font-bold ${sustainPct <= siResult.verified_pct ? 'text-emerald-600' : 'text-red-600'}`}>{sustainPct <= siResult.verified_pct ? 'Claim Met' : 'Claim Gap'}</div>
                    <div className="text-xs text-gray-500 mt-1">vs {sustainPct}% target</div>
                  </div>
                </div>
              </Section>
            )}
            <Section title="Investee-Level Criteria Checklist">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">Investee</th>
                  <th className="text-center py-2 text-gray-500">DNSH</th>
                  <th className="text-center py-2 text-gray-500">Social Good</th>
                  <th className="text-center py-2 text-gray-500">Governance</th>
                  <th className="text-center py-2 text-gray-500">Additionality</th>
                  <th className="text-center py-2 text-gray-500">Verified</th>
                </tr></thead>
                <tbody>
                  {INVESTEES_CHECK.map(inv => {
                    const verified = inv.dnsh && inv.social && inv.governance && inv.additionality;
                    const Check = ({ v }) => <span className={`text-base ${v ? 'text-emerald-600' : 'text-red-400'}`}>{v ? '✓' : '✗'}</span>;
                    return (
                      <tr key={inv.name} className={`border-b border-gray-100 ${verified ? 'bg-emerald-50' : ''}`}>
                        <td className="py-2 font-medium">{inv.name}</td>
                        <td className="py-2 text-center"><Check v={inv.dnsh} /></td>
                        <td className="py-2 text-center"><Check v={inv.social} /></td>
                        <td className="py-2 text-center"><Check v={inv.governance} /></td>
                        <td className="py-2 text-center"><Check v={inv.additionality} /></td>
                        <td className={`py-2 text-center font-bold ${verified ? 'text-emerald-700' : 'text-red-600'}`}>{verified ? 'Verified' : 'Failed'}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* ── Tab 3: Taxonomy Disclosure ── */}
        {tab === 3 && (
          <>
            <Section title="EU Taxonomy Disclosure by Objective" subtitle="Eligible % and aligned % per environmental objective">
              <Btn onClick={runTax} loading={taxLoading}>Refresh Taxonomy Data</Btn>
              {taxError && <div className="text-xs text-amber-600 mt-2">{taxError}</div>}
            </Section>
            <Section title="Eligible vs Aligned by Objective (% of portfolio)">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={TAXONOMY_DATA} margin={{ top: 4, right: 16, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="objective" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 10 }} unit="%" />
                  <Tooltip />
                  <Legend wrapperStyle={{ fontSize: 10 }} />
                  <Bar dataKey="eligible" name="Eligible %" fill="#a7f3d0" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="aligned" name="Aligned %" fill={EM} radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
              <table className="w-full text-xs mt-4">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">Objective</th>
                  <th className="text-left py-2 text-gray-500">Full Name</th>
                  <th className="text-right py-2 text-gray-500">Eligible %</th>
                  <th className="text-right py-2 text-gray-500">Aligned %</th>
                  <th className="text-right py-2 text-gray-500">Alignment Rate</th>
                </tr></thead>
                <tbody>
                  {TAXONOMY_DATA.map((r, i) => {
                    const fullNames = ['Climate Change Mitigation', 'Climate Change Adaptation', 'Water & Marine Resources', 'Circular Economy', 'Pollution Prevention', 'Biodiversity & Ecosystems'];
                    return (
                      <tr key={r.objective} className="border-b border-gray-100">
                        <td className="py-1.5 font-bold text-emerald-700">{r.objective}</td>
                        <td className="py-1.5 text-gray-600">{fullNames[i]}</td>
                        <td className="py-1.5 text-right font-mono">{r.eligible}%</td>
                        <td className="py-1.5 text-right font-mono">{r.aligned}%</td>
                        <td className="py-1.5 text-right font-mono">{Math.round(r.aligned / r.eligible * 100)}%</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </Section>
          </>
        )}

        {/* ── Tab 4: Reference ── */}
        {tab === 4 && (
          <>
            <Section title="Annex III vs Annex V — Sections Comparison">
              <table className="w-full text-xs">
                <thead><tr className="border-b border-gray-200">
                  <th className="text-left py-2 text-gray-500">Section</th>
                  <th className="text-center py-2 text-gray-500">Annex III (Art 8)</th>
                  <th className="text-center py-2 text-gray-500">Annex V (Art 9)</th>
                </tr></thead>
                <tbody>
                  {ANNEX_COMPARISON.map((r, i) => (
                    <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                      <td className="py-1.5">{r.section}</td>
                      <td className={`py-1.5 text-center font-bold text-base ${r.annex3 ? 'text-emerald-600' : 'text-gray-300'}`}>{r.annex3 ? '✓' : '—'}</td>
                      <td className={`py-1.5 text-center font-bold text-base ${r.annex5 ? 'text-emerald-600' : 'text-gray-300'}`}>{r.annex5 ? '✓' : '—'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </Section>
            <Section title="Website Disclosure Requirements" subtitle="RTS 2022/1288 Articles 10-12">
              <div className="space-y-2 text-xs">
                {[
                  { art: 'Art 8', req: 'E/S characteristics description, investment strategies, reference benchmark, website information for E/S products' },
                  { art: 'Art 9', req: 'Sustainable investment objective, methodology, reference benchmark, impact reporting on website' },
                  { art: 'Art 10', req: 'Pre-contractual info published on website; periodic reports accessible; updates within 10 business days of change' },
                  { art: 'Art 12', req: 'Engagement policy if applicable; comply-or-explain basis for stewardship' },
                ].map(r => (
                  <div key={r.art} className="p-3 rounded-lg bg-gray-50 border border-gray-200">
                    <span className="font-bold text-emerald-700 mr-2">{r.art}:</span>
                    <span className="text-gray-600">{r.req}</span>
                  </div>
                ))}
              </div>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
