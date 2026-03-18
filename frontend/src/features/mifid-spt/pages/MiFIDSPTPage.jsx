/**
 * MiFIDSPTPage.jsx — Route: /mifid-spt
 * MiFID II Sustainability Preferences Test (SPT)
 * ESMA Guidelines on Sustainability Preferences — Art. 54/54a MiFID II Delegated Regulation
 */
import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';

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
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>;
}

function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <span className="text-xs text-gray-500 w-48 shrink-0">{label}</span>
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

const DEMO_PRODUCTS = [
  { product_id: 'P001', product_name: 'EU Climate Focus Fund',     article: 'art_9', taxonomy_pct: 45, sfdr_pct: 80, has_pais: true },
  { product_id: 'P002', product_name: 'Global ESG Bond',           article: 'art_8', taxonomy_pct: 8,  sfdr_pct: 20, has_pais: true },
  { product_id: 'P003', product_name: 'Standard Equity Fund',      article: 'art_6', taxonomy_pct: 0,  sfdr_pct: 0,  has_pais: false },
];

const DEFAULT_PREFS = {
  client_id: 'CLIENT-001',
  preference_category_a_min_pct: 30,
  preference_category_b_min_pct: 20,
  preference_category_c: true,
  investor_type: 'retail',
  risk_profile: 'balanced',
};

const BATCH_CLIENTS = [
  { client_id: 'C001', client_name: 'Anne Martinez',    preference_category_a_min_pct: 40, preference_category_b_min_pct: 30, preference_category_c: true,  investor_type: 'retail',       risk_profile: 'growth' },
  { client_id: 'C002', client_name: 'Thomas Becker',    preference_category_a_min_pct: 20, preference_category_b_min_pct: 10, preference_category_c: false, investor_type: 'professional', risk_profile: 'balanced' },
  { client_id: 'C003', client_name: 'Ingrid Svensson',  preference_category_a_min_pct: 0,  preference_category_b_min_pct: 0,  preference_category_c: false, investor_type: 'retail',       risk_profile: 'conservative' },
];

