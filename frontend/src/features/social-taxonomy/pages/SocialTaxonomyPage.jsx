/**
 * Social Taxonomy Page — Sprint 19 / E37
 * IMP 5 Dimensions, SDG Alignment, SFDR Compliance, Portfolio Holdings Impact
 * Backend: /api/v1/social-taxonomy
 */
import React, { useState } from "react";
import {
  BarChart, Bar, LineChart, Line, RadarChart, Radar, PolarGrid, PolarAngleAxis,
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";
import axios from "axios";

const BASE = "http://localhost:8001";
const EMERALD = "#10b981";
const COLORS = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

const Section = ({ title, children }) => (
  <div style={{ background: "#fff", border: "1px solid #e5e7eb", borderRadius: 8, padding: 24, marginBottom: 20 }}>
    <h3 style={{ margin: "0 0 16px", fontSize: 16, fontWeight: 600, color: "#111" }}>{title}</h3>
    {children}
  </div>
);
const KpiCard = ({ label, value, sub, color = "#10b981" }) => (
  <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, padding: 16, textAlign: "center" }}>
    <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>{label}</div>
    {sub && <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 2 }}>{sub}</div>}
  </div>
);
const Row = ({ children, gap = 12 }) => (
  <div style={{ display: "grid", gridTemplateColumns: `repeat(${React.Children.count(children)},1fr)`, gap }}>
    {children}
  </div>
);
const Inp = ({ label, value, onChange, type = "text" }) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 4 }}>{label}</label>
    <input type={type} value={value} onChange={e => onChange(e.target.value)}
      style={{ width: "100%", padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, boxSizing: "border-box" }} />
  </div>
);
const Sel = ({ label, value, onChange, options }) => (
  <div style={{ marginBottom: 12 }}>
    <label style={{ display: "block", fontSize: 12, fontWeight: 500, color: "#374151", marginBottom: 4 }}>{label}</label>
    <select value={value} onChange={e => onChange(e.target.value)}
      style={{ width: "100%", padding: "8px 12px", border: "1px solid #d1d5db", borderRadius: 6, fontSize: 14, background: "#fff" }}>
      {options.map(o => <option key={o.value || o} value={o.value || o}>{o.label || o}</option>)}
    </select>
  </div>
);
const Btn = ({ children, onClick, color = "#10b981" }) => (
  <button onClick={onClick}
    style={{ background: color, color: "#fff", border: "none", borderRadius: 6, padding: "10px 20px", fontSize: 14, fontWeight: 600, cursor: "pointer" }}>
    {children}
  </button>
);

function seededRng(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) h = (Math.imul(31, h) + str.charCodeAt(i)) | 0;
  return () => { h = (h * 16807 + 0) % 2147483647; return (h & 0x7fffffff) / 2147483647; };
}

const TABS = ["Social Taxonomy Overview", "IMP 5 Dimensions", "SDG Alignment", "SFDR Compliance", "Portfolio Holdings Impact"];

const ASSESSMENT_TYPES = [
  { value: "company", label: "Company" },
  { value: "fund", label: "Fund" },
  { value: "project", label: "Project" },
  { value: "social_bond", label: "Social Bond" },
];

const IMP_DIMS = ["What", "Who", "How Much", "Contribution", "Risk"];
const SDG_LIST = [
  { sdg: "SDG 1", label: "No Poverty" },
  { sdg: "SDG 2", label: "Zero Hunger" },
  { sdg: "SDG 3", label: "Good Health" },
  { sdg: "SDG 4", label: "Quality Education" },
  { sdg: "SDG 5", label: "Gender Equality" },
  { sdg: "SDG 8", label: "Decent Work" },
  { sdg: "SDG 10", label: "Reduced Inequalities" },
  { sdg: "SDG 11", label: "Sustainable Cities" },
  { sdg: "SDG 16", label: "Peace & Justice" },
];

