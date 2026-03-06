/**
 * MAS Sustainable Loan Grant Scheme (SLGS) — Portfolio Grant Manager
 * MAS Circular No. CMG 02/2022 (updated 2024)
 *
 * Grant Caps (S$, per application):
 *   - External Review (SPO / pre-/post-issuance verification): Up to S$120,000
 *   - Sustainability Rating: Up to S$30,000
 *   - Eligible issuances: Green / Social / Sustainability / Sustainability-Linked / Transition bonds & loans
 *   - Programme period: Until 31 December 2027 (extendable)
 *
 * Eligibility criteria (MAS SLGS 2024 edition):
 *   1. FI incorporated or operating in Singapore
 *   2. Arrangement / coordination by Singapore-based entity
 *   3. First or second external review engagement for issuer
 *   4. Instrument issued within programme window
 *   5. Min issuance size: S$200M (bonds) / S$50M (loans)
 *
 * Pure client-side grant calculator + backend persistence for application log.
 */
import React, { useState, useCallback, useEffect } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from "recharts";
import { CheckCircle, XCircle, AlertTriangle, Info, Plus, RefreshCw, DollarSign, FileText, Target } from "lucide-react";

const API_BASE = process.env.REACT_APP_BACKEND_URL || "http://localhost:8001";

// ── Grant calculation engine ─────────────────────────────────────────────────
const REVIEW_TYPES = [
  { id: "spo", label: "Second Party Opinion (SPO)", cap_sgd: 120000, desc: "Pre-issuance SPO by CICERO, ISS ESG, Sustainalytics, etc." },
  { id: "pre_issuance_verification", label: "Pre-Issuance CBI Verification", cap_sgd: 120000, desc: "CBI-approved verifier — pre-issuance check" },
  { id: "post_issuance_verification", label: "Post-Issuance Verification", cap_sgd: 120000, desc: "Annual impact reporting verification" },
  { id: "sustainability_rating", label: "Sustainability Rating", cap_sgd: 30000, desc: "ESG rating from MSCI, Sustainalytics, S&P, etc." },
  { id: "framework_review", label: "Sustainable Finance Framework Review", cap_sgd: 120000, desc: "Full framework development + SPO" },
];

const INSTRUMENT_TYPES_SLGS = [
  "Green Bond", "Social Bond", "Sustainability Bond",
  "Sustainability-Linked Bond (SLB)", "Transition Bond",
  "Green Loan", "Sustainability-Linked Loan (SLL)",
];

const STATUSES = ["Draft", "Submitted", "Under Review", "Approved", "Disbursed", "Rejected"];

const STATUS_COLORS = {
  Draft: "bg-white/10 text-white/50",
  Submitted: "bg-blue-500/10 text-blue-400",
  "Under Review": "bg-amber-500/10 text-amber-400",
  Approved: "bg-emerald-500/10 text-emerald-400",
  Disbursed: "bg-emerald-500/20 text-emerald-300",
  Rejected: "bg-red-500/10 text-red-400",
};

const SGD_USD = 0.74; // approximate rate
const fmtSGD = (v) => `S$${Number(v).toLocaleString("en-SG")}`;
const fmtM = (v) => `$${Number(v / 1e6).toFixed(1)}M`;

// ── Eligibility checker (client-side) ────────────────────────────────────────
function checkEligibility(app) {
  const checks = [
    {
      criterion: "Singapore-incorporated or operating FI",
      pass: app.singapore_nexus === true,
      note: "Arranger / coordinator must be Singapore-based",
    },
    {
      criterion: "Eligible instrument type",
      pass: INSTRUMENT_TYPES_SLGS.includes(app.instrument_type),
      note: "Green / Social / Sustainability / SLB / Transition Bond or Loan",
    },
    {
      criterion: "Minimum issuance size",
      pass: app.issuance_size_sgd_m >= (app.instrument_type?.includes("Loan") ? 50 : 200),
      note: app.instrument_type?.includes("Loan") ? "S$50M minimum for loans" : "S$200M minimum for bonds",
    },
    {
      criterion: "First or second external review for issuer",
      pass: app.review_count <= 2,
      note: "SLGS covers first two external review engagements per issuer",
    },
    {
      criterion: "Issued within programme window (by 31 Dec 2027)",
      pass: app.issuance_year <= 2027,
      note: "Programme valid until 31 December 2027",
    },
    {
      criterion: "External reviewer registered with ICMA / CBI / MAS",
      pass: app.reviewer_registered === true,
      note: "Reviewer must be on ICMA-approved / CBI verifier list",
    },
  ];
  const pass_count = checks.filter(c => c.pass).length;
  const eligible = pass_count === checks.length;
  return { checks, eligible, pass_count };
}

