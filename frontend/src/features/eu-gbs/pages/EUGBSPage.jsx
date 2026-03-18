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

const TABS = ['Bond Assessment', 'GBFS Factsheet', 'Reporting', 'Standards Comparison', 'Reference'];
const ENV_OBJECTIVES = ['CCM', 'CCA', 'WMR', 'CE', 'PPE', 'BIO'];

export default function EUGBSPage() {
  const [activeTab, setActiveTab] = useState(0);

  // Bond Assessment form state
  const [bondId, setBondId] = useState('BOND-2026-001');
  const [issuerName, setIssuerName] = useState('Green Finance Corp SA');
  const [bondType, setBondType] = useState('senior_unsecured');
  const [principalAmount, setPrincipalAmount] = useState('500000000');
  const [currency, setCurrency] = useState('EUR');
  const [taxonomyAlignmentPct, setTaxonomyAlignmentPct] = useState(95);
  const [dnshConfirmed, setDnshConfirmed] = useState(true);
  const [minSafeguardsConfirmed, setMinSafeguardsConfirmed] = useState(true);
  const [envObjectives, setEnvObjectives] = useState(['CCM', 'CCA']);
  const [hasExternalReviewer, setHasExternalReviewer] = useState(true);
  const [erName, setErName] = useState('Sustainalytics');
  const [hasPreIssuanceReview, setHasPreIssuanceReview] = useState(true);
  const [isSovereign, setIsSovereign] = useState(false);

  // Assessment results
  const [assessLoading, setAssessLoading] = useState(false);
  const [assessError, setAssessError] = useState('');
  const [assessResult, setAssessResult] = useState(null);

  // Factsheet state
  const [factsheetLoading, setFactsheetLoading] = useState(false);
  const [factsheetError, setFactsheetError] = useState('');
  const [factsheetResult, setFactsheetResult] = useState(null);

  // Reporting state
  const [reportSubTab, setReportSubTab] = useState('allocation');
  const [reportingPeriod, setReportingPeriod] = useState('2025-H1');
  const [totalAllocatedPct, setTotalAllocatedPct] = useState('92');
  const [taxonomyAlignedPct, setTaxonomyAlignedPct] = useState('100');
  const [unallocatedPct, setUnallocatedPct] = useState('8');
  const [allocationCCM, setAllocationCCM] = useState(75);
  const [allocationCCA, setAllocationCCA] = useState(25);
  const [allocLoading, setAllocLoading] = useState(false);
  const [allocError, setAllocError] = useState('');
  const [allocResult, setAllocResult] = useState(null);

  const [impactPeriod, setImpactPeriod] = useState('2025-H1');
  const [co2Avoided, setCo2Avoided] = useState('12500');
  const [renewableMwh, setRenewableMwh] = useState('85000');
  const [methodologyDesc, setMethodologyDesc] = useState('GHG Protocol Corporate Standard');
  const [alignmentMaintained, setAlignmentMaintained] = useState(true);
  const [impactLoading, setImpactLoading] = useState(false);
  const [impactError, setImpactError] = useState('');
  const [impactResult, setImpactResult] = useState(null);

  // Standards comparison state
  const [stdLoading, setStdLoading] = useState(false);
  const [stdError, setStdError] = useState('');
  const [stdData, setStdData] = useState(null);

  // Reference state
  const [refLoading, setRefLoading] = useState(false);
  const [refError, setRefError] = useState('');
  const [bondTypes, setBondTypes] = useState(null);
  const [erRequirements, setErRequirements] = useState(null);
  const [timeline, setTimeline] = useState(null);

  const toggleEnvObjective = useCallback((obj) => {
    setEnvObjectives(prev =>
      prev.includes(obj) ? prev.filter(o => o !== obj) : [...prev, obj]
    );
  }, []);

  const buildFormPayload = useCallback(() => ({
    bond_id: bondId,
    issuer_name: issuerName,
    bond_type: bondType,
    principal_amount: parseFloat(principalAmount),
    currency,
    taxonomy_alignment_pct: taxonomyAlignmentPct,
    dnsh_confirmed: dnshConfirmed,
    min_safeguards_confirmed: minSafeguardsConfirmed,
    environmental_objectives: envObjectives,
    has_external_reviewer: hasExternalReviewer,
    er_name: erName,
    has_pre_issuance_review: hasPreIssuanceReview,
    is_sovereign: isSovereign,
  }), [bondId, issuerName, bondType, principalAmount, currency, taxonomyAlignmentPct,
      dnshConfirmed, minSafeguardsConfirmed, envObjectives, hasExternalReviewer,
      erName, hasPreIssuanceReview, isSovereign]);

  const handleAssess = useCallback(async () => {
    setAssessLoading(true);
    setAssessError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eu-gbs/assess-issuance`, buildFormPayload());
      setAssessResult(data);
    } catch (e) {
      setAssessError(e?.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setAssessLoading(false);
    }
  }, [buildFormPayload]);

  const handleGenerateFactsheet = useCallback(async () => {
    setFactsheetLoading(true);
    setFactsheetError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eu-gbs/generate-factsheet`, buildFormPayload());
      setFactsheetResult(data);
    } catch (e) {
      setFactsheetError(e?.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setFactsheetLoading(false);
    }
  }, [buildFormPayload]);

  const handleAllocationReport = useCallback(async () => {
    setAllocLoading(true);
    setAllocError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eu-gbs/allocation-report`, {
        bond_id: bondId,
        reporting_period: reportingPeriod,
        total_allocated_pct: parseFloat(totalAllocatedPct),
        taxonomy_aligned_pct: parseFloat(taxonomyAlignedPct),
        unallocated_pct: parseFloat(unallocatedPct),
        allocation_by_objective: { CCM: allocationCCM, CCA: allocationCCA },
      });
      setAllocResult(data);
    } catch (e) {
      setAllocError(e?.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setAllocLoading(false);
    }
  }, [bondId, reportingPeriod, totalAllocatedPct, taxonomyAlignedPct, unallocatedPct, allocationCCM, allocationCCA]);

  const handleImpactReport = useCallback(async () => {
    setImpactLoading(true);
    setImpactError('');
    try {
      const { data } = await axios.post(`${API}/api/v1/eu-gbs/impact-report`, {
        bond_id: bondId,
        reporting_period: impactPeriod,
        impact_indicators: {
          co2_avoided_tonnes: parseFloat(co2Avoided),
          renewable_mwh: parseFloat(renewableMwh),
        },
        methodology_description: methodologyDesc,
        alignment_maintained: alignmentMaintained,
      });
      setImpactResult(data);
    } catch (e) {
      setImpactError(e?.response?.data?.detail || e.message || 'Request failed');
    } finally {
      setImpactLoading(false);
    }
  }, [bondId, impactPeriod, co2Avoided, renewableMwh, methodologyDesc, alignmentMaintained]);

  useEffect(() => {
    if (activeTab === 3 && !stdData) {
      setStdLoading(true);
      setStdError('');
      axios.get(`${API}/api/v1/eu-gbs/ref/standards-comparison`)
        .then(r => setStdData(r.data))
        .catch(e => setStdError(e?.response?.data?.detail || e.message || 'Failed to load'))
        .finally(() => setStdLoading(false));
    }
  }, [activeTab, stdData]);

  useEffect(() => {
    if (activeTab === 4 && !bondTypes) {
      setRefLoading(true);
      setRefError('');
      Promise.all([
        axios.get(`${API}/api/v1/eu-gbs/ref/bond-types`),
        axios.get(`${API}/api/v1/eu-gbs/ref/er-requirements`),
        axios.get(`${API}/api/v1/eu-gbs/ref/timeline`),
      ])
        .then(([bt, er, tl]) => {
          setBondTypes(bt.data);
          setErRequirements(er.data);
          setTimeline(tl.data);
        })
        .catch(e => setRefError(e?.response?.data?.detail || e.message || 'Failed to load'))
        .finally(() => setRefLoading(false));
    }
  }, [activeTab, bondTypes]);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Page title bar */}
      <div className="bg-black text-white px-6 py-4 flex items-center gap-3">
        <span className="font-semibold text-sm">EU Green Bond Standard</span>
        <Badge label="Regulation (EU) 2023/2631" color="green" />
        <Badge label="GBFS v1.0" color="blue" />
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

        {/* TAB 0 — Bond Assessment */}
        {activeTab === 0 && (
          <div>
            <Section title="Bond Details">
              <Row label="Bond ID"><Inp value={bondId} onChange={setBondId} placeholder="BOND-2026-001" /></Row>
              <Row label="Issuer Name"><Inp value={issuerName} onChange={setIssuerName} /></Row>
              <Row label="Bond Type">
                <Sel value={bondType} onChange={setBondType} options={[
                  { value: 'senior_unsecured', label: 'Senior Unsecured' },
                  { value: 'covered_bond', label: 'Covered Bond' },
                  { value: 'sovereign', label: 'Sovereign' },
                  { value: 'high_yield', label: 'High Yield' },
                ]} />
              </Row>
              <Row label="Principal Amount"><Inp value={principalAmount} onChange={setPrincipalAmount} type="number" /></Row>
              <Row label="Currency">
                <Sel value={currency} onChange={setCurrency} options={['EUR', 'GBP', 'USD']} />
              </Row>
            </Section>

            <Section title="Taxonomy Alignment">
              <Row label={`Taxonomy Alignment (${taxonomyAlignmentPct}%)`}>
                <input type="range" min={0} max={100} step={1} value={taxonomyAlignmentPct}
                  onChange={e => setTaxonomyAlignmentPct(Number(e.target.value))}
                  className="w-full accent-emerald-600" />
              </Row>
              <Row label="DNSH Confirmed">
                <input type="checkbox" checked={dnshConfirmed} onChange={e => setDnshConfirmed(e.target.checked)}
                  className="accent-emerald-600" />
              </Row>
              <Row label="Minimum Safeguards Confirmed">
                <input type="checkbox" checked={minSafeguardsConfirmed} onChange={e => setMinSafeguardsConfirmed(e.target.checked)}
                  className="accent-emerald-600" />
              </Row>
              <Row label="Environmental Objectives">
                <div className="flex flex-wrap gap-3">
                  {ENV_OBJECTIVES.map(obj => (
                    <label key={obj} className="flex items-center gap-1 cursor-pointer">
                      <input type="checkbox" checked={envObjectives.includes(obj)}
                        onChange={() => toggleEnvObjective(obj)} className="accent-emerald-600" />
                      <span className="text-xs text-gray-700 font-medium">{obj}</span>
                    </label>
                  ))}
                </div>
              </Row>
            </Section>

            <Section title="External Review">
              <Row label="Has External Reviewer">
                <input type="checkbox" checked={hasExternalReviewer} onChange={e => setHasExternalReviewer(e.target.checked)}
                  className="accent-emerald-600" />
              </Row>
              {hasExternalReviewer && (
                <Row label="Reviewer Name"><Inp value={erName} onChange={setErName} /></Row>
              )}
              <Row label="Pre-Issuance Review">
                <input type="checkbox" checked={hasPreIssuanceReview} onChange={e => setHasPreIssuanceReview(e.target.checked)}
                  className="accent-emerald-600" />
              </Row>
              <Row label="Sovereign Issuer">
                <input type="checkbox" checked={isSovereign} onChange={e => setIsSovereign(e.target.checked)}
                  className="accent-emerald-600" />
              </Row>
            </Section>

            <div className="mb-4">
              <Btn onClick={handleAssess} disabled={assessLoading}>
                {assessLoading ? 'Assessing...' : 'Assess Issuance'}
              </Btn>
            </div>

            {assessError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-xs text-red-700">{assessError}</div>
            )}

            {assessResult && (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
                  <KpiCard
                    label="Compliance Score"
                    value={`${assessResult.compliance_score ?? '--'}%`}
                    color={(assessResult.compliance_score ?? 0) >= 75 ? 'text-emerald-700' : 'text-red-700'}
                  />
                  <KpiCard label="GBFS Completeness" value={`${assessResult.gbfs_completeness_pct ?? '--'}%`} />
                  <KpiCard label="Taxonomy Alignment" value={`${assessResult.taxonomy_alignment_pct ?? '--'}%`} />
                  <KpiCard
                    label="Overall Status"
                    value={assessResult.overall_compliant ? 'Compliant' : 'Non-Compliant'}
                    color={assessResult.overall_compliant ? 'text-emerald-700' : 'text-red-700'}
                  />
                </div>

                <Section title="Status Details">
                  <div className="flex gap-2 flex-wrap">
                    <span className="text-xs text-gray-500 self-center">Overall:</span>
                    <Badge
                      label={assessResult.overall_compliant ? 'Compliant' : 'Non-Compliant'}
                      color={assessResult.overall_compliant ? 'green' : 'red'}
                    />
                    {assessResult.dnsh_status && (
                      <>
                        <span className="text-xs text-gray-500 self-center ml-2">DNSH:</span>
                        <Badge
                          label={assessResult.dnsh_status}
                          color={assessResult.dnsh_status === 'confirmed' ? 'green' : 'red'}
                        />
                      </>
                    )}
                    {assessResult.er_status && (
                      <>
                        <span className="text-xs text-gray-500 self-center ml-2">External Review:</span>
                        <Badge
                          label={assessResult.er_status}
                          color={assessResult.er_status === 'verified' ? 'green' : 'amber'}
                        />
                      </>
                    )}
                  </div>
                </Section>

                {assessResult.blocking_gaps && assessResult.blocking_gaps.length > 0 && (
                  <Section title="Blocking Gaps">
                    {assessResult.blocking_gaps.map((gap, i) => (
                      <div key={i} className="bg-red-50 border border-red-200 rounded p-2 mb-2 text-xs text-red-700">
                        {gap}
                      </div>
                    ))}
                  </Section>
                )}

                {assessResult.priority_actions && assessResult.priority_actions.length > 0 && (
                  <Section title="Priority Actions">
                    <div className="bg-amber-50 border border-amber-200 rounded p-3">
                      <ol className="list-decimal list-inside space-y-1">
                        {assessResult.priority_actions.map((action, i) => (
                          <li key={i} className="text-xs text-amber-800">{action}</li>
                        ))}
                      </ol>
                    </div>
                  </Section>
                )}
              </>
            )}
          </div>
        )}

        {/* TAB 1 — GBFS Factsheet */}
        {activeTab === 1 && (
          <div>
            <div className="mb-4 flex items-center gap-3">
              <Btn onClick={handleGenerateFactsheet} disabled={factsheetLoading}>
                {factsheetLoading ? 'Generating...' : 'Generate Factsheet'}
              </Btn>
              <span className="text-xs text-gray-500">Uses bond details from Bond Assessment tab</span>
            </div>

            {factsheetError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 mb-4 text-xs text-red-700">{factsheetError}</div>
            )}

            {factsheetLoading && <div className="text-xs text-gray-500 py-4">Loading...</div>}

            {!factsheetResult && !factsheetLoading && !factsheetError && (
              <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-xs text-gray-400">
                Click Generate Factsheet to produce the EU GBS Green Bond Factsheet
              </div>
            )}

            {factsheetResult && (() => {
              const sectionKeys = Object.keys(factsheetResult).filter(k =>
                k.toLowerCase().includes('section') || ['general', 'use_of_proceeds', 'environmental_objectives',
                 'governance', 'reporting', 'external_review'].includes(k)
              );
              const displayKeys = sectionKeys.length > 0 ? sectionKeys : Object.keys(factsheetResult).slice(0, 5);
              return displayKeys.map((key, idx) => {
                const sectionData = factsheetResult[key];
                const sectionNum = idx + 1;
                const isUseOfProceeds = key.includes('proceed') || key.includes('2');
                const title = typeof sectionData === 'object' && sectionData?.title
                  ? `Section ${sectionNum} — ${sectionData.title}`
                  : `Section ${sectionNum} — ${key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}`;
                return (
                  <Section key={key} title={title}>
                    {isUseOfProceeds && (
                      <div className="mb-3">
                        <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                          <span>Taxonomy Alignment Progress</span>
                          <span>{taxonomyAlignmentPct}%</span>
                        </div>
                        <div className="bg-gray-100 rounded-full h-2">
                          <div
                            className="bg-emerald-500 h-2 rounded-full transition-all"
                            style={{ width: `${taxonomyAlignmentPct}%` }}
                          />
                        </div>
                      </div>
                    )}
                    {sectionData && typeof sectionData === 'object' && !Array.isArray(sectionData) &&
                      Object.entries(sectionData)
                        .filter(([k]) => k !== 'title')
                        .map(([k, v]) => (
                          <div key={k} className="flex items-start gap-3 py-1.5 border-b border-gray-50 last:border-0">
                            <span className="text-[10px] text-gray-400 w-48 shrink-0 pt-0.5 capitalize">
                              {k.replace(/_/g, ' ')}
                            </span>
                            <span className="text-xs text-gray-800 flex-1">
                              {Array.isArray(v) ? v.join(', ') : (typeof v === 'boolean' ? (v ? 'Yes' : 'No') : String(v ?? '—'))}
                            </span>
                          </div>
                        ))
                    }
                    {Array.isArray(sectionData) && (
                      <ul className="space-y-1">
                        {sectionData.map((item, i) => (
                          <li key={i} className="text-xs text-gray-700">{typeof item === 'string' ? item : JSON.stringify(item)}</li>
                        ))}
                      </ul>
                    )}
                    {typeof sectionData === 'string' && (
                      <p className="text-xs text-gray-700">{sectionData}</p>
                    )}
                  </Section>
                );
              });
            })()}
          </div>
        )}

        {/* TAB 2 — Reporting */}
        {activeTab === 2 && (
          <div>
            <div className="flex gap-1 mb-4">
              {[['allocation', 'Allocation Report'], ['impact', 'Impact Report']].map(([key, label]) => (
                <button key={key} onClick={() => setReportSubTab(key)}
                  className={`px-3 py-1.5 text-xs font-medium rounded transition-colors ${
                    reportSubTab === key
                      ? 'bg-emerald-600 text-white'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}>
                  {label}
                </button>
              ))}
            </div>

            {reportSubTab === 'allocation' && (
              <Section title="Allocation Report — Article 22 EU GBS">
                <Row label="Reporting Period"><Inp value={reportingPeriod} onChange={setReportingPeriod} /></Row>
                <Row label="Total Allocated (%)"><Inp value={totalAllocatedPct} onChange={setTotalAllocatedPct} type="number" /></Row>
                <Row label="Taxonomy Aligned (%)"><Inp value={taxonomyAlignedPct} onChange={setTaxonomyAlignedPct} type="number" /></Row>
                <Row label="Unallocated (%)"><Inp value={unallocatedPct} onChange={setUnallocatedPct} type="number" /></Row>
                <Row label={`CCM Allocation (${allocationCCM}%)`}>
                  <input type="range" min={0} max={100} step={1} value={allocationCCM}
                    onChange={e => setAllocationCCM(Number(e.target.value))}
                    className="w-full accent-emerald-600" />
                </Row>
                <Row label={`CCA Allocation (${allocationCCA}%)`}>
                  <input type="range" min={0} max={100} step={1} value={allocationCCA}
                    onChange={e => setAllocationCCA(Number(e.target.value))}
                    className="w-full accent-emerald-600" />
                </Row>
                <div className="mt-3">
                  <Btn onClick={handleAllocationReport} disabled={allocLoading}>
                    {allocLoading ? 'Submitting...' : 'Submit Allocation Report'}
                  </Btn>
                </div>
                {allocError && (
                  <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2">{allocError}</div>
                )}
                {allocResult && (
                  <div className="mt-3 space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge
                        label={allocResult.compliant ? 'Compliant' : 'Non-Compliant'}
                        color={allocResult.compliant ? 'green' : 'red'}
                      />
                      {allocResult.message && <span className="text-xs text-gray-600">{allocResult.message}</span>}
                    </div>
                    {allocResult.gaps && allocResult.gaps.length > 0 && (
                      <ul className="text-xs text-red-700 list-disc list-inside space-y-1 bg-red-50 rounded p-2">
                        {allocResult.gaps.map((g, i) => <li key={i}>{g}</li>)}
                      </ul>
                    )}
                  </div>
                )}
              </Section>
            )}

            {reportSubTab === 'impact' && (
              <Section title="Impact Report — Article 23 EU GBS">
                <Row label="Reporting Period"><Inp value={impactPeriod} onChange={setImpactPeriod} /></Row>
                <Row label="CO2 Avoided (tonnes)"><Inp value={co2Avoided} onChange={setCo2Avoided} type="number" /></Row>
                <Row label="Renewable Energy (MWh)"><Inp value={renewableMwh} onChange={setRenewableMwh} type="number" /></Row>
                <Row label="Methodology Description"><Inp value={methodologyDesc} onChange={setMethodologyDesc} /></Row>
                <Row label="Alignment Maintained">
                  <input type="checkbox" checked={alignmentMaintained}
                    onChange={e => setAlignmentMaintained(e.target.checked)}
                    className="accent-emerald-600" />
                </Row>
                <div className="mt-3">
                  <Btn onClick={handleImpactReport} disabled={impactLoading}>
                    {impactLoading ? 'Submitting...' : 'Submit Impact Report'}
                  </Btn>
                </div>
                {impactError && (
                  <div className="mt-2 text-xs text-red-700 bg-red-50 border border-red-200 rounded p-2">{impactError}</div>
                )}
                {impactResult && (
                  <div className="mt-3 flex items-center gap-2">
                    <Badge
                      label={impactResult.compliant ? 'Compliant' : 'Non-Compliant'}
                      color={impactResult.compliant ? 'green' : 'red'}
                    />
                    {impactResult.message && <span className="text-xs text-gray-600">{impactResult.message}</span>}
                  </div>
                )}
              </Section>
            )}
          </div>
        )}

        {/* TAB 3 — Standards Comparison */}
        {activeTab === 3 && (
          <div>
            {stdLoading && <div className="text-xs text-gray-500 py-4">Loading...</div>}
            {stdError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700">{stdError}</div>
            )}
            {stdData && (
              <Section title="Standards Comparison — EU GBS vs ICMA GBP vs Climate Bonds Standard">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 pr-6 text-gray-500 font-medium w-52">Feature</th>
                        <th className="text-left py-2 px-3 font-semibold">
                          <span className="text-emerald-700">EU GBS</span>
                          <span className="ml-1 text-[9px] text-emerald-400">2023/2631</span>
                        </th>
                        <th className="text-left py-2 px-3 font-semibold">
                          <span className="text-blue-700">ICMA GBP</span>
                          <span className="ml-1 text-[9px] text-blue-400">2021</span>
                        </th>
                        <th className="text-left py-2 px-3 font-semibold">
                          <span className="text-amber-700">Climate Bonds Standard</span>
                          <span className="ml-1 text-[9px] text-amber-400">v4.0</span>
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(stdData).map(([feature, values]) => {
                        const cols = Array.isArray(values)
                          ? [values[0], values[1], values[2]]
                          : [values.eu_gbs ?? values.eu ?? values, values.icma_gbp ?? values.icma ?? '—', values.climate_bonds ?? values.cbs ?? '—'];
                        const colColors = ['text-emerald-700', 'text-blue-700', 'text-amber-700'];
                        return (
                          <tr key={feature} className="border-b border-gray-50 hover:bg-gray-50">
                            <td className="py-2 pr-6 text-gray-700 capitalize font-medium">
                              {feature.replace(/_/g, ' ')}
                            </td>
                            {cols.map((val, si) => {
                              const isBool = typeof val === 'boolean';
                              return (
                                <td key={si} className={`py-2 px-3 ${isBool ? colColors[si] : 'text-gray-700'}`}>
                                  {isBool ? (val ? '✓' : '✗') : (val === null || val === undefined ? '—' : String(val))}
                                </td>
                              );
                            })}
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Section>
            )}
            {!stdData && !stdLoading && !stdError && (
              <div className="bg-gray-50 border border-gray-200 rounded p-8 text-center text-xs text-gray-400">
                Fetching standards comparison data...
              </div>
            )}
          </div>
        )}

        {/* TAB 4 — Reference */}
        {activeTab === 4 && (
          <div>
            {refLoading && <div className="text-xs text-gray-500 py-4">Loading...</div>}
            {refError && (
              <div className="bg-red-50 border border-red-200 rounded p-3 text-xs text-red-700">{refError}</div>
            )}

            {bondTypes && (
              <Section title="Bond Types — Article References">
                <div className="overflow-x-auto">
                  <table className="w-full text-xs">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-2 pr-4 text-gray-500 font-medium">Type</th>
                        <th className="text-left py-2 pr-4 text-gray-500 font-medium">Name</th>
                        <th className="text-left py-2 pr-4 text-gray-500 font-medium">Article</th>
                        <th className="text-left py-2 text-gray-500 font-medium">Taxonomy Req</th>
                      </tr>
                    </thead>
                    <tbody>
                      {(Array.isArray(bondTypes)
                        ? bondTypes
                        : Object.entries(bondTypes).map(([k, v]) => ({ type: k, ...(typeof v === 'object' ? v : { name: v }) }))
                      ).map((bt, i) => (
                        <tr key={i} className="border-b border-gray-50 hover:bg-gray-50">
                          <td className="py-2 pr-4 font-mono text-gray-700 text-[11px]">{bt.type ?? bt.id ?? i + 1}</td>
                          <td className="py-2 pr-4 text-gray-800">{bt.name ?? bt.label ?? '—'}</td>
                          <td className="py-2 pr-4 text-gray-500">{bt.article ?? bt.ref ?? '—'}</td>
                          <td className="py-2">
                            <Badge
                              label={bt.taxonomy_required === false ? 'Optional' : 'Required'}
                              color={bt.taxonomy_required === false ? 'amber' : 'green'}
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Section>
            )}

            {erRequirements && (
              <Section title="External Reviewer Requirements">
                <ul className="space-y-2">
                  {(Array.isArray(erRequirements) ? erRequirements : Object.values(erRequirements)).map((req, i) => (
                    <li key={i} className="flex items-start gap-2">
                      <span className="text-emerald-600 text-sm leading-none mt-0.5">✓</span>
                      <span className="text-xs text-gray-700">
                        {typeof req === 'string'
                          ? req
                          : (req.requirement ?? req.description ?? req.text ?? JSON.stringify(req))}
                      </span>
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            {timeline && (
              <Section title="Implementation Timeline">
                <div className="space-y-4">
                  {(Array.isArray(timeline)
                    ? timeline
                    : Object.entries(timeline).map(([k, v]) => ({ date: k, ...(typeof v === 'object' ? v : { event: v }) }))
                  ).map((item, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <div className="shrink-0 pt-0.5">
                        <Badge label={item.date ?? item.year ?? `Step ${i + 1}`} color="green" />
                      </div>
                      <div className="flex-1">
                        <p className="text-xs text-gray-800">
                          {item.event ?? item.description ?? item.text ?? JSON.stringify(item)}
                        </p>
                        {item.article && (
                          <p className="text-[10px] text-gray-400 mt-0.5">{item.article}</p>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </Section>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
