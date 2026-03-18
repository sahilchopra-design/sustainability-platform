/**
 * UKSDRPage.jsx — Route: /uk-sdr
 * UK Sustainability Disclosure Requirements (SDR) — E11
 * FCA PS 23/16 — Investment Labels · AGR · Naming & Marketing Requirements
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

function Section({ title, children }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg mb-4">
      <div className="px-4 py-3 border-b border-gray-100">
        <span className="font-medium text-sm text-gray-700">{title}</span>
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}

function KpiCard({ label, value, sub, color = 'text-gray-900' }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Badge({ label, color = 'gray' }) {
  const cls = {
    green:  'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber:  'bg-amber-50  text-amber-700  border-amber-200',
    red:    'bg-red-50    text-red-700    border-red-200',
    blue:   'bg-blue-50   text-blue-700   border-blue-200',
    gray:   'bg-gray-50   text-gray-600   border-gray-200',
    purple: 'bg-purple-50 text-purple-700 border-purple-200',
    teal:   'bg-teal-50   text-teal-700   border-teal-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>;
}

function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="text-xs text-gray-500 w-44 shrink-0">{label}</span>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'text', placeholder = '' }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500">
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Chk({ checked, onChange, label }) {
  return (
    <label className="flex items-center gap-2 text-xs text-gray-700 cursor-pointer">
      <input type="checkbox" checked={checked} onChange={e => onChange(e.target.checked)}
        className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500" />
      {label}
    </label>
  );
}

function Btn({ onClick, loading, children, disabled }) {
  return (
    <button onClick={onClick} disabled={disabled || loading}
      className="px-4 py-1.5 rounded text-xs font-medium bg-black text-white hover:bg-gray-800 disabled:opacity-50">
      {loading ? 'Running...' : children}
    </button>
  );
}

function ErrBox({ msg }) {
  return <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700 mb-4">{msg}</div>;
}

const LABEL_COLOR  = { sustainable_focus: 'green', sustainable_improvers: 'blue', sustainable_impact: 'purple', mixed_goals: 'amber' };
const LABEL_DISPLAY = { sustainable_focus: 'Sustainable Focus', sustainable_improvers: 'Sustainable Improvers', sustainable_impact: 'Sustainable Impact', mixed_goals: 'Mixed Goals' };
const ICIS_COLOR   = { exemplary: 'green', robust: 'blue', developing: 'amber', inadequate: 'red' };
const STATUS_COLOR = { eligible: 'green', partial: 'amber', not_eligible: 'red', review_needed: 'amber' };

const DEFAULT_PRODUCT = {
  product_id: 'PROD_DEMO_001', product_name: 'UK Sustainable Equity Fund',
  product_type: 'equity_fund', aum_gbp: 100000000, fca_authorised: true,
  qualifying_sustainable_pct: 72, has_improvement_targets: false, has_measurable_impact_kpis: false,
  impact_additionality: false, uses_sustainability_terms_in_name: true,
  sustainability_evidence_quality: 'adequate', methodology_published: true, third_party_verified: false,
  data_coverage_pct: 85, claims_reviewed_by_legal: true, claims_updated_on_change: true,
  pre_contractual_disclosure_produced: false, ongoing_disclosure_produced: false, entity_disclosure_produced: false,
  sfdr_classification: 'art_8', eu_taxonomy_alignment_pct: 22,
};

const PRODUCT_TYPE_OPTIONS = [
  { value: 'equity_fund', label: 'Equity Fund' }, { value: 'bond_fund', label: 'Bond Fund' },
  { value: 'mixed_asset_fund', label: 'Mixed Asset Fund' }, { value: 'etf', label: 'ETF' },
  { value: 'private_equity', label: 'Private Equity' }, { value: 'infrastructure_fund', label: 'Infrastructure Fund' },
  { value: 'private_debt', label: 'Private Debt' },
];

const EVIDENCE_OPTIONS = [
  { value: 'none', label: 'None (0 pts)' }, { value: 'weak', label: 'Weak (10 pts)' },
  { value: 'adequate', label: 'Adequate (22 pts)' }, { value: 'strong', label: 'Strong (30 pts)' },
];

function SDRAssessmentTab() {
  const [form, setForm] = useState(DEFAULT_PRODUCT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const set = useCallback((k, v) => setForm(f => ({ ...f, [k]: v })), []);

  const run = async () => {
    setLoading(true); setErr(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/uk-sdr/assess`, { product: form });
      setResult(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Section title="Product Configuration">
        <div className="grid grid-cols-2 gap-x-8">
          <div>
            <Row label="Product ID"><Inp value={form.product_id} onChange={v => set('product_id', v)} /></Row>
            <Row label="Product Name"><Inp value={form.product_name} onChange={v => set('product_name', v)} /></Row>
            <Row label="Product Type"><Sel value={form.product_type} onChange={v => set('product_type', v)} options={PRODUCT_TYPE_OPTIONS} /></Row>
            <Row label="AUM (GBP)"><Inp type="number" value={form.aum_gbp} onChange={v => set('aum_gbp', parseFloat(v))} /></Row>
            <Row label="SFDR Classification">
              <Sel value={form.sfdr_classification || 'none'} onChange={v => set('sfdr_classification', v === 'none' ? null : v)} options={[
                { value: 'none', label: 'None' }, { value: 'art_6', label: 'Art. 6' },
                { value: 'art_8', label: 'Art. 8' }, { value: 'art_9', label: 'Art. 9' },
              ]} />
            </Row>
            <Row label="EU Taxonomy %">
              <Inp type="number" value={form.eu_taxonomy_alignment_pct ?? ''} onChange={v => set('eu_taxonomy_alignment_pct', v ? parseFloat(v) : null)} />
            </Row>
            <Row label="Evidence Quality"><Sel value={form.sustainability_evidence_quality} onChange={v => set('sustainability_evidence_quality', v)} options={EVIDENCE_OPTIONS} /></Row>
            <Row label={`Qualifying % (${form.qualifying_sustainable_pct}%)`}>
              <input type="range" min="0" max="100" value={form.qualifying_sustainable_pct}
                onChange={e => set('qualifying_sustainable_pct', parseFloat(e.target.value))} className="w-full accent-emerald-600" />
            </Row>
            <Row label={`Data Coverage % (${form.data_coverage_pct}%)`}>
              <input type="range" min="0" max="100" value={form.data_coverage_pct}
                onChange={e => set('data_coverage_pct', parseFloat(e.target.value))} className="w-full accent-emerald-600" />
            </Row>
          </div>
          <div className="space-y-2">
            <Chk checked={form.fca_authorised} onChange={v => set('fca_authorised', v)} label="FCA Authorised" />
            <Chk checked={form.uses_sustainability_terms_in_name} onChange={v => set('uses_sustainability_terms_in_name', v)} label="Uses Sustainability Terms in Name" />
            <Chk checked={form.methodology_published} onChange={v => set('methodology_published', v)} label="Methodology Published" />
            <Chk checked={form.third_party_verified} onChange={v => set('third_party_verified', v)} label="Third-Party Verified" />
            <Chk checked={form.claims_reviewed_by_legal} onChange={v => set('claims_reviewed_by_legal', v)} label="Claims Reviewed by Legal" />
            <Chk checked={form.claims_updated_on_change} onChange={v => set('claims_updated_on_change', v)} label="Claims Updated on Change" />
            <Chk checked={form.pre_contractual_disclosure_produced} onChange={v => set('pre_contractual_disclosure_produced', v)} label="Pre-contractual Disclosure" />
            <Chk checked={form.ongoing_disclosure_produced} onChange={v => set('ongoing_disclosure_produced', v)} label="Ongoing Disclosure Produced" />
            <Chk checked={form.has_improvement_targets} onChange={v => set('has_improvement_targets', v)} label="Has Improvement Targets" />
            <Chk checked={form.has_measurable_impact_kpis} onChange={v => set('has_measurable_impact_kpis', v)} label="Has Measurable Impact KPIs" />
            <Chk checked={form.impact_additionality} onChange={v => set('impact_additionality', v)} label="Impact Additionality" />
          </div>
        </div>
        <div className="mt-4"><Btn onClick={run} loading={loading}>Run SDR Assessment</Btn></div>
      </Section>

      {err && <ErrBox msg={err} />}

      {result && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <KpiCard label="Recommended Label"
              value={result.headline.recommended_label ? LABEL_DISPLAY[result.headline.recommended_label] || result.headline.recommended_label : 'None'}
              color={result.headline.recommended_label ? 'text-emerald-700' : 'text-red-600'} />
            <KpiCard label="ICIS Score" value={`${result.icis?.score ?? 0}/100`} sub={result.icis?.tier}
              color={{ green: 'text-emerald-700', blue: 'text-blue-700', amber: 'text-amber-700', red: 'text-red-600' }[ICIS_COLOR[result.icis?.tier]] || 'text-gray-700'} />
            <KpiCard label="AGR Compliant" value={result.headline.agr_compliant ? 'PASS' : 'FAIL'}
              sub={`${result.headline.agr_blocking_gaps} blocking gap(s)`}
              color={result.headline.agr_compliant ? 'text-emerald-700' : 'text-red-600'} />
            <KpiCard label="Labels Eligible" value={`${result.headline.labels_eligible_count} / 4`} sub="SDR investment labels" />
          </div>

          <div className="flex items-center gap-2 mb-4">
            <span className="text-xs text-gray-500">Status:</span>
            <Badge label={(result.headline.overall_status || '').replace(/_/g, ' ').toUpperCase()} color={STATUS_COLOR[result.headline.overall_status] || 'gray'} />
            {result.icis?.tier && <Badge label={`ICIS: ${result.icis.tier}`} color={ICIS_COLOR[result.icis.tier] || 'gray'} />}
            {result.headline.recommended_label && <Badge label={LABEL_DISPLAY[result.headline.recommended_label]} color={LABEL_COLOR[result.headline.recommended_label] || 'gray'} />}
          </div>

          <Section title="Label Eligibility">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium">Label</th><th className="pb-2 font-medium">Eligible</th>
                <th className="pb-2 font-medium">Qualifying %</th><th className="pb-2 font-medium">Threshold %</th>
                <th className="pb-2 font-medium">Gaps</th>
              </tr></thead>
              <tbody>
                {(result.label_eligibility || []).map(lr => (
                  <tr key={lr.label_id} className="border-b border-gray-50">
                    <td className="py-2"><Badge label={LABEL_DISPLAY[lr.label_id] || lr.label_name} color={LABEL_COLOR[lr.label_id] || 'gray'} /></td>
                    <td className="py-2"><span className={lr.eligible ? 'text-emerald-600 font-semibold' : 'text-gray-400'}>{lr.eligible ? 'Yes' : 'No'}</span></td>
                    <td className="py-2 font-mono">{(lr.qualifying_pct ?? 0).toFixed(1)}%</td>
                    <td className="py-2 font-mono">{(lr.threshold_pct ?? 0).toFixed(1)}%</td>
                    <td className="py-2 text-gray-500 text-[10px]">{(lr.gaps || []).join('; ') || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          <Section title="Anti-Greenwashing Rule (AGR) Assessment">
            <div className="flex items-center gap-3 mb-3">
              <Badge label={result.agr_assessment?.compliant ? 'AGR COMPLIANT' : 'AGR NON-COMPLIANT'} color={result.agr_assessment?.compliant ? 'green' : 'red'} />
              <span className="text-xs text-gray-500">{result.agr_assessment?.blocking_gaps} blocking gap(s)</span>
            </div>
            <table className="w-full text-xs">
              <thead><tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium w-16">ID</th><th className="pb-2 font-medium">Title</th>
                <th className="pb-2 font-medium w-20">Blocking</th><th className="pb-2 font-medium w-24">Status</th>
              </tr></thead>
              <tbody>
                {(result.agr_assessment?.requirements || []).map(r => (
                  <tr key={r.req_id} className={`border-b border-gray-50 ${!r.compliant && r.blocking ? 'bg-red-50' : ''}`}>
                    <td className="py-1.5 font-mono text-gray-500">{r.req_id}</td>
                    <td className="py-1.5">{r.title}</td>
                    <td className="py-1.5">{r.blocking ? <Badge label="Blocking" color="red" /> : <span className="text-gray-400 text-[10px]">Advisory</span>}</td>
                    <td className="py-1.5"><Badge label={r.status} color={r.compliant ? 'green' : r.blocking ? 'red' : 'amber'} /></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>

          {result.naming_assessment && (
            <Section title="Naming and Marketing Assessment">
              <div className="flex items-center gap-3 mb-3">
                <Badge label={result.naming_assessment.naming_compliant ? 'NAMING COMPLIANT' : 'NAMING ISSUES'} color={result.naming_assessment.naming_compliant ? 'green' : 'red'} />
                {result.naming_assessment.contains_sustainability_terms && <Badge label="Sustainability Terms Used" color="amber" />}
                {result.naming_assessment.label_held && <Badge label={`Label: ${result.naming_assessment.label_held}`} color="green" />}
              </div>
              {(result.naming_assessment.prohibited_terms_found || []).length > 0 && (
                <div className="mb-2 flex items-center gap-2 flex-wrap">
                  <span className="text-xs text-gray-500">Prohibited terms found:</span>
                  {result.naming_assessment.prohibited_terms_found.map(t => <Badge key={t} label={t} color="red" />)}
                </div>
              )}
              {(result.naming_assessment.required_actions || []).length > 0 && (
                <ul className="text-xs text-gray-600 space-y-1 mt-2">
                  {result.naming_assessment.required_actions.map((a, i) => <li key={i} className="flex gap-2"><span className="text-amber-500">!</span>{a}</li>)}
                </ul>
              )}
            </Section>
          )}

          {(result.priority_actions || []).length > 0 && (
            <Section title="Priority Actions">
              <ol className="text-xs text-gray-700 space-y-1.5 list-decimal list-inside">
                {result.priority_actions.map((a, i) => <li key={i}>{a}</li>)}
              </ol>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

function AGRCheckerTab() {
  const [form, setForm] = useState({ ...DEFAULT_PRODUCT, product_id: 'PROD_AGR_001', product_name: 'Apex Green Bond Fund', claims_reviewed_by_legal: false });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const set = useCallback((k, v) => setForm(f => ({ ...f, [k]: v })), []);

  const run = async () => {
    setLoading(true); setErr(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/uk-sdr/agr-check`, { product: form });
      setResult(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Section title="AGR Check - Product Inputs">
        <div className="grid grid-cols-2 gap-x-8">
          <div>
            <Row label="Product ID"><Inp value={form.product_id} onChange={v => set('product_id', v)} /></Row>
            <Row label="Product Name"><Inp value={form.product_name} onChange={v => set('product_name', v)} /></Row>
            <Row label="Evidence Quality"><Sel value={form.sustainability_evidence_quality} onChange={v => set('sustainability_evidence_quality', v)} options={EVIDENCE_OPTIONS} /></Row>
            <Row label={`Data Coverage % (${form.data_coverage_pct}%)`}>
              <input type="range" min="0" max="100" value={form.data_coverage_pct}
                onChange={e => set('data_coverage_pct', parseFloat(e.target.value))} className="w-full accent-emerald-600" />
            </Row>
          </div>
          <div className="space-y-2">
            <Chk checked={form.methodology_published} onChange={v => set('methodology_published', v)} label="Methodology Published" />
            <Chk checked={form.third_party_verified} onChange={v => set('third_party_verified', v)} label="Third-Party Verified" />
            <Chk checked={form.claims_reviewed_by_legal} onChange={v => set('claims_reviewed_by_legal', v)} label="Claims Reviewed by Legal" />
            <Chk checked={form.claims_updated_on_change} onChange={v => set('claims_updated_on_change', v)} label="Claims Updated on Change" />
            <Chk checked={form.pre_contractual_disclosure_produced} onChange={v => set('pre_contractual_disclosure_produced', v)} label="Pre-contractual Disclosure" />
            <Chk checked={form.ongoing_disclosure_produced} onChange={v => set('ongoing_disclosure_produced', v)} label="Ongoing Disclosure Produced" />
          </div>
        </div>
        <div className="mt-4"><Btn onClick={run} loading={loading}>Check AGR Compliance</Btn></div>
      </Section>
      {err && <ErrBox msg={err} />}
      {result && (
        <>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <KpiCard label="AGR Status" value={result.agr_compliant ? 'COMPLIANT' : 'NON-COMPLIANT'} color={result.agr_compliant ? 'text-emerald-700' : 'text-red-600'} />
            <KpiCard label="Blocking Gaps" value={result.blocking_gaps} sub="of 6 blocking requirements" color={result.blocking_gaps > 0 ? 'text-red-600' : 'text-emerald-700'} />
            <KpiCard label="Requirements Passed" value={`${(result.requirements || []).filter(r => r.compliant).length} / ${(result.requirements || []).length}`} />
          </div>
          <Section title="AGR Requirements - Detailed">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium w-16">ID</th><th className="pb-2 font-medium">Requirement</th>
                <th className="pb-2 font-medium w-20">Blocking</th><th className="pb-2 font-medium w-24">Status</th>
                <th className="pb-2 font-medium w-32">Source</th>
              </tr></thead>
              <tbody>
                {(result.requirements || []).map(r => (
                  <tr key={r.req_id} className={`border-b border-gray-50 ${!r.compliant && r.blocking ? 'bg-red-50' : ''}`}>
                    <td className="py-1.5 font-mono text-gray-500">{r.req_id}</td>
                    <td className="py-1.5">{r.title}</td>
                    <td className="py-1.5">{r.blocking ? <Badge label="Blocking" color="red" /> : <span className="text-gray-400 text-[10px]">Advisory</span>}</td>
                    <td className="py-1.5"><Badge label={r.status} color={r.compliant ? 'green' : r.blocking ? 'red' : 'amber'} /></td>
                    <td className="py-1.5 text-gray-400 text-[10px]">{r.source || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Section>
          {(result.priority_actions || []).length > 0 && (
            <Section title="AGR Priority Actions">
              <ul className="text-xs text-gray-700 space-y-1.5">
                {result.priority_actions.map((a, i) => <li key={i} className="flex gap-2"><span className="text-red-500 font-bold">!</span>{a}</li>)}
              </ul>
            </Section>
          )}
        </>
      )}
    </div>
  );
}

const BATCH_DEMO = [
  { product: { ...DEFAULT_PRODUCT, product_id: 'PROD_B_001', product_name: 'UK Sustainable Focus Equity Fund', qualifying_sustainable_pct: 78, third_party_verified: true, sustainability_evidence_quality: 'strong' } },
  { product: { ...DEFAULT_PRODUCT, product_id: 'PROD_B_002', product_name: 'UK Improvers Bond Fund', qualifying_sustainable_pct: 32, has_improvement_targets: true, uses_sustainability_terms_in_name: false, sustainability_evidence_quality: 'adequate', product_type: 'bond_fund' } },
  { product: { ...DEFAULT_PRODUCT, product_id: 'PROD_B_003', product_name: 'Apex Green ETF', qualifying_sustainable_pct: 8, uses_sustainability_terms_in_name: true, sustainability_evidence_quality: 'weak', claims_reviewed_by_legal: false, product_type: 'etf' } },
];

function BatchTab() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const run = async () => {
    setLoading(true); setErr(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/uk-sdr/assess/batch`, { products: BATCH_DEMO });
      setResult(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Section title="Batch Demo - 3 Products">
        <p className="text-xs text-gray-500 mb-3">Demo batch: high-qualifying fund (Focus eligible), mid-range improver, low-qualifying ETF with naming issues.</p>
        <table className="w-full text-xs mb-4">
          <thead><tr className="text-left text-gray-500 border-b border-gray-100">
            <th className="pb-2 font-medium">Product</th><th className="pb-2 font-medium">Type</th>
            <th className="pb-2 font-medium">Qualifying %</th><th className="pb-2 font-medium">Evidence</th>
          </tr></thead>
          <tbody>
            {BATCH_DEMO.map(item => (
              <tr key={item.product.product_id} className="border-b border-gray-50">
                <td className="py-1.5 font-medium">{item.product.product_name}</td>
                <td className="py-1.5 text-gray-500">{item.product.product_type}</td>
                <td className="py-1.5 font-mono">{item.product.qualifying_sustainable_pct}%</td>
                <td className="py-1.5">
                  <Badge label={item.product.sustainability_evidence_quality} color={item.product.sustainability_evidence_quality === 'strong' ? 'green' : item.product.sustainability_evidence_quality === 'adequate' ? 'blue' : 'amber'} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        <Btn onClick={run} loading={loading}>Run Batch Assessment</Btn>
      </Section>
      {err && <ErrBox msg={err} />}
      {result && (
        <>
          <div className="grid grid-cols-4 gap-3 mb-4">
            <KpiCard label="Products Assessed" value={result.batch_count} />
            <KpiCard label="With SDR Label" value={result.products_with_label} color="text-emerald-700" />
            <KpiCard label="AGR Compliant" value={result.products_agr_compliant} color="text-blue-700" />
            <KpiCard label="Naming Issues" value={result.products_naming_issues} color={result.products_naming_issues > 0 ? 'text-red-600' : 'text-emerald-700'} />
          </div>
          <Section title="Batch Results">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium">Product</th><th className="pb-2 font-medium">Label</th>
                <th className="pb-2 font-medium">Status</th><th className="pb-2 font-medium">AGR</th>
                <th className="pb-2 font-medium">ICIS</th>
              </tr></thead>
              <tbody>
                {(result.assessments || []).map(a => (
                  <tr key={a.product_id} className="border-b border-gray-50">
                    <td className="py-2 font-medium">{a.product_name}</td>
                    <td className="py-2">{a.headline.recommended_label ? <Badge label={LABEL_DISPLAY[a.headline.recommended_label] || a.headline.recommended_label} color={LABEL_COLOR[a.headline.recommended_label] || 'gray'} /> : <span className="text-red-400 text-[10px]">No Label</span>}</td>
                    <td className="py-2"><Badge label={(a.headline.overall_status || '').replace(/_/g, ' ')} color={STATUS_COLOR[a.headline.overall_status] || 'gray'} /></td>
                    <td className="py-2"><Badge label={a.headline.agr_compliant ? 'Pass' : 'Fail'} color={a.headline.agr_compliant ? 'green' : 'red'} /></td>
                    <td className="py-2 font-mono">{a.headline.icis_score ?? '-'}</td>
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

const LABEL_CARD_COLORS = {
  sustainable_focus:     { border: 'border-emerald-200', bg: 'bg-emerald-50', text: 'text-emerald-700' },
  sustainable_improvers: { border: 'border-blue-200',    bg: 'bg-blue-50',    text: 'text-blue-700' },
  sustainable_impact:    { border: 'border-purple-200',  bg: 'bg-purple-50',  text: 'text-purple-700' },
  mixed_goals:           { border: 'border-amber-200',   bg: 'bg-amber-50',   text: 'text-amber-700' },
};

function LabelReferenceTab() {
  const [labels, setLabels] = useState(null);
  const [agr, setAgr] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    Promise.all([axios.get(`${API}/api/v1/uk-sdr/ref/labels`), axios.get(`${API}/api/v1/uk-sdr/ref/agr-requirements`)])
      .then(([l, a]) => { setLabels(l.data); setAgr(a.data); })
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading reference data...</div>;
  if (err) return <ErrBox msg={err} />;

  return (
    <div>
      {labels && (
        <Section title={`SDR Investment Labels - ${labels.regime}`}>
          <div className="grid grid-cols-2 gap-4 mb-3">
            {(labels.labels || []).map(l => {
              const c = LABEL_CARD_COLORS[l.label_id] || LABEL_CARD_COLORS.mixed_goals;
              return (
                <div key={l.label_id} className={`border rounded-lg p-3 ${c.border} ${c.bg}`}>
                  <p className={`font-semibold text-sm mb-1 ${c.text}`}>{l.label_name}</p>
                  <p className="text-xs text-gray-600 mb-2">{l.description}</p>
                  <div className="text-xs space-y-1">
                    {l.threshold_pct != null && <div><span className="text-gray-500">Threshold: </span><span className="font-mono font-semibold">{l.threshold_pct}% qualifying assets</span></div>}
                    {l.qualifying_assets_definition && <div><span className="text-gray-500">Definition: </span><span>{l.qualifying_assets_definition}</span></div>}
                    {(l.key_criteria || []).length > 0 && (
                      <div className="mt-1">
                        <p className="text-gray-500 font-medium">Key criteria:</p>
                        <ul className="mt-0.5 space-y-0.5 pl-2">
                          {l.key_criteria.map((k, i) => <li key={i} className={c.text}>- {k}</li>)}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
          <p className="text-[10px] text-gray-400">Effective: {labels.effective_date}</p>
        </Section>
      )}
      {agr && (
        <Section title={`Anti-Greenwashing Rule - ${agr.total} Requirements (${agr.blocking} Blocking) - Effective ${agr.effective_date}`}>
          <table className="w-full text-xs">
            <thead><tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="pb-2 font-medium w-16">ID</th><th className="pb-2 font-medium">Requirement</th>
              <th className="pb-2 font-medium w-20">Blocking</th><th className="pb-2 font-medium">Source</th>
            </tr></thead>
            <tbody>
              {(agr.requirements || []).map(r => (
                <tr key={r.req_id} className="border-b border-gray-50">
                  <td className="py-1.5 font-mono text-gray-500">{r.req_id}</td>
                  <td className="py-1.5">{r.title}</td>
                  <td className="py-1.5">{r.blocking ? <Badge label="Blocking" color="red" /> : <Badge label="Advisory" color="gray" />}</td>
                  <td className="py-1.5 text-gray-400 text-[10px]">{r.source || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="text-[10px] text-gray-400 mt-2">{agr.reference}</p>
        </Section>
      )}
    </div>
  );
}

function CrossFrameworkTab() {
  const [fw, setFw] = useState(null);
  const [tl, setTl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    Promise.all([axios.get(`${API}/api/v1/uk-sdr/ref/cross-framework`), axios.get(`${API}/api/v1/uk-sdr/ref/timeline`)])
      .then(([f, t]) => { setFw(f.data); setTl(t.data); })
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading...</div>;
  if (err) return <ErrBox msg={err} />;

  return (
    <div>
      {fw && (
        <Section title="SDR - SFDR / ISSB S1-S2 / EU Taxonomy Cross-Mapping">
          {fw.note && <p className="text-xs text-gray-500 mb-3 italic">{fw.note}</p>}
          <table className="w-full text-xs mb-4">
            <thead><tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="pb-2 font-medium">Framework</th><th className="pb-2 font-medium">SDR Equivalent</th>
              <th className="pb-2 font-medium">Alignment</th><th className="pb-2 font-medium">Notes</th>
            </tr></thead>
            <tbody>
              {(fw.mappings || []).map((m, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-1.5 font-semibold">{m.framework}</td>
                  <td className="py-1.5 text-gray-600">{m.sdr_equivalent || m.label_equivalent || m.sdr_label || '-'}</td>
                  <td className="py-1.5">
                    <Badge label={m.alignment_level || m.similarity || 'Partial'} color={{ high: 'green', medium: 'blue', low: 'amber' }[m.alignment_level] || 'gray'} />
                  </td>
                  <td className="py-1.5 text-gray-500 text-[10px]">{m.notes || m.note || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="grid grid-cols-2 gap-3">
            {fw.uk_taxonomy_status && (
              <div className="bg-blue-50 border border-blue-200 rounded p-2.5 text-xs">
                <span className="font-semibold text-blue-700">UK Green Taxonomy: </span>
                <span className="text-gray-600">{fw.uk_taxonomy_status}</span>
              </div>
            )}
            {fw.issb_srs_status && (
              <div className="bg-purple-50 border border-purple-200 rounded p-2.5 text-xs">
                <span className="font-semibold text-purple-700">UK SRS / ISSB: </span>
                <span className="text-gray-600">{fw.issb_srs_status}</span>
              </div>
            )}
          </div>
        </Section>
      )}
      {tl && (
        <Section title={`SDR Regulatory Timeline - ${tl.regime}`}>
          <div className="space-y-2 mb-4">
            {(tl.milestones || []).map((m, i) => (
              <div key={i} className="flex items-start gap-3">
                <div className="shrink-0 mt-0.5"><Badge label={m.date} color="blue" /></div>
                <p className="text-xs text-gray-700">{m.event}</p>
              </div>
            ))}
          </div>
          {tl.scope && (
            <div className="grid grid-cols-3 gap-3 text-xs">
              <div className="bg-emerald-50 border border-emerald-200 rounded p-2.5">
                <p className="font-semibold text-emerald-700 mb-1">In Scope</p>
                <p className="text-gray-600">{tl.scope.in_scope}</p>
              </div>
              <div className="bg-red-50 border border-red-200 rounded p-2.5">
                <p className="font-semibold text-red-700 mb-1">Out of Scope</p>
                <p className="text-gray-600">{tl.scope.out_of_scope}</p>
              </div>
              <div className="bg-amber-50 border border-amber-200 rounded p-2.5">
                <p className="font-semibold text-amber-700 mb-1">Overseas Extension</p>
                <p className="text-gray-600">{tl.scope.overseas_extension}</p>
              </div>
            </div>
          )}
          {tl.reference && <p className="text-[10px] text-gray-400 mt-3">{tl.reference}</p>}
        </Section>
      )}
    </div>
  );
}

const TABS = [
  { id: 'assess',          label: 'SDR Assessment' },
  { id: 'agr',             label: 'AGR Checker' },
  { id: 'batch',           label: 'Batch Assessment' },
  { id: 'labels',          label: 'Label Reference' },
  { id: 'cross-framework', label: 'Cross-Framework' },
];

export default function UKSDRPage() {
  const [tab, setTab] = useState('assess');
  return (
    <div className="p-4 max-w-6xl mx-auto">
      <DemoBanner />
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">UK SDR - Sustainability Disclosure Requirements</h1>
          <Badge label="FCA PS 23/16" color="blue" />
          <Badge label="E11" color="gray" />
        </div>
        <p className="text-xs text-gray-500">
          4 Investment Labels - Anti-Greenwashing Rule (10 requirements, 6 blocking) - Naming and Marketing Requirements - ICIS Proxy Score - SDR / SFDR / ISSB / EU Taxonomy Cross-Framework
        </p>
      </div>
      <div className="flex gap-1 mb-4 border-b border-gray-200">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-2 text-xs font-medium rounded-t transition-colors ${tab === t.id ? 'bg-black text-white' : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'}`}>
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'assess'          && <SDRAssessmentTab />}
      {tab === 'agr'             && <AGRCheckerTab />}
      {tab === 'batch'           && <BatchTab />}
      {tab === 'labels'          && <LabelReferenceTab />}
      {tab === 'cross-framework' && <CrossFrameworkTab />}
    </div>
  );
}
