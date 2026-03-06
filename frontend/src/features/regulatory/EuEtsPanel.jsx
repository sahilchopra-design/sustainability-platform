/**
 * EU ETS Phase 4 Compliance Panel
 * EU Emissions Trading System — Phase 4 (2021–2030).
 * Directive 2003/87/EC as amended by Directive 2018/410/EU (Phase 4)
 * and Directive 2023/959/EU (Fit for 55 / REPowerEU amendments).
 * Covers: Stationary installations (power + industry), Aviation, Maritime (ETS2 from 2027).
 */
import React, { useState } from 'react';
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, ReferenceLine,
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
const ETS_SECTORS = [
  { v: 'power', l: 'Power & Heat Generation (no free allocation)' },
  { v: 'manufacturing_carbon_leakage', l: 'Manufacturing — Carbon Leakage Sector (free allocation eligible)' },
  { v: 'manufacturing_non_cl', l: 'Manufacturing — Non-Carbon Leakage (reduced free allocation)' },
  { v: 'aviation_intra_eea', l: 'Aviation — Intra-EEA flights (ETS + CORSIA)' },
  { v: 'maritime', l: 'Maritime — Phased-in from 2024 (40% in 2024, 70% in 2025, 100% from 2026)' },
  { v: 'new_ets2', l: 'Buildings / Road Transport — ETS2 (from 2027)' },
];

// EU ETS cap trajectory 2021-2030 (million tonnes CO₂e, approximate)
// Phase 4 starts at ~1,572 Mt and declines at 2.2% LRF per year
const ETS_CAP_DATA = (() => {
  const cap2021 = 1572;
  const lrf = 0.022;
  return Array.from({ length: 10 }, (_, i) => {
    const year = 2021 + i;
    const cap = Math.round(cap2021 * Math.pow(1 - lrf, i));
    return { year, cap };
  });
})();

const COMPLIANCE_CHECKLIST = [
  { id: 'monitoring_plan', label: 'Monitoring Plan (MP) approved by competent authority' },
  { id: 'annual_reporting', label: 'Annual Emissions Report (AER) submitted by 31 March' },
  { id: 'verification', label: 'Annual Emissions Report independently verified (Tier A accredited verifier)' },
  { id: 'surrender', label: 'Allowances surrendered by 30 April (Art. 12)' },
  { id: 'registry', label: 'EU Registry account active (Holding Account)' },
  { id: 'free_alloc', label: 'Free allocation application submitted (if applicable)' },
  { id: 'newentrant', label: 'New Entrant Reserve (NER) application if new installation' },
  { id: 'cbam', label: 'CBAM obligations reviewed for imported goods (from 2026)' },
];

const CBAM_SECTORS = ['Cement', 'Aluminium', 'Fertilisers', 'Iron & Steel', 'Electricity', 'Hydrogen', 'Polymers (2026+)'];