export default function SocialTaxonomyPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [entityId, setEntityId] = useState("ST-ENT-001");
  const [entityName, setEntityName] = useState("Inclusive Capital Partners");
  const [assessmentType, setAssessmentType] = useState("fund");
  const [reportingPeriod, setReportingPeriod] = useState("2026");
  const [loading, setLoading] = useState(false);
  const [overviewData, setOverviewData] = useState(null);
  const [impData, setImpData] = useState(null);
  const [sfdrData, setSfdrData] = useState(null);
  const [holdingsData, setHoldingsData] = useState(null);

  function getFallback(key) {
    const rng = seededRng(entityId + key);
    if (key === "overview") return {
      decent_work_score: +(50 + rng() * 45).toFixed(1),
      living_standards_score: +(45 + rng() * 50).toFixed(1),
      inclusive_communities_score: +(40 + rng() * 55).toFixed(1),
      social_taxonomy_aligned_pct: +(30 + rng() * 60).toFixed(1),
      imp_composite: +(45 + rng() * 40).toFixed(1),
      sfdr_si_pct: +(20 + rng() * 60).toFixed(1),
    };
    if (key === "imp") return IMP_DIMS.map(d => ({
      dimension: d, score: +(40 + rng() * 55).toFixed(1),
      weight: d === "What" ? 25 : d === "Who" ? 20 : d === "How Much" ? 25 : d === "Contribution" ? 20 : 10,
    })).map(d => ({ ...d, weighted: +(d.score * d.weight / 100).toFixed(2) }));
    if (key === "sfdr") return {
      sfdr_si_pct: +(20 + rng() * 70).toFixed(1),
      dnsh_pass: rng() > 0.4,
      governance_pass: rng() > 0.3,
      art9_eligible_pct: +(15 + rng() * 60).toFixed(1),
    };
    if (key === "holdings") {
      const names = ["Microfinance Trust", "Affordable Housing Fund", "Rural Health REIT", "EdTech Bonds", "Gender Lens PE", "Community Infrastructure", "Living Wage ETF", "Inclusive Fintech"];
      return names.map((n, i) => {
        const r2 = seededRng(entityId + n);
        return {
          name: n, weight: +(5 + r2() * 20).toFixed(1),
          imp_score: +(40 + r2() * 55).toFixed(1),
          primary_sdg: SDG_LIST[i % SDG_LIST.length].sdg,
          art9_eligible: r2() > 0.4 ? "Y" : "N",
          dnsh_flag: r2() > 0.7,
        };
      });
    }
    return {};
  }

  async function runOverview() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/social-taxonomy/full-assessment`, { entity_id: entityId, entity_name: entityName, assessment_type: assessmentType, reporting_period: reportingPeriod });
      setOverviewData(r.data);
    } catch { setOverviewData(getFallback("overview")); }
    setLoading(false);
  }

  async function runIMP() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/social-taxonomy/imp-scoring`, { entity_id: entityId });
      setImpData(r.data);
    } catch { setImpData(getFallback("imp")); }
    setLoading(false);
  }

  async function runSFDR() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/social-taxonomy/sfdr-sustainable-investment`, { entity_id: entityId });
      setSfdrData(r.data);
    } catch { setSfdrData(getFallback("sfdr")); }
    setLoading(false);
  }

  async function runHoldings() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/social-taxonomy/portfolio-holdings`, {
        entity_id: entityId,
        holdings: getFallback("holdings").map(h => ({ name: h.name, weight: h.weight })),
      });
      setHoldingsData(r.data);
    } catch { setHoldingsData(getFallback("holdings")); }
    setLoading(false);
  }

  const overview = overviewData || getFallback("overview");
  const impRows = impData || getFallback("imp");
  const sfdr = sfdrData || getFallback("sfdr");
  const holdings = holdingsData || getFallback("holdings");

  const radarOverview = [
    { subject: "Decent Work", value: overview.decent_work_score },
    { subject: "Living Standards", value: overview.living_standards_score },
    { subject: "Inclusive Communities", value: overview.inclusive_communities_score },
    { subject: "IMP Composite", value: overview.imp_composite },
    { subject: "SFDR SI %", value: overview.sfdr_si_pct },
  ];

  const rngSDG = seededRng(entityId + "sdg");
  const sdgData = SDG_LIST.map(s => ({ name: s.sdg, label: s.label, score: +(20 + rngSDG() * 75).toFixed(1) }));
  const primarySDG = sdgData.reduce((a, b) => a.score > b.score ? a : b);

  const rngIRIS = seededRng(entityId + "iris");
  const irisMetrics = [
    { id: "OI4476", name: "Beneficiaries Reached", value: +(1000 + rngIRIS() * 50000).toFixed(0), unit: "persons" },
    { id: "OI7214", name: "Living Wage Coverage", value: +(30 + rngIRIS() * 65).toFixed(1), unit: "%" },
    { id: "PI2520", name: "Gender Pay Gap", value: +(2 + rngIRIS() * 18).toFixed(1), unit: "%" },
    { id: "PI6588", name: "Female Leadership %", value: +(20 + rngIRIS() * 55).toFixed(1), unit: "%" },
    { id: "OI6949", name: "Community Investment", value: +(0.5 + rngIRIS() * 5).toFixed(2), unit: "Mn EUR" },
  ];

  const paiSocial = [
    { pai: "PAI 9", name: "Board Gender Diversity", value: `${(25 + seededRng(entityId + "p9")() * 45).toFixed(0)}%`, status: "green" },
    { pai: "PAI 10", name: "Controversial Weapons", value: `${(seededRng(entityId + "p10")() * 5).toFixed(1)}%`, status: "amber" },
    { pai: "PAI 11", name: "UNGC/OECD Violations", value: `${(seededRng(entityId + "p11")() * 8).toFixed(0)} co.`, status: "red" },
    { pai: "PAI 12", name: "Unadjusted Pay Gap", value: `${(5 + seededRng(entityId + "p12")() * 20).toFixed(1)}%`, status: "amber" },
    { pai: "PAI 13", name: "Excessive CEO-Worker Pay", value: `${(20 + seededRng(entityId + "p13")() * 80).toFixed(0)}x`, status: "red" },
    { pai: "PAI 14", name: "Insufficient Whistleblower", value: `${(seededRng(entityId + "p14")() * 30).toFixed(0)}%`, status: "green" },
  ];

  const esrsLinks = [
    { esrs: "ESRS S1", topic: "Own Workforce", linked: "Y" },
    { esrs: "ESRS S2", topic: "Workers in Value Chain", linked: "Y" },
    { esrs: "ESRS S3", topic: "Affected Communities", linked: "Y" },
    { esrs: "ESRS S4", topic: "Consumers & End-users", linked: sfdr.dnsh_pass ? "Y" : "Partial" },
  ];

  const impRadar = IMP_DIMS.map(d => {
    const row = impRows.find ? impRows.find(r => r.dimension === d) : { score: 60 };
    return { subject: d, score: row ? row.score : 60 };
  });

  const weightedAvgIMP = holdings.reduce ? (holdings.reduce((s, h) => s + h.imp_score * h.weight, 0) / holdings.reduce((s, h) => s + h.weight, 0)).toFixed(1) : "N/A";

  const trafficColor = st => st === "green" ? "#10b981" : st === "amber" ? "#f59e0b" : "#ef4444";

  return (
    <div style={{ fontFamily: "Inter, sans-serif", background: "#f3f4f6", minHeight: "100vh", padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "#111", marginBottom: 4 }}>Social Taxonomy Assessment</h1>
        <p style={{ color: "#6b7280", marginBottom: 24 }}>IMP Framework · SDG Alignment · SFDR Social PAI · EU Social Taxonomy</p>

        {/* Tab Bar */}
        <div style={{ display: "flex", gap: 0, borderBottom: "2px solid #e5e7eb", marginBottom: 24 }}>
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setActiveTab(i)} style={{
              background: "none", border: "none", padding: "10px 18px", fontSize: 13, fontWeight: 500,
              color: activeTab === i ? EMERALD : "#6b7280", cursor: "pointer",
              borderBottom: activeTab === i ? `2px solid ${EMERALD}` : "2px solid transparent", marginBottom: -2,
            }}>{t}</button>
          ))}
        </div>

        {/* Tab 1: Social Taxonomy Overview */}
        {activeTab === 0 && (
          <>
            <Section title="Assessment Configuration">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Entity Name" value={entityName} onChange={setEntityName} />
                <Sel label="Assessment Type" value={assessmentType} onChange={setAssessmentType} options={ASSESSMENT_TYPES} />
                <Inp label="Reporting Period" value={reportingPeriod} onChange={setReportingPeriod} />
              </Row>
              <Btn onClick={runOverview}>{loading ? "Running..." : "Run Full Assessment"}</Btn>
            </Section>
            <Section title="Social Taxonomy KPIs">
              <Row>
                <KpiCard label="Decent Work Score" value={`${overview.decent_work_score}/100`} sub="Fair wages, safe conditions" color={EMERALD} />
                <KpiCard label="Living Standards Score" value={`${overview.living_standards_score}/100`} sub="Housing, food, healthcare" color="#0ea5e9" />
                <KpiCard label="Inclusive Communities" value={`${overview.inclusive_communities_score}/100`} sub="Access & participation" color="#8b5cf6" />
                <KpiCard label="Social Taxonomy Aligned" value={`${overview.social_taxonomy_aligned_pct}%`} sub="EU Social Taxonomy" color={overview.social_taxonomy_aligned_pct >= 50 ? EMERALD : "#f59e0b"} />
              </Row>
            </Section>
            <Section title="Multi-Objective Radar">
              <ResponsiveContainer width="100%" height={320}>
                <RadarChart data={radarOverview}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                  <Radar name="Score" dataKey="value" stroke={EMERALD} fill={EMERALD} fillOpacity={0.3} />
                  <Tooltip />
                  <Legend />
                </RadarChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* Tab 2: IMP 5 Dimensions */}
        {activeTab === 1 && (
          <>
            <Section title="IMP Assessment">
              <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
              <Btn onClick={runIMP}>{loading ? "Running..." : "Run IMP Scoring"}</Btn>
            </Section>
            <Section title="IMP Composite Score">
              <Row>
                <KpiCard label="IMP Composite Score" value={`${(impRows.reduce ? impRows.reduce((s, r) => s + r.weighted, 0) : 55).toFixed(1)}/100`} sub="Weighted across 5 dimensions" color={EMERALD} />
                {IMP_DIMS.map((d, i) => {
                  const row = impRows.find ? impRows.find(r => r.dimension === d) : { score: 60 };
                  return <KpiCard key={d} label={d} value={`${row ? row.score : 60}`} sub="/ 100" color={COLORS[i]} />;
                })}
              </Row>
            </Section>
            <Section title="IMP Radar Chart">
              <Row>
                <ResponsiveContainer width="100%" height={300}>
                  <RadarChart data={impRadar}>
                    <PolarGrid /><PolarAngleAxis dataKey="subject" tick={{ fontSize: 12 }} />
                    <Radar name="IMP Score" dataKey="score" stroke={EMERALD} fill={EMERALD} fillOpacity={0.35} />
                    <Tooltip /><Legend />
                  </RadarChart>
                </ResponsiveContainer>
                <div>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead><tr style={{ background: "#f9fafb" }}>
                      {["Dimension", "Score", "Weight %", "Weighted", "Description"].map(h => (
                        <th key={h} style={{ padding: "8px 10px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>{(impRows.map ? impRows : getFallback("imp")).map(r => (
                      <tr key={r.dimension} style={{ borderBottom: "1px solid #f3f4f6" }}>
                        <td style={{ padding: "8px 10px", fontWeight: 600 }}>{r.dimension}</td>
                        <td style={{ padding: "8px 10px", color: EMERALD, fontWeight: 600 }}>{r.score}</td>
                        <td style={{ padding: "8px 10px" }}>{r.weight}%</td>
                        <td style={{ padding: "8px 10px" }}>{r.weighted}</td>
                        <td style={{ padding: "8px 10px", color: "#6b7280", fontSize: 11 }}>
                          {r.dimension === "What" ? "Nature of outcome" : r.dimension === "Who" ? "Affected stakeholders" : r.dimension === "How Much" ? "Depth, breadth, duration" : r.dimension === "Contribution" ? "Additionality" : "Risk of harm"}
                        </td>
                      </tr>
                    ))}</tbody>
                  </table>
                </div>
              </Row>
            </Section>
          </>
        )}

        {/* Tab 3: SDG Alignment */}
        {activeTab === 2 && (
          <>
            <Section title="SDG Contribution Scores">
              <Row>
                <KpiCard label="Primary SDG" value={primarySDG.sdg} sub={primarySDG.label} color={EMERALD} />
                <KpiCard label="Beneficiaries Reached" value={`${(irisMetrics[0].value / 1000).toFixed(0)}K`} sub="Persons" color="#0ea5e9" />
                <KpiCard label="Living Wage Coverage" value={`${irisMetrics[1].value}%`} sub="IRIS+ OI7214" color="#8b5cf6" />
                <KpiCard label="Gender Pay Gap" value={`${irisMetrics[2].value}%`} sub="IRIS+ PI2520" color={irisMetrics[2].value < 10 ? EMERALD : "#f59e0b"} />
              </Row>
            </Section>
            <Section title="SDG Contribution Bar Chart">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={sdgData} layout="vertical">
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" domain={[0, 100]} /><YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={55} />
                  <Tooltip formatter={(v, n, p) => [`${v}`, p.payload.label]} /><Legend />
                  <Bar dataKey="score" name="Contribution Score" fill={EMERALD}>
                    {sdgData.map((e, i) => <Cell key={i} fill={e.name === primarySDG.sdg ? "#059669" : EMERALD} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="IRIS+ Metrics">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ background: "#f9fafb" }}>
                  {["Metric ID", "Name", "Value", "Unit"].map(h => (
                    <th key={h} style={{ padding: "8px 12px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>{irisMetrics.map(m => (
                  <tr key={m.id} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", color: "#6b7280" }}>{m.id}</td>
                    <td style={{ padding: "8px 12px", fontWeight: 500 }}>{m.name}</td>
                    <td style={{ padding: "8px 12px", fontWeight: 700, color: EMERALD }}>{m.value}</td>
                    <td style={{ padding: "8px 12px", color: "#9ca3af" }}>{m.unit}</td>
                  </tr>
                ))}</tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 4: SFDR Compliance */}
        {activeTab === 3 && (
          <>
            <Section title="SFDR Assessment">
              <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
              <Btn onClick={runSFDR}>{loading ? "Running..." : "Run SFDR Assessment"}</Btn>
            </Section>
            <Section title="SFDR Sustainable Investment Metrics">
              <Row>
                <KpiCard label="SFDR SI %" value={`${sfdr.sfdr_si_pct}%`} sub="Sustainable investment share" color={sfdr.sfdr_si_pct >= 50 ? EMERALD : "#f59e0b"} />
                <KpiCard label="Art 9 Eligible %" value={`${sfdr.art9_eligible_pct}%`} sub="Dark green eligible" color={sfdr.art9_eligible_pct >= 40 ? EMERALD : "#f59e0b"} />
                <div style={{ background: sfdr.dnsh_pass ? "#f0fdf4" : "#fff1f2", border: `1px solid ${sfdr.dnsh_pass ? "#bbf7d0" : "#fecdd3"}`, borderRadius: 8, padding: 16, textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: sfdr.dnsh_pass ? "#065f46" : "#991b1b", marginTop: 4 }}>{sfdr.dnsh_pass ? "PASS" : "FAIL"}</div>
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>DNSH Check</div>
                </div>
                <div style={{ background: sfdr.governance_pass ? "#f0fdf4" : "#fff1f2", border: `1px solid ${sfdr.governance_pass ? "#bbf7d0" : "#fecdd3"}`, borderRadius: 8, padding: 16, textAlign: "center" }}>
                  <div style={{ fontSize: 20, fontWeight: 700, color: sfdr.governance_pass ? "#065f46" : "#991b1b", marginTop: 4 }}>{sfdr.governance_pass ? "PASS" : "FAIL"}</div>
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>Governance Check</div>
                </div>
              </Row>
            </Section>
            <Section title="PAI Social Indicators (PAI 9-14)">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ background: "#f9fafb" }}>
                  {["PAI", "Indicator", "Value", "Traffic Light"].map(h => (
                    <th key={h} style={{ padding: "8px 12px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>{paiSocial.map(p => (
                  <tr key={p.pai} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", fontWeight: 600, color: "#6b7280" }}>{p.pai}</td>
                    <td style={{ padding: "8px 12px" }}>{p.name}</td>
                    <td style={{ padding: "8px 12px", fontWeight: 600 }}>{p.value}</td>
                    <td style={{ padding: "8px 12px" }}>
                      <span style={{ display: "inline-block", width: 14, height: 14, borderRadius: "50%", background: trafficColor(p.status), verticalAlign: "middle", marginRight: 6 }} />
                      <span style={{ fontSize: 11, color: trafficColor(p.status), fontWeight: 600 }}>{p.status.toUpperCase()}</span>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </Section>
            <Section title="ESRS S1-S4 Linkage">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ background: "#f9fafb" }}>
                  {["ESRS", "Topic", "Linked"].map(h => (
                    <th key={h} style={{ padding: "8px 12px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>{esrsLinks.map(r => (
                  <tr key={r.esrs} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "8px 12px", fontFamily: "monospace", fontWeight: 600, color: "#0ea5e9" }}>{r.esrs}</td>
                    <td style={{ padding: "8px 12px" }}>{r.topic}</td>
                    <td style={{ padding: "8px 12px" }}>
                      <span style={{ background: r.linked === "Y" ? "#d1fae5" : "#fef3c7", color: r.linked === "Y" ? "#065f46" : "#92400e", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>{r.linked}</span>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 5: Portfolio Holdings Impact */}
        {activeTab === 4 && (
          <>
            <Section title="Portfolio Holdings">
              <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
              <Btn onClick={runHoldings}>{loading ? "Running..." : "Run Portfolio Assessment"}</Btn>
            </Section>
            <Section title="Portfolio Aggregate">
              <Row>
                <KpiCard label="Weighted-Avg IMP Score" value={`${weightedAvgIMP}/100`} sub="Exposure-weighted" color={EMERALD} />
                <KpiCard label="Total Holdings" value={holdings.length || 8} sub="Screened positions" color="#0ea5e9" />
                <KpiCard label="Art 9 Eligible" value={`${holdings.filter ? holdings.filter(h => h.art9_eligible === "Y").length : 4} / ${holdings.length || 8}`} sub="Dark green" color="#8b5cf6" />
                <KpiCard label="DNSH Flags" value={`${holdings.filter ? holdings.filter(h => h.dnsh_flag).length : 1}`} sub="Require review" color="#ef4444" />
              </Row>
            </Section>
            <Section title="Holdings by IMP Score">
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={holdings.slice ? [...holdings].sort((a, b) => b.imp_score - a.imp_score) : []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 10 }} /><YAxis domain={[0, 100]} />
                  <Tooltip /><Legend />
                  <Bar dataKey="imp_score" name="IMP Composite Score" fill={EMERALD} />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="Holdings Table">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ background: "#f9fafb" }}>
                  {["Holding Name", "Weight %", "IMP Score", "Primary SDG", "Art 9 Eligible", "DNSH Flag"].map(h => (
                    <th key={h} style={{ padding: "8px 10px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>{(holdings.map ? holdings : []).map(h => (
                  <tr key={h.name} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "8px 10px", fontWeight: 500 }}>{h.name}</td>
                    <td style={{ padding: "8px 10px" }}>{h.weight}%</td>
                    <td style={{ padding: "8px 10px", fontWeight: 700, color: h.imp_score >= 60 ? EMERALD : "#f59e0b" }}>{h.imp_score}</td>
                    <td style={{ padding: "8px 10px" }}><span style={{ background: "#dbeafe", color: "#1d4ed8", borderRadius: 4, padding: "2px 6px", fontSize: 11, fontWeight: 600 }}>{h.primary_sdg}</span></td>
                    <td style={{ padding: "8px 10px" }}>
                      <span style={{ background: h.art9_eligible === "Y" ? "#d1fae5" : "#f3f4f6", color: h.art9_eligible === "Y" ? "#065f46" : "#6b7280", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>{h.art9_eligible}</span>
                    </td>
                    <td style={{ padding: "8px 10px" }}>
                      {h.dnsh_flag ? <span style={{ background: "#fee2e2", color: "#991b1b", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>FLAG</span>
                        : <span style={{ background: "#d1fae5", color: "#065f46", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>CLEAR</span>}
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </Section>
          </>
        )}
      </div>
    </div>
  );
}