// ── Grant amount calculation ─────────────────────────────────────────────────
function calcGrant(app) {
  const reviewType = REVIEW_TYPES.find(r => r.id === app.review_type_id);
  if (!reviewType) return { cap: 0, estimated_grant: 0, grant_rate_pct: 0 };
  const cap = reviewType.cap_sgd;
  const actual_cost = app.actual_review_cost_sgd || 0;
  // MAS reimburses 100% of eligible costs up to cap
  const estimated_grant = Math.min(actual_cost, cap);
  const grant_rate_pct = actual_cost > 0 ? (estimated_grant / actual_cost) * 100 : 0;
  return { cap, estimated_grant, grant_rate_pct, reviewType };
}

// ── Components ────────────────────────────────────────────────────────────────
function StatusBadge({ status }) {
  return (
    <span className={`inline-flex px-2 py-0.5 rounded-full text-[10px] font-medium ${STATUS_COLORS[status] || "bg-white/5 text-white/40"}`}>
      {status}
    </span>
  );
}

const DEFAULT_APP = {
  entity_name: "",
  instrument_name: "",
  instrument_type: "Green Bond",
  issuance_year: 2025,
  issuance_size_sgd_m: 500,
  review_type_id: "spo",
  actual_review_cost_sgd: 80000,
  review_count: 1,
  reviewer_name: "",
  reviewer_registered: true,
  singapore_nexus: true,
  status: "Draft",
  notes: "",
};