/* ── Component ────────────────────────────────────────────────────────────── */
export default function EuEtsPanel() {
  const [sector, setSector] = useState('manufacturing_carbon_leakage');
  const [reportingYear, setReportingYear] = useState(2024);
  const [verifiedEmissions, setVerifiedEmissions] = useState('');
  const [freeAllocation, setFreeAllocation] = useState('');
  const [euaPrice, setEuaPrice] = useState('65');
  const [annualRevenue, setAnnualRevenue] = useState('');
  const [purchasedAllowances, setPurchasedAllowances] = useState('');
  const [cbiAuditments, setCbiAuditments] = useState(() => {
    const init = {};
    COMPLIANCE_CHECKLIST.forEach(c => { init[c.id] = false; });
    return init;
  });
  const [result, setResult] = useState(null);

  const toggleCheck = (id) => setCbiAuditments(prev => ({ ...prev, [id]: !prev[id] }));

  const compute = () => {
    const emissions = parseFloat(verifiedEmissions || 0);
    const freeAlloc = parseFloat(freeAllocation || 0);
    const price = parseFloat(euaPrice || 0);
    const purchased = parseFloat(purchasedAllowances || 0);
    const revenue = parseFloat(annualRevenue || 0);

    const netPosition = freeAlloc - emissions; // positive = surplus, negative = shortfall
    const shortfall = Math.max(0, -netPosition);
    const surplus = Math.max(0, netPosition);
    const marketExposure = shortfall * price;
    const totalCarbonCost = (emissions - freeAlloc) * price;
    const carbonCostPctRevenue = revenue > 0 ? (Math.max(0, totalCarbonCost) / revenue) * 100 : 0;

    // Phase 4 allowance pathway for this installation (proportional scaling)
    const emissionsBase = emissions || 1000000;
    const installationCap = ETS_CAP_DATA.map(d => ({
      year: d.year,
      cap: d.cap,
      emissions: year => emissionsBase * Math.pow(0.97, year - reportingYear),
    }));

    const complianceScore = (Object.values(cbiAuditments).filter(Boolean).length / COMPLIANCE_CHECKLIST.length) * 100;

    // Maritime phase-in
    const maritimePctMap = { 2024: 40, 2025: 70, 2026: 100 };
    const maritimePct = maritimePctMap[reportingYear] || (reportingYear >= 2026 ? 100 : reportingYear <= 2023 ? 0 : 40);

    setResult({
      emissions, freeAlloc, netPosition, shortfall, surplus, price,
      marketExposure: Math.round(marketExposure),
      totalCarbonCost: Math.round(Math.max(0, totalCarbonCost)),
      carbonCostPctRevenue: parseFloat(carbonCostPctRevenue.toFixed(2)),
      complianceScore: parseFloat(complianceScore.toFixed(0)),
      maritimePct,
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="EU ETS Phase 4 (2021–2030)" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Directive 2018/410/EU" color="bg-purple-400/10 text-purple-300" />
        <Badge label="LRF 2.2%/yr (4.2% from 2028)" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label="CBAM (from 2026)" color="bg-amber-500/10 text-amber-700" />
        <Badge label="ETS2 Buildings/Transport (2027)" color="bg-emerald-400/10 text-emerald-400" />
      </div>

      {/* Installation Setup */}
      <Card title="EU ETS Phase 4 — Annual Compliance Calculator" subtitle="Calculate verified emissions vs free allocation, market exposure, carbon cost, and compliance checklist status.">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
          <div className="md:col-span-2">
            <label className="block text-xs text-white/40 mb-1">ETS Sector / Installation Type</label>
            <select className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={sector} onChange={e => setSector(e.target.value)}>
              {ETS_SECTORS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Reporting Year</label>
            <select className="w-full border border-white/[0.06] rounded-lg px-3 py-2 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={reportingYear} onChange={e => setReportingYear(parseInt(e.target.value))}>
              {[2021,2022,2023,2024,2025,2026,2027,2028,2029,2030].map(y => (
                <option key={y} value={y}>{y}</option>
              ))}
            </select>
          </div>
        </div>

        {/* Emissions & Allowances */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-xs text-white/40 mb-1">Verified Emissions (tCO₂e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={verifiedEmissions} onChange={e => setVerifiedEmissions(e.target.value)} placeholder="e.g. 250000" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Free Allocation Received (EUAs)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={freeAllocation} onChange={e => setFreeAllocation(e.target.value)} placeholder="e.g. 200000" />
            {sector === 'power' && <p className="text-[10px] text-amber-400 mt-1">Power sector: no free allocation</p>}
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">EUA Market Price (€/tCO₂e)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={euaPrice} onChange={e => setEuaPrice(e.target.value)} placeholder="€/tCO₂e" />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Annual Revenue (€)</label>
            <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={annualRevenue} onChange={e => setAnnualRevenue(e.target.value)} placeholder="e.g. 500000000" />
          </div>
        </div>

        {/* Compliance Checklist */}
        <div className="border border-white/[0.06] rounded-xl p-4 mb-6">
          <h3 className="text-xs font-bold text-white/60 uppercase tracking-wide mb-3">Annual Compliance Checklist</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {COMPLIANCE_CHECKLIST.map(item => (
              <div key={item.id} className={`flex items-center gap-2 p-2 rounded-lg border cursor-pointer transition-all ${cbiAuditments[item.id] ? 'border-emerald-500/20 bg-emerald-500/[0.06]' : 'border-white/[0.04] bg-white/[0.01]'}`}
                onClick={() => toggleCheck(item.id)}>
                <input type="checkbox" checked={cbiAuditments[item.id]} onChange={() => {}} className="accent-emerald-400" />
                <span className="text-xs text-white/60">{item.label}</span>
              </div>
            ))}
          </div>
        </div>

        <div className="flex justify-end">
          <button onClick={compute}
            className="bg-cyan-400 hover:bg-cyan-300 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
            Calculate ETS Compliance Position
          </button>
        </div>
      </Card>

      {result && (
        <div className="space-y-6">
          {/* Position Summary */}
          <div className={`p-5 rounded-xl border ${result.netPosition < 0 ? 'border-red-500/20 bg-red-500/[0.06]' : 'border-emerald-500/20 bg-emerald-500/[0.06]'}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-white/70 mb-1">Allowance Position ({reportingYear})</p>
                <p className={`text-3xl font-bold ${result.netPosition < 0 ? 'text-red-400' : 'text-emerald-400'}`}>
                  {result.netPosition >= 0 ? '+' : ''}{result.netPosition.toLocaleString()} EUAs
                </p>
                <p className="text-xs text-white/40 mt-1">
                  {result.netPosition < 0 ? `Shortfall: must purchase ${result.shortfall.toLocaleString()} EUAs by 30 April` : `Surplus: ${result.surplus.toLocaleString()} EUAs available to sell/bank`}
                </p>
              </div>
              <Badge
                label={result.netPosition < 0 ? 'NET BUYER' : 'NET SELLER'}
                color={result.netPosition < 0 ? 'bg-red-500/20 text-red-400' : 'bg-emerald-500/20 text-emerald-400'}
              />
            </div>
          </div>

          {/* KPI Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatCard
              label="Market Exposure (€)"
              value={`€${(result.marketExposure / 1e6).toFixed(2)}M`}
              color={result.marketExposure > 0 ? 'text-red-400' : 'text-emerald-400'}
              sub={`${result.shortfall.toLocaleString()} EUAs × €${result.price}/t`}
            />
            <StatCard
              label="Total Carbon Cost (€)"
              value={`€${(result.totalCarbonCost / 1e6).toFixed(2)}M`}
              color="text-amber-400"
              sub="Net of free allocation"
            />
            <StatCard
              label="Carbon Cost / Revenue"
              value={`${result.carbonCostPctRevenue.toFixed(2)}%`}
              color={result.carbonCostPctRevenue > 5 ? 'text-red-400' : result.carbonCostPctRevenue > 2 ? 'text-amber-400' : 'text-emerald-400'}
              sub="As % of annual revenue"
            />
            <StatCard
              label="Compliance Checklist"
              value={`${result.complianceScore}%`}
              color={result.complianceScore >= 80 ? 'text-emerald-400' : result.complianceScore >= 50 ? 'text-amber-400' : 'text-red-400'}
              sub={`${Object.values(cbiAuditments).filter(Boolean).length}/${COMPLIANCE_CHECKLIST.length} items complete`}
            />
          </div>

          {/* Phase 4 Cap Trajectory */}
          <Card title={`EU ETS Phase 4 Cap Trajectory (2021–2030) — Linear Reduction Factor 2.2%/yr`}>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={ETS_CAP_DATA}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="year" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <YAxis tick={{ fontSize: 9, fill: '#ffffff60' }} tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
                <Tooltip
                  contentStyle={{ background: '#0d1424', border: '1px solid #ffffff10', borderRadius: 8 }}
                  formatter={v => [`${v.toLocaleString()} Mt CO₂e`]}
                />
                <Line type="monotone" dataKey="cap" name="EU ETS Cap (Mt)" stroke="#3b82f6" strokeWidth={2} dot={{ fill: '#3b82f6', r: 3 }} />
                <ReferenceLine x={reportingYear} stroke="#f59e0b" strokeDasharray="4 4" label={{ value: 'Reporting Year', fontSize: 9, fill: '#f59e0b' }} />
              </LineChart>
            </ResponsiveContainer>
          </Card>

          {/* Maritime phase-in note */}
          {sector === 'maritime' && (
            <div className="p-4 border border-cyan-400/20 bg-cyan-400/[0.04] rounded-xl">
              <p className="text-xs font-semibold text-cyan-300 mb-1">Maritime ETS Phase-In ({reportingYear})</p>
              <p className="text-xs text-white/60">
                {result.maritimePct}% of verified emissions must be covered by EUAs in {reportingYear}.
                Full coverage (100%) from 2026. Intra-EEA voyages: 100%. Extra-EEA voyages: 50%.
              </p>
            </div>
          )}
        </div>
      )}

      {/* CBAM Section */}
      <Card title="CBAM — Carbon Border Adjustment Mechanism" subtitle="CBAM links to EU ETS from 2026. Importers of CBAM goods pay the equivalent carbon price for emissions embodied in imports.">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
          {CBAM_SECTORS.map(s => (
            <div key={s} className="flex items-center gap-2 p-2.5 border border-white/[0.06] rounded-lg bg-white/[0.01]">
              <div className="w-2 h-2 rounded-full bg-amber-400 flex-shrink-0" />
              <span className="text-xs text-white/60">{s}</span>
            </div>
          ))}
        </div>
        <p className="text-[11px] text-white/40">
          CBAM transitional phase (Oct 2023 – Dec 2025): reporting only. Financial obligations from 1 Jan 2026. CBAM certificates linked to EUA price. Reduces carbon leakage risk for ETS-covered sectors.
        </p>
      </Card>

      {/* Methodology */}
      <Card title="Methodology Reference" className="border-white/[0.03]">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-white/50">
          <div><span className="font-semibold text-white/70">Legal Base:</span> Directive 2003/87/EC (ETS) as amended</div>
          <div><span className="font-semibold text-white/70">Phase 4 LRF:</span> 2.2%/yr (2021–2027), 4.2%/yr (2028–2030)</div>
          <div><span className="font-semibold text-white/70">Free Alloc:</span> Benchmark-based (2021-25 and 2026-30 periods)</div>
          <div><span className="font-semibold text-white/70">Surrender:</span> 30 April each year (Art. 12 Directive)</div>
          <div><span className="font-semibold text-white/70">Aviation:</span> Intra-EEA + CORSIA for extra-EEA (from 2027)</div>
          <div><span className="font-semibold text-white/70">CBAM:</span> Linked to EUA price from 2026 (Reg. 2023/956)</div>
        </div>
      </Card>
    </div>
  );
}
