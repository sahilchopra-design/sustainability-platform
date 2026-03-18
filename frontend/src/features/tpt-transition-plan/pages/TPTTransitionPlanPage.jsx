/**
 * TPT Transition Plan Taskforce Page
 *
 * 5 tabs: TPT Assessment | Element Scores | Gap Analysis |
 *         Interim Targets | Reference
 * Backend: /api/v1/tpt-transition-plan
 * Regulatory basis: FCA PS23/22, TPT Disclosure Framework (Oct 2023)
 */
import React, { useState, useMemo } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, LineChart, Line, Cell,
} from "recharts";

const API = process.env.REACT_APP_API_URL || "";
const EMERALD = "#10b981";
const COLORS = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#64748b"];

const TABS = ["TPT Assessment", "Element Scores", "Gap Analysis", "Interim Targets", "Reference"];

const rng = (seed) => { let s = seed; return () => { s = (s * 1664525 + 1013904223) & 0xffffffff; return (s >>> 0) / 0xffffffff; }; };

/* ── Primitives ─────────────────────────────────────────────────────────── */
const Section = ({ title, children }) => (
  <div className="mb-6">
    {title && <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-3">{title}</div>}
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, accent }) => (
  <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
    <div className="text-xs text-gray-500 mb-1">{label}</div>
    <div className={`text-2xl font-bold ${accent ? "text-emerald-600" : "text-black"}`}>{value}</div>
    {sub && <div className="text-xs text-gray-400 mt-1">{sub}</div>}
  </div>
);
const Row = ({ children }) => <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">{children}</div>;
const Inp = ({ label, ...p }) => (
  <div className="mb-3">
    <label className="block text-xs text-gray-500 mb-1">{label}</label>
    <input className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400" {...p} />
  </div>
);
const Sel = ({ label, children, ...p }) => (
  <div className="mb-3">
    <label className="block text-xs text-gray-500 mb-1">{label}</label>
    <select className="w-full border border-gray-200 rounded px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-emerald-400" {...p}>{children}</select>
  </div>
);
const Btn = ({ children, ...p }) => (
  <button className="bg-black text-white text-sm px-4 py-2 rounded hover:bg-gray-800 transition-colors" {...p}>{children}</button>
);

/* ── Static data ─────────────────────────────────────────────────────────── */
const r0 = rng(55);

const ELEMENTS = [
  { key: "foundations", label: "Foundations", weight: 20 },
  { key: "implementation", label: "Implementation Strategy", weight: 20 },
  { key: "engagement", label: "Engagement", weight: 15 },
  { key: "metrics", label: "Metrics & Targets", weight: 20 },
  { key: "governance", label: "Governance", weight: 15 },
  { key: "finance", label: "Finance", weight: 10 },
];

const SUB_ELEMENTS = {
  foundations: [
    { sub: "1.1 Strategic ambition — Paris alignment", complete: true },
    { sub: "1.2 Scope & boundary definition", complete: true },
    { sub: "1.3 Business model dependency on nature/land", complete: false },
    { sub: "1.4 Just Transition consideration", complete: false },
  ],
  implementation: [
    { sub: "2.1 Short-term actions (1-3 years)", complete: true },
    { sub: "2.2 Medium-term plan (3-5 years)", complete: true },
    { sub: "2.3 Long-term transformation roadmap", complete: false },
    { sub: "2.4 Product/service decarbonisation", complete: false },
  ],
  engagement: [
    { sub: "3.1 Value chain engagement strategy", complete: true },
    { sub: "3.2 Policy engagement", complete: false },
    { sub: "3.3 Industry collaboration", complete: true },
    { sub: "3.4 Investor & stakeholder engagement", complete: false },
  ],
  metrics: [
    { sub: "4.1 GHG targets (Scope 1/2/3)", complete: true },
    { sub: "4.2 Internal carbon price", complete: true },
    { sub: "4.3 Climate CapEx & revenue mix", complete: false },
    { sub: "4.4 Financed emissions trajectory", complete: false },
  ],
  governance: [
    { sub: "5.1 Board oversight & accountability", complete: true },
    { sub: "5.2 Management responsibility", complete: true },
    { sub: "5.3 Remuneration linkage", complete: false },
    { sub: "5.4 Incentive structure alignment", complete: false },
  ],
  finance: [
    { sub: "6.1 Capital allocation commitment", complete: true },
    { sub: "6.2 Internal carbon pricing mechanism", complete: false },
    { sub: "6.3 Green / transition finance plan", complete: false },
  ],
};

