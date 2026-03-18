/**
 * BaselCapitalPage.jsx
 * Route: /basel-capital
 * Badge: Basel IV·CRR3
 *
 * Tab 1 — Capital Adequacy      POST /api/v1/basel-capital/capital-adequacy
 * Tab 2 — Credit Risk           POST /api/v1/basel-capital/credit-risk
 * Tab 3 — Market Risk           POST /api/v1/basel-capital/market-risk
 * Tab 4 — Liquidity             POST /api/v1/basel-capital/liquidity
 * Tab 5 — Climate Add-ons       POST /api/v1/basel-capital/climate-risk-capital
 */
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend, PieChart, Pie, LineChart, Line,
  RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  ReferenceLine,
} from 'recharts';
import DemoBanner from '../../../components/shared/DemoBanner';

const BASE = '/api/v1';
const TOOLTIP_STYLE = { backgroundColor: '#fff', border: '1px solid rgba(0,0,0,0.08)', color: '#111', fontSize: 11 };

/* ── Seed RNG ───────────────────────────────────────────────────────────── */
function mkRng(seed) {
  let s = seed;
  return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; };
}

/* ── Shared primitives ──────────────────────────────────────────────────── */
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

function KpiCard({ label, value, sub, color = 'text-gray-900', threshold, thresholdLabel }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
      {threshold && <p className="text-[10px] text-gray-400 mt-0.5">Min: {thresholdLabel || threshold}</p>}
    </div>
  );
}

function Badge({ label, color }) {
  const cls = {
    green:  'bg-emerald-50 text-emerald-700 border-emerald-200',
    amber:  'bg-amber-50 text-amber-700 border-amber-200',
    red:    'bg-red-50 text-red-700 border-red-200',
    blue:   'bg-blue-50 text-blue-700 border-blue-200',
    gray:   'bg-gray-50 text-gray-600 border-gray-200',
  }[color] || 'bg-gray-50 text-gray-600 border-gray-200';
  return <span className={`px-1.5 py-0.5 rounded border text-[10px] font-medium ${cls}`}>{label}</span>;
}

function Inp({ label, value, onChange, type = 'text' }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</label>
      <input
        type={type}
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-emerald-400"
      />
    </div>
  );
}

function Sel({ label, value, onChange, options }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-[10px] text-gray-500 uppercase tracking-wider">{label}</label>
      <select
        value={value}
        onChange={e => onChange(e.target.value)}
        className="border border-gray-200 rounded px-2.5 py-1.5 text-xs text-gray-800 focus:outline-none focus:border-emerald-400 bg-white"
      >
        {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
      </select>
    </div>
  );
}

function Btn({ onClick, children, disabled }) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className="px-4 py-1.5 bg-black text-white text-xs font-medium rounded hover:bg-gray-800 disabled:opacity-50 transition-colors"
    >
      {children}
    </button>
  );
}