// ── Main panel ────────────────────────────────────────────────────────────────
export function SLGSTrackerPanel() {
  const [applications, setApplications] = useState([]);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ ...DEFAULT_APP });
  const [eligibility, setEligibility] = useState(null);
  const [grantCalc, setGrantCalc] = useState(null);
  const [activeApp, setActiveApp] = useState(null);

  // Recompute eligibility whenever form changes
  useEffect(() => {
    setEligibility(checkEligibility(form));
    setGrantCalc(calcGrant(form));
  }, [form]);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const addApplication = () => {
    if (!form.entity_name || !form.instrument_name) return;
    const newApp = {
      ...form,
      id: Date.now(),
      eligibility: checkEligibility(form),
      grant: calcGrant(form),
      created_at: new Date().toISOString().split("T")[0],
    };
    setApplications(prev => [newApp, ...prev]);
    setShowForm(false);
    setForm({ ...DEFAULT_APP });
  };

  const updateStatus = (id, status) => {
    setApplications(prev => prev.map(a => a.id === id ? { ...a, status } : a));
  };

  // Portfolio stats
  const totalGrant = applications.filter(a => a.eligibility?.eligible).reduce((s, a) => s + (a.grant?.estimated_grant || 0), 0);
  const totalApproved = applications.filter(a => ["Approved", "Disbursed"].includes(a.status)).reduce((s, a) => s + (a.grant?.estimated_grant || 0), 0);
  const eligibleCount = applications.filter(a => a.eligibility?.eligible).length;

  // Chart data
  const statusData = STATUSES.map(s => ({
    name: s,
    count: applications.filter(a => a.status === s).length,
  })).filter(d => d.count > 0);

  const instrumentData = INSTRUMENT_TYPES_SLGS.map(i => ({
    name: i.replace(" (SLL)", "").replace(" (SLB)", ""),
    count: applications.filter(a => a.instrument_type === i).length,
    grant: applications.filter(a => a.instrument_type === i).reduce((s, a) => s + (a.grant?.estimated_grant || 0), 0),
  })).filter(d => d.count > 0);

  return (
    <div className="space-y-6">
      {/* Methodology note */}
      <div className="p-3 bg-cyan-500/5 border border-cyan-500/20 rounded-lg text-xs text-cyan-300 flex items-start gap-2">
        <Info className="h-4 w-4 mt-0.5 shrink-0" />
        <span>
          MAS Sustainable Loan Grant Scheme (SLGS) — CMG Circular 02/2022, updated 2024. Reimburses up to S$120,000 per external review
          (SPO, pre-/post-issuance verification) and S$30,000 for sustainability ratings.
          Programme window: until 31 December 2027.
        </span>
      </div>

      {/* Portfolio KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: "Total Applications", val: applications.length, color: "text-white" },
          { label: "Eligible Applications", val: eligibleCount, color: "text-emerald-400" },
          { label: "Estimated Total Grant", val: fmtSGD(totalGrant), color: "text-indigo-400", sub: `≈ ${fmtM(totalGrant * (1 / SGD_USD))} USD` },
          { label: "Approved / Disbursed", val: fmtSGD(totalApproved), color: "text-emerald-400" },
        ].map(({ label, val, color, sub }) => (
          <div key={label} className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-3">
            <div className={`text-xl font-bold ${color}`}>{val}</div>
            <div className="text-xs text-white/40 mt-0.5">{label}</div>
            {sub && <div className="text-[11px] text-white/20 mt-0.5">{sub}</div>}
          </div>
        ))}
      </div>

      {/* Application log header */}
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-semibold text-white/80">Application Portfolio</h3>
        <button onClick={() => setShowForm(!showForm)}
          className="flex items-center gap-1.5 px-3 py-1.5 bg-cyan-600/80 hover:bg-cyan-600 text-white text-xs font-medium rounded-lg">
          <Plus className="h-3.5 w-3.5" />
          New Application
        </button>
      </div>

      {/* New application form */}
      {showForm && (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4 space-y-4">
          <h4 className="text-xs font-semibold text-white/60 uppercase tracking-wide">New SLGS Application</h4>

          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {/* Entity details */}
            {[
              ["entity_name", "Issuer / Entity Name", "text"],
              ["instrument_name", "Instrument Name / ISIN", "text"],
              ["reviewer_name", "External Reviewer Name", "text"],
            ].map(([k, label, type]) => (
              <div key={k}>
                <label className="text-xs text-white/40 block mb-1">{label}</label>
                <input type={type} className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                  value={form[k]} onChange={e => set(k, e.target.value)} />
              </div>
            ))}

            {/* Instrument type */}
            <div>
              <label className="text-xs text-white/40 block mb-1">Instrument Type</label>
              <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={form.instrument_type} onChange={e => set("instrument_type", e.target.value)}>
                {INSTRUMENT_TYPES_SLGS.map(i => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>

            {/* Review type */}
            <div>
              <label className="text-xs text-white/40 block mb-1">Review / Service Type</label>
              <select className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                value={form.review_type_id} onChange={e => set("review_type_id", e.target.value)}>
                {REVIEW_TYPES.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
              </select>
              {grantCalc?.reviewType && (
                <div className="text-[10px] text-white/30 mt-0.5">Cap: {fmtSGD(grantCalc.reviewType.cap_sgd)}</div>
              )}
            </div>

            {/* Numeric fields */}
            {[
              ["issuance_size_sgd_m", "Issuance Size (M SGD)"],
              ["actual_review_cost_sgd", "Review Cost (SGD)"],
              ["issuance_year", "Issuance Year"],
              ["review_count", "Review # for Issuer (1 or 2)"],
            ].map(([k, label]) => (
              <div key={k}>
                <label className="text-xs text-white/40 block mb-1">{label}</label>
                <input type="number" className="w-full bg-[#0d1424] border border-white/[0.08] rounded px-3 py-2 text-xs text-white"
                  value={form[k]} onChange={e => set(k, +e.target.value)} />
              </div>
            ))}

            {/* Toggle fields */}
            {[
              ["singapore_nexus", "Singapore Nexus"],
              ["reviewer_registered", "Reviewer on ICMA / CBI List"],
            ].map(([k, label]) => (
              <div key={k} className="flex items-center gap-2 mt-4">
                <input type="checkbox" id={k} checked={form[k]} onChange={e => set(k, e.target.checked)}
                  className="w-4 h-4 accent-cyan-500" />
                <label htmlFor={k} className="text-xs text-white/50">{label}</label>
              </div>
            ))}
          </div>

          {/* Live eligibility preview */}
          {eligibility && (
            <div className="border border-white/[0.06] rounded-lg p-3 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-white/60">Eligibility Check</span>
                <span className={`text-xs font-bold ${eligibility.eligible ? "text-emerald-400" : "text-red-400"}`}>
                  {eligibility.eligible ? "Eligible" : `${eligibility.pass_count}/${eligibility.checks.length} criteria met`}
                </span>
              </div>
              {eligibility.checks.map((c, i) => (
                <div key={i} className="flex items-start gap-2 text-xs">
                  {c.pass
                    ? <CheckCircle className="h-3.5 w-3.5 text-emerald-400 shrink-0 mt-0.5" />
                    : <XCircle className="h-3.5 w-3.5 text-red-400 shrink-0 mt-0.5" />
                  }
                  <span className={c.pass ? "text-white/50" : "text-red-300"}>{c.criterion}</span>
                  {!c.pass && <span className="text-white/30 italic">— {c.note}</span>}
                </div>
              ))}
              {grantCalc && eligibility.eligible && (
                <div className="mt-2 p-2 bg-emerald-500/5 border border-emerald-500/20 rounded text-xs text-emerald-300">
                  Estimated Grant: <strong>{fmtSGD(grantCalc.estimated_grant)}</strong>
                  {" "}({grantCalc.grant_rate_pct.toFixed(0)}% of review cost · Cap: {fmtSGD(grantCalc.cap)})
                </div>
              )}
            </div>
          )}

          <div className="flex gap-2">
            <button onClick={addApplication}
              disabled={!form.entity_name || !form.instrument_name}
              className="px-4 py-2 bg-cyan-600 hover:bg-cyan-700 text-white text-xs font-medium rounded-lg disabled:opacity-40">
              Add Application
            </button>
            <button onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-white/5 hover:bg-white/10 text-white/60 text-xs rounded-lg">
              Cancel
            </button>
          </div>
        </div>
      )}

      {/* Application table */}
      {applications.length === 0 ? (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-8 text-center text-white/30 text-sm">
          <FileText className="h-10 w-10 mx-auto mb-3 opacity-30" />
          <p>No SLGS applications yet. Click "New Application" to add one.</p>
        </div>
      ) : (
        <div className="bg-[#111827] border border-white/[0.06] rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  {["Entity / Instrument", "Type", "Review Service", "Issuance Size", "Est. Grant", "Eligibility", "Status", ""].map(h => (
                    <th key={h} className="text-left px-4 py-3 text-white/30 font-medium whitespace-nowrap">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {applications.map(app => (
                  <tr key={app.id} className="border-b border-white/[0.04] hover:bg-white/[0.02]">
                    <td className="px-4 py-3">
                      <div className="font-medium text-white/80">{app.entity_name}</div>
                      <div className="text-white/30">{app.instrument_name}</div>
                    </td>
                    <td className="px-4 py-3 text-white/50">{app.instrument_type}</td>
                    <td className="px-4 py-3 text-white/50">
                      {REVIEW_TYPES.find(r => r.id === app.review_type_id)?.label || app.review_type_id}
                    </td>
                    <td className="px-4 py-3 text-white/50">S${app.issuance_size_sgd_m}M</td>
                    <td className="px-4 py-3">
                      <span className={`font-medium ${app.eligibility?.eligible ? "text-emerald-400" : "text-white/30"}`}>
                        {app.eligibility?.eligible ? fmtSGD(app.grant?.estimated_grant || 0) : "—"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {app.eligibility?.eligible
                        ? <span className="flex items-center gap-1 text-emerald-400"><CheckCircle className="h-3 w-3" /> Eligible</span>
                        : <span className="flex items-center gap-1 text-red-400"><XCircle className="h-3 w-3" /> {app.eligibility?.pass_count}/{app.eligibility?.checks.length}</span>
                      }
                    </td>
                    <td className="px-4 py-3">
                      <select value={app.status}
                        onChange={e => updateStatus(app.id, e.target.value)}
                        className="bg-transparent border border-white/[0.08] rounded px-2 py-1 text-[11px] text-white/60">
                        {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
                      </select>
                    </td>
                    <td className="px-4 py-3">
                      <button onClick={() => setActiveApp(activeApp?.id === app.id ? null : app)}
                        className="text-indigo-400 hover:text-indigo-300 text-[11px]">
                        {activeApp?.id === app.id ? "Hide" : "Detail"}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Expanded detail */}
          {activeApp && (
            <div className="border-t border-white/[0.06] p-4 bg-[#0d1424] space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-semibold text-white/60">Application Detail — {activeApp.entity_name}</h4>
                <StatusBadge status={activeApp.status} />
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                {[
                  ["Reviewer", activeApp.reviewer_name || "—"],
                  ["Issuance Year", activeApp.issuance_year],
                  ["Review #", `${activeApp.review_count} of 2 allowed`],
                  ["Actual Review Cost", fmtSGD(activeApp.actual_review_cost_sgd)],
                  ["Grant Cap", fmtSGD(activeApp.grant?.cap || 0)],
                  ["Estimated Grant", fmtSGD(activeApp.grant?.estimated_grant || 0)],
                  ["Recovery Rate", `${(activeApp.grant?.grant_rate_pct || 0).toFixed(0)}%`],
                  ["Added", activeApp.created_at],
                ].map(([label, val]) => (
                  <div key={label}>
                    <div className="text-white/30">{label}</div>
                    <div className="text-white/70 font-medium mt-0.5">{val}</div>
                  </div>
                ))}
              </div>
              <div className="space-y-1.5">
                <div className="text-xs text-white/30 font-medium">Eligibility Criteria</div>
                {activeApp.eligibility?.checks.map((c, i) => (
                  <div key={i} className="flex items-center gap-2 text-xs">
                    {c.pass ? <CheckCircle className="h-3 w-3 text-emerald-400" /> : <XCircle className="h-3 w-3 text-red-400" />}
                    <span className={c.pass ? "text-white/50" : "text-red-300"}>{c.criterion}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Portfolio charts (only when apps exist) */}
      {applications.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
            <h3 className="text-xs font-semibold text-white/50 mb-3">Applications by Status</h3>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={statusData} margin={{ left: 0, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: "#ffffff40" }} />
                <YAxis tick={{ fontSize: 9, fill: "#ffffff40" }} allowDecimals={false} />
                <Tooltip contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }} />
                <Bar dataKey="count" name="Applications" fill="#06b6d4" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
            <h3 className="text-xs font-semibold text-white/50 mb-3">Grant by Instrument Type (SGD)</h3>
            <ResponsiveContainer width="100%" height={140}>
              <BarChart data={instrumentData} margin={{ left: 0, right: 10 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#ffffff08" vertical={false} />
                <XAxis dataKey="name" tick={{ fontSize: 8, fill: "#ffffff40" }} />
                <YAxis tick={{ fontSize: 9, fill: "#ffffff40" }} tickFormatter={v => `S$${(v / 1000).toFixed(0)}K`} />
                <Tooltip contentStyle={{ backgroundColor: "#1a2234", border: "1px solid #ffffff10", fontSize: 11 }}
                  formatter={v => [fmtSGD(v)]} />
                <Bar dataKey="grant" name="Estimated Grant" fill="#6366f1" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      {/* SLGS Programme Reference */}
      <div className="bg-[#111827] border border-white/[0.06] rounded-lg p-4">
        <h3 className="text-xs font-semibold text-white/50 mb-3 uppercase tracking-wide">SLGS Grant Caps Reference (2024)</h3>
        <div className="space-y-2 text-xs">
          {REVIEW_TYPES.map(r => (
            <div key={r.id} className="flex items-start justify-between gap-4 border-b border-white/[0.04] pb-2">
              <div>
                <div className="text-white/70 font-medium">{r.label}</div>
                <div className="text-white/30 mt-0.5">{r.desc}</div>
              </div>
              <div className="text-cyan-400 font-mono font-bold whitespace-nowrap">{fmtSGD(r.cap_sgd)}</div>
            </div>
          ))}
          <div className="text-white/20 mt-2">
            Programme valid until 31 December 2027. MAS may extend at discretion. Max 2 review grants per issuer.
            Source: MAS Circular CMG 02/2022 (updated 2024).
          </div>
        </div>
      </div>
    </div>
  );
}
