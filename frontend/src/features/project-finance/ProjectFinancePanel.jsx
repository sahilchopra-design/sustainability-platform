/**
 * ProjectFinancePanel — DSCR / LLCR / IRR / PPA modelling for renewable energy projects.
 * Embedded in SectorAssessmentsPage under the Power Plant tab.
 * Sprint 3 — WHOOP for Sustainability platform.
 */
import React, { useState, useCallback } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine, ComposedChart,
} from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// ─────────────────────────────────────────────────────────
// Formatters
// ─────────────────────────────────────────────────────────
const fmt = {
  currency: (v, decimals = 0) =>
    v == null ? '—' : `$${Number(v).toLocaleString('en-US', { minimumFractionDigits: decimals, maximumFractionDigits: decimals })}`,
  mUSD: (v) => v == null ? '—' : `$${(v / 1e6).toFixed(1)}M`,
  pct: (v, d = 1) => v == null ? '—' : `${Number(v).toFixed(d)}%`,
  x: (v, d = 2) => v == null ? '—' : `${Number(v).toFixed(d)}x`,
  mwh: (v) => v == null ? '—' : `${(v / 1000).toFixed(0)} GWh`,
};

// ─────────────────────────────────────────────────────────
// Small UI primitives
// ─────────────────────────────────────────────────────────
const KpiCard = ({ label, value, sub, highlight, testId }) => (
  <div
    data-testid={testId}
    className={`rounded-lg p-4 border ${highlight ? 'border-cyan-500/40 bg-cyan-500/5' : 'border-white/10 bg-white/3'}`}
    style={{ fontFamily: 'IBM Plex Mono, monospace' }}
  >
    <div className="text-xs text-gray-400 mb-1">{label}</div>
    <div className="text-2xl font-bold text-white">{value}</div>
    {sub && <div className="text-xs text-gray-500 mt-1">{sub}</div>}
  </div>
);

const BankabilityBadge = ({ bankable, testId }) => (
  <div
    data-testid={testId || 'project-finance-bankable-badge'}
    className={`inline-flex items-center gap-2 px-4 py-2 rounded-full text-sm font-bold tracking-wide ${
      bankable
        ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/40'
        : 'bg-red-500/20 text-red-400 border border-red-500/40'
    }`}
  >
    <span className={`w-2 h-2 rounded-full ${bankable ? 'bg-emerald-400' : 'bg-red-400'}`} />
    {bankable ? 'BANKABLE' : 'BELOW THRESHOLD'}
  </div>
);

const SectionTitle = ({ children }) => (
  <h3 className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">{children}</h3>
);

const FormField = ({ label, children, hint }) => (
  <div className="space-y-1">
    <label className="block text-xs text-gray-400">{label}</label>
    {children}
    {hint && <p className="text-xs text-gray-600">{hint}</p>}
  </div>
);

const NumberInput = ({ value, onChange, placeholder, min, max, step = 'any' }) => (
  <input
    type="number"
    value={value}
    onChange={e => onChange(e.target.value)}
    placeholder={placeholder}
    min={min}
    max={max}
    step={step}
    className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500/60"
    style={{ fontFamily: 'IBM Plex Mono, monospace' }}
  />
);

const Toggle = ({ label, value, onChange }) => (
  <label className="flex items-center gap-3 cursor-pointer">
    <div
      className={`relative w-10 h-5 rounded-full transition-colors ${value ? 'bg-cyan-500' : 'bg-white/20'}`}
      onClick={() => onChange(!value)}
    >
      <div className={`absolute top-0.5 w-4 h-4 rounded-full bg-white transition-transform ${value ? 'translate-x-5' : 'translate-x-0.5'}`} />
    </div>
    <span className="text-sm text-gray-300">{label}</span>
  </label>
);