/* ── Gauge component ────────────────────────────────────────────────────── */
function Gauge({ value, min = 0, max = 25, threshold, label, unit = '%' }) {
  const pct = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));
  const color = value >= threshold ? 'bg-emerald-500' : value >= threshold * 0.8 ? 'bg-amber-500' : 'bg-red-500';
  return (
    <div className="p-3 bg-gray-50 rounded-lg">
      <p className="text-[10px] text-gray-500 uppercase mb-1">{label}</p>
      <div className="flex items-baseline gap-1 mb-2">
        <span className={`text-2xl font-bold font-mono ${value >= threshold ? 'text-emerald-600' : 'text-amber-600'}`}>{value.toFixed(1)}</span>
        <span className="text-xs text-gray-500">{unit}</span>
        <span className="text-[10px] text-gray-400 ml-1">min: {threshold}{unit}</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-3 relative">
        <div className={`h-3 rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
        <div
          className="absolute top-0 h-3 w-0.5 bg-black/40"
          style={{ left: `${((threshold - min) / (max - min)) * 100}%` }}
        />
      </div>
    </div>
  );
}

/* ── Tab 1: Capital Adequacy ────────────────────────────────────────────── */
const CAP_FORM_DEFAULT = {
  entity_name: 'Demo Bank AG',
  rwa_credit: '45000',
  rwa_market: '8500',
  rwa_operational: '6500',
  tier1_capital: '6200',
  cet1_capital: '5400',
  total_capital: '7100',
};

function CapitalAdequacy() {
  const [form, setForm] = useState(CAP_FORM_DEFAULT);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const calcLocal = () => {
    const totalRWA = Number(form.rwa_credit) + Number(form.rwa_market) + Number(form.rwa_operational);
    return {
      total_rwa: totalRWA,
      cet1_ratio: (Number(form.cet1_capital) / totalRWA) * 100,
      tier1_ratio: (Number(form.tier1_capital) / totalRWA) * 100,
      total_car: (Number(form.total_capital) / totalRWA) * 100,
    };
  };

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/basel-capital/capital-adequacy`, form);
      setResult(r.data);
    } catch {
      setResult(calcLocal());
    }
    setLoading(false);
  };

  useEffect(() => { setResult(calcLocal()); }, []);

  const res = result || calcLocal();
  const rwaData = [
    { name: 'Credit Risk', rwa: Number(form.rwa_credit), fill: '#3b82f6' },
    { name: 'Market Risk', rwa: Number(form.rwa_market), fill: '#f59e0b' },
    { name: 'Operational', rwa: Number(form.rwa_operational), fill: '#8b5cf6' },
  ];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="CET1 Ratio" value={`${res.cet1_ratio?.toFixed(1)}%`} sub="Min 4.5% + 2.5% buffer" color={res.cet1_ratio >= 7 ? 'text-emerald-600' : 'text-amber-600'} />
        <KpiCard label="Tier 1 Ratio" value={`${res.tier1_ratio?.toFixed(1)}%`} sub="Min 6.0% + buffer" color={res.tier1_ratio >= 8 ? 'text-emerald-600' : 'text-amber-600'} />
        <KpiCard label="Total CAR" value={`${res.total_car?.toFixed(1)}%`} sub="Min 8.0% regulatory" color={res.total_car >= 10 ? 'text-emerald-600' : 'text-red-600'} />
        <KpiCard label="Total RWA" value={`€${(res.total_rwa / 1000).toFixed(0)}B`} sub="Risk-weighted assets" />
      </div>

      <Section title="RWA Composition">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
          <Inp label="Credit Risk RWA (€M)" value={form.rwa_credit} onChange={v => setForm(f => ({ ...f, rwa_credit: v }))} type="number" />
          <Inp label="Market Risk RWA (€M)" value={form.rwa_market} onChange={v => setForm(f => ({ ...f, rwa_market: v }))} type="number" />
          <Inp label="Operational RWA (€M)" value={form.rwa_operational} onChange={v => setForm(f => ({ ...f, rwa_operational: v }))} type="number" />
          <Inp label="CET1 Capital (€M)" value={form.cet1_capital} onChange={v => setForm(f => ({ ...f, cet1_capital: v }))} type="number" />
          <Inp label="Tier 1 Capital (€M)" value={form.tier1_capital} onChange={v => setForm(f => ({ ...f, tier1_capital: v }))} type="number" />
          <Inp label="Total Capital (€M)" value={form.total_capital} onChange={v => setForm(f => ({ ...f, total_capital: v }))} type="number" />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Calculating…' : 'Calculate Capital Adequacy'}</Btn>
      </Section>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Section title="Capital Ratios vs Thresholds">
          <div className="space-y-3">
            <Gauge value={res.cet1_ratio || 0} threshold={7} max={20} label="CET1 Ratio" />
            <Gauge value={res.tier1_ratio || 0} threshold={8.5} max={20} label="Tier 1 Ratio" />
            <Gauge value={res.total_car || 0} threshold={10.5} max={25} label="Total CAR" />
          </div>
        </Section>

        <Section title="RWA Breakdown">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={rwaData} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} unit="M" />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`€${v.toLocaleString()}M`]} />
              <Bar dataKey="rwa" radius={[4, 4, 0, 0]}>
                {rwaData.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 2: Credit Risk ─────────────────────────────────────────────────── */
const rngCR = mkRng(1001);
const CR_COMPARISON = [
  { approach: 'SA — Corporates', sa_rw: 100, irb_rw: Math.round(60 + rngCR() * 40), exposure: 5000 },
  { approach: 'SA — Banks', sa_rw: 40, irb_rw: Math.round(20 + rngCR() * 30), exposure: 3200 },
  { approach: 'SA — Mortgages', sa_rw: 35, irb_rw: Math.round(15 + rngCR() * 20), exposure: 8500 },
  { approach: 'SA — SME', sa_rw: 75, irb_rw: Math.round(40 + rngCR() * 35), exposure: 2100 },
  { approach: 'SA — Sovereign', sa_rw: 0, irb_rw: Math.round(5 + rngCR() * 20), exposure: 6000 },
  { approach: 'SA — Equity', sa_rw: 100, irb_rw: Math.round(70 + rngCR() * 30), exposure: 800 },
];

function CreditRisk() {
  const [form, setForm] = useState({ pd: '1.5', lgd: '45', ead: '10000', approach: 'irb_foundation' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const calcEL = () => ({
    el: ((Number(form.pd) / 100) * (Number(form.lgd) / 100) * Number(form.ead)).toFixed(2),
    irb_rwa: (Number(form.ead) * (Number(form.pd) / 100) * 12.5).toFixed(0),
  });

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/basel-capital/credit-risk`, form);
      setResult(r.data);
    } catch {
      setResult(calcEL());
    }
    setLoading(false);
  };

  const res = result || calcEL();

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Expected Loss" value={`€${Number(res.el || 0).toLocaleString()}`} sub="PD × LGD × EAD" color="text-amber-600" />
        <KpiCard label="IRB RWA" value={`€${Number(res.irb_rwa || 0).toLocaleString()}M`} sub="Risk-weighted assets" />
        <KpiCard label="Output Floor (CRR3)" value="72.5%" sub="vs SA RWA floor" />
        <KpiCard label="Approach" value={form.approach === 'irb_foundation' ? 'F-IRB' : 'SA'} sub="Basel IV CRR3" />
      </div>

      <Section title="Credit Risk — PD/LGD/EAD Inputs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
          <Inp label="PD (%)" value={form.pd} onChange={v => setForm(f => ({ ...f, pd: v }))} type="number" />
          <Inp label="LGD (%)" value={form.lgd} onChange={v => setForm(f => ({ ...f, lgd: v }))} type="number" />
          <Inp label="EAD (€M)" value={form.ead} onChange={v => setForm(f => ({ ...f, ead: v }))} type="number" />
          <Sel label="Approach" value={form.approach} onChange={v => setForm(f => ({ ...f, approach: v }))} options={[
            { value: 'sa', label: 'Standardised (SA)' },
            { value: 'irb_foundation', label: 'Foundation IRB (F-IRB)' },
            { value: 'irb_advanced', label: 'Advanced IRB (A-IRB)' },
          ]} />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Calculating…' : 'Calculate Credit Risk'}</Btn>
      </Section>

      <Section title="SA vs IRB Risk-Weight Comparison by Asset Class (CRR3)">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={CR_COMPARISON} margin={{ left: 10, right: 20, top: 4, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="approach" tick={{ fontSize: 9 }} angle={-30} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10 }} unit="%" domain={[0, 120]} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}%`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="sa_rw" name="SA Risk Weight %" fill="#111" radius={[3, 3, 0, 0]} />
            <Bar dataKey="irb_rw" name="IRB Risk Weight %" fill="#10b981" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 3: Market Risk ─────────────────────────────────────────────────── */
const rngMR = mkRng(1101);
const MR_SEED = [
  { desk: 'FX Trading', var_1d: 2.1 + rngMR() * 1.5, svar: 4.8 + rngMR() * 2, ima: true },
  { desk: 'Rates', var_1d: 3.5 + rngMR() * 2, svar: 8.2 + rngMR() * 3, ima: true },
  { desk: 'Credit', var_1d: 1.8 + rngMR() * 1, svar: 4.1 + rngMR() * 2, ima: false },
  { desk: 'Equity', var_1d: 2.9 + rngMR() * 2, svar: 6.5 + rngMR() * 2.5, ima: true },
  { desk: 'Commodities', var_1d: 1.5 + rngMR() * 1.2, svar: 3.8 + rngMR() * 1.5, ima: false },
];

function MarketRisk() {
  const [form, setForm] = useState({ approach: 'frtb_sa', sensitivity_type: 'delta', confidence: '99', horizon: '10' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/basel-capital/market-risk`, form);
      setResult(r.data);
    } catch {
      const rngR = mkRng(1111);
      setResult({
        total_var_eur: 11.8 + rngR() * 3,
        total_svar_eur: 27.4 + rngR() * 5,
        frtb_sa_capital: 380 + rngR() * 80,
        frtb_ima_capital: 290 + rngR() * 60,
        pla_test_pass: rngR() > 0.3,
      });
    }
    setLoading(false);
  };

  useEffect(() => { submit(); }, []);

  const res = result || {};

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Total VaR" value={`€${res.total_var_eur?.toFixed(1) || '—'}M`} sub="99% / 1-day" color="text-amber-600" />
        <KpiCard label="Stressed VaR" value={`€${res.total_svar_eur?.toFixed(1) || '—'}M`} sub="Stressed period" color="text-red-600" />
        <KpiCard label="FRTB SA Capital" value={`€${res.frtb_sa_capital?.toFixed(0) || '—'}M`} sub="Standardised approach" />
        <KpiCard label="P&L Attribution" value={res.pla_test_pass == null ? '—' : res.pla_test_pass ? 'Pass' : 'Fail'} sub="IMA desk approval" color={res.pla_test_pass ? 'text-emerald-600' : 'text-red-600'} />
      </div>

      <Section title="FRTB Market Risk Configuration">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
          <Sel label="Approach" value={form.approach} onChange={v => setForm(f => ({ ...f, approach: v }))} options={[
            { value: 'frtb_sa', label: 'FRTB Standardised (SA)' },
            { value: 'frtb_ima', label: 'FRTB Internal Model (IMA)' },
            { value: 'legacy_var', label: 'Legacy VaR (pre-FRTB)' },
          ]} />
          <Sel label="Sensitivity Type" value={form.sensitivity_type} onChange={v => setForm(f => ({ ...f, sensitivity_type: v }))} options={[
            { value: 'delta', label: 'Delta' }, { value: 'vega', label: 'Vega' }, { value: 'curvature', label: 'Curvature' },
          ]} />
          <Inp label="Confidence Level (%)" value={form.confidence} onChange={v => setForm(f => ({ ...f, confidence: v }))} type="number" />
          <Inp label="Holding Period (days)" value={form.horizon} onChange={v => setForm(f => ({ ...f, horizon: v }))} type="number" />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Calculating…' : 'Run Market Risk Calculation'}</Btn>
      </Section>

      <Section title="VaR / SVaR by Trading Desk — FRTB">
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={MR_SEED} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="desk" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="M" />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`€${Number(v).toFixed(2)}M`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="var_1d" name="VaR (1-day)" fill="#111" radius={[3, 3, 0, 0]} />
            <Bar dataKey="svar" name="Stressed VaR" fill="#ef4444" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>
    </div>
  );
}

/* ── Tab 4: Liquidity ───────────────────────────────────────────────────── */
const rngLiq = mkRng(1201);
const HQLA_DATA = [
  { name: 'L1 — Cash & CB Reserves', value: 3500, fill: '#10b981' },
  { name: 'L1 — Govt Bonds', value: 8200, fill: '#3b82f6' },
  { name: 'L2A — Agency Bonds', value: 2100, fill: '#f59e0b' },
  { name: 'L2B — Corp Bonds (IG)', value: 800, fill: '#8b5cf6' },
  { name: 'L2B — Equities (index)', value: 400, fill: '#f43f5e' },
];

function Liquidity() {
  const [form, setForm] = useState({ hqla: '14500', net_outflows_30d: '11200', available_stable: '58000', required_stable: '51000' });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const calcLocal = () => ({
    lcr: (Number(form.hqla) / Number(form.net_outflows_30d)) * 100,
    nsfr: (Number(form.available_stable) / Number(form.required_stable)) * 100,
  });

  const submit = async () => {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/basel-capital/liquidity`, form);
      setResult(r.data);
    } catch {
      setResult(calcLocal());
    }
    setLoading(false);
  };

  useEffect(() => { setResult(calcLocal()); }, []);

  const res = result || calcLocal();

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="LCR" value={`${res.lcr?.toFixed(1)}%`} sub="Min 100% — Basel III" color={res.lcr >= 100 ? 'text-emerald-600' : 'text-red-600'} />
        <KpiCard label="NSFR" value={`${res.nsfr?.toFixed(1)}%`} sub="Min 100% — Basel III" color={res.nsfr >= 100 ? 'text-emerald-600' : 'text-red-600'} />
        <KpiCard label="HQLA" value={`€${(Number(form.hqla) / 1000).toFixed(1)}B`} sub="High-quality liquid assets" />
        <KpiCard label="Net 30d Outflows" value={`€${(Number(form.net_outflows_30d) / 1000).toFixed(1)}B`} sub="Net cash outflows" />
      </div>

      <Section title="LCR & NSFR Inputs">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-3">
          <Inp label="HQLA (€M)" value={form.hqla} onChange={v => setForm(f => ({ ...f, hqla: v }))} type="number" />
          <Inp label="Net 30d Outflows (€M)" value={form.net_outflows_30d} onChange={v => setForm(f => ({ ...f, net_outflows_30d: v }))} type="number" />
          <Inp label="Available Stable Funding (€M)" value={form.available_stable} onChange={v => setForm(f => ({ ...f, available_stable: v }))} type="number" />
          <Inp label="Required Stable Funding (€M)" value={form.required_stable} onChange={v => setForm(f => ({ ...f, required_stable: v }))} type="number" />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Calculating…' : 'Calculate Liquidity Ratios'}</Btn>
      </Section>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Section title="LCR & NSFR Gauges">
          <div className="space-y-4">
            <Gauge value={res.lcr || 0} threshold={100} max={200} label="Liquidity Coverage Ratio (LCR)" />
            <Gauge value={res.nsfr || 0} threshold={100} max={150} label="Net Stable Funding Ratio (NSFR)" />
          </div>
        </Section>

        <Section title="HQLA Composition">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={HQLA_DATA}
                cx="50%" cy="50%"
                outerRadius={80}
                dataKey="value"
                nameKey="name"
                label={({ name, percent }) => `${(percent * 100).toFixed(0)}%`}
                labelLine={false}
              >
                {HQLA_DATA.map((d, i) => <Cell key={i} fill={d.fill} />)}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v, n) => [`€${v.toLocaleString()}M`, n]} />
              <Legend iconSize={10} wrapperStyle={{ fontSize: '10px' }} />
            </PieChart>
          </ResponsiveContainer>
        </Section>
      </div>
    </div>
  );
}

