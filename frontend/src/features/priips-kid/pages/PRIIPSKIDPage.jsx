import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';

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
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    yellow: 'bg-yellow-50 text-yellow-700 border-yellow-200',
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

function Inp({ value, onChange, type = 'text', placeholder = '', min, max, step }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)}
      placeholder={placeholder} min={min} max={max} step={step}
      className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-gray-200 rounded px-2 py-1 text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500">
      {options.map(o => <option key={o.value ?? o} value={o.value ?? o}>{o.label ?? o}</option>)}
    </select>
  );
}

function Btn({ onClick, children, disabled, color = 'emerald' }) {
  const c = color === 'emerald'
    ? 'bg-emerald-600 hover:bg-emerald-700 text-white'
    : 'bg-gray-100 hover:bg-gray-200 text-gray-700';
  return (
    <button onClick={onClick} disabled={disabled}
      className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${c} disabled:opacity-50`}>
      {children}
    </button>
  );
}

const TABS = ['KID Generator', 'Performance Scenarios', 'ESG Inserts', 'Cost Summary', 'Reference'];

function sriColor(sri) {
  if (sri <= 2) return 'text-emerald-700';
  if (sri <= 4) return 'text-yellow-600';
  if (sri <= 6) return 'text-orange-600';
  return 'text-red-700';
}

function sriBadgeColor(sri) {
  if (sri <= 2) return 'green';
  if (sri <= 4) return 'yellow';
  if (sri <= 6) return 'orange';
  return 'red';
}

const SCENARIO_STYLES = {
  stress:       { border: 'border-red-300',    bg: 'bg-red-50',    label: 'Stress',       bar: '#ef4444' },
  unfavourable: { border: 'border-orange-300', bg: 'bg-orange-50', label: 'Unfavourable', bar: '#f97316' },
  moderate:     { border: 'border-blue-300',   bg: 'bg-blue-50',   label: 'Moderate',     bar: '#3b82f6' },
  favourable:   { border: 'border-emerald-300',bg: 'bg-emerald-50',label: 'Favourable',   bar: '#10b981' },
};

export default function PRIIPSKIDPage() {
  const [activeTab, setActiveTab] = useState(0);

  // KID Generator form state
  const [productId, setProductId] = useState('FUND-2026-EU-001');
  const [productName, setProductName] = useState('European Equity Sustainable Fund');
  const [productType, setProductType] = useState('UCITS');
  const [isin, setIsin] = useState('LU0123456789');
  const [manufacturer, setManufacturer] = useState('Green Asset Management SA');
  const [rhpYears, setRhpYears] = useState('5');
  const [annualVolatility, setAnnualVolatility] = useState(0.18);
  const [creditQuality, setCreditQuality] = useState('investment_grade');
  const [sfdrClassification, setSfdrClassification] = useState('art_8_pai');
  const [considersPais, setConsidersPais] = useState(true);
  const [taxonomyAlignmentPct, setTaxonomyAlignmentPct] = useState(15);
  const [entryCostPct, setEntryCostPct] = useState('0');
  const [exitCostPct, setExitCostPct] = useState('0');
  const [ongoingCostPct, setOngoingCostPct] = useState('1.5');
  const [performanceFeePct, setPerformanceFeePct] = useState('0');
  const [expectedAnnualReturnPct, setExpectedAnnualReturnPct] = useState('6');

  // KID results
  const [kidLoading, setKidLoading] = useState(false);
  const [kidError, setKidError] = useState('');
  const [kidResult, setKidResult] = useState(null);

  // ESG inserts state
  const [esgLoading, setEsgLoading] = useState(false);
  const [esgError, setEsgError] = useState('');
  const [esgInserts, setEsgInserts] = useState(null);

  // Reference state
  const [refLoading, setRefLoading] = useState(false);
  const [refError, setRefError] = useState('');
  const [kidSections, setKidSections] = useState(null);
  const [sriClasses, setSriClasses] = useState(null);
  const [crossFramework, setCrossFramework] = useState(null);
  const [expandedSection, setExpandedSection] = useState(null);

  const buildKidPayload = useCallback(() => ({
    product_id: productId,
    product_name: productName,
    product_type: productType,
    isin,
    manufacturer,
    rhp_years: parseInt(rhpYears, 10),
    annual_volatility: annualVolatility,
    credit_quality: creditQuality,
    sfdr_classification: sfdrClassification,
    considers_pais: considersPais,
    taxonomy_alignment_pct: taxonomyAlignmentPct,
    entry_cost_pct: parseFloat(entryCostPct),
    exit_cost_pct: parseFloat(exitCostPct),
    ongoing_cost_pct: parseFloat(ongoingCostPct),
    performance_fee_pct: parseFloat(performanceFeePct),
    expected_annual_return_pct: parseFloat(expectedAnnualReturnPct),
  }), [productId, productName, productType, isin, manufacturer, rhpYears, annualVolatility,
      creditQuality, sfdrClassification, considersPais, taxonomyAlignmentPct,
      entryCostPct, exitCostPct, ongoingCostPct, performanceFeePct, expectedAnnualReturnPct]);

  const handleGenerateKID = useCallback(async () => {
    setKidLoading(true);
    setKidError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/priips-kid/generate-kid`, buildKidPayload());
      setKidResult(data);
    } catch (e) {
      setKidError(e?.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setKidLoading(false);
    }
  }, [buildKidPayload]);

  const handleLoadESGInserts = useCallback(async () => {
    setEsgLoading(true);
    setEsgError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/priips-kid/esg-inserts`, {
        sfdr_classification: sfdrClassification,
      });
      setEsgInserts(data);
    } catch (e) {
      setEsgError(e?.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setEsgLoading(false);
    }
  }, [sfdrClassification]);

  useEffect(() => {
    if (activeTab === 4 && !kidSections) {
      setRefLoading(true);
      setRefError('');
      Promise.all([
        axios.get(`${API}/api/v1/priips-kid/ref/kid-sections`),
        axios.get(`${API}/api/v1/priips-kid/ref/sri-classes`),
        axios.get(`${API}/api/v1/priips-kid/ref/cross-framework`),
      ])
        .then(([ks, sc, cf]) => {
          setKidSections(ks.data);
          setSriClasses(sc.data);
          setCrossFramework(cf.data);
        })
        .catch(e => setRefError(e?.response?.data?.detail || e.message || 'Failed to load'))
        .finally(() => setRefLoading(false));
    }
  }, [activeTab, kidSections]);

  // Derived cost data for charts
  const costChartData = [
    { name: 'Entry',       value: parseFloat(entryCostPct) || 0 },
    { name: 'Ongoing',     value: parseFloat(ongoingCostPct) || 0 },
    { name: 'Exit',        value: parseFloat(exitCostPct) || 0 },
    { name: 'Performance', value: parseFloat(performanceFeePct) || 0 },
    { name: 'Transaction', value: kidResult?.cost_summary?.transaction_cost_pct ?? 0 },
  ];

  const performanceScenarios = kidResult?.performance_scenarios ?? null;
  const costSummary = kidResult?.cost_summary ?? null;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page title bar */}
      <div className="bg-black text-white px-6 py-4 flex items-center gap-3">
        <span className="font-semibold text-sm">PRIIPs KID ESG</span>
        <Badge label="Regulation (EU) 1286/2014" color="blue" />
        <Badge label="PRIIPs RTS" color="purple" />
        <Badge label="ESG Amendments" color="green" />
      </div>

      {/* Tab bar */}
      <div className="bg-white border-b border-gray-200 px-6">
        <div className="flex gap-0">
          {TABS.map((t, i) => (
            <button
              key={t}
              onClick={() => setActiveTab(i)}
              className={`px-4 py-3 text-xs font-medium border-b-2 transition-colors ${
                activeTab === i
                  ? 'border-emerald-600 text-emerald-700'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              {t}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 max-w-5xl mx-auto">

        {/* TAB 0 — KID Generator */}
        {activeTab === 0 && (
          <div>
            <Section title="Product Details">
              <Row label="Product ID"><Inp value={productId} onChange={setProductId} /></Row>
              <Row label="Product Name"><Inp value={productName} onChange={setProductName} /></Row>
              <Row label="Product Type">
                <Sel value={productType} onChange={setProductType} options={[
                  { value: 'UCITS', label: 'UCITS Fund' },
                  { value: 'AIF', label: 'AIF' },
                  { value: 'structured_product', label: 'Structured Product' },
                  { value: 'ibip', label: 'Insurance-Based Investment Product' },
                ]} />
              </Row>
              <Row label="ISIN"><Inp value={isin} onChange={setIsin} /></Row>
              <Row label="Manufacturer"><Inp value={manufacturer} onChange={setManufacturer} /></Row>
              <Row label="Recommended Holding Period (yrs)">
                <Inp value={rhpYears} onChange={setRhpYears} type="number" min="1" max="10" />
              </Row>
            </Section>

            <Section title="Risk Parameters">
              <Row label={`Annual Volatility (${(annualVolatility * 100).toFixed(0)}%)`}>
                <input type="range" min={0} max={1} step={0.01} value={annualVolatility}
                  onChange={e => setAnnualVolatility(Number(e.target.value))}
                  className="w-full accent-emerald-600" />
              </Row>
              <Row label="Credit Quality">
                <Sel value={creditQuality} onChange={setCreditQuality} options={[
                  { value: 'investment_grade', label: 'Investment Grade' },
                  { value: 'sub_investment_grade', label: 'Sub-Investment Grade' },
                  { value: 'unrated', label: 'Unrated' },
                ]} />
              </Row>
            </Section>

            <Section title="ESG Classification">
              <Row label="SFDR Classification">
                <Sel value={sfdrClassification} onChange={setSfdrClassification} options={[
                  { value: 'art_6', label: 'Art. 6 — No ESG' },
                  { value: 'art_8', label: 'Art. 8 — ESG Characteristics' },
                  { value: 'art_8_pai', label: 'Art. 8 + PAI' },
                  { value: 'art_8_taxonomy', label: 'Art. 8 + Taxonomy' },
                  { value: 'art_9', label: 'Art. 9 — Sustainable Investment' },
                ]} />
              </Row>
              <Row label="Considers PAIs">
                <input type="checkbox" checked={considersPais} onChange={e => setConsidersPais(e.target.checked)}
                  className="accent-emerald-600" />
              </Row>
              <Row label={`Taxonomy Alignment (${taxonomyAlignmentPct}%)`}>
                <input type="range" min={0} max={100} step={1} value={taxonomyAlignmentPct}
                  onChange={e => setTaxonomyAlignmentPct(Number(e.target.value))}
                  className="w-full accent-emerald-600" />
              </Row>
            </Section>

            <Section title="Costs">
              <Row label="Entry Cost (%)"><Inp value={entryCostPct} onChange={setEntryCostPct} type="number" step="0.1" /></Row>
              <Row label="Exit Cost (%)"><Inp value={exitCostPct} onChange={setExitCostPct} type="number" step="0.1" /></Row>
              <Row label="Ongoing Cost (%)"><Inp value={ongoingCostPct} onChange={setOngoingCostPct} type="number" step="0.1" /></Row>
              <Row label="Performance Fee (%)"><Inp value={performanceFeePct} onChange={setPerformanceFeePct} type="number" step="0.1" /></Row>
              <Row label="Expected Annual Return (%)"><Inp value={expectedAnnualReturnPct} onChange={setExpectedAnnualReturnPct} type="number" step="0.5" /></Row>
            </Section>

            <div className="mb-4">
              <Btn onClick={handleGenerateKID} disabled={kidLoading}>
                {kidLoading ? 'Generating KID...' : 'Generate KID'}
              </Btn>
            </div>

            {kidError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-xs text-red-700">{kidError}</div>
            )}

            {kidResult && (
              <>
                <Section title="Summary Risk Indicator">
                  <div className="flex items-center gap-4 mb-3">
                    <div className="text-center">
                      <p className="text-[10px] text-gray-500 mb-1">SRI CLASS</p>
                      <p className={`text-5xl font-bold font-mono ${sriColor(kidResult.final_sri ?? 3)}`}>
                        {kidResult.final_sri ?? '—'}
                      </p>
                      <p className="text-[10px] text-gray-500 mt-1">out of 7</p>
                    </div>
                    <div className="flex-1">
                      <p className="text-xs text-gray-700 mb-1">
                        {kidResult.sri_description ?? `SRI ${kidResult.final_sri}: This number is indicative of the risk and reward of this product.`}
                      </p>
                      <Badge label={`SRI ${kidResult.final_sri}`} color={sriBadgeColor(kidResult.final_sri ?? 3)} />
                    </div>
                  </div>
                  <div className="mb-2">
                    <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                      <span>KID Completeness</span>
                      <span>{kidResult.kid_completeness_pct ?? 0}%</span>
                    </div>
                    <div className="bg-gray-100 rounded-full h-2">
                      <div
                        className="bg-emerald-500 h-2 rounded-full transition-all"
                        style={{ width: `${kidResult.kid_completeness_pct ?? 0}%` }}
                      />
                    </div>
                  </div>
                </Section>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <KpiCard
                    label="SRI"
                    value={kidResult.final_sri ?? '—'}
                    sub="Summary Risk Indicator"
                    color={sriColor(kidResult.final_sri ?? 3)}
                  />
                  <KpiCard
                    label="KID Completeness"
                    value={`${kidResult.kid_completeness_pct ?? '--'}%`}
                    color={(kidResult.kid_completeness_pct ?? 0) >= 90 ? 'text-emerald-700' : 'text-amber-600'}
                  />
                  <KpiCard
                    label="Total Cost"
                    value={`${kidResult.total_cost_pct ?? costSummary?.total_cost_pct ?? '--'}%`}
                    sub="p.a."
                  />
                  <KpiCard
                    label="RIY"
                    value={`${kidResult.riy_pct ?? costSummary?.riy_pct ?? '--'}%`}
                    sub="Reduction in Yield"
                  />
                </div>

                {kidResult.validation_gaps && kidResult.validation_gaps.length > 0 && (
                  <Section title="Validation Gaps">
                    <ul className="space-y-1">
                      {kidResult.validation_gaps.map((g, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-red-700">
                          <span className="shrink-0 mt-0.5">•</span>{g}
                        </li>
                      ))}
                    </ul>
                  </Section>
                )}

                {kidResult.warnings && kidResult.warnings.length > 0 && (
                  <Section title="Warnings">
                    <ul className="space-y-1">
                      {kidResult.warnings.map((w, i) => (
                        <li key={i} className="flex items-start gap-2 text-xs text-amber-700">
                          <span className="shrink-0 mt-0.5">!</span>{w}
                        </li>
                      ))}
                    </ul>
                  </Section>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 1 — Performance Scenarios */}
        {activeTab === 1 && (
          <div>
            {!performanceScenarios && (
              <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-xs text-gray-400 mb-4">
                Generate a KID first to see performance scenarios
              </div>
            )}

            {performanceScenarios && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
                  {['stress', 'unfavourable', 'moderate', 'favourable'].map(key => {
                    const s = SCENARIO_STYLES[key];
                    const scenario = performanceScenarios[key] ?? {};
                    return (
                      <div key={key} className={`border-2 ${s.border} ${s.bg} rounded-lg p-3`}>
                        <p className="text-[10px] font-semibold uppercase tracking-wider text-gray-600 mb-2">{s.label}</p>
                        <div className="space-y-1.5">
                          <div>
                            <p className="text-[9px] text-gray-500">1-Year Return</p>
                            <p className="text-lg font-bold font-mono">
                              {scenario.return_1yr_pct != null ? `${scenario.return_1yr_pct > 0 ? '+' : ''}${scenario.return_1yr_pct.toFixed(1)}%` : '—'}
                            </p>
                          </div>
                          <div>
                            <p className="text-[9px] text-gray-500">Annualised ({rhpYears}yr)</p>
                            <p className="text-sm font-semibold font-mono">
                              {scenario.return_rhp_annualised_pct != null ? `${scenario.return_rhp_annualised_pct > 0 ? '+' : ''}${scenario.return_rhp_annualised_pct.toFixed(1)}%` : '—'}
                            </p>
                          </div>
                          <div>
                            <p className="text-[9px] text-gray-500">Final Value (€10k)</p>
                            <p className="text-sm font-semibold font-mono">
                              {scenario.final_value_10k != null ? `€${scenario.final_value_10k.toLocaleString()}` : '—'}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>

                <Section title="Scenario Comparison — Annualised Return (%)">
                  <ResponsiveContainer width="100%" height={220}>
                    <BarChart
                      data={['stress', 'unfavourable', 'moderate', 'favourable'].map(k => ({
                        name: SCENARIO_STYLES[k].label,
                        value: performanceScenarios[k]?.return_rhp_annualised_pct ?? 0,
                        fill: SCENARIO_STYLES[k].bar,
                      }))}
                      margin={{ top: 5, right: 20, left: 0, bottom: 5 }}
                    >
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                      <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
                      <Tooltip formatter={(v) => [`${v.toFixed(2)}%`, 'Annualised Return']} />
                      <Bar dataKey="value" radius={[3, 3, 0, 0]}>
                        {['stress', 'unfavourable', 'moderate', 'favourable'].map((key, index) => (
                          <Cell key={index} fill={SCENARIO_STYLES[key].bar} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </Section>
              </>
            )}
          </div>
        )}

        {/* TAB 2 — ESG Inserts */}
        {activeTab === 2 && (
          <div>
            <div className="mb-4 flex items-center gap-3">
              <Btn onClick={handleLoadESGInserts} disabled={esgLoading}>
                {esgLoading ? 'Loading...' : 'Load ESG Inserts'}
              </Btn>
              <span className="text-xs text-gray-500">
                SFDR Classification: <strong>{sfdrClassification}</strong> (set in KID Generator tab)
              </span>
            </div>

            {esgError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-xs text-red-700">{esgError}</div>
            )}

            {esgLoading && <div className="text-xs text-gray-500 py-4">Loading...</div>}

            {!esgInserts && !esgLoading && !esgError && (
              <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-xs text-gray-400">
                Click Load ESG Inserts to fetch applicable disclosure requirements
              </div>
            )}

            {esgInserts && (() => {
              const inserts = Array.isArray(esgInserts) ? esgInserts : (esgInserts.inserts ?? Object.values(esgInserts));
              const sfdrArticleBorder = (article) => {
                if (!article) return 'border-l-gray-300';
                const a = String(article).toLowerCase();
                if (a.includes('3') || a.includes('sfdr_art_3')) return 'border-l-emerald-500';
                if (a.includes('4')) return 'border-l-blue-500';
                if (a.includes('8')) return 'border-l-amber-500';
                if (a.includes('9')) return 'border-l-purple-500';
                return 'border-l-gray-300';
              };
              return (
                <>
                  <div className="mb-4">
                    <KpiCard label="Total ESG Inserts" value={inserts.length} sub="disclosure requirements" />
                  </div>
                  <div className="space-y-3">
                    {inserts.map((insert, i) => (
                      <div key={i} className={`bg-white border border-gray-200 border-l-4 ${sfdrArticleBorder(insert.sfdr_article)} rounded-lg p-4`}>
                        <div className="flex items-start justify-between gap-2 mb-2">
                          <span className="text-sm font-semibold text-gray-800">
                            {insert.insert_type ?? insert.type ?? `Insert ${i + 1}`}
                          </span>
                          <div className="flex gap-1.5 shrink-0">
                            {insert.sfdr_article && <Badge label={`SFDR ${insert.sfdr_article}`} color="blue" />}
                            <Badge
                              label={insert.required ? 'Required' : 'Optional'}
                              color={insert.required ? 'red' : 'gray'}
                            />
                          </div>
                        </div>
                        {insert.text_block && (
                          <p className="text-xs text-gray-600 italic leading-relaxed">{insert.text_block}</p>
                        )}
                        {insert.description && !insert.text_block && (
                          <p className="text-xs text-gray-600 italic leading-relaxed">{insert.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </>
              );
            })()}
          </div>
        )}

        {/* TAB 3 — Cost Summary */}
        {activeTab === 3 && (
          <div>
            {!costSummary && !kidResult && (
              <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-xs text-gray-400 mb-4">
                Generate a KID first to see the cost summary
              </div>
            )}

            <Section title="Cost Breakdown">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={costChartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tick={{ fontSize: 10 }} tickFormatter={v => `${v}%`} />
                  <Tooltip formatter={(v) => [`${v.toFixed(2)}%`, 'Cost']} />
                  <Bar dataKey="value" fill="#10b981" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>

            <Section title="Cost Table">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-2 text-gray-500 font-medium">Cost Type</th>
                    <th className="text-right py-2 text-gray-500 font-medium">Amount (%)</th>
                    <th className="text-left py-2 pl-4 text-gray-500 font-medium">Notes</th>
                  </tr>
                </thead>
                <tbody>
                  {[
                    { type: 'Entry Cost', value: parseFloat(entryCostPct) || 0, note: 'Paid at subscription' },
                    { type: 'Ongoing Cost', value: parseFloat(ongoingCostPct) || 0, note: 'Annual management + admin fees' },
                    { type: 'Exit Cost', value: parseFloat(exitCostPct) || 0, note: 'Paid at redemption' },
                    { type: 'Performance Fee', value: parseFloat(performanceFeePct) || 0, note: 'Charged on outperformance' },
                    { type: 'Transaction Cost', value: costSummary?.transaction_cost_pct ?? 0, note: 'Estimated portfolio turnover costs' },
                  ].map((row, i) => (
                    <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                      <td className="py-2 text-gray-700">{row.type}</td>
                      <td className="py-2 text-right font-mono text-gray-800">{row.value.toFixed(2)}%</td>
                      <td className="py-2 pl-4 text-gray-400">{row.note}</td>
                    </tr>
                  ))}
                  <tr className="border-t-2 border-gray-300 bg-gray-50 font-semibold">
                    <td className="py-2 text-gray-900">Total Cost</td>
                    <td className="py-2 text-right font-mono text-gray-900">
                      {(costSummary?.total_cost_pct ??
                        (parseFloat(entryCostPct) + parseFloat(ongoingCostPct) + parseFloat(exitCostPct) + parseFloat(performanceFeePct))
                      ).toFixed(2)}%
                    </td>
                    <td className="py-2 pl-4 text-gray-500">Combined annual equivalent</td>
                  </tr>
                  {(costSummary?.riy_pct != null) && (
                    <tr className="bg-amber-50">
                      <td className="py-2 text-amber-800 font-semibold">RIY (Reduction in Yield)</td>
                      <td className="py-2 text-right font-mono text-amber-800 font-semibold">
                        {costSummary.riy_pct.toFixed(2)}%
                      </td>
                      <td className="py-2 pl-4 text-amber-600">Over {rhpYears} year RHP</td>
                    </tr>
                  )}
                </tbody>
              </table>
              <div className="mt-3 bg-blue-50 border border-blue-200 rounded p-3 text-xs text-blue-700">
                <strong>Reduction in Yield (RIY)</strong>: shows the impact of total costs on your investment returns
                over the recommended holding period of {rhpYears} year{parseInt(rhpYears) !== 1 ? 's' : ''}.
                A lower RIY indicates a more cost-efficient product.
              </div>
            </Section>
          </div>
        )}

        {/* TAB 4 — Reference */}
        {activeTab === 4 && (
          <div>
            {refLoading && <div className="text-xs text-gray-500 py-4">Loading...</div>}
            {refError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700">{refError}</div>
            )}

            {kidSections && (
              <Section title="KID Required Sections">
                <div className="space-y-2">
                  {(Array.isArray(kidSections) ? kidSections : Object.entries(kidSections).map(([k, v]) => ({ name: k, ...(typeof v === 'object' ? v : { mandatory_fields: [v] }) }))).map((section, i) => {
                    const name = section.name ?? section.section ?? `Section ${i + 1}`;
                    const fields = section.mandatory_fields ?? section.fields ?? [];
                    const isExpanded = expandedSection === i;
                    return (
                      <div key={i} className="border border-gray-200 rounded">
                        <button
                          onClick={() => setExpandedSection(isExpanded ? null : i)}
                          className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors"
                        >
                          <span className="capitalize">{name.replace(/_/g, ' ')}</span>
                          <span className="text-gray-400">{isExpanded ? '▲' : '▼'}</span>
                        </button>
                        {isExpanded && fields.length > 0 && (
                          <div className="px-3 pb-3 pt-1 border-t border-gray-100">
                            <div className="flex flex-wrap gap-1.5">
                              {fields.map((f, fi) => (
                                <span key={fi} className="bg-emerald-50 text-emerald-700 border border-emerald-200 px-2 py-0.5 rounded text-[10px]">
                                  {f}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </Section>
            )}

            {sriClasses && (
              <Section title="SRI Classes 1–7">
                <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
                  {[1, 2, 3, 4, 5, 6, 7].map(num => {
                    const colorMap = {
                      1: 'bg-emerald-600', 2: 'bg-emerald-400', 3: 'bg-yellow-400',
                      4: 'bg-yellow-500', 5: 'bg-orange-500', 6: 'bg-orange-600', 7: 'bg-red-600',
                    };
                    return (
                      <div key={num} className="text-center shrink-0">
                        <div className={`${colorMap[num]} text-white w-8 h-8 rounded flex items-center justify-center text-sm font-bold mb-1`}>
                          {num}
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="space-y-2">
                  {(Array.isArray(sriClasses) ? sriClasses : Object.entries(sriClasses).map(([k, v]) => ({ class: k, ...(typeof v === 'object' ? v : { description: v }) }))).map((cls, i) => {
                    const classNum = cls.class ?? cls.sri_class ?? cls.number ?? (i + 1);
                    const desc = cls.description ?? cls.label ?? JSON.stringify(cls);
                    const colorMap = {
                      1: 'text-emerald-600', 2: 'text-emerald-500', 3: 'text-yellow-600',
                      4: 'text-yellow-700', 5: 'text-orange-600', 6: 'text-orange-700', 7: 'text-red-700',
                    };
                    return (
                      <div key={i} className="flex items-start gap-3">
                        <span className={`font-bold text-sm font-mono w-6 shrink-0 ${colorMap[parseInt(classNum)] ?? 'text-gray-700'}`}>
                          {classNum}
                        </span>
                        <span className="text-xs text-gray-700">{desc}</span>
                      </div>
                    );
                  })}
                </div>
              </Section>
            )}

            {crossFramework && (
              <Section title="Cross-Framework Linkages">
                <table className="w-full text-xs">
                  <thead>
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-2 pr-4 text-gray-500 font-medium">Framework</th>
                      <th className="text-left py-2 text-gray-500 font-medium">Linkage Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(Array.isArray(crossFramework)
                      ? crossFramework
                      : Object.entries(crossFramework).map(([k, v]) => ({ framework: k, description: typeof v === 'string' ? v : v.description ?? JSON.stringify(v) }))
                    ).map((item, i) => (
                      <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                        <td className="py-2 pr-4 font-medium text-gray-800">
                          {item.framework ?? item.name ?? `Framework ${i + 1}`}
                        </td>
                        <td className="py-2 text-gray-600">
                          {item.description ?? item.linkage ?? item.text ?? '—'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </Section>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
