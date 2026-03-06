/**
 * ShippingPanel — IMO CII / EEXI / AER calculation.
 * Embedded in SectorAssessmentsPage.
 * Sprint 5 — WHOOP for Sustainability platform.
 */
import React, { useState } from 'react';
import axios from 'axios';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';

const API = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

const CII_COLOURS = {
  A: { bg: '#10b981', text: '#fff', label: 'Excellent' },
  B: { bg: '#34d399', text: '#fff', label: 'Good' },
  C: { bg: '#f59e0b', text: '#fff', label: 'Moderate' },
  D: { bg: '#f97316', text: '#fff', label: 'Poor — Corrective Action Plan Required' },
  E: { bg: '#ef4444', text: '#fff', label: 'Critical — Enhanced Corrective Action Plan Required' },
};

const VESSEL_TYPES = ['bulker', 'tanker', 'container', 'lng_carrier', 'ro_ro', 'general_cargo'];
const FUEL_TYPES = ['HFO', 'VLSFO', 'MDO', 'LNG', 'METHANOL', 'AMMONIA', 'HYDROGEN'];

const Field = ({ label, children, hint }) => (
  <div>
    <label className="block text-xs text-gray-400 mb-1">{label}</label>
    {children}
    {hint && <p className="text-xs text-gray-600 mt-0.5">{hint}</p>}
  </div>
);

const Num = ({ value, onChange, placeholder, min, max, step = 'any' }) => (
  <input type="number" value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
    min={min} max={max} step={step}
    className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60"
    style={{ fontFamily: 'IBM Plex Mono, monospace' }} />
);

const Select = ({ value, onChange, options }) => (
  <select value={value} onChange={e => onChange(e.target.value)}
    className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60">
    {options.map(o => <option key={o} value={o}>{o}</option>)}
  </select>
);

