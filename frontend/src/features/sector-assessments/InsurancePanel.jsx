/**
 * Insurance Climate Risk Panel
 * Solvency II Article 44a (2024) / EIOPA ORSA Climate Guide 2022
 * Swiss Re sigma Physical Risk Model / Lloyd's RDS
 *
 * Calculates: CAT loss (1-in-100 / 1-in-250), Technical Provision uplift,
 *             SCR climate add-on, reserve adequacy, protection gap.
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "http://localhost:8001";
const fmt = (v, dp = 1) => v == null ? "—" : Number(v).toFixed(dp);
const fmtM = (v) => v == null ? "—" : `€${(Number(v) / 1e6).toFixed(2)}M`;
const fmtPct = (v) => v == null ? "—" : `${(Number(v) * 100).toFixed(1)}%`;

function Badge({ label, color = "bg-white/[0.06] text-white/60" }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = "" }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.04]">
          {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
          {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
function StatCard({ label, value, sub, color = "text-white" }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
      <p className="text-xs text-white/40 font-medium mb-1">{label}</p>
      <p className={`text-xl font-bold ${color}`}>{value}</p>
      {sub && <p className="text-[11px] text-white/30 mt-1">{sub}</p>}
    </div>
  );
}
function Field({ label, hint, children }) {
  return (
    <div>
      <label className="block text-xs font-medium text-white/60 mb-1">{label}</label>
      {children}
      {hint && <p className="text-[10px] text-white/30 mt-0.5">{hint}</p>}
    </div>
  );
}
function Input({ value, onChange, type = "text", ...rest }) {
  return (
    <input type={type} value={value}
      onChange={e => onChange(type === "number" ? parseFloat(e.target.value) || 0 : e.target.value)}
      className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
      {...rest} />
  );
}
function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full border border-white/[0.06] rounded-lg bg-[#0b1120] text-white/70 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-cyan-400/50">
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}

const PERILS = [
  { v: "tropical_cyclone", l: "Tropical Cyclone" },
  { v: "flood", l: "Flood" },
  { v: "wildfire", l: "Wildfire" },
  { v: "drought", l: "Drought" },
  { v: "winter_storm", l: "Winter Storm" },
  { v: "hail", l: "Hail" },
  { v: "earthquake", l: "Earthquake" },
];
const SCENARIOS = [
  { v: "1.5C", l: "1.5°C — Paris-aligned" },
  { v: "2C",   l: "2°C — Orderly Transition" },
  { v: "3C",   l: "3°C — Disorderly / Hot House" },
];
const HORIZONS = [
  { v: 2030, l: "2030 (Near-term)" },
  { v: 2040, l: "2040 (Medium-term)" },
  { v: 2050, l: "2050 (Long-term)" },
];
const ENTITY_TYPES = [
  { v: "insurer", l: "Insurer (Primary)" },
  { v: "reinsurer", l: "Reinsurer" },
  { v: "captive", l: "Captive Insurance" },
];

const DEFAULT_FORM = {
  entity_name: "Hypothetical P&C Insurer",
  entity_type: "insurer",
  domicile_country: "GB",
  perils_exposed: ["flood", "wildfire"],
  lines_of_business: ["property"],
  gross_written_premium: 500e6,
  technical_provisions: 1200e6,
  gross_cat_loss_1_in_100: 80e6,
  gross_cat_loss_1_in_250: 160e6,
  reinsurance_recovery_pct: 0.65,
  scenario: "2C",
  horizon_year: 2050,
};

export default function InsurancePanel() {
  const [form, setForm] = useState(DEFAULT_FORM);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm(prev => ({ ...prev, [k]: v }));

  const togglePeril = (peril) => {
    setForm(prev => ({
      ...prev,
      perils_exposed: prev.perils_exposed.includes(peril)
        ? prev.perils_exposed.filter(p => p !== peril)
        : [...prev.perils_exposed, peril],
    }));
  };

  const handleCalc = async () => {
    setLoading(true); setError(null); setResult(null);
    try {
      const { data } = await axios.post(`${API}/api/v1/insurance/calculate`, form);
      setResult(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message);
    } finally {
      setLoading(false);
    }
  };

  // Chart data: baseline vs climate-adjusted CAT losses
  const catChartData = result ? [
    {
      period: "1-in-100 Gross",
      baseline: form.gross_cat_loss_1_in_100 / 1e6,
      climate: result.gross_cat_loss_1in100_climate / 1e6,
    },
    {
      period: "1-in-250 Gross",
      baseline: form.gross_cat_loss_1_in_250 / 1e6,
      climate: result.gross_cat_loss_1in250_climate / 1e6,
    },
    {
      period: "1-in-100 Net",
      baseline: (form.gross_cat_loss_1_in_100 * (1 - form.reinsurance_recovery_pct)) / 1e6,
      climate: result.net_cat_loss_1in100_climate / 1e6,
    },
    {
      period: "1-in-250 Net",
      baseline: (form.gross_cat_loss_1_in_250 * (1 - form.reinsurance_recovery_pct)) / 1e6,
      climate: result.net_cat_loss_1in250_climate / 1e6,
    },
  ] : [];

  const radarData = result ? [
    { metric: "TP Adequacy", score: Math.max(0, 100 - result.tp_uplift_pct * 500) },
    { metric: "SCR Buffer",  score: Math.max(0, 100 - result.scr_climate_loading_pct * 200) },
    { metric: "Reserve Ratio", score: Math.min(100, result.reserve_adequacy_ratio * 50) },
    { metric: "Protection Gap", score: Math.max(0, 100 - result.protection_gap_pct) },
    { metric: "ReIns Cover", score: result.reinsurance_sufficiency === "SUFFICIENT" ? 85 : result.reinsurance_sufficiency === "MARGINAL" ? 50 : 20 },
  ] : [];

  const rsSufStyle = (s) => ({
    SUFFICIENT: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
    MARGINAL: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    INSUFFICIENT: "text-red-400 bg-red-500/10 border-red-500/20",
  }[s] || "text-white/60");

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="Solvency II Art. 44a" color="bg-purple-500/10 text-purple-300" />
        <Badge label="EIOPA ORSA Climate 2022" color="bg-blue-500/10 text-blue-300" />
        <Badge label="Swiss Re sigma 2023" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="Lloyd's RDS" color="bg-amber-500/10 text-amber-400" />
        <Badge label="IPCC AR6 Physical Risk" color="bg-white/[0.06] text-white/60" />
      </div>

      <Card title="Insurance Entity Parameters"
        subtitle="Solvency II climate-adjusted CAT risk, technical provisions uplift and SCR add-on">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
          <Field label="Entity Name">
            <Input value={form.entity_name} onChange={v => set("entity_name", v)} />
          </Field>
          <Field label="Entity Type">
            <Sel value={form.entity_type} onChange={v => set("entity_type", v)} options={ENTITY_TYPES} />
          </Field>
          <Field label="Domicile Country (ISO2)">
            <Input value={form.domicile_country} onChange={v => set("domicile_country", v)} />
          </Field>
          <Field label="Gross Written Premium (EUR)">
            <Input type="number" value={form.gross_written_premium} onChange={v => set("gross_written_premium", v)} />
          </Field>
          <Field label="Technical Provisions (EUR)">
            <Input type="number" value={form.technical_provisions} onChange={v => set("technical_provisions", v)} />
          </Field>
          <Field label="Reinsurance Recovery (%)" hint="Fraction recovered from reinsurance on gross CAT losses">
            <Input type="number" value={form.reinsurance_recovery_pct * 100}
              onChange={v => set("reinsurance_recovery_pct", v / 100)} min="0" max="100" step="1" />
          </Field>
          <Field label="Gross CAT Loss 1-in-100 AEP (EUR)" hint="Current climate baseline">
            <Input type="number" value={form.gross_cat_loss_1_in_100} onChange={v => set("gross_cat_loss_1_in_100", v)} />
          </Field>
          <Field label="Gross CAT Loss 1-in-250 AEP (EUR)">
            <Input type="number" value={form.gross_cat_loss_1_in_250} onChange={v => set("gross_cat_loss_1_in_250", v)} />
          </Field>
          <Field label="Climate Scenario">
            <Sel value={form.scenario} onChange={v => set("scenario", v)} options={SCENARIOS} />
          </Field>
          <Field label="Horizon Year">
            <Sel value={form.horizon_year} onChange={v => set("horizon_year", parseInt(v))} options={HORIZONS} />
          </Field>
        </div>

        <div className="mt-5">
          <p className="text-xs font-medium text-white/60 mb-2">Perils Exposed</p>
          <div className="flex flex-wrap gap-2">
            {PERILS.map(p => (
              <button key={p.v} onClick={() => togglePeril(p.v)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium border transition-all ${
                  form.perils_exposed.includes(p.v)
                    ? "bg-cyan-400/10 border-cyan-400/30 text-cyan-300"
                    : "bg-white/[0.02] border-white/[0.06] text-white/40 hover:text-white/60"
                }`}>
                {p.l}
              </button>
            ))}
          </div>
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={handleCalc} disabled={loading}
            className="bg-cyan-400 hover:bg-cyan-300 disabled:opacity-50 text-white text-sm font-semibold px-8 py-2.5 rounded-lg transition-colors">
            {loading ? "Computing…" : "Run Insurance Climate Risk Assessment"}
          </button>
        </div>
      </Card>

      {error && (
        <div className="bg-red-500/10 border border-red-500/20 rounded-lg p-4 text-sm text-red-400">{error}</div>
      )}

      {result && (
        <div className="space-y-6">
          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="TP Climate Uplift"
              value={fmtM(result.tp_climate_uplift_eur)}
              color="text-amber-400"
              sub={`+${fmtPct(result.tp_uplift_pct)} to Technical Provisions`} />
            <StatCard label="SCR CAT Add-on"
              value={fmtM(result.scr_cat_addon_eur)}
              color="text-red-400"
              sub={`+${fmtPct(result.scr_climate_loading_pct)} Pillar 2 buffer`} />
            <StatCard label="Reserve Adequacy Ratio"
              value={`${fmt(result.reserve_adequacy_ratio, 2)}x`}
              color={result.reserve_adequacy_ratio >= 1 ? "text-emerald-400" : "text-red-400"}
              sub={result.reserve_shortfall_eur > 0 ? `Shortfall: ${fmtM(result.reserve_shortfall_eur)}` : "Reserves adequate"} />
            <StatCard label="Protection Gap"
              value={`${fmt(result.protection_gap_pct, 1)}%`}
              color={result.protection_gap_pct > 40 ? "text-red-400" : "text-amber-400"}
              sub="Economic loss not covered by insurance" />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <StatCard label="Net 1-in-100 (Climate)"
              value={fmtM(result.net_cat_loss_1in100_climate)}
              sub={`Gross: ${fmtM(result.gross_cat_loss_1in100_climate)}`} />
            <StatCard label="Net 1-in-250 (Climate)"
              value={fmtM(result.net_cat_loss_1in250_climate)}
              sub={`Gross: ${fmtM(result.gross_cat_loss_1in250_climate)}`} />
            <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-5">
              <p className="text-xs text-white/40 font-medium mb-1">Reinsurance Sufficiency</p>
              <div className={`inline-flex items-center px-3 py-1.5 rounded-lg border text-sm font-bold mt-1 ${rsSufStyle(result.reinsurance_sufficiency)}`}>
                {result.reinsurance_sufficiency}
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card title="CAT Loss: Baseline vs Climate-Adjusted" subtitle="EUR millions">
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={catChartData} barGap={4}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="period" tick={{ fontSize: 9 }} />
                  <YAxis tick={{ fontSize: 10 }} label={{ value: "€M", angle: -90, position: "insideLeft", fontSize: 10 }} />
                  <Tooltip formatter={(v) => [`€${v.toFixed(1)}M`]} />
                  <Legend />
                  <Bar dataKey="baseline" name="Baseline" fill="#6366f1" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="climate" name="Climate-Adjusted" fill="#ef4444" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Card>

            <Card title="Climate Risk Profile" subtitle="Solvency II / EIOPA composite scoring (0–100)">
              <ResponsiveContainer width="100%" height={260}>
                <RadarChart data={radarData}>
                  <PolarGrid stroke="#f1f5f9" />
                  <PolarAngleAxis dataKey="metric" tick={{ fontSize: 9 }} />
                  <Radar dataKey="score" stroke="#6366f1" fill="#6366f1" fillOpacity={0.25} name="Risk Score" />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Card>
          </div>

          {/* Solvency II Flags */}
          {result.solvency_ii_flags?.length > 0 && (
            <Card title="Solvency II / EIOPA Supervisory Flags">
              <div className="space-y-2">
                {result.solvency_ii_flags.map((flag, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400 mt-1.5 flex-shrink-0" />
                    <p className="text-xs text-amber-300">{flag}</p>
                  </div>
                ))}
              </div>
            </Card>
          )}

          {/* Methodology note */}
          <Card title="Methodology Reference">
            <div className="space-y-1 text-[11px] text-white/40">
              <p><span className="text-white/60 font-medium">CAT Loss Multipliers:</span> Swiss Re sigma 2023 / EIOPA CCRST 2022 / Lloyd's Market Risk Committee — peril × scenario scaling factors applied to current-climate baseline losses.</p>
              <p><span className="text-white/60 font-medium">TP Uplift:</span> EIOPA Supervisory Statement on Climate Risk 2024 — additional % loading on technical provisions: +4% (1.5°C), +9% (2°C), +18% (3°C).</p>
              <p><span className="text-white/60 font-medium">SCR CAT Add-on:</span> Solvency II Delegated Regulation (EU) 2015/35, Annex XIII — per-peril shock factors applied to gross written premium as Pillar 2 buffer.</p>
              <p><span className="text-white/60 font-medium">Protection Gap:</span> Economic loss estimated at 2.5× insured loss (Lloyd's / Swiss Re global sigma ratio); protection gap = 1 − (insured / economic).</p>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