const CROSS_FRAMEWORK = [
  { framework: "TCFD — Governance", tpt: "Element 5 — Governance" },
  { framework: "TCFD — Strategy", tpt: "Elements 1+2 — Foundations & Implementation" },
  { framework: "TCFD — Metrics & Targets", tpt: "Element 4 — Metrics & Targets" },
  { framework: "ISSB S2 Para 22", tpt: "Element 1+4 — Scenario analysis, targets" },
  { framework: "CSRD ESRS E1-3", tpt: "Element 1 — Foundations (Paris, NZ target)" },
  { framework: "CSRD ESRS E1-4", tpt: "Element 4 — Metrics (transition plan KPIs)" },
  { framework: "CSRD ESRS G1-1", tpt: "Element 5 — Governance (business conduct)" },
];

const QUALITY_TIERS = [
  { tier: "Initial", range: "0-40", desc: "Commitments stated, limited specificity; ambition acknowledged but no detailed plan" },
  { tier: "Developing", range: "41-60", desc: "Near-term actions defined; partial coverage of elements; some implementation detail" },
  { tier: "Advanced", range: "61-80", desc: "Comprehensive near and medium-term strategy; most elements addressed with evidence" },
  { tier: "Leading", range: "81-100", desc: "Full TPT framework alignment; robust governance; cross-value-chain engagement; credible finance plan" },
];

function makeTierBadge(score) {
  if (score >= 81) return { tier: "Leading", cls: "bg-emerald-100 text-emerald-800" };
  if (score >= 61) return { tier: "Advanced", cls: "bg-blue-100 text-blue-800" };
  if (score >= 41) return { tier: "Developing", cls: "bg-amber-100 text-amber-800" };
  return { tier: "Initial", cls: "bg-gray-100 text-gray-600" };
}

function calcElementScores(form) {
  const r = rng(parseInt(form.greenCapex || 15) + form.entity.length + parseInt(form.nzYear || 2050));
  return ELEMENTS.map((el) => ({ ...el, score: Math.round(r() * 35 + 45) }));
}