export default function ShippingPanel() {
  const [form, setForm] = useState({
    vessel_name: 'MV Pacific Star',
    vessel_type: 'bulker',
    dwt: 80000,
    gross_tonnage: 45000,
    fuel_type: 'VLSFO',
    annual_fuel_tonnes: 8500,
    annual_distance_nm: 75000,
    annual_cargo_tonnes: 4200000,
    build_year: 2012,
    reference_year: 2024,
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const set = (k, v) => setForm(p => ({ ...p, [k]: v }));
  const setN = (k, v) => setForm(p => ({ ...p, [k]: parseFloat(v) || 0 }));

  const handleCalculate = async () => {
    setLoading(true); setError(null);
    try {
      const resp = await axios.post(`${API}/api/v1/sector-calculators/shipping/calculate`, {
        ...form,
        dwt: parseFloat(form.dwt),
        gross_tonnage: parseFloat(form.gross_tonnage),
        annual_fuel_tonnes: parseFloat(form.annual_fuel_tonnes),
        annual_distance_nm: parseFloat(form.annual_distance_nm),
        annual_cargo_tonnes: parseFloat(form.annual_cargo_tonnes),
        build_year: parseInt(form.build_year),
        reference_year: parseInt(form.reference_year),
      });
      setResult(resp.data);
    } catch (err) {
      setError(err.response?.data?.detail || err.message);
    } finally { setLoading(false); }
  };

  const ciiInfo = result ? (CII_COLOURS[result.cii_rating] || CII_COLOURS.C) : null;

  // Efficiency improvement chart
  const improvementData = result ? [
    { name: 'Current AER', value: parseFloat(result.aer), fill: ciiInfo?.bg },
    { name: 'IMO 2030 Target', value: parseFloat(result.imo_2030_target_aer), fill: '#10b981' },
    { name: 'CII Reference', value: parseFloat(result.cii_reference), fill: '#6b7280' },
  ] : [];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-white" style={{ fontFamily: 'Space Grotesk, sans-serif' }}>Shipping Decarbonisation</h2>
        <p className="text-sm text-gray-400 mt-0.5">IMO CII Rating / EEXI / AER — 2023 GHG Strategy alignment</p>
      </div>

      {/* Form */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
        <div className="col-span-2 md:col-span-3">
          <Field label="Vessel Name">
            <input type="text" value={form.vessel_name} onChange={e => set('vessel_name', e.target.value)}
              className="w-full bg-white/5 border border-white/15 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-cyan-500/60" />
          </Field>
        </div>
        <Field label="Vessel Type"><Select value={form.vessel_type} onChange={v => set('vessel_type', v)} options={VESSEL_TYPES} /></Field>
        <Field label="Fuel Type"><Select value={form.fuel_type} onChange={v => set('fuel_type', v)} options={FUEL_TYPES} /></Field>
        <Field label="DWT" hint="Deadweight tonnage"><Num value={form.dwt} onChange={v => setN('dwt', v)} placeholder="80000" /></Field>
        <Field label="Gross Tonnage"><Num value={form.gross_tonnage} onChange={v => setN('gross_tonnage', v)} placeholder="45000" /></Field>
        <Field label="Annual Fuel (tonnes)"><Num value={form.annual_fuel_tonnes} onChange={v => setN('annual_fuel_tonnes', v)} placeholder="8500" /></Field>
        <Field label="Annual Distance (nm)"><Num value={form.annual_distance_nm} onChange={v => setN('annual_distance_nm', v)} placeholder="75000" /></Field>
        <Field label="Annual Cargo (tonnes)"><Num value={form.annual_cargo_tonnes} onChange={v => setN('annual_cargo_tonnes', v)} placeholder="4200000" /></Field>
        <Field label="Build Year"><Num value={form.build_year} onChange={v => setN('build_year', v)} min={1950} max={2025} step={1} /></Field>
      </div>

      <button onClick={handleCalculate} disabled={loading}
        className="w-full py-3 rounded-lg text-sm font-semibold text-white disabled:opacity-50"
        style={{ background: 'linear-gradient(135deg, hsl(199,89%,40%), hsl(199,89%,30%))' }}
        data-testid="shipping-calculate-btn">
        {loading ? 'Calculating...' : 'Calculate CII Rating'}
      </button>

      {error && <div className="bg-red-500/10 border border-red-500/30 rounded p-3 text-sm text-red-400">{error}</div>}

      {result && (
        <div className="space-y-5">
          {/* CII Grade Card — WHOOP-style prominent score */}
          <div className="rounded-xl p-6 flex items-center gap-6"
            style={{ background: `${ciiInfo?.bg}20`, border: `1px solid ${ciiInfo?.bg}40` }}>
            <div className="flex-shrink-0 w-20 h-20 rounded-full flex items-center justify-center text-4xl font-black border-4"
              style={{ color: ciiInfo?.bg, borderColor: ciiInfo?.bg, fontFamily: 'Space Grotesk, sans-serif' }}
              data-testid="shipping-cii-rating">
              {result.cii_rating}
            </div>
            <div>
              <div className="text-sm text-gray-400">CII Rating — {form.vessel_name}</div>
              <div className="text-lg font-semibold text-white mt-0.5">{ciiInfo?.label}</div>
              <div className="text-sm text-gray-400 mt-1">
                AER: <span className="text-white font-mono">{parseFloat(result.aer).toFixed(3)}</span> gCO₂/dwt-nm
                &nbsp;|&nbsp; EEXI: <span className="text-white font-mono">{result.eexi ? parseFloat(result.eexi).toFixed(3) : '—'}</span>
              </div>
            </div>
          </div>

          {/* Key metrics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Annual CO₂', value: `${(parseFloat(result.annual_co2_tonnes) / 1000).toFixed(1)} kt`, sub: 'tCO₂ per year' },
              { label: 'AER', value: `${parseFloat(result.aer).toFixed(3)}`, sub: 'gCO₂/dwt-nm', testId: 'shipping-aer' },
              { label: 'vs IMO 2030', value: `${parseFloat(result.pct_vs_2030_target) > 0 ? '+' : ''}${parseFloat(result.pct_vs_2030_target).toFixed(1)}%`, sub: parseFloat(result.pct_vs_2030_target) > 0 ? 'Above target' : 'On track' },
              { label: 'Stranding Year', value: result.projected_stranding_year || '—', sub: result.projected_stranding_year ? 'Projected CII D/E' : 'No imminent risk' },
            ].map((k, i) => (
              <div key={i} data-testid={k.testId} className="rounded-lg p-3 border border-white/10 bg-white/3">
                <div className="text-xs text-gray-400 mb-1">{k.label}</div>
                <div className="text-xl font-bold text-white" style={{ fontFamily: 'IBM Plex Mono, monospace' }}>{k.value}</div>
                <div className="text-xs text-gray-500 mt-0.5">{k.sub}</div>
              </div>
            ))}
          </div>

          {/* AER comparison chart */}
          <div>
            <div className="text-sm font-semibold text-gray-300 uppercase tracking-wider mb-3">AER vs Benchmarks</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={improvementData} layout="vertical" margin={{ left: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
                <XAxis type="number" tick={{ fill: '#9ca3af', fontSize: 11 }} tickFormatter={v => `${v.toFixed(1)}`} />
                <YAxis type="category" dataKey="name" tick={{ fill: '#9ca3af', fontSize: 11 }} width={110} />
                <Tooltip contentStyle={{ backgroundColor: '#0f172a', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 8 }}
                  formatter={v => [`${Number(v).toFixed(3)} gCO₂/dwt-nm`]} />
                <Bar dataKey="value" radius={[0, 4, 4, 0]}>
                  {improvementData.map((entry, i) => (
                    <rect key={i} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Narrative & improvement pathway */}
          {result.narrative && (
            <div className="rounded-lg bg-blue-500/10 border border-blue-500/20 p-4">
              <div className="text-xs font-semibold text-blue-400 uppercase tracking-wider mb-2">Assessment Summary</div>
              <p className="text-sm text-gray-300 leading-relaxed">{result.narrative}</p>
              {result.required_fuel_switch_to_A && (
                <div className="mt-3 flex items-start gap-2">
                  <span className="text-xs bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 rounded px-2 py-0.5 font-medium">
                    Path to CII-A
                  </span>
                  <span className="text-sm text-gray-300">{result.required_fuel_switch_to_A}</span>
                </div>
              )}
              {result.required_efficiency_improvement_pct && (
                <div className="mt-2 flex items-start gap-2">
                  <span className="text-xs bg-amber-500/20 text-amber-400 border border-amber-500/30 rounded px-2 py-0.5 font-medium">
                    Efficiency Required
                  </span>
                  <span className="text-sm text-gray-300">
                    {parseFloat(result.required_efficiency_improvement_pct).toFixed(1)}% AER reduction needed for CII Rating A
                  </span>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
