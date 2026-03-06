/**
 * GRI 305 Emissions Panel
 * GRI Standard 305: Emissions (2016, updated 2023 cross-reference to ESRS E1)
 * Covers disclosures 305-1 through 305-7 (Scope 1, 2, 3 GHG, intensity,
 * reductions, ODS, and other significant air emissions).
 */
import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell,
} from 'recharts';

/* ── Helpers ─────────────────────────────────────────────────────────────── */
function Badge({ label, color = 'bg-[#0d1424]/[0.06] text-white/40' }) {
  return <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ${color}`}>{label}</span>;
}
function Card({ title, subtitle, children, className = '' }) {
  return (
    <div className={`bg-[#0d1424] rounded-xl border border-white/[0.06] ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-white/[0.05]">
          {title && <h2 className="text-sm font-semibold text-white/90">{title}</h2>}
          {subtitle && <p className="text-xs text-white/40 mt-0.5">{subtitle}</p>}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}
function StatCard({ label, value, unit, sub, color = 'text-white' }) {
  return (
    <div className="bg-[#0d1424] rounded-xl border border-white/[0.06] p-4">
      <p className="text-xs text-white/40 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>
        {value}{unit && <span className="text-xs text-white/30 ml-1">{unit}</span>}
      </p>
      {sub && <p className="text-[10px] text-white/30 mt-1">{sub}</p>}
    </div>
  );
}

/* ── Reference Data ───────────────────────────────────────────────────────── */
const SCOPE3_CATEGORIES = [
  { id: 'c1', cat: 1, label: 'Purchased goods and services' },
  { id: 'c2', cat: 2, label: 'Capital goods' },
  { id: 'c3', cat: 3, label: 'Fuel- and energy-related activities' },
  { id: 'c4', cat: 4, label: 'Upstream transportation and distribution' },
  { id: 'c5', cat: 5, label: 'Waste generated in operations' },
  { id: 'c6', cat: 6, label: 'Business travel' },
  { id: 'c7', cat: 7, label: 'Employee commuting' },
  { id: 'c8', cat: 8, label: 'Upstream leased assets' },
  { id: 'c9', cat: 9, label: 'Downstream transportation and distribution' },
  { id: 'c10', cat: 10, label: 'Processing of sold products' },
  { id: 'c11', cat: 11, label: 'Use of sold products' },
  { id: 'c12', cat: 12, label: 'End-of-life treatment of sold products' },
  { id: 'c13', cat: 13, label: 'Downstream leased assets' },
  { id: 'c14', cat: 14, label: 'Franchises' },
  { id: 'c15', cat: 15, label: 'Investments (financed emissions)' },
];

const DISCLOSURE_STATUS = [
  { v: 'not_calculated', l: 'Not Calculated' },
  { v: 'estimated', l: 'Estimated (Tier 2/3)' },
  { v: 'calculated', l: 'Calculated (Tier 1)' },
  { v: 'third_party_verified', l: 'Third-Party Verified' },
];

const STATUS_COLOR = {
  not_calculated: 'bg-red-500/10 text-red-600 border-red-500/20',
  estimated: 'bg-amber-500/10 text-amber-400 border-amber-200',
  calculated: 'bg-blue-500/10 text-blue-300 border-blue-500/20',
  third_party_verified: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
};

const GHG_GASES = ['CO₂', 'CH₄', 'N₂O', 'HFCs', 'PFCs', 'SF₆', 'NF₃'];

/* ── Component ────────────────────────────────────────────────────────────── */
export default function Gri305Panel() {
  const [reportingYear, setReportingYear] = useState(2024);
  const [baseYear, setBaseYear] = useState(2019);

  // 305-1 Scope 1
  const [scope1Total, setScope1Total] = useState('');
  const [scope1Method, setScope1Method] = useState('ghg_protocol');
  const [scope1Status, setScope1Status] = useState('calculated');

  // 305-2 Scope 2
  const [scope2Market, setScope2Market] = useState('');
  const [scope2Location, setScope2Location] = useState('');
  const [scope2Status, setScope2Status] = useState('calculated');

  // 305-3 Scope 3
  const [scope3, setScope3] = useState(() => {
    const init = {};
    SCOPE3_CATEGORIES.forEach(c => { init[c.id] = { value: '', status: 'not_calculated', material: false }; });
    return init;
  });

  // 305-4 Intensity
  const [intensityNumerator, setIntensityNumerator] = useState('');
  const [intensityDenominator, setIntensityDenominator] = useState('revenue');
  const [intensityDenominatorValue, setIntensityDenominatorValue] = useState('');

  // 305-5 Reductions
  const [reductionsTco2e, setReductionsTco2e] = useState('');
  const [baseYearEmissions, setBaseYearEmissions] = useState('');

  // 305-6 ODS (Ozone-Depleting Substances)
  const [odsTotal, setOdsTotal] = useState('');

  // 305-7 Other air emissions
  const [nox, setNox] = useState('');
  const [sox, setSox] = useState('');
  const [pm, setPm] = useState('');

  const [result, setResult] = useState(null);

  const setScope3Field = (id, k, v) => setScope3(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const compute = () => {
    const s1 = parseFloat(scope1Total || 0);
    const s2m = parseFloat(scope2Market || 0);
    const s2l = parseFloat(scope2Location || 0);
    const scope3Material = SCOPE3_CATEGORIES.filter(c => scope3[c.id]?.material);
    const scope3Total = scope3Material.reduce((s, c) => s + parseFloat(scope3[c.id]?.value || 0), 0);
    const totalMarket = s1 + s2m + scope3Total;
    const totalLocation = s1 + s2l + scope3Total;

    // Intensity
    const denomVal = parseFloat(intensityDenominatorValue || 1);
    const intensityMarket = denomVal > 0 ? (s1 + s2m) / denomVal : 0;

    // Reduction vs base year
    const baseYearTotal = parseFloat(baseYearEmissions || 0);
    const reductionPct = baseYearTotal > 0 ? ((baseYearTotal - (s1 + s2m)) / baseYearTotal) * 100 : 0;

    // Scope 3 coverage
    const calculatedCats = SCOPE3_CATEGORIES.filter(c => scope3[c.id]?.status !== 'not_calculated').length;

    const chartData = [
      { name: 'Scope 1', value: s1, fill: '#3b82f6' },
      { name: 'Scope 2 (market)', value: s2m, fill: '#8b5cf6' },
      { name: 'Scope 2 (location)', value: s2l, fill: '#a78bfa' },
      { name: 'Scope 3 (material)', value: scope3Total, fill: '#10b981' },
    ].filter(d => d.value > 0);

    setResult({
      s1, s2m, s2l, scope3Total, totalMarket, totalLocation,
      intensityMarket: parseFloat(intensityMarket.toFixed(4)),
      reductionPct: parseFloat(reductionPct.toFixed(1)),
      reductionsTco2e: parseFloat(reductionsTco2e || 0),
      calculatedCats, materialCats: scope3Material.length,
      chartData,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="GRI 305: Emissions (2016)" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="GHG Protocol Corporate Standard" color="bg-blue-400/10 text-blue-300" />
        <Badge label="ISO 14064-1:2018" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="ESRS E1 Cross-Reference" color="bg-purple-400/10 text-purple-300" />
        <Badge label="SBTi Compatible" color="bg-white/[0.06] text-white/60" />
      </div>

      {/* 305-1 Scope 1 */}
      <Card title="GRI 305-1 — Direct (Scope 1) GHG Emissions" subtitle="Total gross Scope 1 GHG emissions in metric tonnes CO₂e. Report by GHG type if applicable.">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs text-white/40 mb-1">Reporting Year</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={reportingYear} onChange={e => setReportingYear(parseInt(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Base Year</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={baseYear} onChange={e => setBaseYear(parseInt(e.target.value))} />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Scope 1 Total (tCO₂e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={scope1Total} onChange={e => setScope1Total(e.target.value)} placeholder="e.g. 15000" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Verification Status</label>
            <select className={`w-full border rounded px-2 py-1.5 text-xs focus:outline-none ${STATUS_COLOR[scope1Status]}`}
              value={scope1Status} onChange={e => setScope1Status(e.target.value)}>
              {DISCLOSURE_STATUS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
            </select>
          </div>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {GHG_GASES.map(g => (
            <Badge key={g} label={g} color="bg-white/[0.04] text-white/40" />
          ))}
          <span className="text-[10px] text-white/30 self-center">Break down by GHG type if material</span>
        </div>
      </Card>

      {/* 305-2 Scope 2 */}
      <Card title="GRI 305-2 — Energy Indirect (Scope 2) GHG Emissions" subtitle="Both location-based AND market-based methods required under GRI 305-2.">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-xs text-white/40 mb-1">Scope 2 Market-Based (tCO₂e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={scope2Market} onChange={e => setScope2Market(e.target.value)} placeholder="Using contractual instruments" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Scope 2 Location-Based (tCO₂e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={scope2Location} onChange={e => setScope2Location(e.target.value)} placeholder="Using grid average EFs" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Verification Status</label>
            <select className={`w-full border rounded px-2 py-1.5 text-xs focus:outline-none ${STATUS_COLOR[scope2Status]}`}
              value={scope2Status} onChange={e => setScope2Status(e.target.value)}>
              {DISCLOSURE_STATUS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
            </select>
          </div>
        </div>
      </Card>

      {/* 305-3 Scope 3 */}
      <Card title="GRI 305-3 — Other Indirect (Scope 3) GHG Emissions" subtitle="15 Scope 3 categories per GHG Protocol Corporate Value Chain Standard. Mark material categories.">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SCOPE3_CATEGORIES.map(cat => (
            <div key={cat.id} className={`border rounded-lg p-3 ${scope3[cat.id]?.material ? 'border-cyan-400/20 bg-cyan-400/[0.03]' : 'border-white/[0.04]'}`}>
              <div className="flex items-center gap-2 mb-2">
                <input type="checkbox" checked={scope3[cat.id]?.material || false}
                  onChange={e => setScope3Field(cat.id, 'material', e.target.checked)} className="accent-cyan-400" />
                <Badge label={`Cat ${cat.cat}`} color="bg-white/[0.06] text-white/40" />
                <span className="text-xs text-white/60">{cat.label}</span>
              </div>
              {scope3[cat.id]?.material && (
                <div className="flex gap-2">
                  <input type="number" className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none"
                    placeholder="tCO₂e" value={scope3[cat.id]?.value || ''}
                    onChange={e => setScope3Field(cat.id, 'value', e.target.value)} />
                  <select className={`border rounded px-2 py-1 text-xs focus:outline-none w-36 ${STATUS_COLOR[scope3[cat.id]?.status]}`}
                    value={scope3[cat.id]?.status}
                    onChange={e => setScope3Field(cat.id, 'status', e.target.value)}>
                    {DISCLOSURE_STATUS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
                  </select>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* 305-4 Intensity / 305-5 Reductions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="GRI 305-4 — GHG Emissions Intensity" subtitle="tCO₂e per unit of organizational metric.">
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-white/40 mb-1">Intensity Denominator Type</label>
              <select className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={intensityDenominator} onChange={e => setIntensityDenominator(e.target.value)}>
                <option value="revenue">Net Revenue (USD/GBP/EUR)</option>
                <option value="fte">Full-Time Equivalent (FTEs)</option>
                <option value="unit">Units Produced (tonnes/MWh/m²)</option>
                <option value="floor_area">Floor Area (m²)</option>
              </select>
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">Denominator Value</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={intensityDenominatorValue} onChange={e => setIntensityDenominatorValue(e.target.value)} placeholder="e.g. 100000000" />
            </div>
          </div>
        </Card>

        <Card title="GRI 305-5 — Reduction of GHG Emissions" subtitle="Reductions vs base year (tCO₂e). Excludes offsets.">
          <div className="space-y-3">
            <div>
              <label className="block text-xs text-white/40 mb-1">Base Year Emissions (tCO₂e Scope 1+2)</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={baseYearEmissions} onChange={e => setBaseYearEmissions(e.target.value)} placeholder={`${baseYear} baseline`} />
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">Reductions Achieved (tCO₂e, excl. offsets)</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={reductionsTco2e} onChange={e => setReductionsTco2e(e.target.value)} placeholder="e.g. 2500" />
            </div>
          </div>
        </Card>
      </div>

      {/* 305-6 ODS / 305-7 Other air */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card title="GRI 305-6 — Ozone-Depleting Substances" subtitle="Total ODS production/destruction (metric tonnes CFC-11 equivalent).">
          <div>
            <label className="block text-xs text-white/40 mb-1">Total ODS (tonnes CFC-11e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={odsTotal} onChange={e => setOdsTotal(e.target.value)} placeholder="e.g. 0.5" />
          </div>
        </Card>

        <Card title="GRI 305-7 — NOₓ, SOₓ and Other Significant Air Emissions" subtitle="Significant air emissions in kg or tonnes per emission type.">
          <div className="space-y-2">
            <div>
              <label className="block text-xs text-white/40 mb-1">NOₓ (kg or tonnes)</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={nox} onChange={e => setNox(e.target.value)} placeholder="e.g. 450" />
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">SOₓ (kg or tonnes)</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={sox} onChange={e => setSox(e.target.value)} placeholder="e.g. 120" />
            </div>
            <div>
              <label className="block text-xs text-white/40 mb-1">Particulate Matter — PM2.5/PM10 (kg or tonnes)</label>
              <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
                value={pm} onChange={e => setPm(e.target.value)} placeholder="e.g. 80" />
            </div>
          </div>
        </Card>
      </div>

      <div className="flex justify-end">
        <button onClick={compute}
          className="bg-emerald-400 hover:bg-emerald-300 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
          Compute GRI 305 Summary
        </button>
      </div>

      {result && (
        <div className="space-y-6">
          {/* KPIs */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="Scope 1 (tCO₂e)" value={result.s1.toLocaleString()} color="text-blue-300" sub="Direct emissions" />
            <StatCard label="Scope 2 Market-Based (tCO₂e)" value={result.s2m.toLocaleString()} color="text-purple-300" sub="Contractual instruments" />
            <StatCard label="Total Scope 1+2 Market (tCO₂e)" value={(result.s1 + result.s2m).toLocaleString()} color="text-cyan-300" sub="Primary GRI metric" />
            <StatCard label="Scope 3 Material Cats (tCO₂e)" value={result.scope3Total.toLocaleString()} color="text-emerald-400"
              sub={`${result.materialCats} categories reported`} />
          </div>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard label="GHG Intensity (tCO₂e/unit)" value={result.intensityMarket.toFixed(4)} color="text-white"
              sub={`Per unit of ${intensityDenominator}`} />
            <StatCard label="Reduction vs Base Year" value={`${result.reductionPct > 0 ? '-' : '+'}${Math.abs(result.reductionPct)}%`}
              color={result.reductionPct > 0 ? 'text-emerald-400' : 'text-red-500'}
              sub={`vs ${baseYear} baseline (Scope 1+2)`} />
            <StatCard label="Scope 3 Categories Calculated" value={`${result.calculatedCats}/15`} color="text-cyan-300"
              sub="GRI 305-3 coverage" />
            <StatCard label="Absolute Reductions (tCO₂e)" value={result.reductionsTco2e.toLocaleString()}
              color="text-emerald-400" sub="Excl. offsets (305-5)" />
          </div>

          {/* Chart */}
          {result.chartData.length > 0 && (
            <Card title="GHG Emissions Breakdown (tCO₂e)">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={result.chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                  <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#ffffff60' }} />
                  <YAxis tick={{ fontSize: 9, fill: '#ffffff60' }} tickFormatter={v => v.toLocaleString()} />
                  <Tooltip
                    contentStyle={{ background: '#0d1424', border: '1px solid #ffffff10', borderRadius: 8 }}
                    formatter={v => [`${v.toLocaleString()} tCO₂e`]}
                  />
                  <Bar dataKey="value" name="tCO₂e" radius={[4, 4, 0, 0]}>
                    {result.chartData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Card>
          )}
        </div>
      )}

      {/* Methodology */}
      <Card title="Methodology Reference" className="border-white/[0.03]">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-white/50">
          <div><span className="font-semibold text-white/70">Standard:</span> GRI 305: Emissions (2016)</div>
          <div><span className="font-semibold text-white/70">Protocol:</span> GHG Protocol Corporate Standard + Scope 3</div>
          <div><span className="font-semibold text-white/70">ISO:</span> ISO 14064-1:2018</div>
          <div><span className="font-semibold text-white/70">ESRS E1:</span> Cross-reference for EU CSRD reporters</div>
          <div><span className="font-semibold text-white/70">S2 Methods:</span> Both location & market-based required</div>
          <div><span className="font-semibold text-white/70">Scope 3:</span> 15 categories per GHG Protocol Scope 3 Standard</div>
        </div>
      </Card>
    </div>
  );
}
