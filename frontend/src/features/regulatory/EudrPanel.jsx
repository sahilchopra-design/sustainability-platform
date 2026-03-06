/**
 * EU Deforestation Regulation (EUDR) Compliance Panel
 * Regulation (EU) 2023/1115 — in force from 29 June 2023.
 * Mandatory due diligence for 7 forest-risk commodities and their derived products.
 * Large operators/traders: 30 December 2025.
 * SMEs: 30 June 2026 (delayed per EU Delegated Regulation 2024/2955).
 */
import React, { useState } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, PieChart, Pie, Legend,
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

/* ── Reference Data ───────────────────────────────────────────────────────── */
const COMMODITIES = [
  { id: 'cattle', label: 'Cattle & Derived Products', icon: '🐄', hs_codes: 'HS 0201, 0202, 0206, 4101, 4104, 4107, 6501' },
  { id: 'cocoa', label: 'Cocoa & Derived Products', icon: '', hs_codes: 'HS 1801, 1802, 1803, 1804, 1805, 1806' },
  { id: 'coffee', label: 'Coffee & Derived Products', icon: '', hs_codes: 'HS 0901, 2101' },
  { id: 'palm_oil', label: 'Palm Oil & Derived Products', icon: '', hs_codes: 'HS 1511, 1513, 2306, 3823' },
  { id: 'soya', label: 'Soya & Derived Products', icon: '', hs_codes: 'HS 1201, 1208, 1507, 2304' },
  { id: 'wood', label: 'Wood & Derived Products', icon: '', hs_codes: 'HS 4401–4421, 4701–4707, 9401, 9403' },
  { id: 'rubber', label: 'Rubber & Derived Products', icon: '', hs_codes: 'HS 4001, 4002, 4005–4017' },
];

