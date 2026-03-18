/**
 * Basel Liquidity Page — Sprint 19 / E36
 * LCR, NSFR, IRRBB/ALM Gap, Liquidity Stress Test, Full Assessment
 * Backend: /api/v1/basel3-liquidity
 */
import React, { useState } from "react";
import {
  BarChart, Bar, LineChart, Line, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, RadarChart, PolarGrid, PolarAngleAxis, Radar,
} from "recharts";
import axios from "axios";

const BASE = "http://localhost:8001";
const EMERALD = "#10b981";
const COLORS = ["#10b981", "#0ea5e9", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

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

const TABS = ["LCR Dashboard", "NSFR Analysis", "IRRBB / ALM Gap", "Liquidity Stress Test", "Full Assessment"];
const NGFS_SCENARIOS = [
  { value: "net_zero_2050", label: "Net Zero 2050" },
  { value: "below_2c", label: "Below 2C" },
  { value: "delayed_transition", label: "Delayed Transition" },
  { value: "current_policies", label: "Current Policies" },
];
const RATE_SHOCKS = [
  { value: "parallel_up", label: "Parallel Up" },
  { value: "parallel_down", label: "Parallel Down" },
  { value: "steepener", label: "Steepener" },
  { value: "flattener", label: "Flattener" },
  { value: "short_up", label: "Short Up" },
  { value: "short_down", label: "Short Down" },
];

export default function BaselLiquidityPage() {
  const [activeTab, setActiveTab] = useState(0);
  const [entityId, setEntityId] = useState("ENT-001");
  const [entityName, setEntityName] = useState("Meridian Bank AG");
  const [reportingDate, setReportingDate] = useState("2026-03-17");
  const [scenario, setScenario] = useState("net_zero_2050");
  const [rateShock, setRateShock] = useState("parallel_up");
  const [loading, setLoading] = useState(false);
  const [lcrData, setLcrData] = useState(null);
  const [nsfrData, setNsfrData] = useState(null);
  const [irrbbData, setIrrbbData] = useState(null);
  const [stressData, setStressData] = useState(null);
  const [fullData, setFullData] = useState(null);
  const [showModal, setShowModal] = useState(false);

  function getFallback(key) {
    const rng = seededRng(entityId + key);
    const s = rng();
    const lcr = 95 + s * 60;
    const nsfr = 98 + s * 30;
    const hqla1 = 400 + rng() * 300;
    const hqla2a = 150 + rng() * 150;
    const hqla2b = 50 + rng() * 100;
    const netOut = (hqla1 + hqla2a * 0.85 + hqla2b * 0.75) / (lcr / 100);
    if (key === "lcr") return {
      lcr_pct: +lcr.toFixed(1),
      hqla_stock_mn: +(hqla1 + hqla2a + hqla2b).toFixed(0),
      net_outflow_mn: +netOut.toFixed(0),
      level1_mn: +hqla1.toFixed(0), level2a_mn: +hqla2a.toFixed(0), level2b_mn: +hqla2b.toFixed(0),
      status: lcr >= 110 ? "PASS" : lcr >= 100 ? "WARNING" : "BREACH",
    };
    if (key === "nsfr") {
      const asf = 800 + rng() * 400; const rsf = 700 + rng() * 350;
      return { nsfr_pct: +(asf / rsf * 100).toFixed(1), asf_mn: +asf.toFixed(0), rsf_mn: +rsf.toFixed(0), gap_mn: +(asf - rsf).toFixed(0) };
    }
    if (key === "irrbb") {
      const eve = -5 + rng() * 12; const nii = -3 + rng() * 8; const dur = -0.5 + rng() * 2;
      return { eve_pct: +eve.toFixed(2), nii_pct: +nii.toFixed(2), duration_gap_yr: +dur.toFixed(2), eba_breach: Math.abs(eve) > 8 };
    }
    if (key === "stress") {
      const surv = 15 + rng() * 40; const lar = 200 + rng() * 600;
      return { survival_horizon_days: +surv.toFixed(0), liquidity_at_risk_mn: +lar.toFixed(0), stressed_deposit_outflow_mn: +(100 + rng() * 300).toFixed(0), wholesale_outflow_mn: +(50 + rng() * 200).toFixed(0) };
    }
    return {};
  }

  async function runLCR() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/basel3-liquidity/lcr-assessment`, {
        entity_id: entityId, entity_name: entityName,
        hqla_breakdown: { level1_mn: 500, level2a_mn: 200, level2b_mn: 100 },
        outflow_breakdown: { retail_stable: 300, wholesale_financial: 500 },
        inflow_breakdown: { performing_loans: 200 },
        scenario_id: scenario,
      });
      setLcrData(r.data);
    } catch { setLcrData(getFallback("lcr")); }
    setLoading(false);
  }

  async function runNSFR() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/basel3-liquidity/nsfr-assessment`, { entity_id: entityId, entity_name: entityName });
      setNsfrData(r.data);
    } catch { setNsfrData(getFallback("nsfr")); }
    setLoading(false);
  }

  async function runIRRBB() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/basel3-liquidity/irrbb-assessment`, { entity_id: entityId, rate_shock: rateShock });
      setIrrbbData(r.data);
    } catch { setIrrbbData(getFallback("irrbb")); }
    setLoading(false);
  }

  async function runStress() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/basel3-liquidity/stress-test`, { entity_id: entityId, scenario_id: scenario });
      setStressData(r.data);
    } catch { setStressData(getFallback("stress")); }
    setLoading(false);
  }

  async function runFull() {
    setLoading(true);
    try {
      const r = await axios.post(`${BASE}/api/v1/basel3-liquidity/full-assessment`, { entity_id: entityId, entity_name: entityName, scenario_id: scenario });
      setFullData(r.data);
    } catch {
      const l = getFallback("lcr"); const n = getFallback("nsfr"); const i = getFallback("irrbb"); const s = getFallback("stress");
      setFullData({ lcr: l, nsfr: n, irrbb: i, stress: s });
    }
    setLoading(false);
  }

  const lcr = lcrData || getFallback("lcr");
  const nsfr = nsfrData || getFallback("nsfr");
  const irrbb = irrbbData || getFallback("irrbb");
  const stress = stressData || getFallback("stress");

  const lcrColor = lcr.lcr_pct >= 110 ? "#10b981" : lcr.lcr_pct >= 100 ? "#f59e0b" : "#ef4444";
  const statusColor = lcr.status === "PASS" ? "#10b981" : lcr.status === "WARNING" ? "#f59e0b" : "#ef4444";

  const hqlaChartData = [
    { name: "Level 1", value: lcr.level1_mn, fill: "#10b981" },
    { name: "Level 2A", value: lcr.level2a_mn, fill: "#0ea5e9" },
    { name: "Level 2B", value: lcr.level2b_mn, fill: "#f59e0b" },
    { name: "Net Outflow", value: lcr.net_outflow_mn, fill: "#ef4444" },
  ];

  const rng2 = seededRng(entityId + "nsfr-cat");
  const nsfrCats = ["Retail Deposits", "Wholesale Funding", "Secured Funding", "Derivatives", "Other"].map(n => ({
    name: n, asf: +(100 + rng2() * 300).toFixed(0), rsf: +(80 + rng2() * 250).toFixed(0),
  }));

  const buckets = ["O/N", "1W", "1M", "3M", "6M", "1Y", ">1Y"];
  const rng3 = seededRng(entityId + "alm");
  const almData = buckets.map((b, i) => {
    const assets = +(100 + rng3() * 400).toFixed(0);
    const liabilities = +(80 + rng3() * 350).toFixed(0);
    const gap = assets - liabilities;
    return { bucket: b, assets, liabilities, gap, cumulativeGap: gap * (i + 1) * 0.8 };
  });

  const rng4 = seededRng(entityId + "stress30d");
  const stressDays = Array.from({ length: 10 }, (_, i) => {
    const d = (i + 1) * 3;
    return { day: `Day ${d}`, outflow: +(50 + rng4() * 200 + i * 30).toFixed(0), cumulative: +(100 + i * 80 + rng4() * 150).toFixed(0) };
  });

  const monitorMetrics = [
    { label: "Concentration (CONC)", value: Math.min(100, 40 + seededRng(entityId + "c1")() * 50), thresh: 75 },
    { label: "Cash Flow Mismatch (CASHF)", value: Math.min(100, 55 + seededRng(entityId + "c2")() * 40), thresh: 80 },
    { label: "Intraday Liquidity (ILP)", value: Math.min(100, 60 + seededRng(entityId + "c3")() * 35), thresh: 70 },
    { label: "Run-Off Rates (RunOff)", value: Math.min(100, 30 + seededRng(entityId + "c4")() * 60), thresh: 65 },
  ];

  const ngfsHaircuts = NGFS_SCENARIOS.map((s, i) => ({
    scenario: s.label, haircut: +(2 + i * 1.5 + seededRng(s.value)() * 3).toFixed(1),
  }));

  const fullMetrics = [
    { metric: "LCR", value: `${lcr.lcr_pct}%`, threshold: "100%", status: lcr.status },
    { metric: "NSFR", value: `${nsfr.nsfr_pct}%`, threshold: "100%", status: nsfr.nsfr_pct >= 100 ? "PASS" : "BREACH" },
    { metric: "EVE Sensitivity", value: `${irrbb.eve_pct}%`, threshold: "+/-15%", status: Math.abs(irrbb.eve_pct) <= 15 ? "PASS" : "BREACH" },
    { metric: "NII Sensitivity", value: `${irrbb.nii_pct}%`, threshold: "+/-5%", status: Math.abs(irrbb.nii_pct) <= 5 ? "PASS" : "BREACH" },
    { metric: "Survival Horizon", value: `${stress.survival_horizon_days}d`, threshold: "30d", status: stress.survival_horizon_days >= 30 ? "PASS" : "BREACH" },
  ];

  const regGrid = [
    { reg: "CRR2 Art. 412 (LCR)", met: lcr.lcr_pct >= 100 },
    { reg: "CRR2 Art. 428 (NSFR)", met: nsfr.nsfr_pct >= 100 },
    { reg: "BCBS 238 Intraday Liq.", met: monitorMetrics[2].value >= 50 },
    { reg: "BCBS 295 IRRBB", met: !irrbb.eba_breach },
    { reg: "EBA IRRBB Guidelines", met: Math.abs(irrbb.eve_pct) <= 12 },
  ];

  return (
    <div style={{ fontFamily: "Inter, sans-serif", background: "#f3f4f6", minHeight: "100vh", padding: 24 }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>
        <h1 style={{ fontSize: 24, fontWeight: 700, color: "#111", marginBottom: 4 }}>Basel III Liquidity Risk</h1>
        <p style={{ color: "#6b7280", marginBottom: 24 }}>LCR · NSFR · IRRBB / ALM · Stress Testing — CRR2 / BCBS 238 / BCBS 295</p>

        {/* Tab Bar */}
        <div style={{ display: "flex", gap: 0, borderBottom: "2px solid #e5e7eb", marginBottom: 24 }}>
          {TABS.map((t, i) => (
            <button key={t} onClick={() => setActiveTab(i)} style={{
              background: "none", border: "none", padding: "10px 20px", fontSize: 14, fontWeight: 500,
              color: activeTab === i ? EMERALD : "#6b7280", cursor: "pointer",
              borderBottom: activeTab === i ? `2px solid ${EMERALD}` : "2px solid transparent",
              marginBottom: -2,
            }}>{t}</button>
          ))}
        </div>

        {/* Tab 1: LCR Dashboard */}
        {activeTab === 0 && (
          <>
            <Section title="Entity & Scenario">
              <Row><Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Entity Name" value={entityName} onChange={setEntityName} />
                <Inp label="Reporting Date" value={reportingDate} onChange={setReportingDate} type="date" />
                <Sel label="NGFS Scenario" value={scenario} onChange={setScenario} options={NGFS_SCENARIOS} />
              </Row>
              <Btn onClick={runLCR}>{loading ? "Running..." : "Run LCR Assessment"}</Btn>
            </Section>
            <Section title="LCR Summary">
              <Row>
                <KpiCard label="LCR Ratio" value={`${lcr.lcr_pct}%`} sub="Minimum 100%" color={lcrColor} />
                <KpiCard label="HQLA Stock (Mn)" value={`€${lcr.hqla_stock_mn}`} sub="Total eligible HQLA" color={EMERALD} />
                <KpiCard label="Net 30d Outflow (Mn)" value={`€${lcr.net_outflow_mn}`} sub="After inflow offset" color="#0ea5e9" />
                <div style={{ background: "#f9fafb", border: "1px solid #e5e7eb", borderRadius: 8, padding: 16, textAlign: "center" }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: statusColor, marginTop: 8 }}>{lcr.status}</div>
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>Regulatory Status</div>
                </div>
              </Row>
            </Section>
            <Section title="HQLA Breakdown vs Net Outflow">
              <Row>
                <div>
                  <ResponsiveContainer width="100%" height={280}>
                    <BarChart data={hqlaChartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="name" /><YAxis />
                      <Tooltip /><Legend />
                      <Bar dataKey="value" name="Amount (Mn)">
                        {hqlaChartData.map((e, i) => <Cell key={i} fill={e.fill} />)}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                <div>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                    <thead><tr style={{ background: "#f9fafb" }}>
                      {["Level", "Amount (Mn)", "Haircut %", "Eligible (Mn)"].map(h => (
                        <th key={h} style={{ padding: "8px 12px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                      ))}
                    </tr></thead>
                    <tbody>
                      {[
                        { level: "Level 1", amt: lcr.level1_mn, hc: 0, elig: lcr.level1_mn },
                        { level: "Level 2A", amt: lcr.level2a_mn, hc: 15, elig: +(lcr.level2a_mn * 0.85).toFixed(0) },
                        { level: "Level 2B", amt: lcr.level2b_mn, hc: 25, elig: +(lcr.level2b_mn * 0.75).toFixed(0) },
                      ].map(r => (
                        <tr key={r.level} style={{ borderBottom: "1px solid #f3f4f6" }}>
                          <td style={{ padding: "8px 12px" }}>{r.level}</td>
                          <td style={{ padding: "8px 12px" }}>€{r.amt}</td>
                          <td style={{ padding: "8px 12px" }}>{r.hc}%</td>
                          <td style={{ padding: "8px 12px", color: EMERALD, fontWeight: 600 }}>€{r.elig}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Row>
            </Section>
          </>
        )}

        {/* Tab 2: NSFR Analysis */}
        {activeTab === 1 && (
          <>
            <Section title="NSFR Assessment">
              <Row><Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Entity Name" value={entityName} onChange={setEntityName} />
              </Row>
              <Btn onClick={runNSFR}>{loading ? "Running..." : "Run NSFR Assessment"}</Btn>
            </Section>
            <Section title="NSFR Key Metrics">
              <Row>
                <KpiCard label="NSFR Ratio" value={`${nsfr.nsfr_pct}%`} sub="Minimum 100%" color={nsfr.nsfr_pct >= 100 ? EMERALD : "#ef4444"} />
                <KpiCard label="Available Stable Funding" value={`€${nsfr.asf_mn}Mn`} sub="Weighted liabilities" color={EMERALD} />
                <KpiCard label="Required Stable Funding" value={`€${nsfr.rsf_mn}Mn`} sub="Weighted assets" color="#0ea5e9" />
                <KpiCard label="Gap to 100" value={`€${nsfr.gap_mn}Mn`} sub="ASF minus RSF" color={nsfr.gap_mn >= 0 ? EMERALD : "#ef4444"} />
              </Row>
            </Section>
            <Section title="ASF vs RSF by Category">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={nsfrCats}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" tick={{ fontSize: 11 }} /><YAxis />
                  <Tooltip /><Legend />
                  <Bar dataKey="asf" name="ASF (Mn)" fill={EMERALD} />
                  <Bar dataKey="rsf" name="RSF (Mn)" fill="#0ea5e9" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            <Section title="ASF / RSF Category Breakdown">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ background: "#f9fafb" }}>
                  {["Category", "ASF (Mn)", "RSF (Mn)", "Net (Mn)", "Status"].map(h => (
                    <th key={h} style={{ padding: "8px 12px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>{nsfrCats.map(r => (
                  <tr key={r.name} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "8px 12px", fontWeight: 500 }}>{r.name}</td>
                    <td style={{ padding: "8px 12px" }}>€{r.asf}</td>
                    <td style={{ padding: "8px 12px" }}>€{r.rsf}</td>
                    <td style={{ padding: "8px 12px", color: r.asf - r.rsf >= 0 ? EMERALD : "#ef4444", fontWeight: 600 }}>€{r.asf - r.rsf}</td>
                    <td style={{ padding: "8px 12px" }}>
                      <span style={{ background: r.asf >= r.rsf ? "#d1fae5" : "#fee2e2", color: r.asf >= r.rsf ? "#065f46" : "#991b1b", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>
                        {r.asf >= r.rsf ? "OK" : "SHORTFALL"}
                      </span>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </Section>
          </>
        )}

        {/* Tab 3: IRRBB / ALM Gap */}
        {activeTab === 2 && (
          <>
            <Section title="IRRBB Settings">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Sel label="Rate Shock Scenario" value={rateShock} onChange={setRateShock} options={RATE_SHOCKS} />
              </Row>
              <Btn onClick={runIRRBB}>{loading ? "Running..." : "Run IRRBB Assessment"}</Btn>
            </Section>
            <Section title="IRRBB Metrics">
              <Row>
                <KpiCard label="EVE Sensitivity" value={`${irrbb.eve_pct}%`} sub="EBA threshold +/-15%" color={Math.abs(irrbb.eve_pct) > 15 ? "#ef4444" : EMERALD} />
                <KpiCard label="NII Sensitivity" value={`${irrbb.nii_pct}%`} sub="Net interest income" color={Math.abs(irrbb.nii_pct) > 5 ? "#f59e0b" : EMERALD} />
                <KpiCard label="Duration Gap" value={`${irrbb.duration_gap_yr}yr`} sub="Asset-liability mismatch" color="#0ea5e9" />
                <div style={{ background: irrbb.eba_breach ? "#fee2e2" : "#d1fae5", border: `1px solid ${irrbb.eba_breach ? "#fca5a5" : "#6ee7b7"}`, borderRadius: 8, padding: 16, textAlign: "center" }}>
                  <div style={{ fontSize: 16, fontWeight: 700, color: irrbb.eba_breach ? "#991b1b" : "#065f46", marginTop: 8 }}>
                    {irrbb.eba_breach ? "EBA BREACH" : "EBA COMPLIANT"}
                  </div>
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>BCBS 295 / EBA Threshold</div>
                </div>
              </Row>
            </Section>
            <Section title="ALM Time Bucket Analysis">
              <ResponsiveContainer width="100%" height={320}>
                <LineChart data={almData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="bucket" /><YAxis />
                  <Tooltip /><Legend />
                  <Line type="monotone" dataKey="assets" stroke={EMERALD} name="Assets (Mn)" strokeWidth={2} />
                  <Line type="monotone" dataKey="liabilities" stroke="#ef4444" name="Liabilities (Mn)" strokeWidth={2} />
                  <Line type="monotone" dataKey="gap" stroke="#f59e0b" name="Gap (Mn)" strokeWidth={2} strokeDasharray="5 5" />
                  <Line type="monotone" dataKey="cumulativeGap" stroke="#8b5cf6" name="Cumulative Gap" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </Section>
          </>
        )}

        {/* Tab 4: Liquidity Stress Test */}
        {activeTab === 3 && (
          <>
            <Section title="Stress Test Configuration">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Sel label="NGFS Scenario" value={scenario} onChange={setScenario} options={NGFS_SCENARIOS} />
              </Row>
              <Btn onClick={runStress}>{loading ? "Running..." : "Run Stress Test"}</Btn>
            </Section>
            <Section title="Stress Test KPIs">
              <Row>
                <KpiCard label="Survival Horizon" value={`${stress.survival_horizon_days}d`} sub="BCBS 238 minimum 30d" color={stress.survival_horizon_days >= 30 ? EMERALD : "#ef4444"} />
                <KpiCard label="Liquidity at Risk" value={`€${stress.liquidity_at_risk_mn}Mn`} sub="99% confidence" color="#f59e0b" />
                <KpiCard label="Stressed Deposit Outflow" value={`€${stress.stressed_deposit_outflow_mn}Mn`} sub="30-day projection" color="#ef4444" />
                <KpiCard label="Wholesale Outflow" value={`€${stress.wholesale_outflow_mn}Mn`} sub="Unsecured 30d" color="#8b5cf6" />
              </Row>
            </Section>
            <Section title="Stressed Outflow Accumulation (30 Days)">
              <ResponsiveContainer width="100%" height={280}>
                <AreaChart data={stressDays}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="day" /><YAxis />
                  <Tooltip /><Legend />
                  <Area type="monotone" dataKey="outflow" stroke="#ef4444" fill="#fee2e2" name="Daily Outflow (Mn)" />
                  <Area type="monotone" dataKey="cumulative" stroke="#f59e0b" fill="#fef3c7" name="Cumulative (Mn)" />
                </AreaChart>
              </ResponsiveContainer>
            </Section>
            <Section title="BCBS 238 Monitoring Metrics">
              {monitorMetrics.map(m => (
                <div key={m.label} style={{ marginBottom: 16 }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4, fontSize: 13 }}>
                    <span style={{ fontWeight: 500 }}>{m.label}</span>
                    <span style={{ color: m.value > m.thresh ? "#ef4444" : EMERALD, fontWeight: 600 }}>{m.value.toFixed(0)}% / {m.thresh}%</span>
                  </div>
                  <div style={{ background: "#f3f4f6", borderRadius: 6, height: 10, overflow: "hidden" }}>
                    <div style={{ width: `${Math.min(m.value, 100)}%`, height: "100%", background: m.value > m.thresh ? "#ef4444" : EMERALD, transition: "width 0.4s" }} />
                  </div>
                </div>
              ))}
            </Section>
          </>
        )}

        {/* Tab 5: Full Assessment */}
        {activeTab === 4 && (
          <>
            <Section title="Full Assessment">
              <Row>
                <Inp label="Entity ID" value={entityId} onChange={setEntityId} />
                <Inp label="Entity Name" value={entityName} onChange={setEntityName} />
                <Sel label="NGFS Scenario" value={scenario} onChange={setScenario} options={NGFS_SCENARIOS} />
              </Row>
              <div style={{ display: "flex", gap: 12 }}>
                <Btn onClick={runFull}>{loading ? "Running..." : "Run Full Assessment"}</Btn>
                <Btn onClick={() => setShowModal(true)} color="#374151">Export JSON</Btn>
              </div>
            </Section>
            <Section title="Summary Metrics">
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ background: "#f9fafb" }}>
                  {["Metric", "Value", "Threshold", "Status"].map(h => (
                    <th key={h} style={{ padding: "8px 12px", textAlign: "left", borderBottom: "1px solid #e5e7eb", fontWeight: 600 }}>{h}</th>
                  ))}
                </tr></thead>
                <tbody>{fullMetrics.map(r => (
                  <tr key={r.metric} style={{ borderBottom: "1px solid #f3f4f6" }}>
                    <td style={{ padding: "8px 12px", fontWeight: 500 }}>{r.metric}</td>
                    <td style={{ padding: "8px 12px", fontWeight: 600 }}>{r.value}</td>
                    <td style={{ padding: "8px 12px", color: "#6b7280" }}>{r.threshold}</td>
                    <td style={{ padding: "8px 12px" }}>
                      <span style={{ background: r.status === "PASS" ? "#d1fae5" : "#fee2e2", color: r.status === "PASS" ? "#065f46" : "#991b1b", borderRadius: 4, padding: "2px 8px", fontSize: 11, fontWeight: 600 }}>{r.status}</span>
                    </td>
                  </tr>
                ))}</tbody>
              </table>
            </Section>
            <Section title="Regulatory Compliance Grid">
              <Row>
                {regGrid.map(r => (
                  <div key={r.reg} style={{ background: r.met ? "#f0fdf4" : "#fff1f2", border: `1px solid ${r.met ? "#bbf7d0" : "#fecdd3"}`, borderRadius: 8, padding: 12, textAlign: "center" }}>
                    <div style={{ fontSize: 18 }}>{r.met ? "✓" : "✗"}</div>
                    <div style={{ fontSize: 12, fontWeight: 600, color: r.met ? "#065f46" : "#9f1239", marginTop: 4 }}>{r.reg}</div>
                  </div>
                ))}
              </Row>
            </Section>
            <Section title="Climate HQLA Haircut Impact by Scenario">
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={ngfsHaircuts}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="scenario" tick={{ fontSize: 11 }} /><YAxis unit="%" />
                  <Tooltip /><Legend />
                  <Bar dataKey="haircut" name="Additional Haircut %" fill="#f59e0b" />
                </BarChart>
              </ResponsiveContainer>
            </Section>
            {showModal && (
              <div style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.5)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}>
                <div style={{ background: "#fff", borderRadius: 12, padding: 24, maxWidth: 600, width: "90%", maxHeight: "80vh", overflow: "auto" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 16 }}>
                    <h3 style={{ margin: 0 }}>Full Assessment Export</h3>
                    <Btn onClick={() => setShowModal(false)} color="#6b7280">Close</Btn>
                  </div>
                  <pre style={{ background: "#f9fafb", padding: 16, borderRadius: 8, fontSize: 12, overflow: "auto" }}>
                    {JSON.stringify({ entity_id: entityId, entity_name: entityName, scenario, lcr, nsfr, irrbb, stress }, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
