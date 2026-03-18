/**
 * GarEtsPage.jsx
 * Route: /gar-ets
 *
 * Green Asset Ratio (GAR) & EU ETS Phase 4 module.
 * Tabs:
 *   1. GAR Dashboard        — EU Taxonomy alignment KPIs, exposure waterfall, objective breakdown
 *   2. Free Allocation      — ETS free allocation per installation (HAL × benchmark × factor)
 *   3. ETS Compliance       — Compliance position: verified emissions vs. allocation vs. purchases
 *   4. Carbon Price Forecast — NGFS-aligned EUA price paths to 2050
 *   5. ETS2 Readiness       — Buildings & transport ETS2 scope assessment
 */
import React, { useState, useMemo, useEffect } from 'react';
import { usePersonaDefaults } from '../../../context/PersonaContext';
import axios from 'axios';
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, PieChart, Pie, ReferenceLine,
} from 'recharts';
import {
  Leaf, BarChart2, Zap, TrendingUp, Building2,
  ChevronRight, AlertTriangle, CheckCircle, Info,
  Download, RefreshCw,
} from 'lucide-react';
import DemoBanner from '../../../components/shared/DemoBanner';

const API = process.env.REACT_APP_API_URL || 'http://localhost:8001';

// ── Deterministic seed-based RNG ──────────────────────────────────────────
function seededRand(seed) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 4294967296; };
}

// ── Theme primitives ──────────────────────────────────────────────────────
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