// ─────────────────────────────────────────────────────────
// DSCR Waterfall Chart (stacked bars + DSCR line)
// ─────────────────────────────────────────────────────────
const DSCRWaterfallChart = ({ yearByYear, loanTenor }) => {
  const data = (yearByYear || []).slice(0, loanTenor || 20).map(row => ({
    year: row.year,
    ppaRevenue: Math.round(row.ppa_revenue / 1000),
    etcRevenue: Math.round(row.etc_revenue / 1000),
    opex: -Math.round(row.opex / 1000),
    tax: -Math.round(row.tax / 1000),
    debtService: -Math.round(row.debt_service / 1000),
    dscr: row.dscr,
  }));

  return (
    <div data-testid="project-finance-waterfall-chart">
      <SectionTitle>Cash Flow Waterfall (USD '000) + DSCR</SectionTitle>
      <ResponsiveContainer width="100%" height={280}>
        <ComposedChart data={data} margin={{ top: 5, right: 30, bottom: 5, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="year" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <YAxis yAxisId="left" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <YAxis yAxisId="right" orientation="right" domain={[0, 3]} tick={{ fill: '#9ca3af', fontSize: 11 }}
            tickFormatter={v => `${v}x`} />
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
            labelStyle={{ color: '#e5e7eb' }}
            itemStyle={{ color: '#9ca3af' }}
            formatter={(v, name) => name === 'dscr' ? [`${Number(v).toFixed(2)}x`, 'DSCR'] : [`$${Math.abs(Number(v)).toLocaleString()}k`, name]}
          />
          <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11 }} />
          <Bar yAxisId="left" dataKey="ppaRevenue" stackId="a" fill="#22d3ee" name="PPA Revenue" />
          <Bar yAxisId="left" dataKey="etcRevenue" stackId="a" fill="#10b981" name="Carbon Revenue" />
          <Bar yAxisId="left" dataKey="opex" stackId="a" fill="#f59e0b" name="OPEX" />
          <Bar yAxisId="left" dataKey="tax" stackId="a" fill="#ef4444" name="Tax" />
          <Bar yAxisId="left" dataKey="debtService" stackId="a" fill="#8b5cf6" name="Debt Service" />
          <Line yAxisId="right" type="monotone" dataKey="dscr" stroke="#ffffff" strokeWidth={2}
            dot={false} name="DSCR" />
          <ReferenceLine yAxisId="right" y={1.25} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '1.25x min', fill: '#ef4444', fontSize: 10, position: 'insideTopRight' }} />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// DSCR Curve Chart (base vs stress)
// ─────────────────────────────────────────────────────────
const DSCRCurveChart = ({ baseDSCR, stressDSCR, loanTenor }) => {
  const data = (baseDSCR || []).slice(0, loanTenor || 20).map((d, i) => ({
    year: i + 1,
    base: Number(d.toFixed(2)),
    stress: stressDSCR ? Number((stressDSCR[i] || 0).toFixed(2)) : undefined,
  }));

  return (
    <div data-testid="project-finance-dscr-curve">
      <SectionTitle>DSCR by Year — Base (P50) vs Stress (P90)</SectionTitle>
      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis dataKey="year" tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `Y${v}`} />
          <YAxis domain={[0, 3]} tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `${v}x`} />
          <Tooltip
            contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
            formatter={(v, name) => [`${Number(v).toFixed(2)}x`, name === 'base' ? 'Base (P50)' : 'Stress (P90)']}
          />
          <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 11 }} />
          <ReferenceLine y={1.25} stroke="#ef4444" strokeDasharray="4 4" label={{ value: '1.25x', fill: '#ef4444', fontSize: 10, position: 'insideTopRight' }} />
          <Line type="monotone" dataKey="base" stroke="#22d3ee" strokeWidth={2} dot={false} name="Base (P50)" />
          <Line type="monotone" dataKey="stress" stroke="#f59e0b" strokeWidth={2} dot={false} strokeDasharray="5 3" name="Stress (P90)" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Financial Summary Table