// ── Tab 1: SPT Assessment ────────────────────────────────────────────────────
function SPTAssessmentTab() {
  const [prefs, setPrefs] = useState(DEFAULT_PREFS);
  const [products] = useState(DEMO_PRODUCTS);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);
  const set = useCallback((k, v) => setPrefs(f => ({ ...f, [k]: v })), []);

  const run = async () => {
    setLoading(true); setErr(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/mifid-spt/assess`, {
        client_preferences: prefs, products,
      });
      setResult(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Section title="Client Sustainability Preferences">
        <div className="grid grid-cols-2 gap-x-8">
          <div>
            <Row label="Client ID"><Inp value={prefs.client_id} onChange={v => set('client_id', v)} /></Row>
            <Row label="Investor Type">
              <Sel value={prefs.investor_type} onChange={v => set('investor_type', v)}
                options={[{ value: 'retail', label: 'Retail' }, { value: 'professional', label: 'Professional' }]} />
            </Row>
            <Row label="Risk Profile">
              <Sel value={prefs.risk_profile} onChange={v => set('risk_profile', v)}
                options={[{ value: 'conservative', label: 'Conservative' }, { value: 'balanced', label: 'Balanced' }, { value: 'growth', label: 'Growth' }]} />
            </Row>
            <Row label={`Category A min % (${prefs.preference_category_a_min_pct}%)`}>
              <input type="range" min="0" max="100" value={prefs.preference_category_a_min_pct}
                onChange={e => set('preference_category_a_min_pct', parseInt(e.target.value))}
                className="w-full accent-emerald-600" />
            </Row>
            <Row label={`Category B min % (${prefs.preference_category_b_min_pct}%)`}>
              <input type="range" min="0" max="100" value={prefs.preference_category_b_min_pct}
                onChange={e => set('preference_category_b_min_pct', parseInt(e.target.value))}
                className="w-full accent-emerald-600" />
            </Row>
          </div>
          <div className="space-y-3 pt-1">
            <Chk checked={prefs.preference_category_c} onChange={v => set('preference_category_c', v)}
              label="Category C — Considers PAI (Principal Adverse Impacts)" />
            <div className="bg-blue-50 border border-blue-200 rounded p-2.5 text-xs text-blue-700">
              <p className="font-semibold mb-1">Category Definitions</p>
              <p><strong>A:</strong> EU Taxonomy-aligned investments (min % of portfolio)</p>
              <p><strong>B:</strong> SFDR-sustainable investments (Art. 2(17) SFDR)</p>
              <p><strong>C:</strong> Considers Principal Adverse Impacts on sustainability factors</p>
            </div>
          </div>
        </div>
        <div className="mt-4"><Btn onClick={run} loading={loading}>Run SPT Assessment</Btn></div>
      </Section>

      <Section title="Demo Product Universe">
        <table className="w-full text-xs">
          <thead><tr className="text-left text-gray-500 border-b border-gray-100">
            <th className="pb-2 font-medium">Product</th>
            <th className="pb-2 font-medium">SFDR Article</th>
            <th className="pb-2 font-medium">EU Taxonomy %</th>
            <th className="pb-2 font-medium">SFDR Sustainable %</th>
            <th className="pb-2 font-medium">PAIs Considered</th>
          </tr></thead>
          <tbody>
            {products.map(p => (
              <tr key={p.product_id} className="border-b border-gray-50">
                <td className="py-1.5 font-medium">{p.product_name}</td>
                <td className="py-1.5"><Badge label={p.article.replace('_', ' ').toUpperCase()} color={p.article === 'art_9' ? 'green' : p.article === 'art_8' ? 'blue' : 'gray'} /></td>
                <td className="py-1.5 font-mono">{p.taxonomy_pct}%</td>
                <td className="py-1.5 font-mono">{p.sfdr_pct}%</td>
                <td className="py-1.5">{p.has_pais ? <Badge label="Yes" color="green" /> : <Badge label="No" color="gray" />}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>

      {err && <ErrBox msg={err} />}

      {result && (
        <>
          <div className="grid grid-cols-3 gap-3 mb-4">
            <KpiCard label="Match Rate" value={`${(result.match_rate_pct ?? 0).toFixed(1)}%`}
              color={result.match_rate_pct >= 66 ? 'text-emerald-700' : result.match_rate_pct >= 33 ? 'text-amber-700' : 'text-red-600'}
              sub={`${result.matched_count} / ${result.total_products} products matched`} />
            <KpiCard label="Client" value={result.client_id || prefs.client_id} sub={`${prefs.investor_type} · ${prefs.risk_profile}`} />
            <KpiCard label="Adjustment" value={result.adjustment_recommended ? 'Recommended' : 'Not Required'}
              color={result.adjustment_recommended ? 'text-amber-700' : 'text-emerald-700'} />
          </div>

          {result.adjustment_recommended && (
            <div className="bg-amber-50 border border-amber-200 rounded p-3 mb-4 text-xs text-amber-800">
              <p className="font-semibold mb-1">Preference Adjustment Recommended</p>
              <p>{result.adjustment_note || 'Current preferences cannot be satisfied by available products. Consider adjusting minimum thresholds or broadening product universe.'}</p>
            </div>
          )}

          <Section title="Product Match Results">
            <table className="w-full text-xs">
              <thead><tr className="text-left text-gray-500 border-b border-gray-100">
                <th className="pb-2 font-medium">Product</th>
                <th className="pb-2 font-medium">Cat A</th>
                <th className="pb-2 font-medium">Cat B</th>
                <th className="pb-2 font-medium">Cat C</th>
                <th className="pb-2 font-medium">Score</th>
                <th className="pb-2 font-medium">Match</th>
              </tr></thead>
              <tbody>
                {(result.product_results || []).map(p => (
                  <tr key={p.product_id} className="border-b border-gray-50">
                    <td className="py-2 font-medium">{p.product_name}</td>
                    <td className="py-2">{p.category_a_met ? <Badge label="✓" color="green" /> : <Badge label="✗" color="red" />}</td>
                    <td className="py-2">{p.category_b_met ? <Badge label="✓" color="green" /> : <Badge label="✗" color="red" />}</td>
                    <td className="py-2">{p.category_c_met ? <Badge label="✓" color="green" /> : <Badge label="✗" color="red" />}</td>
                    <td className="py-2 font-mono">{(p.match_score ?? 0).toFixed(0)}/100</td>
                    <td className="py-2">
                      <Badge label={p.overall_match ? 'MATCH' : 'NO MATCH'}
                        color={p.overall_match ? 'green' : 'red'} />
                    </td>
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

// ── Tab 2: Suitability Report ────────────────────────────────────────────────
function SuitabilityReportTab() {
  const [form] = useState({ client_id: 'CLIENT-001', ...DEFAULT_PREFS });
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const generate = async () => {
    setLoading(true); setErr(null); setReport(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/mifid-spt/suitability-report`, {
        client_id: form.client_id,
        client_preferences: DEFAULT_PREFS,
        products: DEMO_PRODUCTS,
      });
      setReport(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  const SECTION_KEYS = [
    { key: 'client_summary',       label: 'Client Summary' },
    { key: 'preference_summary',   label: 'Preference Summary' },
    { key: 'match_summary',        label: 'Match Summary' },
    { key: 'recommendation_text',  label: 'Recommendation' },
    { key: 'disclosure_statement', label: 'Disclosure Statement' },
  ];

  return (
    <div>
      <Section title="Generate Suitability Report">
        <p className="text-xs text-gray-500 mb-3">
          Generates a structured MiFID II suitability report capturing client sustainability preferences and product match outcome per ESMA Guidelines on Art. 54a.
        </p>
        <Btn onClick={generate} loading={loading}>Generate Suitability Report</Btn>
      </Section>

      {err && <ErrBox msg={err} />}

      {report && (
        <>
          <div className="flex items-center gap-3 mb-4">
            <Badge label={`Report: ${report.report_id || 'SR-001'}`} color="blue" />
            <Badge label={`Date: ${report.generated_at ? new Date(report.generated_at).toLocaleDateString() : new Date().toLocaleDateString()}`} color="gray" />
            <Badge label={`Client: ${report.client_id || 'CLIENT-001'}`} color="gray" />
          </div>
          <div className="space-y-3">
            {SECTION_KEYS.map(({ key, label }) => report[key] && (
              <div key={key} className="bg-white border border-gray-200 rounded-lg border-l-4 border-l-emerald-500 p-4">
                <p className="text-xs font-semibold text-gray-700 mb-2 uppercase tracking-wider">{label}</p>
                <p className="text-xs text-gray-600 leading-relaxed">
                  {typeof report[key] === 'string' ? report[key] : JSON.stringify(report[key], null, 2)}
                </p>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

// ── Tab 3: Batch Assessment ──────────────────────────────────────────────────
function BatchAssessmentTab() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  const run = async () => {
    setLoading(true); setErr(null); setResult(null);
    try {
      const payload = BATCH_CLIENTS.map(c => ({
        client_preferences: c, products: DEMO_PRODUCTS,
      }));
      const { data } = await axios.post(`${API}/api/v1/mifid-spt/assess/batch`, { assessments: payload });
      setResult(data);
    } catch (e) { setErr(e?.response?.data?.detail || e.message); }
    finally { setLoading(false); }
  };

  return (
    <div>
      <Section title="Batch Demo — 3 Clients">
        <p className="text-xs text-gray-500 mb-3">
          Three clients with varied sustainability preferences assessed against the same product universe.
        </p>
        <table className="w-full text-xs mb-4">
          <thead><tr className="text-left text-gray-500 border-b border-gray-100">
            <th className="pb-2 font-medium">Client</th>
            <th className="pb-2 font-medium">Type</th>
            <th className="pb-2 font-medium">Profile</th>
            <th className="pb-2 font-medium">Cat A min</th>
            <th className="pb-2 font-medium">Cat B min</th>
            <th className="pb-2 font-medium">Cat C</th>
          </tr></thead>
          <tbody>
            {BATCH_CLIENTS.map(c => (
              <tr key={c.client_id} className="border-b border-gray-50">
                <td className="py-1.5 font-medium">{c.client_name}</td>
                <td className="py-1.5"><Badge label={c.investor_type} color={c.investor_type === 'professional' ? 'blue' : 'gray'} /></td>
                <td className="py-1.5"><Badge label={c.risk_profile} color={c.risk_profile === 'growth' ? 'green' : c.risk_profile === 'balanced' ? 'blue' : 'gray'} /></td>
                <td className="py-1.5 font-mono">{c.preference_category_a_min_pct}%</td>
                <td className="py-1.5 font-mono">{c.preference_category_b_min_pct}%</td>
                <td className="py-1.5">{c.preference_category_c ? <Badge label="Yes" color="green" /> : <Badge label="No" color="gray" />}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <Btn onClick={run} loading={loading}>Run Batch Assessment</Btn>
      </Section>

      {err && <ErrBox msg={err} />}

      {result && (
        <Section title="Batch Results">
          <table className="w-full text-xs">
            <thead><tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="pb-2 font-medium">Client</th>
              <th className="pb-2 font-medium">Match Rate</th>
              <th className="pb-2 font-medium">Matched / Total</th>
              <th className="pb-2 font-medium">Adjustment Flag</th>
            </tr></thead>
            <tbody>
              {(result.results || result.assessments || []).map((r, i) => {
                const name = BATCH_CLIENTS[i]?.client_name || r.client_id || `Client ${i + 1}`;
                const matchRate = r.match_rate_pct ?? r.match_rate ?? 0;
                return (
                  <tr key={i} className="border-b border-gray-50">
                    <td className="py-2 font-medium">{name}</td>
                    <td className="py-2 font-mono">{matchRate.toFixed(1)}%</td>
                    <td className="py-2 font-mono">{r.matched_count ?? '-'} / {r.total_products ?? DEMO_PRODUCTS.length}</td>
                    <td className="py-2">
                      {r.adjustment_recommended
                        ? <Badge label="Adjustment Recommended" color="amber" />
                        : <Badge label="No Adjustment" color="green" />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Section>
      )}
    </div>
  );
}

// ── Tab 4: Preference Categories ─────────────────────────────────────────────
function PreferenceCategoriesTab() {
  const [cats, setCats] = useState(null);
  const [process, setProcess] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/v1/mifid-spt/ref/preference-categories`),
      axios.get(`${API}/api/v1/mifid-spt/ref/suitability-process`),
    ])
      .then(([c, p]) => { setCats(c.data); setProcess(p.data); })
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading reference data...</div>;
  if (err) return <ErrBox msg={err} />;

  const CAT_COLORS = { A: 'emerald', B: 'blue', C: 'purple' };

  return (
    <div>
      {cats && (
        <Section title="MiFID II Sustainability Preference Categories">
          <div className="grid grid-cols-3 gap-4 mb-2">
            {(cats.categories || []).map(cat => {
              const color = CAT_COLORS[cat.category_id] || 'gray';
              const bg = { emerald: 'bg-emerald-50 border-emerald-200', blue: 'bg-blue-50 border-blue-200', purple: 'bg-purple-50 border-purple-200' }[color] || 'bg-gray-50 border-gray-200';
              const text = { emerald: 'text-emerald-700', blue: 'text-blue-700', purple: 'text-purple-700' }[color] || 'text-gray-700';
              return (
                <div key={cat.category_id} className={`border rounded-lg p-3 ${bg}`}>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge label={`Category ${cat.category_id}`} color={color} />
                    <span className={`text-xs font-semibold ${text}`}>{cat.name}</span>
                  </div>
                  <p className="text-xs text-gray-600 mb-2">{cat.description}</p>
                  {cat.measurement && (
                    <p className="text-[10px] text-gray-500"><span className="font-medium">Measurement:</span> {cat.measurement}</p>
                  )}
                  {cat.regulation_reference && (
                    <p className="text-[10px] text-gray-400 mt-1">{cat.regulation_reference}</p>
                  )}
                </div>
              );
            })}
          </div>
        </Section>
      )}

      {process && (
        <Section title="MiFID II Suitability Assessment Process (5 Steps)">
          <div className="space-y-3">
            {(process.steps || []).map((step, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="shrink-0 w-8 h-8 rounded-full bg-black text-white flex items-center justify-center text-xs font-bold">
                  {i + 1}
                </div>
                <div className="flex-1 border-b border-gray-100 pb-3">
                  <p className="text-xs font-semibold text-gray-800 mb-0.5">{step.title || step.name}</p>
                  <p className="text-xs text-gray-500">{step.description}</p>
                  {step.regulation && <p className="text-[10px] text-gray-400 mt-0.5">{step.regulation}</p>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Tab 5: Cross-Framework ───────────────────────────────────────────────────
function CrossFrameworkTab() {
  const [fw, setFw] = useState(null);
  const [tl, setTl] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState(null);

  useEffect(() => {
    Promise.all([
      axios.get(`${API}/api/v1/mifid-spt/ref/cross-framework`),
      axios.get(`${API}/api/v1/mifid-spt/ref/timeline`),
    ])
      .then(([f, t]) => { setFw(f.data); setTl(t.data); })
      .catch(e => setErr(e?.response?.data?.detail || e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-xs text-gray-400 py-4 text-center">Loading...</div>;
  if (err) return <ErrBox msg={err} />;

  return (
    <div>
      {fw && (
        <Section title="MiFID II SPT — Cross-Framework Linkages">
          <table className="w-full text-xs mb-3">
            <thead><tr className="text-left text-gray-500 border-b border-gray-100">
              <th className="pb-2 font-medium">Framework</th>
              <th className="pb-2 font-medium">Linkage</th>
              <th className="pb-2 font-medium">Alignment</th>
              <th className="pb-2 font-medium">Notes</th>
            </tr></thead>
            <tbody>
              {(fw.mappings || []).map((m, i) => (
                <tr key={i} className="border-b border-gray-50">
                  <td className="py-1.5 font-semibold">{m.framework}</td>
                  <td className="py-1.5 text-gray-600">{m.linkage || m.sdr_equivalent || '-'}</td>
                  <td className="py-1.5">
                    <Badge label={m.alignment_level || 'Partial'}
                      color={{ high: 'green', medium: 'blue', low: 'amber' }[m.alignment_level] || 'gray'} />
                  </td>
                  <td className="py-1.5 text-gray-500 text-[10px]">{m.notes || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Section>
      )}

      {tl && (
        <Section title="MiFID II SPT Regulatory Timeline">
          <div className="space-y-4">
            {(tl.milestones || []).map((m, i) => (
              <div key={i} className="flex items-start gap-4">
                <div className="shrink-0">
                  <Badge label={m.date} color="blue" />
                </div>
                <div className="flex-1 border-l-2 border-gray-100 pl-4 pb-2">
                  <p className="text-xs font-semibold text-gray-800">{m.event || m.title}</p>
                  {m.description && <p className="text-xs text-gray-500 mt-0.5">{m.description}</p>}
                  {m.reference && <p className="text-[10px] text-gray-400 mt-0.5">{m.reference}</p>}
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}

// ── Page Shell ───────────────────────────────────────────────────────────────
const TABS = [
  { id: 'assess',      label: 'SPT Assessment' },
  { id: 'suitability', label: 'Suitability Report' },
  { id: 'batch',       label: 'Batch Assessment' },
  { id: 'categories',  label: 'Preference Categories' },
  { id: 'cross',       label: 'Cross-Framework' },
];

export default function MiFIDSPTPage() {
  const [tab, setTab] = useState('assess');
  return (
    <div className="p-4 max-w-6xl mx-auto">
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">MiFID II Sustainability Preferences Test</h1>
          <Badge label="MiFID II Art. 54a" color="blue" />
          <Badge label="ESMA 2022" color="gray" />
        </div>
        <p className="text-xs text-gray-500">
          SPT Assessment · Category A/B/C Preferences · Suitability Report Generation · SFDR / EU Taxonomy / PAI Integration
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
      {tab === 'assess'      && <SPTAssessmentTab />}
      {tab === 'suitability' && <SuitabilityReportTab />}
      {tab === 'batch'       && <BatchAssessmentTab />}
      {tab === 'categories'  && <PreferenceCategoriesTab />}
      {tab === 'cross'       && <CrossFrameworkTab />}
    </div>
  );
}