export default function TPTTransitionPlanPage() {
  const [tab, setTab] = useState(0);
  const [form, setForm] = useState({
    entity: "Clearwater Bank plc", entityType: "bank",
    planYear: "2024", nzYear: "2050", greenCapex: "22",
  });
  const [elementSel, setElementSel] = useState("foundations");
  const [gapFilter, setGapFilter] = useState("All");
  const [targets, setTargets] = useState({ t2025: "15", t2030: "40", t2035: "60", t2040: "75" });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const elementScores = useMemo(() => calcElementScores(form), [form]);
  const overall = Math.round(elementScores.reduce((acc, e) => acc + e.score * e.weight / 100, 0));
  const tierBadge = makeTierBadge(overall);

  const barData = elementScores.map(e => ({ name: e.label, score: e.score }));

  async function runAssessment() {
    setLoading(true);
    try {
      const res = await axios.post(`${API}/api/v1/tpt-transition-plan/assess`, form);
      setResult(res.data);
    } catch { /* use computed */ }
    finally { setLoading(false); }
  }

  const gaps = [
    { element: "Foundations", sub: "Just Transition", desc: "No reference to workforce impact in transition; social equity considerations absent", priority: "High", action: "Commission Just Transition impact assessment; align with ILO guidelines" },
    { element: "Foundations", sub: "Nature dependency", desc: "Land-use and nature-related dependencies not quantified", priority: "High", action: "Conduct TNFD LEAP assessment; map material nature dependencies" },
    { element: "Implementation", sub: "Long-term roadmap", desc: "2035-2050 transformation actions not specified", priority: "High", action: "Develop long-term roadmap with sector-level technology transition milestones" },
    { element: "Engagement", sub: "Policy engagement", desc: "No disclosure of policy lobbying alignment with Paris goals", priority: "Medium", action: "Publish policy engagement positions; align lobbying with net-zero commitments" },
    { element: "Metrics", sub: "Financed emissions trajectory", desc: "Portfolio-level decarbonisation pathway not disclosed against NZBA benchmarks", priority: "High", action: "Apply PACTA methodology; disclose sector alignment benchmarks" },
    { element: "Governance", sub: "Remuneration linkage", desc: "No disclosed KPIs linking executive pay to climate targets", priority: "Medium", action: "Embed climate metrics in short and long-term incentive plans" },
    { element: "Finance", sub: "Transition finance plan", desc: "Committed green and transition finance quantum not stated", priority: "Medium", action: "Quantify and disclose transition finance commitment (EUR target)" },
    { element: "Finance", sub: "Internal carbon price", desc: "Shadow carbon price not applied in investment decisions", priority: "Low", action: "Adopt and disclose internal carbon price; apply to new investments" },
  ];

  const filteredGaps = gapFilter === "All" ? gaps : gaps.filter(g => g.priority === gapFilter);

  const gapByElement = ELEMENTS.map(el => ({
    name: el.label.split(" ")[0],
    count: gaps.filter(g => g.element === el.label.split(" ")[0] || g.element === el.label).length,
  }));

  // Trajectory chart data
  const milestones = [2024, 2025, 2030, 2035, 2040, 2050];
  const trajectoryData = milestones.map(y => {
    const baseline = 100;
    const tMap = { 2025: Number(targets.t2025), 2030: Number(targets.t2030), 2035: Number(targets.t2035), 2040: Number(targets.t2040), 2050: 95 };
    const target = tMap[y] || 0;
    return {
      year: String(y),
      target: y === 2024 ? 0 : target,
      current: y === 2024 ? 0 : Math.max(0, target - Math.round(rng(y)() * 8 - 4)),
    };
  });

  return (
    <div className="min-h-screen bg-white text-black p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-black">TPT Transition Plan Assessment</h1>
          <p className="text-sm text-gray-500 mt-1">Transition Plan Taskforce Disclosure Framework (Oct 2023) — FCA PS23/22</p>
        </div>

        <div className="flex border-b border-gray-200 mb-6 gap-1 flex-wrap">
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setTab(i)}
              className={`px-4 py-2 text-sm transition-colors ${tab === i ? "border-b-2 border-emerald-500 text-black font-semibold" : "text-gray-500 hover:text-black"}`}>
              {t}
            </button>
          ))}
        </div>

        {/* Tab 1 — TPT Assessment */}
        {tab === 0 && (
          <div>
            <Section title="Entity Details">
              <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
                <Inp label="Entity Name" value={form.entity} onChange={e => setForm({ ...form, entity: e.target.value })} />
                <Sel label="Entity Type" value={form.entityType} onChange={e => setForm({ ...form, entityType: e.target.value })}>
                  <option value="bank">Bank</option>
                  <option value="insurer">Insurer</option>
                  <option value="asset_manager">Asset Manager</option>
                  <option value="pension">Pension Fund</option>
                  <option value="corporate">Corporate</option>
                </Sel>
                <Sel label="Plan Year" value={form.planYear} onChange={e => setForm({ ...form, planYear: e.target.value })}>
                  <option value="2024">2024</option>
                  <option value="2025">2025</option>
                </Sel>
                <Sel label="Net Zero Target Year" value={form.nzYear} onChange={e => setForm({ ...form, nzYear: e.target.value })}>
                  <option value="2040">2040</option>
                  <option value="2045">2045</option>
                  <option value="2050">2050</option>
                </Sel>
                <Inp label="Green CapEx %" type="number" value={form.greenCapex} onChange={e => setForm({ ...form, greenCapex: e.target.value })} />
              </div>
            </Section>
            <div className="mb-6"><Btn onClick={runAssessment} disabled={loading}>{loading ? "Running..." : "Run TPT Assessment"}</Btn></div>

            <div className="mb-6 flex items-center gap-4">
              <div className="bg-white border border-gray-200 rounded-lg p-5 shadow-sm flex-1">
                <div className="text-xs text-gray-500 mb-1">Overall Quality Score</div>
                <div className="flex items-baseline gap-3">
                  <div className="text-4xl font-bold text-emerald-600">{overall}/100</div>
                  <span className={`px-3 py-1 rounded-full text-sm font-semibold ${tierBadge.cls}`}>{tierBadge.tier}</span>
                </div>
                <div className="mt-3 h-2 bg-gray-100 rounded-full">
                  <div className="h-2 rounded-full bg-emerald-500" style={{ width: `${overall}%` }} />
                </div>
              </div>
            </div>

            <Row>
              {elementScores.map((e, i) => (
                <KpiCard key={e.key} label={e.label} value={`${e.score}/100`} sub={`Weight: ${e.weight}%`} />
              ))}
            </Row>

            <Section title="Element Scores">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={barData} layout="vertical" margin={{ top: 4, right: 30, left: 110, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" horizontal={false} />
                  <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} />
                  <YAxis type="category" dataKey="name" tick={{ fontSize: 12 }} width={110} />
                  <Tooltip formatter={v => `${v}/100`} />
                  <Bar dataKey="score" name="Score" fill={EMERALD} radius={[0, 3, 3, 0]}>
                    {barData.map((entry, i) => <Cell key={i} fill={entry.score >= 70 ? EMERALD : entry.score >= 50 ? "#f59e0b" : "#ef4444"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>

            <Section title="Priority Actions (Top 5)">
              <ol className="space-y-2">
                {gaps.filter(g => g.priority === "High").slice(0, 5).map((g, i) => (
                  <li key={i} className="flex gap-3 bg-gray-50 rounded p-3 text-sm">
                    <span className="w-5 h-5 rounded-full bg-black text-white text-xs flex items-center justify-center flex-shrink-0">{i + 1}</span>
                    <div><span className="font-medium">{g.element} — {g.sub}:</span> <span className="text-gray-600">{g.action}</span></div>
                  </li>
                ))}
              </ol>
            </Section>
          </div>
        )}

        {/* Tab 2 — Element Scores */}
        {tab === 1 && (
          <div>
            <Section title="Element Selector">
              <div className="max-w-xs mb-4">
                <Sel label="Select Element" value={elementSel} onChange={e => setElementSel(e.target.value)}>
                  {ELEMENTS.map(el => <option key={el.key} value={el.key}>{el.label}</option>)}
                </Sel>
              </div>
            </Section>

            {(() => {
              const el = ELEMENTS.find(e => e.key === elementSel);
              const subs = SUB_ELEMENTS[elementSel] || [];
              const score = elementScores.find(e => e.key === elementSel)?.score || 0;
              const completeCount = subs.filter(s => s.complete).length;
              return (
                <>
                  <div className="mb-6 bg-white border border-gray-200 rounded-lg p-5">
                    <div className="flex justify-between items-center mb-2">
                      <div className="font-semibold">{el.label}</div>
                      <div className="text-2xl font-bold text-emerald-600">{score}/100</div>
                    </div>
                    <div className="h-3 bg-gray-100 rounded-full">
                      <div className="h-3 rounded-full bg-emerald-500 transition-all" style={{ width: `${score}%` }} />
                    </div>
                    <div className="text-xs text-gray-500 mt-2">{completeCount}/{subs.length} sub-elements complete — Weight: {el.weight}%</div>
                  </div>
                  <Section title="Sub-Element Checklist">
                    <div className="space-y-2">
                      {subs.map((s, i) => (
                        <div key={i} className={`flex items-center gap-3 p-3 rounded border ${s.complete ? "border-emerald-200 bg-emerald-50" : "border-gray-200 bg-white"}`}>
                          <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 ${s.complete ? "bg-emerald-500" : "border-2 border-gray-300"}`}>
                            {s.complete && <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>}
                          </div>
                          <span className="text-sm">{s.sub}</span>
                          <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${s.complete ? "bg-emerald-100 text-emerald-700" : "bg-gray-100 text-gray-500"}`}>{s.complete ? "Complete" : "Gap"}</span>
                        </div>
                      ))}
                    </div>
                  </Section>
                  <Section title="Sub-Element Compliance Table">
                    <div className="overflow-auto">
                      <table className="w-full text-sm">
                        <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Sub-Element</th><th className="text-left p-3">Status</th><th className="text-left p-3">Guidance Note</th></tr></thead>
                        <tbody>
                          {subs.map((s, i) => (
                            <tr key={i} className="border-t border-gray-100">
                              <td className="p-3 font-medium">{s.sub}</td>
                              <td className="p-3"><span className={`px-2 py-0.5 rounded-full text-xs ${s.complete ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"}`}>{s.complete ? "Disclosed" : "Not Disclosed"}</span></td>
                              <td className="p-3 text-xs text-gray-500">{s.complete ? "Meets TPT minimum standard" : "Required for credible transition plan per TPT Section 4"}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </Section>
                </>
              );
            })()}
          </div>
        )}

        {/* Tab 3 — Gap Analysis */}
        {tab === 2 && (
          <div>
            <div className="flex gap-2 mb-4">
              {["All", "High", "Medium", "Low"].map(f => (
                <button key={f} onClick={() => setGapFilter(f)}
                  className={`px-3 py-1 text-xs rounded-full border transition-colors ${gapFilter === f ? "bg-black text-white border-black" : "border-gray-200 text-gray-600 hover:border-gray-400"}`}>
                  {f}
                </button>
              ))}
            </div>
            <Section title="Gap Register">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-gray-50 text-xs text-gray-500">
                      <th className="text-left p-3">Element</th>
                      <th className="text-left p-3">Sub-Element</th>
                      <th className="text-left p-3">Gap Description</th>
                      <th className="text-left p-3">Priority</th>
                      <th className="text-left p-3">Recommended Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredGaps.map((g, i) => (
                      <tr key={i} className="border-t border-gray-100 hover:bg-gray-50">
                        <td className="p-3 font-medium text-emerald-700">{g.element}</td>
                        <td className="p-3 font-medium">{g.sub}</td>
                        <td className="p-3 text-gray-600 text-xs">{g.desc}</td>
                        <td className="p-3">
                          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${g.priority === "High" ? "bg-red-100 text-red-700" : g.priority === "Medium" ? "bg-amber-100 text-amber-700" : "bg-gray-100 text-gray-500"}`}>{g.priority}</span>
                        </td>
                        <td className="p-3 text-xs text-gray-500">{g.action}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Gap Count by Element">
              <ResponsiveContainer width="100%" height={220}>
                <BarChart data={gapByElement} margin={{ top: 4, right: 20, bottom: 20, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 11 }} />
                  <Tooltip />
                  <Bar dataKey="count" name="Gaps" fill="#ef4444" radius={[3, 3, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* Tab 4 — Interim Targets */}
        {tab === 3 && (
          <div>
            <Section title="Target Inputs (Financed Emissions Reduction %)">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <Inp label="2025 Target %" type="number" value={targets.t2025} onChange={e => setTargets({ ...targets, t2025: e.target.value })} />
                <Inp label="2030 Target %" type="number" value={targets.t2030} onChange={e => setTargets({ ...targets, t2030: e.target.value })} />
                <Inp label="2035 Target %" type="number" value={targets.t2035} onChange={e => setTargets({ ...targets, t2035: e.target.value })} />
                <Inp label="2040 Target %" type="number" value={targets.t2040} onChange={e => setTargets({ ...targets, t2040: e.target.value })} />
              </div>
            </Section>

            <Section title="Transition Milestones Timeline">
              <div className="relative flex items-start gap-0 overflow-x-auto pb-4">
                <div className="absolute top-5 left-0 right-0 h-0.5 bg-gray-200 z-0" />
                {[
                  { year: "2024", label: "Baseline", fe: "0%", capex: `${form.greenCapex}%`, tf: "5%" },
                  { year: "2025", label: "Near-term", fe: `${targets.t2025}%`, capex: "25%", tf: "12%" },
                  { year: "2030", label: "Mid-term", fe: `${targets.t2030}%`, capex: "40%", tf: "25%" },
                  { year: "2035", label: "Mid-term+", fe: `${targets.t2035}%`, capex: "55%", tf: "40%" },
                  { year: "2040", label: "Long-term", fe: `${targets.t2040}%`, capex: "70%", tf: "60%" },
                  { year: "2050", label: "Net Zero", fe: "95%", capex: "90%", tf: "85%" },
                ].map((m, i) => (
                  <div key={m.year} className="flex-1 min-w-28 flex flex-col items-center relative z-10 px-1">
                    <div className={`w-4 h-4 rounded-full border-2 ${i === 0 ? "bg-black border-black" : "bg-emerald-500 border-emerald-500"} mb-2`} />
                    <div className="font-bold text-sm">{m.year}</div>
                    <div className="text-xs text-gray-500 mb-2">{m.label}</div>
                    <div className="text-xs text-center space-y-0.5">
                      <div><span className="text-gray-400">FE:</span> <span className="font-medium text-emerald-700">{m.fe}</span></div>
                      <div><span className="text-gray-400">CapEx:</span> <span className="font-medium">{m.capex}</span></div>
                      <div><span className="text-gray-400">TF:</span> <span className="font-medium text-blue-700">{m.tf}</span></div>
                    </div>
                  </div>
                ))}
              </div>
            </Section>

            <Section title="Emissions Trajectory vs Target Pathway">
              <ResponsiveContainer width="100%" height={260}>
                <LineChart data={trajectoryData} margin={{ top: 4, right: 20, bottom: 4, left: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                  <YAxis tickFormatter={v => `${v}%`} tick={{ fontSize: 11 }} />
                  <Tooltip formatter={v => `${v}%`} />
                  <Legend />
                  <Line type="monotone" dataKey="target" name="Target Pathway %" stroke={EMERALD} strokeWidth={2} strokeDasharray="5 5" dot={{ r: 4, fill: EMERALD }} />
                  <Line type="monotone" dataKey="current" name="Current Trajectory %" stroke="#0ea5e9" strokeWidth={2} dot={{ r: 4, fill: "#0ea5e9" }} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </div>
        )}

        {/* Tab 5 — Reference */}
        {tab === 4 && (
          <div>
            <Section title="TPT 6-Element Framework">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                {[
                  { num: "1", title: "Foundations", desc: "Paris alignment ambition, scope boundaries, business model, Just Transition" },
                  { num: "2", title: "Implementation Strategy", desc: "Short, medium, long-term actions; product/service decarbonisation" },
                  { num: "3", title: "Engagement", desc: "Value chain, policy engagement, industry collaboration, investor engagement" },
                  { num: "4", title: "Metrics & Targets", desc: "GHG targets (Scopes 1-3), carbon price, climate CapEx, financed emissions" },
                  { num: "5", title: "Governance", desc: "Board oversight, management responsibility, remuneration linkage" },
                  { num: "6", title: "Finance", desc: "Capital allocation, internal carbon price, green and transition finance" },
                ].map(el => (
                  <div key={el.num} className="bg-white border border-gray-200 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2">
                      <div className="w-7 h-7 rounded-full bg-emerald-600 text-white text-sm font-bold flex items-center justify-center">{el.num}</div>
                      <div className="font-semibold text-sm">{el.title}</div>
                    </div>
                    <div className="text-xs text-gray-500">{el.desc}</div>
                  </div>
                ))}
              </div>
            </Section>
            <Section title="Cross-Framework Mapping">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Framework Requirement</th><th className="text-left p-3">TPT Element</th></tr></thead>
                  <tbody>
                    {CROSS_FRAMEWORK.map((row, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3">{row.framework}</td>
                        <td className="p-3 text-emerald-700 font-medium">{row.tpt}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Quality Tier Thresholds">
              <div className="overflow-auto">
                <table className="w-full text-sm">
                  <thead><tr className="bg-gray-50 text-xs text-gray-500"><th className="text-left p-3">Tier</th><th className="text-left p-3">Score Range</th><th className="text-left p-3">Description</th></tr></thead>
                  <tbody>
                    {QUALITY_TIERS.map((t, i) => (
                      <tr key={i} className="border-t border-gray-100">
                        <td className="p-3 font-medium">{t.tier}</td>
                        <td className="p-3 font-mono text-xs">{t.range}</td>
                        <td className="p-3 text-gray-600">{t.desc}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Section>
            <Section title="Regulatory Context">
              <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700">
                <div className="font-semibold mb-2">FCA PS23/22 — Sustainability Disclosure Requirements and Investment Labels</div>
                <ul className="list-disc list-inside space-y-1 text-xs text-gray-600">
                  <li>Published: November 2023. Effective from 2024 reporting cycle.</li>
                  <li>Requires UK-authorised FIs to publish transition plan disclosures aligned to TPT framework.</li>
                  <li>Dovetails with TCFD and ISSB S2 disclosure requirements (cross-applicable pillars).</li>
                  <li>CSRD ESRS E1 transition plan requirements closely mirror TPT Elements 1-4.</li>
                  <li>TPT framework is also referenced in IOSCO, G7, and FSB transition finance guidance.</li>
                </ul>
              </div>
            </Section>
          </div>
        )}
      </div>
    </div>
  );
}