const COUNTRY_RISK = [
  { v: 'low', l: 'Low Risk — Simplified DDS Allowed', color: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' },
  { v: 'standard', l: 'Standard Risk — Full DDS Required', color: 'bg-amber-500/10 text-amber-400 border-amber-200' },
  { v: 'high', l: 'High Risk — Enhanced DDS + Mitigation', color: 'bg-red-500/10 text-red-600 border-red-500/20' },
  { v: 'unknown', l: 'Unknown / Not Benchmarked', color: 'bg-white/[0.06] text-white/40 border-white/[0.08]' },
];

const DDS_STEPS = [
  {
    id: 'information', label: 'Step 1 — Information Collection', ref: 'Art. 9',
    items: [
      { id: 'geo_data', label: 'Geo-location coordinates (polygon/point) collected for all plots' },
      { id: 'country_origin', label: 'Country of production / harvest identified per commodity lot' },
      { id: 'quantity_date', label: 'Quantity and production date documented per shipment' },
      { id: 'supplier_id', label: 'Supplier name, address, and country registered in DDS system' },
      { id: 'cutoff_date', label: 'Non-deforestation cutoff: plot was forest before 31 Dec 2020' },
    ],
  },
  {
    id: 'risk_assessment', label: 'Step 2 — Risk Assessment', ref: 'Art. 10',
    items: [
      { id: 'country_benchmark', label: 'Country/region risk benchmark reviewed (EC delegated act)' },
      { id: 'deforestation_check', label: 'Satellite/remote sensing data reviewed for deforestation evidence' },
      { id: 'legislation_check', label: 'Producer country legislation compliance verified (land title, FPIC)' },
      { id: 'traceability', label: 'Supply chain traceability to plot level confirmed' },
    ],
  },
  {
    id: 'risk_mitigation', label: 'Step 3 — Risk Mitigation', ref: 'Art. 11',
    items: [
      { id: 'third_party_audit', label: 'Third-party audit or certification covering EUDR requirements' },
      { id: 'supplier_training', label: 'Supplier training and capacity building programme in place' },
      { id: 'corrective_action', label: 'Corrective action process for non-compliant suppliers' },
      { id: 'remediation', label: 'Remediation plan for identified deforestation risks' },
    ],
  },
];

const COMPLIANCE_STATUS = [
  { v: 'not_started', l: 'Not Started' },
  { v: 'in_progress', l: 'In Progress' },
  { v: 'compliant', l: 'Compliant' },
  { v: 'non_compliant', l: 'Non-Compliant' },
  { v: 'na', l: 'N/A — Not Sourced' },
];

const STATUS_COLOR = {
  not_started: 'bg-red-500/10 text-red-600 border-red-500/20',
  in_progress: 'bg-amber-500/10 text-amber-400 border-amber-200',
  compliant: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
  non_compliant: 'bg-red-700/20 text-red-400 border-red-700/20',
  na: 'bg-white/[0.04] text-white/30 border-white/[0.06]',
};

/* ── Component ────────────────────────────────────────────────────────────── */
export default function EudrPanel() {
  const [entitySize, setEntitySize] = useState('large');
  const [role, setRole] = useState('operator');

  const [commodityData, setCommodityData] = useState(() => {
    const init = {};
    COMMODITIES.forEach(c => {
      init[c.id] = {
        active: false,
        volume_kt: '',
        country_risk: 'standard',
        geo_data_pct: '',
      };
    });
    return init;
  });

  const [ddsReadiness, setDdsReadiness] = useState(() => {
    const init = {};
    DDS_STEPS.flatMap(s => s.items).forEach(i => { init[i.id] = { status: 'not_started', notes: '' }; });
    return init;
  });

  const [result, setResult] = useState(null);

  const setCommodity = (id, k, v) => setCommodityData(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));
  const setDds = (id, k, v) => setDdsReadiness(prev => ({ ...prev, [id]: { ...prev[id], [k]: v } }));

  const compute = () => {
    const activeCommodities = COMMODITIES.filter(c => commodityData[c.id]?.active);
    const compliantItems = Object.values(ddsReadiness).filter(d => d.status === 'compliant').length;
    const totalItems = DDS_STEPS.flatMap(s => s.items).length;
    const readinessPct = (compliantItems / totalItems) * 100;

    const stepScores = DDS_STEPS.map(step => {
      const compliant = step.items.filter(i => ddsReadiness[i.id]?.status === 'compliant').length;
      return {
        step: step.label.split(' — ')[1],
        compliant, total: step.items.length,
        pct: Math.round((compliant / step.items.length) * 100),
      };
    });

    const riskSummary = activeCommodities.reduce((acc, c) => {
      const risk = commodityData[c.id]?.country_risk || 'unknown';
      acc[risk] = (acc[risk] || 0) + 1;
      return acc;
    }, {});

    const deadline = entitySize === 'sme' ? '30 June 2026' : '30 December 2025';
    const gaps = DDS_STEPS.flatMap(step =>
      step.items
        .filter(i => ddsReadiness[i.id]?.status !== 'compliant' && ddsReadiness[i.id]?.status !== 'na')
        .map(i => ({ step: step.label, label: i.label, status: ddsReadiness[i.id]?.status || 'not_started' }))
    );

    setResult({ activeCommodities: activeCommodities.length, readinessPct: parseFloat(readinessPct.toFixed(1)), compliantItems, totalItems, stepScores, riskSummary, deadline, gaps });
  };

  const deadline = entitySize === 'sme' ? '30 Jun 2026' : '30 Dec 2025';

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap gap-2">
        <Badge label="EU 2023/1115 (EUDR)" color="bg-emerald-400/10 text-emerald-400" />
        <Badge label="7 Forest-Risk Commodities" color="bg-blue-400/10 text-blue-300" />
        <Badge label="Due Diligence System" color="bg-cyan-400/10 text-cyan-300" />
        <Badge label={`Deadline: ${deadline}`} color="bg-amber-500/10 text-amber-700" />
      </div>

      {/* Entity Setup */}
      <Card title="EUDR Compliance Tracker" subtitle="EU Regulation 2023/1115 — due diligence system for 7 forest-risk commodities. Applies to operators placing products on the EU market or exporting from it.">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-2">
          <div>
            <label className="block text-xs text-white/40 mb-1">Entity Size</label>
            <select className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={entitySize} onChange={e => setEntitySize(e.target.value)}>
              <option value="large">Large Operator (>250 employees OR >€50M turnover)</option>
              <option value="sme">SME (≤250 employees AND ≤€50M turnover)</option>
            </select>
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Role in Supply Chain</label>
            <select className="w-full border border-white/[0.06] rounded px-2 py-1.5 text-sm bg-[#0b1120] text-white/70 focus:outline-none"
              value={role} onChange={e => setRole(e.target.value)}>
              <option value="operator">Operator (places product on EU market)</option>
              <option value="trader">Trader (makes available on EU market)</option>
              <option value="sme_trader">Trader — SME (simplified obligations apply)</option>
            </select>
          </div>
          <div className="flex items-center gap-2 p-3 bg-amber-500/[0.06] border border-amber-500/10 rounded-lg col-span-2">
            <div>
              <p className="text-[10px] text-white/40">Your Compliance Deadline</p>
              <p className="text-sm font-bold text-amber-400">{deadline}</p>
              <p className="text-[10px] text-white/30">
                {entitySize === 'sme' ? 'SME extended deadline (EU Del. Reg. 2024/2955)' : 'Large operators / non-EU companies'}
              </p>
            </div>
          </div>
        </div>
      </Card>

      {/* Commodity Scoping */}
      <Card title="Commodity Scoping — Activate Relevant Commodities" subtitle="Select all commodities you source, produce or trade. Confirm origin country risk level and geolocation data coverage.">
        <div className="space-y-3">
          {COMMODITIES.map(c => (
            <div key={c.id} className={`border rounded-xl p-4 transition-all ${commodityData[c.id]?.active ? 'border-cyan-400/20 bg-cyan-400/[0.03]' : 'border-white/[0.04]'}`}>
              <div className="flex items-center gap-3 mb-2">
                <input type="checkbox" checked={commodityData[c.id]?.active || false}
                  onChange={e => setCommodity(c.id, 'active', e.target.checked)} className="accent-cyan-400" />
                <span className="text-sm font-semibold text-white/80">{c.label}</span>
                <span className="text-[10px] text-white/30 ml-auto">{c.hs_codes}</span>
              </div>
              {commodityData[c.id]?.active && (
                <div className="grid grid-cols-3 gap-3 mt-2">
                  <div>
                    <label className="block text-xs text-white/40 mb-1">Volume (kt/yr)</label>
                    <input type="number" className="w-full border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none"
                      value={commodityData[c.id]?.volume_kt || ''} onChange={e => setCommodity(c.id, 'volume_kt', e.target.value)} placeholder="e.g. 5.0" />
                  </div>
                  <div>
                    <label className="block text-xs text-white/40 mb-1">Country Risk Level</label>
                    <select className={`w-full border rounded px-2 py-1 text-xs focus:outline-none ${COUNTRY_RISK.find(r => r.v === commodityData[c.id]?.country_risk)?.color || ''}`}
                      value={commodityData[c.id]?.country_risk}
                      onChange={e => setCommodity(c.id, 'country_risk', e.target.value)}>
                      {COUNTRY_RISK.map(r => <option key={r.v} value={r.v}>{r.l}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs text-white/40 mb-1">Geolocation Data Coverage (%)</label>
                    <input type="number" min="0" max="100" className="w-full border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/70 focus:outline-none"
                      value={commodityData[c.id]?.geo_data_pct || ''} onChange={e => setCommodity(c.id, 'geo_data_pct', Math.min(100, Math.max(0, parseFloat(e.target.value) || 0)))} placeholder="0–100%" />
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>

      {/* Due Diligence System */}
      <Card title="Due Diligence System Readiness — 3-Step Process (Art. 8–11)" subtitle="Score each DDS component. Step 3 (Risk Mitigation) required only for standard and high-risk countries.">
        <div className="space-y-5">
          {DDS_STEPS.map(step => (
            <div key={step.id} className="border border-white/[0.06] rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold text-white/80">{step.label}</h3>
                <Badge label={step.ref} color="bg-white/[0.06] text-white/40" />
              </div>
              <div className="space-y-2">
                {step.items.map(item => (
                  <div key={item.id} className="bg-[#0b1120] rounded-lg p-2.5 border border-white/[0.04]">
                    <p className="text-xs text-white/60 mb-2">{item.label}</p>
                    <div className="flex items-center gap-2">
                      <select className={`border rounded px-2 py-1 text-xs focus:outline-none w-48 ${STATUS_COLOR[ddsReadiness[item.id]?.status] || ''}`}
                        value={ddsReadiness[item.id]?.status}
                        onChange={e => setDds(item.id, 'status', e.target.value)}>
                        {COMPLIANCE_STATUS.map(s => <option key={s.v} value={s.v}>{s.l}</option>)}
                      </select>
                      <input className="flex-1 border border-white/[0.06] rounded px-2 py-1 text-xs bg-[#0b1120] text-white/40 focus:outline-none"
                        placeholder="Notes / evidence / system name"
                        value={ddsReadiness[item.id]?.notes || ''}
                        onChange={e => setDds(item.id, 'notes', e.target.value)} />
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        <div className="mt-6 flex justify-end">
          <button onClick={compute}
            className="bg-emerald-400 hover:bg-emerald-300 text-[#080e1c] text-sm font-semibold px-8 py-2.5 rounded-lg shadow transition-colors">
            Generate EUDR Compliance Report
          </button>
        </div>
      </Card>

      {result && (
        <div className="space-y-6">
          {/* KPI summary */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className={`rounded-xl border p-5 text-center ${result.readinessPct >= 75 ? 'bg-emerald-500/10 border-emerald-500/20' : result.readinessPct >= 50 ? 'bg-amber-500/10 border-amber-200' : 'bg-red-500/10 border-red-500/20'}`}>
              <p className="text-xs text-white/40 mb-1">DDS Readiness</p>
              <p className={`text-3xl font-bold ${result.readinessPct >= 75 ? 'text-emerald-400' : result.readinessPct >= 50 ? 'text-amber-400' : 'text-red-500'}`}>
                {result.readinessPct.toFixed(0)}%
              </p>
              <p className="text-[10px] text-white/30 mt-1">{result.compliantItems}/{result.totalItems} items compliant</p>
            </div>
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-4 text-center">
              <p className="text-xs text-white/40 mb-1">Active Commodities</p>
              <p className="text-2xl font-bold text-cyan-300">{result.activeCommodities}</p>
              <p className="text-[10px] text-white/30 mt-1">of 7 EUDR commodities</p>
            </div>
            {Object.entries(result.riskSummary).map(([risk, count]) => {
              const riskObj = COUNTRY_RISK.find(r => r.v === risk);
              return (
                <div key={risk} className={`border rounded-xl p-4 text-center ${riskObj?.color || ''}`}>
                  <p className="text-xs mb-1">{risk.replace('_', ' ')} risk</p>
                  <p className="text-2xl font-bold">{count}</p>
                  <p className="text-[10px] mt-1">commodities</p>
                </div>
              );
            })}
          </div>

          {/* DDS Step completion chart */}
          <Card title="DDS Step Completion (% of requirements met)">
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={result.stepScores}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff10" />
                <XAxis dataKey="step" tick={{ fontSize: 9, fill: '#ffffff60' }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 9, fill: '#ffffff60' }} tickFormatter={v => `${v}%`} />
                <Tooltip contentStyle={{ background: '#0d1424', border: '1px solid #ffffff10', borderRadius: 8 }} formatter={v => [`${v}%`]} />
                <Bar dataKey="pct" name="Compliance %" radius={[4, 4, 0, 0]}>
                  {result.stepScores.map((s, i) => (
                    <Cell key={i} fill={s.pct >= 75 ? '#10b981' : s.pct >= 50 ? '#f59e0b' : '#ef4444'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Card>

          {/* Gaps */}
          {result.gaps.length > 0 && (
            <Card title={`EUDR Compliance Gaps — ${result.gaps.length} open items`}>
              <div className="space-y-2">
                {result.gaps.map((g, i) => (
                  <div key={i} className={`flex items-start gap-3 p-2.5 border rounded-lg ${STATUS_COLOR[g.status] || ''}`}>
                    <Badge label={g.status.replace('_', ' ')} color={STATUS_COLOR[g.status] || ''} />
                    <span className="text-xs flex-1">{g.label}</span>
                  </div>
                ))}
              </div>
            </Card>
          )}
        </div>
      )}

      {/* Methodology */}
      <Card title="Methodology Reference" className="border-white/[0.03]">
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3 text-xs text-white/50">
          <div><span className="font-semibold text-white/70">Regulation:</span> EU 2023/1115 (EUDR)</div>
          <div><span className="font-semibold text-white/70">Cutoff Date:</span> 31 December 2020</div>
          <div><span className="font-semibold text-white/70">Commodities:</span> Cattle, Cocoa, Coffee, Palm Oil, Soya, Wood, Rubber</div>
          <div><span className="font-semibold text-white/70">DDS:</span> Art. 8–11 (Information, Risk Assessment, Mitigation)</div>
          <div><span className="font-semibold text-white/70">Large Ops:</span> 30 December 2025</div>
          <div><span className="font-semibold text-white/70">SMEs:</span> 30 June 2026 (Del. Reg. 2024/2955)</div>
        </div>
      </Card>
    </div>
  );
}