/* ── Tab 5: Climate Add-ons ─────────────────────────────────────────────── */
const SECTOR_CLIMATE = [
  { sector: 'Energy', base_rwa: 4200, physical_uplift: 0.18, transition_uplift: 0.25 },
  { sector: 'Transport', base_rwa: 2800, physical_uplift: 0.12, transition_uplift: 0.20 },
  { sector: 'Real Estate', base_rwa: 8500, physical_uplift: 0.22, transition_uplift: 0.08 },
  { sector: 'Agriculture', base_rwa: 1200, physical_uplift: 0.28, transition_uplift: 0.15 },
  { sector: 'Manufacturing', base_rwa: 3100, physical_uplift: 0.10, transition_uplift: 0.18 },
  { sector: 'Mining', base_rwa: 900, physical_uplift: 0.15, transition_uplift: 0.30 },
];

function ClimateAddons() {
  const [scenario, setScenario] = useState('delayed_transition');
  const [form, setForm] = useState({ horizon: '2030', confidence: '95' });
  const [loading, setLoading] = useState(false);

  const scenarioMultipliers = {
    net_zero_2050: { physical: 0.6, transition: 1.5 },
    below_2c: { physical: 0.8, transition: 1.2 },
    delayed_transition: { physical: 1.0, transition: 1.8 },
    current_policies: { physical: 1.4, transition: 0.8 },
  };

  const mult = scenarioMultipliers[scenario] || { physical: 1, transition: 1 };

  const enrichedData = SECTOR_CLIMATE.map(s => ({
    ...s,
    climate_rwa_uplift: Math.round(s.base_rwa * ((s.physical_uplift * mult.physical + s.transition_uplift * mult.transition) / 2)),
    total_rwa: Math.round(s.base_rwa * (1 + (s.physical_uplift * mult.physical + s.transition_uplift * mult.transition) / 2)),
    physical_add_on_pct: (s.physical_uplift * mult.physical * 100).toFixed(1),
    transition_add_on_pct: (s.transition_uplift * mult.transition * 100).toFixed(1),
  }));

  const totalBaseRWA = enrichedData.reduce((a, b) => a + b.base_rwa, 0);
  const totalClimateRWA = enrichedData.reduce((a, b) => a + b.total_rwa, 0);
  const avgUplift = ((totalClimateRWA - totalBaseRWA) / totalBaseRWA * 100).toFixed(1);

  const submit = async () => {
    setLoading(true);
    try {
      await axios.post(`${BASE}/basel-capital/climate-risk-capital`, { scenario, ...form });
    } catch {}
    setLoading(false);
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Base RWA" value={`€${(totalBaseRWA / 1000).toFixed(1)}B`} sub="Pre-climate adjustment" />
        <KpiCard label="Climate-Adjusted RWA" value={`€${(totalClimateRWA / 1000).toFixed(1)}B`} sub="Post-climate add-on" color="text-amber-600" />
        <KpiCard label="Average Uplift" value={`+${avgUplift}%`} sub="Climate RWA increase" color="text-red-600" />
        <KpiCard label="Scenario" value={scenario.replace('_', ' ')} sub="NGFS scenario" />
      </div>

      <Section title="Climate RWA Scenario">
        <div className="grid grid-cols-3 gap-3 mb-3">
          <Sel label="NGFS Scenario" value={scenario} onChange={setScenario} options={[
            { value: 'net_zero_2050', label: 'Net Zero 2050' },
            { value: 'below_2c', label: 'Below 2°C' },
            { value: 'delayed_transition', label: 'Delayed Transition' },
            { value: 'current_policies', label: 'Current Policies' },
          ]} />
          <Inp label="Horizon Year" value={form.horizon} onChange={v => setForm(f => ({ ...f, horizon: v }))} />
          <Inp label="Confidence Level (%)" value={form.confidence} onChange={v => setForm(f => ({ ...f, confidence: v }))} type="number" />
        </div>
        <Btn onClick={submit} disabled={loading}>{loading ? 'Running…' : 'Calculate Climate Capital Add-ons'}</Btn>
      </Section>

      <Section title="Climate-Adjusted RWA by Sector">
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={enrichedData} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="sector" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit="M" />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`€${v.toLocaleString()}M`]} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: '11px' }} />
            <Bar dataKey="base_rwa" name="Base RWA" fill="#e5e7eb" radius={[3, 3, 0, 0]} stackId="a" />
            <Bar dataKey="climate_rwa_uplift" name="Climate Add-on" fill="#ef4444" radius={[3, 3, 0, 0]} stackId="a" />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Sector-Level Climate Add-on Detail">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-gray-200">
                {['Sector', 'Base RWA (€M)', 'Physical Add-on', 'Transition Add-on', 'Climate RWA Uplift', 'Total RWA'].map(h => (
                  <th key={h} className="text-left py-2 px-2 text-gray-500 font-medium">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {enrichedData.map((row, i) => (
                <tr key={i} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-2 font-medium text-gray-800">{row.sector}</td>
                  <td className="py-2 px-2 font-mono">{row.base_rwa.toLocaleString()}</td>
                  <td className="py-2 px-2 font-mono text-blue-700">+{row.physical_add_on_pct}%</td>
                  <td className="py-2 px-2 font-mono text-amber-700">+{row.transition_add_on_pct}%</td>
                  <td className="py-2 px-2 font-mono text-red-700">+{row.climate_rwa_uplift.toLocaleString()}</td>
                  <td className="py-2 px-2 font-mono font-semibold text-gray-800">{row.total_rwa.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Section>
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────── */
const TABS = [
  { id: 'capital', label: 'Capital Adequacy' },
  { id: 'credit', label: 'Credit Risk' },
  { id: 'market', label: 'Market Risk' },
  { id: 'liquidity', label: 'Liquidity' },
  { id: 'climate', label: 'Climate Add-ons' },
];

export default function BaselCapitalPage() {
  const [tab, setTab] = useState('capital');

  return (
    <div className="p-4 max-w-7xl mx-auto">
      <DemoBanner />
      <div className="mb-4">
        <div className="flex items-center gap-3 mb-1">
          <h1 className="text-lg font-semibold text-gray-900">Basel IV Capital</h1>
          <span className="text-[10px] font-mono font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded">Basel IV·CRR3</span>
        </div>
        <p className="text-xs text-gray-500">Basel IV / CRR3 capital adequacy, credit risk (SA/IRB), market risk (FRTB), liquidity (LCR/NSFR) and climate-adjusted RWA add-ons.</p>
      </div>

      <div className="flex gap-1 mb-5 border-b border-gray-200 overflow-x-auto">
        {TABS.map(t => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-4 py-2.5 text-xs font-medium whitespace-nowrap transition-colors border-b-2 -mb-px ${tab === t.id ? 'border-emerald-500 text-emerald-700' : 'border-transparent text-gray-500 hover:text-gray-800'}`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'capital'   && <CapitalAdequacy />}
      {tab === 'credit'    && <CreditRisk />}
      {tab === 'market'    && <MarketRisk />}
      {tab === 'liquidity' && <Liquidity />}
      {tab === 'climate'   && <ClimateAddons />}
    </div>
  );
}