// ─────────────────────────────────────────────────────────
const FinancialSummaryTable = ({ result }) => {
  if (!result) return null;
  const rows = [
    { metric: 'Minimum DSCR (P50)', base: fmt.x(result.min_dscr), stress: fmt.x(result.stress_min_dscr), testId: 'project-finance-dscr-min' },
    { metric: 'Average DSCR (P50)', base: fmt.x(result.avg_dscr), stress: '—' },
    { metric: 'LLCR', base: fmt.x(result.llcr), stress: '—' },
    { metric: 'PLCR', base: fmt.x(result.plcr), stress: '—' },
    { metric: 'Equity IRR', base: fmt.pct(result.equity_irr_pct), stress: fmt.pct(result.stress_equity_irr_pct), testId: 'project-finance-irr' },
    { metric: 'Total Debt', base: fmt.mUSD(result.total_debt_usd), stress: '—' },
    { metric: 'Total Equity', base: fmt.mUSD(result.total_equity_usd), stress: '—' },
    { metric: 'DSRA Recommendation', base: result.dsra_recommendation_months > 0 ? `${result.dsra_recommendation_months} months` : 'Not required', stress: '—' },
  ];

  if (result.etc_irr_delta_pct != null) {
    rows.push({ metric: 'ETC Revenue IRR Uplift', base: `+${fmt.pct(result.etc_irr_delta_pct)}`, stress: '—' });
    rows.push({ metric: 'ETC Revenue DSCR Uplift', base: `+${fmt.x(result.etc_dscr_delta)}`, stress: '—' });
  }

  return (
    <div>
      <SectionTitle>Financial Summary</SectionTitle>
      <div className="overflow-x-auto">
        <table className="w-full text-sm" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
          <thead>
            <tr className="border-b border-white/10">
              <th className="text-left py-2 text-xs text-gray-400 font-medium">Metric</th>
              <th className="text-right py-2 text-xs text-gray-400 font-medium">Base (P50)</th>
              <th className="text-right py-2 text-xs text-gray-400 font-medium">Stress (P90)</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr key={i} className="border-b border-white/5 hover:bg-white/3">
                <td className="py-2 text-gray-300">{row.metric}</td>
                <td className="py-2 text-right text-white" data-testid={row.testId}>{row.base}</td>
                <td className={`py-2 text-right ${row.stress === '—' ? 'text-gray-600' : 'text-amber-400'}`}>{row.stress}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────────────────
// Main Panel
// ─────────────────────────────────────────────────────────
const DEFAULT_INPUTS = {
  asset_name: '',
  total_capex_usd: 120000000,
  debt_equity_ratio: 0.70,
  loan_tenor_years: 15,
  interest_rate_pct: 7.5,
  grace_period_months: 0,
  ppa_price_usd_mwh: 55,
  ppa_tenor_years: 20,
  price_escalation_pct: 2.0,
  capacity_mw: 70,
  capacity_factor_p50: 0.27,
  capacity_factor_p90: 0.22,
  curtailment_pct: 0.03,
  opex_usd_year: 2100000,
  include_etc_revenue: false,
  etc_price_usd_tco2: 18,
  annual_etc_tonnes: 0,
  discount_rate_pct: 8.0,
  tax_rate_pct: 25.0,
};

export default function ProjectFinancePanel({ powerPlantId, powerPlantName }) {
  const [inputs, setInputs] = useState({ ...DEFAULT_INPUTS, asset_name: powerPlantName || '' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('inputs');

  const set = (key, val) => setInputs(prev => ({ ...prev, [key]: val }));
  const setNum = (key, val) => setInputs(prev => ({ ...prev, [key]: parseFloat(val) || 0 }));
  const setBool = (key, val) => setInputs(prev => ({ ...prev, [key]: val }));

  const handleCalculate = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.post(`${API}/api/v1/project-finance/calculate`, inputs);
      setResult(resp.data);
      setActiveTab('results');
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Calculation failed');
    } finally {
      setLoading(false);
    }
  }, [inputs]);

  const handleLoadDemo = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await axios.get(`${API}/api/v1/project-finance/demo/sample`);
      setResult(resp.data);
      setInputs(prev => ({
        ...prev,
        asset_name: resp.data.asset_name,
        total_capex_usd: resp.data.inputs_summary.total_capex_usd,
        debt_equity_ratio: resp.data.inputs_summary.debt_equity_ratio,
        loan_tenor_years: resp.data.inputs_summary.loan_tenor_years,
        capacity_mw: resp.data.inputs_summary.capacity_mw,
        capacity_factor_p50: resp.data.inputs_summary.capacity_factor_p50,
        capacity_factor_p90: resp.data.inputs_summary.capacity_factor_p90,
      }));
      setActiveTab('results');
    } catch (err) {
      setError('Failed to load demo data');
    } finally {
      setLoading(false);
    }
  }, []);

  const tabs = [
    { id: 'inputs', label: 'Inputs' },
    { id: 'results', label: 'Results', disabled: !result },
    { id: 'cashflows', label: 'Cash Flows', disabled: !result },
  ];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-lg font-semibold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>
            Project Finance Model
          </h2>
          <p className="text-sm text-gray-400 mt-0.5">DSCR / LLCR / IRR / PPA — renewable energy bankability assessment</p>
        </div>
        <button
          onClick={handleLoadDemo}
          className="text-xs text-cyan-400 border border-cyan-500/30 rounded px-3 py-1.5 hover:bg-cyan-500/10"
        >
          Load Demo (70MW Solar)
        </button>
      </div>

      {/* Bankability badge when result available */}
      {result && (
        <div className="flex items-center gap-4">
          <BankabilityBadge bankable={result.is_bankable} />
          <span className="text-xs text-gray-500">Base (P50) |</span>
          <BankabilityBadge bankable={result.stress_is_bankable} testId="project-finance-stress-bankable-badge" />
          <span className="text-xs text-gray-500">Stress (P90)</span>
        </div>
      )}

      {/* Tab navigation */}
      <div className="flex gap-1 border-b border-white/10">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => !tab.disabled && setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium rounded-t transition-colors ${
              activeTab === tab.id
                ? 'text-cyan-400 border-b-2 border-cyan-400'
                : tab.disabled
                ? 'text-gray-600 cursor-not-allowed'
                : 'text-gray-400 hover:text-white'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-3 text-sm text-red-400">{error}</div>
      )}

      {/* ── INPUTS TAB ── */}
      {activeTab === 'inputs' && (
        <div className="space-y-6">
          {/* Project basics */}
          <div>
            <SectionTitle>Project Details</SectionTitle>
            <div className="grid grid-cols-2 gap-3">
              <div className="col-span-2">
                <FormField label="Asset Name">
                  <input
                    type="text"
                    value={inputs.asset_name}
                    onChange={e => set('asset_name', e.target.value)}
                    placeholder="Project / plant name"
                    className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-white text-sm focus:outline-none focus:border-cyan-500/60"
                  />
                </FormField>
              </div>
              <FormField label="Total CAPEX (USD)" hint="e.g. 120,000,000">
                <NumberInput value={inputs.total_capex_usd} onChange={v => setNum('total_capex_usd', v)} placeholder="120000000" />
              </FormField>
              <FormField label="Debt / Equity Ratio" hint="0.70 = 70% debt">
                <NumberInput value={inputs.debt_equity_ratio} onChange={v => setNum('debt_equity_ratio', v)} min={0.1} max={0.95} step={0.01} />
              </FormField>
              <FormField label="Loan Tenor (years)">
                <NumberInput value={inputs.loan_tenor_years} onChange={v => setNum('loan_tenor_years', v)} min={1} max={30} step={1} />
              </FormField>
              <FormField label="Interest Rate (%)">
                <NumberInput value={inputs.interest_rate_pct} onChange={v => setNum('interest_rate_pct', v)} min={1} max={20} step={0.1} />
              </FormField>
              <FormField label="Grace Period (months)">
                <NumberInput value={inputs.grace_period_months} onChange={v => setNum('grace_period_months', v)} min={0} max={36} step={1} />
              </FormField>
              <FormField label="Tax Rate (%)">
                <NumberInput value={inputs.tax_rate_pct} onChange={v => setNum('tax_rate_pct', v)} min={0} max={50} step={1} />
              </FormField>
            </div>
          </div>

          {/* PPA Parameters */}
          <div>
            <SectionTitle>PPA Parameters</SectionTitle>
            <div className="grid grid-cols-2 gap-3">
              <FormField label="PPA Price (USD/MWh)">
                <NumberInput value={inputs.ppa_price_usd_mwh} onChange={v => setNum('ppa_price_usd_mwh', v)} min={10} max={300} step={0.5} />
              </FormField>
              <FormField label="PPA Tenor (years)">
                <NumberInput value={inputs.ppa_tenor_years} onChange={v => setNum('ppa_tenor_years', v)} min={5} max={30} step={1} />
              </FormField>
              <FormField label="Price Escalation (%/yr)">
                <NumberInput value={inputs.price_escalation_pct} onChange={v => setNum('price_escalation_pct', v)} min={0} max={10} step={0.1} />
              </FormField>
              <FormField label="Capacity (MW)">
                <NumberInput value={inputs.capacity_mw} onChange={v => setNum('capacity_mw', v)} min={1} max={5000} step={1} />
              </FormField>
              <FormField label="Capacity Factor P50" hint="e.g. 0.27 for 27%">
                <NumberInput value={inputs.capacity_factor_p50} onChange={v => setNum('capacity_factor_p50', v)} min={0.05} max={0.95} step={0.01} />
              </FormField>
              <FormField label="Capacity Factor P90" hint="Conservative stress case">
                <NumberInput value={inputs.capacity_factor_p90} onChange={v => setNum('capacity_factor_p90', v)} min={0.01} max={0.90} step={0.01} />
              </FormField>
              <FormField label="Curtailment (%)" hint="e.g. 0.03 for 3%">
                <NumberInput value={inputs.curtailment_pct} onChange={v => setNum('curtailment_pct', v)} min={0} max={0.3} step={0.01} />
              </FormField>
              <FormField label="Annual OPEX (USD)">
                <NumberInput value={inputs.opex_usd_year} onChange={v => setNum('opex_usd_year', v)} min={0} />
              </FormField>
            </div>
          </div>

          {/* Carbon Revenue */}
          <div>
            <SectionTitle>Carbon Revenue (Optional)</SectionTitle>
            <div className="space-y-3">
              <Toggle
                label="Include ETC / Carbon Credit Revenue"
                value={inputs.include_etc_revenue}
                onChange={v => setBool('include_etc_revenue', v)}
              />
              {inputs.include_etc_revenue && (
                <div className="grid grid-cols-2 gap-3 mt-3">
                  <FormField label="Carbon Price (USD/tCO2e)">
                    <NumberInput value={inputs.etc_price_usd_tco2} onChange={v => setNum('etc_price_usd_tco2', v)} min={0} max={300} step={0.5} />
                  </FormField>
                  <FormField label="Annual Credits (tCO2e)">
                    <NumberInput value={inputs.annual_etc_tonnes} onChange={v => setNum('annual_etc_tonnes', v)} min={0} />
                  </FormField>
                </div>
              )}
            </div>
          </div>

          <button
            onClick={handleCalculate}
            disabled={loading}
            data-testid="project-finance-calculate-btn"
            className="w-full py-3 rounded-lg text-sm font-semibold text-white disabled:opacity-50 transition-opacity"
            style={{ background: 'linear-gradient(135deg, hsl(199, 89%, 40%) 0%, hsl(199, 89%, 30%) 100%)' }}
          >
            {loading ? 'Calculating...' : 'Run Project Finance Model'}
          </button>
        </div>
      )}

      {/* ── RESULTS TAB ── */}
      {activeTab === 'results' && result && (
        <div className="space-y-6">
          {/* KPI Strip */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <KpiCard label="Min DSCR (P50)" value={fmt.x(result.min_dscr)} sub={result.is_bankable ? 'Above 1.25x threshold' : 'Below 1.25x threshold'} highlight testId="project-finance-dscr-min" />
            <KpiCard label="LLCR" value={fmt.x(result.llcr)} sub="Loan life coverage ratio" />
            <KpiCard label="Equity IRR" value={fmt.pct(result.equity_irr_pct)} sub="Post-tax equity returns" testId="project-finance-irr" />
            <KpiCard label="DSRA" value={result.dsra_recommendation_months > 0 ? `${result.dsra_recommendation_months} mo` : '0 mo'} sub="Reserve recommendation" />
          </div>

          {/* Stress KPIs */}
          <div>
            <SectionTitle>Stress Case (P90 capacity factor)</SectionTitle>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiCard label="Min DSCR (P90)" value={fmt.x(result.stress_min_dscr)} sub={result.stress_is_bankable ? 'Bankable under stress' : 'Fails stress test'} />
              <KpiCard label="Equity IRR (P90)" value={fmt.pct(result.stress_equity_irr_pct)} sub="Stress case returns" />
              <KpiCard label="Debt Amount" value={fmt.mUSD(result.total_debt_usd)} sub="Senior debt" />
              <KpiCard label="Equity Amount" value={fmt.mUSD(result.total_equity_usd)} sub="Sponsor equity" />
            </div>
          </div>

          {/* ETC delta */}
          {result.etc_irr_delta_pct != null && (
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 p-4">
              <div className="text-xs text-emerald-400 font-semibold uppercase tracking-wider mb-2">Carbon Revenue Impact</div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-xs text-gray-400">IRR Uplift from ETC</div>
                  <div className="text-xl font-bold text-emerald-400" style={{ fontFamily: 'IBM Plex Mono' }}>
                    +{fmt.pct(result.etc_irr_delta_pct)}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-gray-400">DSCR Uplift from ETC</div>
                  <div className="text-xl font-bold text-emerald-400" style={{ fontFamily: 'IBM Plex Mono' }}>
                    +{fmt.x(result.etc_dscr_delta)}
                  </div>
                </div>
              </div>
            </div>
          )}

          <DSCRCurveChart baseDSCR={result.dscr_by_year} stressDSCR={result.stress_dscr_by_year} loanTenor={inputs.loan_tenor_years} />
          <FinancialSummaryTable result={result} />
        </div>
      )}

      {/* ── CASH FLOWS TAB ── */}
      {activeTab === 'cashflows' && result && (
        <div className="space-y-6">
          <DSCRWaterfallChart yearByYear={result.year_by_year} loanTenor={inputs.loan_tenor_years} />

          {/* Cashflow table */}
          <div>
            <SectionTitle>Year-by-Year Cash Flow Statement</SectionTitle>
            <div className="overflow-x-auto">
              <table className="w-full text-xs" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left py-2 text-gray-400 font-medium pr-3">Year</th>
                    <th className="text-right py-2 text-gray-400 font-medium px-2">Gen (GWh)</th>
                    <th className="text-right py-2 text-gray-400 font-medium px-2">Revenue ($k)</th>
                    <th className="text-right py-2 text-gray-400 font-medium px-2">OPEX ($k)</th>
                    <th className="text-right py-2 text-gray-400 font-medium px-2">NOI ($k)</th>
                    <th className="text-right py-2 text-gray-400 font-medium px-2">Debt Svc ($k)</th>
                    <th className="text-right py-2 text-gray-400 font-medium px-2">DSCR</th>
                  </tr>
                </thead>
                <tbody>
                  {(result.year_by_year || []).slice(0, inputs.loan_tenor_years).map(row => (
                    <tr key={row.year} className="border-b border-white/5 hover:bg-white/3">
                      <td className="py-1.5 pr-3 text-gray-300">Y{row.year}</td>
                      <td className="py-1.5 px-2 text-right text-gray-300">{(row.generation_mwh / 1000).toFixed(0)}</td>
                      <td className="py-1.5 px-2 text-right text-white">{Math.round(row.gross_revenue / 1000).toLocaleString()}</td>
                      <td className="py-1.5 px-2 text-right text-amber-400">{Math.round(row.opex / 1000).toLocaleString()}</td>
                      <td className="py-1.5 px-2 text-right text-emerald-400">{Math.round(row.noi / 1000).toLocaleString()}</td>
                      <td className="py-1.5 px-2 text-right text-purple-400">{Math.round(row.debt_service / 1000).toLocaleString()}</td>
                      <td className={`py-1.5 px-2 text-right font-semibold ${row.dscr >= 1.25 ? 'text-emerald-400' : row.dscr >= 1.0 ? 'text-amber-400' : 'text-red-400'}`}>
                        {Number(row.dscr).toFixed(2)}x
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