function Row({ label, children, className = '' }) {
  return (
    <div className={`flex flex-col sm:flex-row sm:items-center gap-2 mb-3 ${className}`}>
      <label className="text-xs font-medium text-gray-600 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = 'number', step, min, max, className = '' }) {
  return (
    <input
      type={type}
      value={value}
      onChange={e => onChange(e.target.value)}
      step={step}
      min={min}
      max={max}
      className={`w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 focus:border-gray-400 bg-white ${className}`}
    />
  );
}

function Sel({ value, onChange, options, className = '' }) {
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className={`w-full text-sm border border-gray-300 rounded-lg px-3 py-1.5 focus:outline-none focus:ring-1 focus:ring-black/20 bg-white ${className}`}
    >
      {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
    </select>
  );
}

function Btn({ onClick, children, loading, variant = 'primary' }) {
  const cls = variant === 'primary'
    ? 'bg-black text-white hover:bg-gray-800'
    : 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50';
  return (
    <button
      onClick={onClick}
      disabled={loading}
      className={`px-4 py-2 rounded-lg text-xs font-semibold transition-colors ${cls} ${loading ? 'opacity-60 cursor-not-allowed' : ''}`}
    >
      {loading ? <span className="flex items-center gap-2"><RefreshCw className="w-3 h-3 animate-spin" />Running…</span> : children}
    </button>
  );
}

const RAG = v => v >= 80 ? 'text-emerald-600' : v >= 50 ? 'text-amber-600' : 'text-red-600';
const RAG_BG = v => v >= 80 ? 'bg-emerald-50 text-emerald-700' : v >= 50 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700';

const OBJECTIVE_COLORS = {
  CCM: '#059669', CCA: '#0284c7', WTR: '#6366f1', CE: '#f59e0b', POL: '#ec4899', BIO: '#8b5cf6',
};

const TABS = [
  { id: 'gar', label: 'GAR Dashboard', icon: Leaf },
  { id: 'alloc', label: 'Free Allocation', icon: Zap },
  { id: 'compliance', label: 'ETS Compliance', icon: CheckCircle },
  { id: 'price', label: 'Carbon Price Forecast', icon: TrendingUp },
  { id: 'ets2', label: 'ETS2 Readiness', icon: Building2 },
];

// ── Seed data generators ───────────────────────────────────────────────────
function genGARData() {
  const rng = seededRand(42001);
  const objectives = ['CCM', 'CCA', 'WTR', 'CE', 'POL', 'BIO'];
  const totalExposure = 4_800_000_000;
  const eligible = totalExposure * (0.55 + rng() * 0.1);
  const aligned = eligible * (0.48 + rng() * 0.1);
  const excluded = totalExposure * 0.08;
  const denominator = totalExposure - excluded;
  const garRatio = (aligned / denominator) * 100;
  const eligibilityRatio = (eligible / denominator) * 100;

  const exposureBreakdown = [
    { name: 'Aligned', value: aligned / 1e9, fill: '#059669' },
    { name: 'Eligible (not aligned)', value: (eligible - aligned) / 1e9, fill: '#f59e0b' },
    { name: 'Not Eligible', value: (totalExposure - eligible - excluded) / 1e9, fill: '#e5e7eb' },
    { name: 'Excluded', value: excluded / 1e9, fill: '#d1d5db' },
  ];

  const byObjective = objectives.map((obj, i) => {
    const r = seededRand(42010 + i);
    const eligible_b = 200 + r() * 600;
    const aligned_b = eligible_b * (0.3 + r() * 0.5);
    return { objective: obj, eligible: +eligible_b.toFixed(1), aligned: +aligned_b.toFixed(1), gar: +((aligned_b / denominator * 1e9) * 100).toFixed(2) };
  });

  const yearlyGAR = [2021, 2022, 2023, 2024, 2025].map((yr, i) => {
    const r = seededRand(42020 + i);
    return { year: yr, gar: +(8 + i * 2.5 + r() * 1.5).toFixed(1), eligibility: +(40 + i * 3 + r() * 2).toFixed(1) };
  });

  return { totalExposure, eligible, aligned, excluded, denominator, garRatio, eligibilityRatio, exposureBreakdown, byObjective, yearlyGAR };
}

function genPriceForecast() {
  const scenarios = {
    FIT_FOR_55: { start: 80, end2030: 130, end2050: 220 },
    NET_ZERO: { start: 80, end2030: 150, end2050: 300 },
    CURRENT_POLICIES: { start: 80, end2030: 75, end2050: 60 },
    DELAYED_TRANSITION: { start: 80, end2030: 90, end2050: 170 },
  };
  const years = [2024, 2026, 2028, 2030, 2035, 2040, 2045, 2050];
  return years.map(yr => {
    const t = (yr - 2024) / 26;
    return {
      year: yr,
      FIT_FOR_55: +(80 + (130 - 80) * Math.min(t * 2, 1) * 0.5 + (220 - 130) * Math.max(t * 2 - 1, 0) * 0.5).toFixed(0),
      NET_ZERO: +(80 + (220 * t) * 1.1).toFixed(0),
      CURRENT_POLICIES: +(80 - 20 * t).toFixed(0),
      DELAYED_TRANSITION: +(80 + 90 * t * 0.8).toFixed(0),
    };
  });
}

// ── Demo exposures sent to GAR API (matches demo portfolio in DemoPortfolioSeeder) ─
const DEMO_GAR_EXPOSURES = [
  { exposure_id: 'E1',  counterparty_name: 'SolarGrid SE',   asset_class: 'corporate_equity', sector_nace: 'D35', ead_eur: 60e6,  pd_base: 0.030, lgd_base: 0.50, taxonomy_eligible: true,  taxonomy_aligned_pct: 72, dnsh_compliant: true,  min_social_safeguards: true,  ccm_aligned: true,  cca_aligned: false, is_sovereign: false, transition_risk_level: 'low',    scenario: 'BASE' },
  { exposure_id: 'E2',  counterparty_name: 'PetroCo NV',     asset_class: 'corporate_loan',   sector_nace: 'B06', ead_eur: 150e6, pd_base: 0.020, lgd_base: 0.48, taxonomy_eligible: false, taxonomy_aligned_pct: 0,  dnsh_compliant: false, min_social_safeguards: false, ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'high',   scenario: 'BASE' },
  { exposure_id: 'E3',  counterparty_name: 'NordSteel GmbH', asset_class: 'corporate_loan',   sector_nace: 'C24', ead_eur: 95e6,  pd_base: 0.018, lgd_base: 0.45, taxonomy_eligible: true,  taxonomy_aligned_pct: 30, dnsh_compliant: false, min_social_safeguards: true,  ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'high',   scenario: 'BASE' },
  { exposure_id: 'E4',  counterparty_name: 'Eurobank AG',    asset_class: 'corporate_bond',   sector_nace: 'K64', ead_eur: 120e6, pd_base: 0.003, lgd_base: 0.40, taxonomy_eligible: false, taxonomy_aligned_pct: 0,  dnsh_compliant: false, min_social_safeguards: false, ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'medium', scenario: 'BASE' },
  { exposure_id: 'E5',  counterparty_name: 'CityRent GmbH',  asset_class: 'commercial_re',    sector_nace: 'L68', ead_eur: 70e6,  pd_base: 0.008, lgd_base: 0.35, taxonomy_eligible: true,  taxonomy_aligned_pct: 55, dnsh_compliant: true,  min_social_safeguards: true,  ccm_aligned: true,  cca_aligned: true,  is_sovereign: false, transition_risk_level: 'low',    scenario: 'BASE' },
  { exposure_id: 'E6',  counterparty_name: 'UrbanGrid SA',   asset_class: 'corporate_bond',   sector_nace: 'D35', ead_eur: 100e6, pd_base: 0.007, lgd_base: 0.38, taxonomy_eligible: true,  taxonomy_aligned_pct: 80, dnsh_compliant: true,  min_social_safeguards: true,  ccm_aligned: true,  cca_aligned: false, is_sovereign: false, transition_risk_level: 'medium', scenario: 'BASE' },
  { exposure_id: 'E7',  counterparty_name: 'TechCore BV',    asset_class: 'corporate_equity', sector_nace: 'J63', ead_eur: 55e6,  pd_base: 0.005, lgd_base: 0.32, taxonomy_eligible: true,  taxonomy_aligned_pct: 45, dnsh_compliant: true,  min_social_safeguards: true,  ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'low',    scenario: 'BASE' },
  { exposure_id: 'E8',  counterparty_name: 'WasteEx SpA',    asset_class: 'corporate_loan',   sector_nace: 'E38', ead_eur: 42e6,  pd_base: 0.015, lgd_base: 0.43, taxonomy_eligible: true,  taxonomy_aligned_pct: 60, dnsh_compliant: true,  min_social_safeguards: true,  ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'medium', scenario: 'BASE' },
  { exposure_id: 'E9',  counterparty_name: 'PharmEU plc',    asset_class: 'corporate_bond',   sector_nace: 'C21', ead_eur: 45e6,  pd_base: 0.002, lgd_base: 0.30, taxonomy_eligible: false, taxonomy_aligned_pct: 0,  dnsh_compliant: false, min_social_safeguards: false, ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'low',    scenario: 'BASE' },
  { exposure_id: 'E10', counterparty_name: 'Alpine RE Ltd',  asset_class: 'corporate_bond',   sector_nace: 'K65', ead_eur: 80e6,  pd_base: 0.002, lgd_base: 0.35, taxonomy_eligible: false, taxonomy_aligned_pct: 0,  dnsh_compliant: false, min_social_safeguards: false, ccm_aligned: false, cca_aligned: false, is_sovereign: false, transition_risk_level: 'low',    scenario: 'BASE' },
];

// ═══════════════════════════════════════════════════════════════════════
// Tab 1: GAR Dashboard  (P0-5 — wired to POST /api/v1/ecl-gar-pillar3/gar-only)
// ═══════════════════════════════════════════════════════════════════════
function GARDashboard() {
  const seed = useMemo(() => genGARData(), []);
  const [apiGar, setApiGar] = useState(null);
  const [loadingGar, setLoadingGar] = useState(true);
  const [dataSource, setDataSource] = useState('seed'); // 'api' | 'seed'

  useEffect(() => {
    let cancelled = false;
    const fetchGar = async () => {
      setLoadingGar(true);
      try {
        const res = await axios.post(`${API}/api/v1/ecl-gar-pillar3/gar-only`, {
          entity_name: 'Demo Portfolio',
          exposures: DEMO_GAR_EXPOSURES,
          scenario: 'BASE',
        });
        if (!cancelled && res.data?.gar) {
          setApiGar(res.data);
          setDataSource('api');
        }
      } catch {
        // fallback to seed — already set
      } finally {
        if (!cancelled) setLoadingGar(false);
      }
    };
    fetchGar();
    return () => { cancelled = true; };
  }, []);

  // ── Derive display values: prefer API, fall back to seed ──────────────
  let garRatio, eligibilityRatio, denominator, aligned, eligible, excluded, exposureBreakdown;
  const { yearlyGAR, byObjective } = seed; // historical / objective breakdown always from seed

  if (apiGar?.gar) {
    const g = apiGar.gar;
    garRatio = g.gar_ratio_pct ?? seed.garRatio;
    denominator = g.gar_denominator_eur ?? seed.denominator;
    aligned = g.gar_numerator_eur ?? seed.aligned;

    // Derive eligible from exposures
    const exps = apiGar.exposures || [];
    eligible = exps.reduce((s, e) => s + (e.taxonomy_eligible ? (e.ead_eur ?? 0) : 0), 0);
    excluded = 0; // Sovereigns / central banks excluded — none in demo
    eligibilityRatio = denominator > 0 ? (eligible / denominator) * 100 : seed.eligibilityRatio;

    const notEligible = denominator - eligible - excluded;
    exposureBreakdown = [
      { name: 'Aligned',              value: aligned / 1e9,      fill: '#059669' },
      { name: 'Eligible (not aligned)', value: (eligible - aligned) / 1e9, fill: '#f59e0b' },
      { name: 'Not Eligible',          value: Math.max(notEligible, 0) / 1e9, fill: '#e5e7eb' },
      { name: 'Excluded',              value: excluded / 1e9,    fill: '#d1d5db' },
    ];
  } else {
    ({ garRatio, eligibilityRatio, totalExposure: _, aligned, eligible, excluded, denominator, exposureBreakdown } = seed);
  }

  return (
    <div>
      {/* Data-source indicator */}
      <div className="flex items-center gap-2 mb-3">
        {loadingGar
          ? <span className="text-[10px] text-gray-400 flex items-center gap-1"><RefreshCw className="w-3 h-3 animate-spin" /> Loading live GAR…</span>
          : dataSource === 'api'
            ? <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200">✓ Live API — POST /ecl-gar-pillar3/gar-only</span>
            : <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-amber-50 text-amber-700 border border-amber-200">Demo data (API offline)</span>
        }
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
        <KpiCard label="GAR (Aligned/Denominator)" value={loadingGar ? '…' : `${garRatio.toFixed(1)}%`} sub="CRR Art. 449a" accent={!loadingGar && garRatio >= 15 ? 'green' : 'amber'} badge="ART 449a" />
        <KpiCard label="Taxonomy Eligibility Ratio" value={loadingGar ? '…' : `${eligibilityRatio.toFixed(1)}%`} sub="Step 1 screen" accent="green" />
        <KpiCard label="Total Denominator" value={loadingGar ? '…' : `€${(denominator / 1e9).toFixed(1)}B`} sub={`Excl. €${((excluded ?? 0) / 1e9).toFixed(1)}B excluded`} />
        <KpiCard label="Taxonomy Aligned" value={loadingGar ? '…' : `€${(aligned / 1e9).toFixed(1)}B`} sub={`of €${(eligible / 1e9).toFixed(1)}B eligible`} accent="green" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <Section title="Exposure Waterfall (€B)" subtitle="Aligned → Eligible → Not Eligible → Excluded">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={exposureBreakdown} layout="vertical" barSize={26}>
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f3f4f6" />
              <XAxis type="number" tick={{ fontSize: 11 }} tickFormatter={v => `€${v.toFixed(0)}B`} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={130} />
              <Tooltip formatter={v => `€${Number(v).toFixed(2)}B`} />
              <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                {exposureBreakdown.map((e, i) => <Cell key={i} fill={e.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="GAR & Eligibility — Historical Trend" subtitle="Annual KPIs 2021–2025">
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={yearlyGAR}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
              <XAxis dataKey="year" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
              <Tooltip formatter={v => `${v}%`} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
              <Line type="monotone" dataKey="gar" stroke="#059669" name="GAR" strokeWidth={2} dot={{ r: 3 }} />
              <Line type="monotone" dataKey="eligibility" stroke="#0284c7" name="Eligibility" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </Section>
      </div>

      <Section title="By EU Taxonomy Objective" subtitle="Eligible and aligned exposure (€B) per environmental objective">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 text-gray-500 font-semibold">Objective</th>
                <th className="text-right py-2 text-gray-500 font-semibold">Eligible (€B)</th>
                <th className="text-right py-2 text-gray-500 font-semibold">Aligned (€B)</th>
                <th className="text-right py-2 text-gray-500 font-semibold">Contribution to GAR</th>
                <th className="py-2 text-gray-500 font-semibold w-32">Alignment Bar</th>
              </tr>
            </thead>
            <tbody>
              {byObjective.map(row => {
                const pct = row.eligible > 0 ? (row.aligned / row.eligible) * 100 : 0;
                return (
                  <tr key={row.objective} className="border-b border-gray-50 hover:bg-gray-50">
                    <td className="py-2.5">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold text-white" style={{ background: OBJECTIVE_COLORS[row.objective] || '#6b7280' }}>
                        {row.objective}
                      </span>
                      <span className="ml-2 text-gray-600">{({ CCM: 'Climate Change Mitigation', CCA: 'Climate Change Adaptation', WTR: 'Water & Marine', CE: 'Circular Economy', POL: 'Pollution Prevention', BIO: 'Biodiversity' })[row.objective]}</span>
                    </td>
                    <td className="text-right py-2.5 font-mono text-gray-800">{row.eligible.toFixed(0)}</td>
                    <td className="text-right py-2.5 font-mono text-emerald-700">{row.aligned.toFixed(0)}</td>
                    <td className="text-right py-2.5 font-mono">{row.gar.toFixed(2)}%</td>
                    <td className="py-2.5">
                      <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                        <div className="h-full bg-emerald-500 rounded-full" style={{ width: `${Math.min(pct, 100)}%` }} />
                      </div>
                      <div className="text-[10px] text-gray-400 mt-0.5">{pct.toFixed(0)}%</div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 2: Free Allocation
// ═══════════════════════════════════════════════════════════════════════
// GAP-012 — Sprint 1: Versioned ETS Product Benchmarks
// Period 1: Decision (EU) 2021/927 — allocation years 2021-2025
const BENCHMARK_VALUES_2021 = {
  hot_metal: 1.328, sintered_ore: 0.171, coke: 0.286, cement_clinker: 0.766, lime: 0.954,
  float_glass: 0.453, ammonia: 1.619, hydrogen: 8.850, aluminium: 1.514, paper: 0.318,
  refinery_products: 0.0295, nitric_acid: 0.302,
  heat_benchmark: 0.0623, fuel_benchmark: 0.0561,
};
// Period 2: Decision (EU) 2024/903 — allocation years 2026-2030 (Fit for 55 revised values)
const BENCHMARK_VALUES_2026 = {
  hot_metal: 1.254, sintered_ore: 0.162, coke: 0.270, cement_clinker: 0.693, lime: 0.867,
  float_glass: 0.415, ammonia: 1.482, hydrogen: 7.438, aluminium: 1.385, paper: 0.294,
  refinery_products: 0.0272, nitric_acid: 0.288,
  heat_benchmark: 0.05725, fuel_benchmark: 0.05163,
};
// CBAM sectors (Article 31 — CBAM Regulation 2023/956)
const CBAM_SECTORS_SET = new Set(['hot_metal', 'cement_clinker', 'aluminium', 'ammonia', 'hydrogen', 'nitric_acid']);

function FreeAllocationTab() {
  const [allocationPeriod, setAllocationPeriod] = useState('2026-2030');

  const BENCHMARK_VALUES = allocationPeriod === '2026-2030' ? BENCHMARK_VALUES_2026 : BENCHMARK_VALUES_2021;

  const BENCHMARKS = [
    { value: 'hot_metal',         label: `Hot Metal (Iron & Steel) — ${BENCHMARK_VALUES.hot_metal} tCO₂/t` },
    { value: 'sintered_ore',      label: `Sintered Ore — ${BENCHMARK_VALUES.sintered_ore} tCO₂/t` },
    { value: 'coke',              label: `Coke — ${BENCHMARK_VALUES.coke} tCO₂/t` },
    { value: 'cement_clinker',    label: `Cement Clinker — ${BENCHMARK_VALUES.cement_clinker} tCO₂/t` },
    { value: 'lime',              label: `Lime / Dolime — ${BENCHMARK_VALUES.lime} tCO₂/t` },
    { value: 'float_glass',       label: `Float Glass — ${BENCHMARK_VALUES.float_glass} tCO₂/t` },
    { value: 'ammonia',           label: `Ammonia — ${BENCHMARK_VALUES.ammonia} tCO₂/t` },
    { value: 'hydrogen',          label: `Hydrogen — ${BENCHMARK_VALUES.hydrogen} tCO₂/t` },
    { value: 'aluminium',         label: `Aluminium — ${BENCHMARK_VALUES.aluminium} tCO₂/t` },
    { value: 'paper',             label: `Paper / Newsprint — ${BENCHMARK_VALUES.paper} tCO₂/t` },
    { value: 'nitric_acid',       label: `Nitric Acid — ${BENCHMARK_VALUES.nitric_acid} tCO₂/t` },
    { value: 'heat_benchmark',    label: `Heat Benchmark — ${(BENCHMARK_VALUES.heat_benchmark * 1000).toFixed(1)} tCO₂/TJ` },
    { value: 'fuel_benchmark',    label: `Fuel Benchmark — ${(BENCHMARK_VALUES.fuel_benchmark * 1000).toFixed(1)} tCO₂/TJ` },
  ];

  // Cross-Sectoral Correction Factor (CSCF) estimates per year
  const CSCF = {
    2021: 1.0, 2022: 0.97, 2023: 0.93, 2024: 0.89, 2025: 0.85,
    2026: 0.88, 2027: 0.84, 2028: 0.80, 2029: 0.76, 2030: 0.72,
  };

  const d = usePersonaDefaults('gar_ets');
  const [form, setForm] = useState({
    installationId: d.installationId || 'INST-001',
    sector: d.sector || 'Iron & Steel',
    benchmark: d.benchmark || 'hot_metal',
    hal: d.hal || '500000',
    year: d.year || '2026',  // default to 2026 — 5th allocation period
    carbonLeakage: d.carbonLeakage !== undefined ? d.carbonLeakage : true,
    carbonPrice: d.carbonPrice || '80',
  });
  useEffect(() => {
    if (d.installationId) setForm(p => ({
      ...p,
      installationId: d.installationId,
      sector: d.sector || p.sector,
      benchmark: d.benchmark || p.benchmark,
      hal: d.hal || p.hal,
      carbonLeakage: d.carbonLeakage !== undefined ? d.carbonLeakage : p.carbonLeakage,
      carbonPrice: d.carbonPrice || p.carbonPrice,
    }));
  }, [d.installationId]); // eslint-disable-line

  // Sync year when period changes so the year stays in range
  useEffect(() => {
    const yr = parseInt(form.year);
    if (allocationPeriod === '2026-2030' && yr < 2026) setForm(p => ({ ...p, year: '2026' }));
    if (allocationPeriod === '2021-2025' && yr > 2025) setForm(p => ({ ...p, year: '2025' }));
  }, [allocationPeriod]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const f = k => v => setForm(p => ({ ...p, [k]: v }));

  const compute = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/eu-ets/free-allocation`, {
        installation_id: form.installationId,
        installation_name: form.sector,
        sector: form.sector,
        product_benchmark: form.benchmark,
        year: parseInt(form.year),
        historical_activity_level: parseFloat(form.hal),
        carbon_leakage_listed: form.carbonLeakage,
        carbon_price_eur: parseFloat(form.carbonPrice),
      });
      setResult(res.data);
    } catch {
      // Fallback deterministic
      const bv = BENCHMARK_VALUES[form.benchmark] || 1.0;
      const cscf = CSCF[parseInt(form.year)] || 0.85;
      const claf = form.carbonLeakage ? 1.0 : 0.3;
      const hal = parseFloat(form.hal) || 0;
      const fa = hal * bv * cscf * claf;
      const price = parseFloat(form.carbonPrice) || 80;
      setResult({
        installation_id: form.installationId,
        free_allocation_tco2: +fa.toFixed(0),
        benchmark_value: bv,
        cscf,
        claf,
        monetary_value_eur: +(fa * price).toFixed(0),
        annual_growth_factor: 1.0,
        note: 'Computed locally (API unavailable)',
      });
    } finally { setLoading(false); }
  };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Section
        title="Installation Parameters"
        subtitle="EU ETS Phase 4 — Article 10a free allocation"
        action={
          <div className="flex items-center gap-1.5">
            <span className="text-[10px] text-gray-500 font-medium">Benchmark period:</span>
            <Sel
              value={allocationPeriod}
              onChange={setAllocationPeriod}
              options={[
                { value: '2021-2025', label: '2021-2025 (Decision 2021/927)' },
                { value: '2026-2030', label: '2026-2030 (Decision 2024/903) ★' },
              ]}
              className="!w-auto text-[11px]"
            />
          </div>
        }
      >
        {allocationPeriod === '2026-2030' && (
          <div className="mb-3 p-2 rounded-lg bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800">
            <strong>Updated values active</strong> — Commission Delegated Decision (EU) 2024/903 (28 Feb 2024).
            5th allocation period 2026-2030 with increased LRF of 4.3% p.a. per Directive 2023/959 (Fit for 55).
            {CBAM_SECTORS_SET.has(form.benchmark) && (
              <span className="ml-1 font-bold text-orange-700">
                ⚠ CBAM sector — free allocation phase-out applies from 2026.
              </span>
            )}
          </div>
        )}
        <Row label="Installation ID"><Inp value={form.installationId} onChange={f('installationId')} type="text" /></Row>
        <Row label="Sector"><Inp value={form.sector} onChange={f('sector')} type="text" /></Row>
        <Row label="Product Benchmark"><Sel value={form.benchmark} onChange={f('benchmark')} options={BENCHMARKS} /></Row>
        <Row label="Historical Activity Level (t)"><Inp value={form.hal} onChange={f('hal')} min="0" /></Row>
        <Row label="Compliance Year">
          <Sel
            value={form.year}
            onChange={f('year')}
            options={allocationPeriod === '2026-2030'
              ? [2026,2027,2028,2029,2030].map(y => ({ value: String(y), label: String(y) }))
              : [2021,2022,2023,2024,2025].map(y => ({ value: String(y), label: String(y) }))}
          />
        </Row>
        <Row label="Carbon Price (€/tCO₂)"><Inp value={form.carbonPrice} onChange={f('carbonPrice')} min="0" step="5" /></Row>
        <Row label="Carbon Leakage Listed">
          <button
            onClick={() => setForm(p => ({ ...p, carbonLeakage: !p.carbonLeakage }))}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${form.carbonLeakage ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-gray-50 text-gray-600 border-gray-300'}`}
          >
            {form.carbonLeakage ? 'Yes — CLAF 100%' : 'No — CLAF 30%'}
          </button>
        </Row>
        <div className="mt-4">
          <Btn onClick={compute} loading={loading}>Calculate Free Allocation</Btn>
        </div>
      </Section>

      <Section title="Allocation Result" subtitle="Phase 4 free allocation (ETS Directive Art. 10a)">
        {result ? (
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <KpiCard label="Free Allocation" value={`${(result.free_allocation_tco2 / 1000).toFixed(1)}k tCO₂`} accent="green" />
              <KpiCard label="Monetary Value" value={`€${(result.monetary_value_eur / 1e6).toFixed(1)}M`} />
              <KpiCard label="Benchmark Value" value={`${result.benchmark_value?.toFixed(3) || '—'}`} sub="tCO₂/unit" />
              <KpiCard label="CSCF" value={result.cscf?.toFixed(2) || '—'} sub="Cross-sectoral factor" />
            </div>
            <div className="text-xs text-gray-500 bg-gray-50 rounded-lg p-3 font-mono">
              FA = HAL × BV × CSCF × CLAF<br />
              = {parseFloat(form.hal).toLocaleString()} × {result.benchmark_value?.toFixed(3)} × {result.cscf?.toFixed(2)} × {result.claf?.toFixed(1)}<br />
              = <strong>{(result.free_allocation_tco2).toLocaleString()} tCO₂</strong>
            </div>
            {result.note && <p className="text-[10px] text-gray-400">{result.note}</p>}
          </div>
        ) : (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            <Info className="w-4 h-4 mr-2" /> Configure parameters and click Calculate
          </div>
        )}
      </Section>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 3: ETS Compliance
// ═══════════════════════════════════════════════════════════════════════
function ETSComplianceTab() {
  const d = usePersonaDefaults('gar_ets');
  const [form, setForm] = useState({
    installationId: d.installationId || 'INST-001',
    year: d.year || '2025',
    verifiedEmissions: d.verifiedEmissions || '520000',
    freeAllocation: d.freeAllocation || '480000',
    purchased: d.purchased || '50000',
    banked: d.banked || '0',
    carbonPrice: d.carbonPrice || '80',
  });
  useEffect(() => {
    if (d.installationId) setForm(p => ({
      ...p,
      installationId: d.installationId,
      verifiedEmissions: d.verifiedEmissions || p.verifiedEmissions,
      freeAllocation: d.freeAllocation || p.freeAllocation,
      carbonPrice: d.carbonPrice || p.carbonPrice,
    }));
  }, [d.installationId]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const f = k => v => setForm(p => ({ ...p, [k]: v }));

  const compute = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/eu-ets/compliance`, {
        installation_id: form.installationId,
        year: parseInt(form.year),
        verified_emissions_tco2: parseFloat(form.verifiedEmissions),
        free_allocation_tco2: parseFloat(form.freeAllocation),
        purchased_allowances_tco2: parseFloat(form.purchased),
        banked_allowances_tco2: parseFloat(form.banked),
        carbon_price_eur: parseFloat(form.carbonPrice),
      });
      setResult(res.data);
    } catch {
      const em = parseFloat(form.verifiedEmissions) || 0;
      const fa = parseFloat(form.freeAllocation) || 0;
      const pur = parseFloat(form.purchased) || 0;
      const ban = parseFloat(form.banked) || 0;
      const pr = parseFloat(form.carbonPrice) || 80;
      const totalAllowances = fa + pur + ban;
      const surplus = totalAllowances - em;
      const compliant = surplus >= 0;
      const surrenderCost = compliant ? 0 : Math.abs(surplus) * pr;
      const penalty = compliant ? 0 : Math.abs(surplus) * 100;
      setResult({
        installation_id: form.installationId,
        year: parseInt(form.year),
        verified_emissions_tco2: em,
        total_allowances_tco2: totalAllowances,
        net_position_tco2: surplus,
        compliant,
        surrender_cost_eur: surrenderCost,
        non_compliance_penalty_eur: penalty,
        compliance_rate_pct: Math.min((totalAllowances / em) * 100, 100),
        note: 'Computed locally',
      });
    } finally { setLoading(false); }
  };

  const barData = result ? [
    { name: 'Verified Emissions', value: result.verified_emissions_tco2 / 1000, fill: '#ef4444' },
    { name: 'Free Allocation', value: parseFloat(form.freeAllocation) / 1000, fill: '#059669' },
    { name: 'Purchased', value: parseFloat(form.purchased) / 1000, fill: '#0284c7' },
    { name: 'Banked', value: parseFloat(form.banked) / 1000, fill: '#8b5cf6' },
  ] : [];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Section title="Compliance Position" subtitle="Verified emissions vs. allowances held">
        <Row label="Installation ID"><Inp value={form.installationId} onChange={f('installationId')} type="text" /></Row>
        <Row label="Compliance Year"><Sel value={form.year} onChange={f('year')} options={[2023,2024,2025].map(y => ({ value: String(y), label: String(y) }))} /></Row>
        <Row label="Verified Emissions (tCO₂)"><Inp value={form.verifiedEmissions} onChange={f('verifiedEmissions')} min="0" /></Row>
        <Row label="Free Allocation (tCO₂)"><Inp value={form.freeAllocation} onChange={f('freeAllocation')} min="0" /></Row>
        <Row label="Purchased Allowances (tCO₂)"><Inp value={form.purchased} onChange={f('purchased')} min="0" /></Row>
        <Row label="Banked Allowances (tCO₂)"><Inp value={form.banked} onChange={f('banked')} min="0" /></Row>
        <Row label="Carbon Price (€/EUA)"><Inp value={form.carbonPrice} onChange={f('carbonPrice')} min="0" step="5" /></Row>
        <div className="mt-4"><Btn onClick={compute} loading={loading}>Assess Compliance</Btn></div>
      </Section>

      <div className="space-y-4">
        {result && (
          <>
            <div className={`rounded-xl border p-4 ${result.compliant ? 'bg-emerald-50 border-emerald-200' : 'bg-red-50 border-red-200'}`}>
              <div className="flex items-center gap-2 mb-2">
                {result.compliant
                  ? <CheckCircle className="w-5 h-5 text-emerald-600" />
                  : <AlertTriangle className="w-5 h-5 text-red-600" />
                }
                <span className={`text-sm font-bold ${result.compliant ? 'text-emerald-700' : 'text-red-700'}`}>
                  {result.compliant ? 'COMPLIANT' : 'NON-COMPLIANT'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs">
                <div><span className="text-gray-500">Net Position</span><div className={`font-mono font-bold text-lg ${result.net_position_tco2 >= 0 ? 'text-emerald-700' : 'text-red-700'}`}>{result.net_position_tco2 >= 0 ? '+' : ''}{(result.net_position_tco2 / 1000).toFixed(1)}k tCO₂</div></div>
                <div><span className="text-gray-500">Compliance Rate</span><div className="font-mono font-bold text-lg text-gray-900">{result.compliance_rate_pct?.toFixed(1)}%</div></div>
                {!result.compliant && <><div><span className="text-gray-500">Surrender Cost</span><div className="font-mono font-bold text-red-700">€{(result.surrender_cost_eur / 1e6).toFixed(2)}M</div></div>
                <div><span className="text-gray-500">Penalty (€100/EUA)</span><div className="font-mono font-bold text-red-700">€{(result.non_compliance_penalty_eur / 1e6).toFixed(2)}M</div></div></>}
              </div>
            </div>
            <Section title="Allowances vs. Emissions (k tCO₂)">
              <ResponsiveContainer width="100%" height={200}>
                <BarChart data={barData} barSize={30}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} />
                  <YAxis tickFormatter={v => `${v}k`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => `${Number(v).toFixed(1)}k tCO₂`} />
                  <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                    {barData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}
        {!result && (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            <Info className="w-4 h-4 mr-2" /> Configure and assess compliance
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 4: Carbon Price Forecast
// ═══════════════════════════════════════════════════════════════════════
function CarbonPriceForecastTab() {
  const [scenario, setScenario] = useState('FIT_FOR_55');
  const [currentPrice, setCurrentPrice] = useState('80');
  const [loading, setLoading] = useState(false);
  const [apiData, setApiData] = useState(null);

  const localData = useMemo(() => genPriceForecast(), []);

  const SCENARIO_OPTS = [
    { value: 'FIT_FOR_55', label: 'Fit for 55' },
    { value: 'NET_ZERO', label: 'Net Zero 2050' },
    { value: 'CURRENT_POLICIES', label: 'Current Policies' },
    { value: 'DELAYED_TRANSITION', label: 'Delayed Transition' },
  ];

  const SCENARIO_COLORS = {
    FIT_FOR_55: '#059669', NET_ZERO: '#0284c7', CURRENT_POLICIES: '#ef4444', DELAYED_TRANSITION: '#f59e0b',
  };

  const fetchForecast = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/eu-ets/carbon-price-forecast`, {
        scenario, current_price_eur: parseFloat(currentPrice),
      });
      setApiData(res.data?.forecast || null);
    } catch { setApiData(null); }
    finally { setLoading(false); }
  };

  const displayData = apiData || localData;

  return (
    <div className="space-y-4">
      <Section title="Scenario Configuration">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="w-56">
            <label className="text-xs font-medium text-gray-600 mb-1 block">NGFS Scenario</label>
            <Sel value={scenario} onChange={setScenario} options={SCENARIO_OPTS} />
          </div>
          <div className="w-40">
            <label className="text-xs font-medium text-gray-600 mb-1 block">Current EUA Price (€)</label>
            <Inp value={currentPrice} onChange={setCurrentPrice} min="0" step="5" />
          </div>
          <Btn onClick={fetchForecast} loading={loading}>Run Forecast</Btn>
        </div>
      </Section>

      <Section title="EUA Carbon Price Forecast — All Scenarios" subtitle="€/tCO₂ 2024–2050">
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={displayData}>
            <defs>
              {Object.entries(SCENARIO_COLORS).map(([k, c]) => (
                <linearGradient key={k} id={`grad_${k}`} x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor={c} stopOpacity={0.15} />
                  <stop offset="95%" stopColor={c} stopOpacity={0} />
                </linearGradient>
              ))}
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f3f4f6" />
            <XAxis dataKey="year" tick={{ fontSize: 11 }} />
            <YAxis tickFormatter={v => `€${v}`} tick={{ fontSize: 11 }} />
            <Tooltip formatter={v => `€${v}/tCO₂`} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            {Object.entries(SCENARIO_COLORS).map(([k, c]) => (
              <Area key={k} type="monotone" dataKey={k} stroke={c} fill={`url(#grad_${k})`} strokeWidth={2} name={SCENARIO_OPTS.find(o => o.value === k)?.label || k} dot={{ r: 2 }} />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Price Table (€/tCO₂)">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-100">
                <th className="text-left py-2 text-gray-500 font-semibold">Year</th>
                {SCENARIO_OPTS.map(s => <th key={s.value} className="text-right py-2 text-gray-500 font-semibold">{s.label}</th>)}
              </tr>
            </thead>
            <tbody>
              {displayData.map(row => (
                <tr key={row.year} className="border-b border-gray-50 hover:bg-gray-50">
                  <td className="py-2 font-mono font-semibold text-gray-700">{row.year}</td>
                  {SCENARIO_OPTS.map(s => (
                    <td key={s.value} className="text-right py-2 font-mono" style={{ color: SCENARIO_COLORS[s.value] }}>
                      €{row[s.value] || '—'}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Tab 5: ETS2 Readiness
// ═══════════════════════════════════════════════════════════════════════
function ETS2ReadinessTab() {
  const d = usePersonaDefaults('gar_ets');
  const [form, setForm] = useState({
    entityType: d.entityType || 'BUILDING_OWNER',
    sector: d.sector || 'Real Estate',
    annualFuelConsumptionGj: d.annualFuelConsumptionGj || '25000',
    scope1EmissionsTco2: d.scope1EmissionsTco2 || '1300',
    annualRevenueEur: d.annualRevenueEur || '50000000',
    hasEmissionMonitoring: d.hasEmissionMonitoring !== undefined ? d.hasEmissionMonitoring : false,
    hasEnergyAudit: d.hasEnergyAudit !== undefined ? d.hasEnergyAudit : false,
    plannedRetrofitYear: d.plannedRetrofitYear || '2027',
  });
  useEffect(() => {
    if (d.sector || d.annualFuelConsumptionGj) setForm(p => ({
      ...p,
      entityType: d.entityType || p.entityType,
      sector: d.sector || p.sector,
      annualFuelConsumptionGj: d.annualFuelConsumptionGj || p.annualFuelConsumptionGj,
      scope1EmissionsTco2: d.scope1EmissionsTco2 || p.scope1EmissionsTco2,
      annualRevenueEur: d.annualRevenueEur || p.annualRevenueEur,
      hasEmissionMonitoring: d.hasEmissionMonitoring !== undefined ? d.hasEmissionMonitoring : p.hasEmissionMonitoring,
      hasEnergyAudit: d.hasEnergyAudit !== undefined ? d.hasEnergyAudit : p.hasEnergyAudit,
      plannedRetrofitYear: d.plannedRetrofitYear || p.plannedRetrofitYear,
    }));
  }, [d.sector]); // eslint-disable-line
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const f = k => v => setForm(p => ({ ...p, [k]: v }));

  const ENTITY_TYPES = [
    { value: 'BUILDING_OWNER', label: 'Building Owner' },
    { value: 'REGULATED_ENTITY', label: 'Regulated Entity (Fuel Supplier)' },
    { value: 'HEAT_SUPPLIER', label: 'District Heat Supplier' },
    { value: 'TRANSPORT_OPERATOR', label: 'Transport Operator' },
  ];

  const compute = async () => {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/eu-ets/ets2-readiness`, {
        entity_type: form.entityType,
        sector: form.sector,
        annual_fuel_consumption_gj: parseFloat(form.annualFuelConsumptionGj),
        scope1_emissions_tco2: parseFloat(form.scope1EmissionsTco2),
        annual_revenue_eur: parseFloat(form.annualRevenueEur),
        has_emission_monitoring: form.hasEmissionMonitoring,
        has_energy_audit: form.hasEnergyAudit,
        planned_retrofit_year: parseInt(form.plannedRetrofitYear),
      });
      setResult(res.data);
    } catch {
      const em = parseFloat(form.scope1EmissionsTco2) || 0;
      const price2027 = 45;
      const liabilityCost = em * price2027;
      let readinessScore = 20;
      if (form.hasEmissionMonitoring) readinessScore += 30;
      if (form.hasEnergyAudit) readinessScore += 25;
      const retrofitYear = parseInt(form.plannedRetrofitYear) || 2030;
      if (retrofitYear <= 2027) readinessScore += 25;
      else if (retrofitYear <= 2029) readinessScore += 10;
      setResult({
        in_scope: true,
        start_date: '2027-01-01',
        estimated_annual_emissions_tco2: em,
        estimated_compliance_cost_eur: liabilityCost,
        readiness_score: readinessScore,
        readiness_rating: readinessScore >= 70 ? 'HIGH' : readinessScore >= 40 ? 'MEDIUM' : 'LOW',
        gaps: [
          !form.hasEmissionMonitoring && 'Emission monitoring system required (MRV)',
          !form.hasEnergyAudit && 'Energy audit under EED Article 8 recommended',
          retrofitYear > 2027 && `Retrofit planned ${retrofitYear} — post ETS2 launch risk`,
        ].filter(Boolean),
        action_plan: [
          'Register with competent authority by Q4 2026',
          'Implement MRV plan per ETS2 Monitoring Regulation',
          'Open surrendering account in Union Registry',
        ],
        note: 'Computed locally',
      });
    } finally { setLoading(false); }
  };

  const RATING_COLOR = { HIGH: 'emerald', MEDIUM: 'amber', LOW: 'red' };

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Section title="Entity Scope Assessment" subtitle="ETS2 — Buildings & Transport (2027 launch)">
        <Row label="Entity Type"><Sel value={form.entityType} onChange={f('entityType')} options={ENTITY_TYPES} /></Row>
        <Row label="Sector"><Inp value={form.sector} onChange={f('sector')} type="text" /></Row>
        <Row label="Annual Fuel Consumption (GJ)"><Inp value={form.annualFuelConsumptionGj} onChange={f('annualFuelConsumptionGj')} min="0" /></Row>
        <Row label="Scope 1 Emissions (tCO₂/yr)"><Inp value={form.scope1EmissionsTco2} onChange={f('scope1EmissionsTco2')} min="0" /></Row>
        <Row label="Annual Revenue (€)"><Inp value={form.annualRevenueEur} onChange={f('annualRevenueEur')} min="0" /></Row>
        <Row label="Emission Monitoring System">
          <button onClick={() => setForm(p => ({ ...p, hasEmissionMonitoring: !p.hasEmissionMonitoring }))}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${form.hasEmissionMonitoring ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-gray-50 text-gray-600 border-gray-300'}`}>
            {form.hasEmissionMonitoring ? 'Yes — MRV in place' : 'No — MRV required'}
          </button>
        </Row>
        <Row label="Energy Audit Completed">
          <button onClick={() => setForm(p => ({ ...p, hasEnergyAudit: !p.hasEnergyAudit }))}
            className={`px-4 py-1.5 rounded-lg text-xs font-semibold border transition-colors ${form.hasEnergyAudit ? 'bg-emerald-50 text-emerald-700 border-emerald-300' : 'bg-gray-50 text-gray-600 border-gray-300'}`}>
            {form.hasEnergyAudit ? 'Yes — EED Art. 8 compliant' : 'No — Audit recommended'}
          </button>
        </Row>
        <Row label="Planned Retrofit Year">
          <Sel value={form.plannedRetrofitYear} onChange={f('plannedRetrofitYear')}
            options={[2026,2027,2028,2029,2030,2031,2032].map(y => ({ value: String(y), label: String(y) }))} />
        </Row>
        <div className="mt-4"><Btn onClick={compute} loading={loading}>Assess ETS2 Readiness</Btn></div>
      </Section>

      <div className="space-y-4">
        {result ? (
          <>
            <div className={`rounded-xl border p-4 ${result.in_scope ? 'bg-amber-50 border-amber-200' : 'bg-gray-50 border-gray-200'}`}>
              <div className="flex items-center gap-2 mb-3">
                <AlertTriangle className={`w-5 h-5 ${result.in_scope ? 'text-amber-600' : 'text-gray-400'}`} />
                <span className={`text-sm font-bold ${result.in_scope ? 'text-amber-700' : 'text-gray-600'}`}>
                  {result.in_scope ? 'IN SCOPE — ETS2 from 2027' : 'OUT OF SCOPE'}
                </span>
              </div>
              <div className="grid grid-cols-2 gap-3 text-xs mb-3">
                <div><span className="text-gray-500">Estimated Annual Emissions</span><div className="font-mono font-bold text-gray-900 text-base">{(result.estimated_annual_emissions_tco2 / 1000).toFixed(1)}k tCO₂</div></div>
                <div><span className="text-gray-500">Est. Compliance Cost (2027)</span><div className="font-mono font-bold text-amber-700 text-base">€{(result.estimated_compliance_cost_eur / 1e6).toFixed(2)}M</div></div>
                <div>
                  <span className="text-gray-500">Readiness Score</span>
                  <div className={`font-mono font-bold text-base ${result.readiness_rating === 'HIGH' ? 'text-emerald-700' : result.readiness_rating === 'MEDIUM' ? 'text-amber-700' : 'text-red-700'}`}>
                    {result.readiness_score}/100 — {result.readiness_rating}
                  </div>
                </div>
                <div><span className="text-gray-500">Start Date</span><div className="font-mono font-bold text-gray-900 text-base">{result.start_date}</div></div>
              </div>
            </div>

            {result.gaps?.length > 0 && (
              <Section title="Readiness Gaps">
                <ul className="space-y-1">
                  {result.gaps.map((g, i) => (
                    <li key={i} className="flex items-start gap-2 text-xs text-red-700">
                      <AlertTriangle className="w-3 h-3 mt-0.5 shrink-0" /> {g}
                    </li>
                  ))}
                </ul>
              </Section>
            )}

            <Section title="Action Plan">
              <ol className="space-y-1">
                {(result.action_plan || []).map((a, i) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-gray-700">
                    <span className="font-bold text-black w-4 shrink-0">{i + 1}.</span> {a}
                  </li>
                ))}
              </ol>
            </Section>
          </>
        ) : (
          <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
            <Info className="w-4 h-4 mr-2" /> Configure parameters and assess readiness
          </div>
        )}
      </div>
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Main Page
// ═══════════════════════════════════════════════════════════════════════
export default function GarEtsPage() {
  const [activeTab, setActiveTab] = useState('gar');

  return (
    <div className="min-h-screen bg-white">
      <DemoBanner message="GAR ratios, ETS allocation figures, and carbon price forecasts display deterministic sample data. Upload your portfolio and connect the EU ETS database to see live values." />
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-gray-900">GAR & EU ETS</h1>
            <p className="text-xs text-gray-500 mt-0.5">
              Green Asset Ratio (CRR Art. 449a) · EU ETS Phase 4 · ETS2 Buildings & Transport
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-bold px-2 py-1 rounded bg-emerald-50 text-emerald-700 border border-emerald-200">EU TAXONOMY</span>
            <span className="text-[10px] font-bold px-2 py-1 rounded bg-blue-50 text-blue-700 border border-blue-200">ETS PHASE 4</span>
            <span className="text-[10px] font-bold px-2 py-1 rounded bg-amber-50 text-amber-700 border border-amber-200">ETS2 2027</span>
          </div>
        </div>

        {/* Tab bar */}
        <div className="flex gap-1 mt-4 overflow-x-auto">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold whitespace-nowrap transition-colors ${active ? 'bg-black text-white' : 'text-gray-600 hover:bg-gray-100'}`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>
      </div>

      {/* Content */}
      <div className="p-6">
        {activeTab === 'gar' && <GARDashboard />}
        {activeTab === 'alloc' && <FreeAllocationTab />}
        {activeTab === 'compliance' && <ETSComplianceTab />}
        {activeTab === 'price' && <CarbonPriceForecastTab />}
        {activeTab === 'ets2' && <ETS2ReadinessTab />}
      </div>
    </div>
  );
}
