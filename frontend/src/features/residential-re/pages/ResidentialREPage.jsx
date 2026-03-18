/**
 * Residential Real Estate — Climate & ESG Assessment
 *
 * Tab 1 — Residential Assessment  /api/v1/residential-re
 * Tab 2 — RICS ESG Assessment     /api/v1/rics-esg
 * Tab 3 — Spatial Hazard          /api/v1/spatial-hazard
 * Tab 4 — CRREM Pathway           /api/v1/crrem-stranding (residential)
 * Tab 5 — Retrofit Planner        /api/v1/retrofit-planner
 */
import React, { useState } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  Cell, LineChart, Line, PieChart, Pie, Legend, AreaChart, Area,
} from "recharts";
import {
  Home, Thermometer, Droplets, Flame, Trees, TrendingUp, TrendingDown,
  ChevronDown, ChevronUp, Play, RefreshCw, AlertTriangle, CheckCircle,
  BarChart3, MapPin, Layers, Wrench, Star,
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";
const TOOLTIP_STYLE = { backgroundColor: "#fff", border: "1px solid rgba(0,0,0,0.08)", color: "#111" };
function sr(seed) { let s = seed; return () => { s = (s * 16807) % 2147483647; return (s - 1) / 2147483646; }; }

/* ── Primitives ──────────────────────────────────────────────────────────── */
function Section({ title, children, defaultOpen = true, icon: Icon }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden mb-4 bg-white">
      <button onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-gray-50 transition-colors">
        <div className="flex items-center gap-2">
          {Icon && <Icon className="h-3.5 w-3.5 text-gray-500" />}
          <span className="font-medium text-sm text-gray-700">{title}</span>
        </div>
        {open ? <ChevronUp className="h-3.5 w-3.5 text-gray-400" /> : <ChevronDown className="h-3.5 w-3.5 text-gray-400" />}
      </button>
      {open && <div className="p-4">{children}</div>}
    </div>
  );
}

function KpiCard({ label, value, sub, color }) {
  return (
    <div className="bg-white border border-gray-200 rounded-lg p-3">
      <p className="text-[10px] text-gray-500 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-xl font-semibold font-mono tabular-nums ${color || "text-gray-900"}`}>{value}</p>
      {sub && <p className="text-[10px] text-gray-500 mt-0.5">{sub}</p>}
    </div>
  );
}

function Row({ label, children }) {
  return (
    <div className="flex items-center gap-3 mb-2">
      <label className="text-[11px] text-gray-500 w-44 shrink-0">{label}</label>
      <div className="flex-1">{children}</div>
    </div>
  );
}

function Inp({ value, onChange, type = "text", placeholder }) {
  return (
    <input type={type} value={value} onChange={e => onChange(e.target.value)} placeholder={placeholder}
      className="w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        placeholder-gray-400 focus:outline-none focus:border-blue-500" />
  );
}

function Sel({ value, onChange, options }) {
  return (
    <select value={value} onChange={e => onChange(e.target.value)}
      className="w-full bg-white border border-gray-300 rounded px-2.5 py-1.5 text-xs text-gray-800
        focus:outline-none focus:border-blue-500">
      {options.map(o => <option key={o.v} value={o.v}>{o.l}</option>)}
    </select>
  );
}

function Btn({ onClick, disabled, loading, children }) {
  return (
    <button onClick={onClick} disabled={disabled || loading}
      className="inline-flex items-center gap-1.5 px-4 py-2 bg-[#164E8A] text-white rounded text-xs font-medium hover:bg-[#12407A] disabled:opacity-40 transition-all">
      {loading && <RefreshCw className="h-3 w-3 animate-spin" />}
      {children}
    </button>
  );
}

function EPCBadge({ grade }) {
  const colors = {
    A: "bg-emerald-50 text-emerald-700 border-emerald-200",
    B: "bg-green-50 text-green-700 border-green-200",
    C: "bg-lime-50 text-lime-700 border-lime-200",
    D: "bg-yellow-50 text-yellow-700 border-yellow-200",
    E: "bg-amber-50 text-amber-700 border-amber-200",
    F: "bg-orange-50 text-orange-700 border-orange-200",
    G: "bg-red-50 text-red-700 border-red-200",
  };
  return <span className={`px-2 py-0.5 rounded border text-xs font-bold ${colors[grade] || "bg-gray-50 text-gray-600"}`}>{grade}</span>;
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 1 — RESIDENTIAL ASSESSMENT
══════════════════════════════════════════════════════════════════════════ */
function ResidentialPanel() {
  const [propertyId, setPropertyId] = useState("prop-001");
  const [propertyType, setPropertyType] = useState("detached");
  const [floorArea, setFloorArea] = useState("145");
  const [buildYear, setBuildYear] = useState("1985");
  const [country, setCountry] = useState("DE");
  const [epcRating, setEpcRating] = useState("D");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const PORTFOLIO = [
    { id: "prop-001", addr: "12 Elm St, Berlin", type: "Detached", epc: "D", stranding: 2028, clvar: 42000 },
    { id: "prop-002", addr: "4 Oak Ave, Munich", type: "Apartment", epc: "B", stranding: 2042, clvar: 8000 },
    { id: "prop-003", addr: "7 Lime Rd, Hamburg", type: "Semi-Det.", epc: "F", stranding: 2025, clvar: 91000 },
    { id: "prop-004", addr: "22 Pine Blvd, Frankfurt", type: "Detached", epc: "C", stranding: 2035, clvar: 19000 },
    { id: "prop-005", addr: "8 Beech Ln, Stuttgart", type: "Terrace", epc: "E", stranding: 2027, clvar: 58000 },
  ];

  const EPC_DIST = [
    { grade: "A", count: 18 }, { grade: "B", count: 34 }, { grade: "C", count: 52 },
    { grade: "D", count: 71 }, { grade: "E", count: 48 }, { grade: "F", count: 29 }, { grade: "G", count: 12 },
  ];

  async function run() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/residential-re/assess`, {
        property_id: propertyId, property_type: propertyType,
        floor_area_sqm: parseFloat(floorArea), build_year: parseInt(buildYear),
        country, epc_rating: epcRating,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Assessment failed");
    } finally { setLoading(false); }
  }

  const EPC_COLORS = { A: "#10b981", B: "#22c55e", C: "#84cc16", D: "#eab308", E: "#f59e0b", F: "#f97316", G: "#ef4444" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Portfolio Properties" value="264" sub="Residential units" />
        <KpiCard label="Avg EPC Rating" value="D" sub="EU MEPS risk at 2025" color="text-amber-600" />
        <KpiCard label="At Stranding Risk" value="41" sub="Before 2030" color="text-red-500" />
        <KpiCard label="Avg Climate VaR" value="€38K" sub="Per property" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Section title="EPC Distribution" icon={BarChart3}>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={EPC_DIST} margin={{ left: 0, right: 10, top: 4, bottom: 4 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
              <XAxis dataKey="grade" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Bar dataKey="count" name="Properties" radius={[3, 3, 0, 0]}>
                {EPC_DIST.map(d => <Cell key={d.grade} fill={EPC_COLORS[d.grade]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Section>

        <Section title="Stranding Timeline" icon={AlertTriangle}>
          {PORTFOLIO.map(p => (
            <div key={p.id} className="flex items-center justify-between py-1.5 border-b border-gray-100 last:border-0 text-xs">
              <div className="min-w-0 flex-1">
                <p className="font-medium text-gray-700 truncate">{p.addr}</p>
                <p className="text-gray-500">{p.type}</p>
              </div>
              <div className="flex items-center gap-3 shrink-0">
                <EPCBadge grade={p.epc} />
                <span className={`font-mono ${p.stranding <= 2027 ? "text-red-500" : p.stranding <= 2032 ? "text-amber-500" : "text-emerald-600"}`}>
                  Strand {p.stranding}
                </span>
                <span className="text-gray-500">€{(p.clvar / 1000).toFixed(0)}K VaR</span>
              </div>
            </div>
          ))}
        </Section>
      </div>

      <Section title="Assess Property" icon={Play}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
          <div>
            <Row label="Property ID"><Inp value={propertyId} onChange={setPropertyId} /></Row>
            <Row label="Property Type">
              <Sel value={propertyType} onChange={setPropertyType} options={[
                { v: "detached", l: "Detached House" }, { v: "semi_detached", l: "Semi-Detached" },
                { v: "terraced", l: "Terrace" }, { v: "apartment", l: "Apartment" }, { v: "bungalow", l: "Bungalow" },
              ]} />
            </Row>
            <Row label="Floor Area (m²)"><Inp value={floorArea} onChange={setFloorArea} type="number" /></Row>
          </div>
          <div>
            <Row label="Build Year"><Inp value={buildYear} onChange={setBuildYear} type="number" /></Row>
            <Row label="Country">
              <Sel value={country} onChange={setCountry} options={[
                { v: "DE", l: "Germany" }, { v: "FR", l: "France" }, { v: "GB", l: "United Kingdom" },
                { v: "NL", l: "Netherlands" }, { v: "ES", l: "Spain" }, { v: "IT", l: "Italy" },
              ]} />
            </Row>
            <Row label="Current EPC Rating">
              <Sel value={epcRating} onChange={setEpcRating} options={
                ["A", "B", "C", "D", "E", "F", "G"].map(g => ({ v: g, l: `EPC ${g}` }))
              } />
            </Row>
          </div>
        </div>
        <Btn onClick={run} loading={loading}><Play className="h-3 w-3" /> Run Assessment</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-2">
            <p className="font-semibold text-gray-700">Assessment Result</p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ["Stranding Year", result.stranding_year ?? "—"],
                ["Climate VaR", result.climate_var_eur ? `€${result.climate_var_eur.toLocaleString()}` : "—"],
                ["Carbon Intensity", result.carbon_intensity_kg ? `${result.carbon_intensity_kg} kgCO₂/m²` : "—"],
                ["MEPS Status", result.meps_compliant ? "Compliant" : "Non-Compliant"],
              ].map(([l, v]) => (
                <div key={l}><span className="text-gray-500">{l}:</span> <span className="font-medium">{v}</span></div>
              ))}
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 2 — RICS ESG ASSESSMENT
══════════════════════════════════════════════════════════════════════════ */
function RICSPanel() {
  const [assetId, setAssetId] = useState("prop-001");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const DIMENSIONS = [
    { dim: "Energy Performance", score: 62, max: 100 },
    { dim: "Carbon Emissions", score: 55, max: 100 },
    { dim: "Water Efficiency", score: 74, max: 100 },
    { dim: "Waste Management", score: 48, max: 100 },
    { dim: "Biodiversity", score: 42, max: 100 },
    { dim: "Indoor Environment", score: 81, max: 100 },
    { dim: "Governance & Disclosure", score: 70, max: 100 },
  ];

  async function run() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/rics-esg/assess`, { asset_id: assetId });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="RICS ESG Score" value="62 / 100" sub="Amber — improvement needed" color="text-amber-600" />
        <KpiCard label="GRESB Rating" value="3-Star" sub="Residential residential" />
        <KpiCard label="Green Premium" value="+4.2%" sub="vs non-certified" color="text-emerald-600" />
        <KpiCard label="Certifications" value="2" sub="BREEAM · EPC B" />
      </div>

      <Section title="ESG Dimension Scores (RICS Global RE Sustainability Benchmark)" icon={Star}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={DIMENSIONS} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
            <YAxis dataKey="dim" type="category" tick={{ fontSize: 10 }} width={140} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => [`${v}/100`, "Score"]} />
            <Bar dataKey="score" radius={[0, 3, 3, 0]}>
              {DIMENSIONS.map((d, i) => (
                <Cell key={i} fill={d.score >= 70 ? "#10b981" : d.score >= 50 ? "#f59e0b" : "#ef4444"} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Run RICS ESG Assessment" icon={Play}>
        <Row label="Asset ID"><Inp value={assetId} onChange={setAssetId} /></Row>
        <Btn onClick={run} loading={loading}><Play className="h-3 w-3" /> Assess</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs">
            <p className="font-semibold text-gray-700 mb-2">RICS ESG Result</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {[
                ["Overall Score", result.overall_score ? `${result.overall_score}/100` : "—"],
                ["Energy Rating", result.energy_rating ?? "—"],
                ["Carbon kg/m²", result.carbon_intensity_kg_m2 ?? "—"],
                ["Green Premium %", result.green_premium_pct ? `${result.green_premium_pct}%` : "—"],
                ["GRESB Stars", result.gresb_stars ?? "—"],
                ["Action Priority", result.action_priority ?? "—"],
              ].map(([l, v]) => (
                <div key={l}><span className="text-gray-500">{l}:</span> <span className="font-medium">{v}</span></div>
              ))}
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 3 — SPATIAL HAZARD
══════════════════════════════════════════════════════════════════════════ */
function SpatialHazardPanel() {
  const [lat, setLat] = useState("52.520");
  const [lng, setLng] = useState("13.405");
  const [scenario, setScenario] = useState("rcp45");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const HAZARD_DATA = [
    { hazard: "Coastal Flood", risk2030: 28, risk2050: 44, risk2100: 71 },
    { hazard: "Riverine Flood", risk2030: 35, risk2050: 52, risk2100: 68 },
    { hazard: "Heat Stress", risk2030: 42, risk2050: 67, risk2100: 89 },
    { hazard: "Wildfire", risk2030: 12, risk2050: 22, risk2100: 38 },
    { hazard: "Extreme Precipitation", risk2030: 30, risk2050: 45, risk2100: 62 },
    { hazard: "Drought", risk2030: 18, risk2050: 31, risk2100: 55 },
  ];

  async function run() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/spatial-hazard/assess`, {
        latitude: parseFloat(lat), longitude: parseFloat(lng), scenario,
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="High-Risk Properties" value="23" sub="Flood zone 1 or 2" color="text-red-500" />
        <KpiCard label="Heat Stress Exposure" value="67%" sub="Portfolio under RCP 4.5 2050" color="text-amber-600" />
        <KpiCard label="Avg Composite Risk" value="42 / 100" sub="Across all hazards" />
        <KpiCard label="CRESTA Zone Coverage" value="98%" sub="Properties geocoded" color="text-emerald-600" />
      </div>

      <Section title="Hazard Risk by Horizon (Score 0-100)" icon={Thermometer}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={HAZARD_DATA} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10 }} />
            <YAxis dataKey="hazard" type="category" tick={{ fontSize: 10 }} width={120} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: "11px" }} />
            <Bar dataKey="risk2030" name="2030" fill="#6b7280" radius={[0, 2, 2, 0]} />
            <Bar dataKey="risk2050" name="2050" fill="#f59e0b" radius={[0, 2, 2, 0]} />
            <Bar dataKey="risk2100" name="2100" fill="#ef4444" radius={[0, 2, 2, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Single Property Hazard Assessment" icon={MapPin}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-8">
          <div>
            <Row label="Latitude"><Inp value={lat} onChange={setLat} type="number" /></Row>
            <Row label="Longitude"><Inp value={lng} onChange={setLng} type="number" /></Row>
          </div>
          <div>
            <Row label="Climate Scenario">
              <Sel value={scenario} onChange={setScenario} options={[
                { v: "rcp26", l: "RCP 2.6 (1.5°C)" }, { v: "rcp45", l: "RCP 4.5 (2°C)" },
                { v: "rcp85", l: "RCP 8.5 (4°C)" },
              ]} />
            </Row>
          </div>
        </div>
        <Btn onClick={run} loading={loading}><Play className="h-3 w-3" /> Run Assessment</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-2">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ["Flood Risk", result.flood_risk_score ?? "—"],
                ["Heat Risk", result.heat_risk_score ?? "—"],
                ["Wildfire Risk", result.wildfire_risk_score ?? "—"],
                ["Composite", result.composite_risk_score ?? "—"],
              ].map(([l, v]) => (
                <div key={l}><span className="text-gray-500">{l}:</span> <span className="font-medium">{v}</span></div>
              ))}
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 4 — CRREM PATHWAY
══════════════════════════════════════════════════════════════════════════ */
function CRREMPanel() {
  const rng = sr(55);
  const YEARS = [2024, 2025, 2026, 2028, 2030, 2032, 2035, 2040, 2045, 2050];

  const PATHWAY_DATA = YEARS.map((y, i) => {
    const actual = Math.max(10, 90 - i * 7 + rng() * 8 - 4);
    const pathway = 90 - i * 7;
    return { year: String(y), actual: +actual.toFixed(1), pathway: +pathway.toFixed(1) };
  });

  const EPC_COLORS = { A: "#10b981", B: "#22c55e", C: "#84cc16", D: "#eab308", E: "#f59e0b", F: "#f97316", G: "#ef4444" };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Current Carbon Intensity" value="68 kgCO₂/m²" sub="Portfolio average" color="text-amber-600" />
        <KpiCard label="CRREM 2030 Target" value="35 kgCO₂/m²" sub="Residential DE pathway" />
        <KpiCard label="Stranding Gap" value="-33 kgCO₂/m²" sub="Needs reduction by 2030" color="text-red-500" />
        <KpiCard label="Net-Zero Year" value="2048" sub="At current trajectory" />
      </div>

      <Section title="Carbon Intensity vs CRREM Pathway (kgCO₂/m²/yr)" icon={TrendingDown}>
        <ResponsiveContainer width="100%" height={260}>
          <AreaChart data={PATHWAY_DATA} margin={{ left: 10, right: 20, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" />
            <XAxis dataKey="year" tick={{ fontSize: 10 }} />
            <YAxis tick={{ fontSize: 10 }} unit=" kg" />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: "11px" }} />
            <Area type="monotone" dataKey="pathway" name="CRREM Target" stroke="#10b981" fill="#10b98120" strokeWidth={2} strokeDasharray="5 5" />
            <Area type="monotone" dataKey="actual" name="Portfolio Actual" stroke="#ef4444" fill="#ef444420" strokeWidth={2.5} />
          </AreaChart>
        </ResponsiveContainer>
      </Section>

      <Section title="EPC Upgrade Roadmap to Net-Zero" icon={Layers} defaultOpen={false}>
        <table className="w-full text-xs">
          <thead>
            <tr className="border-b border-gray-200">
              {["Current EPC", "Target EPC", "Year", "Action Required", "Cost Est.", "NPV"].map(h => (
                <th key={h} className="text-left py-1.5 px-2 text-gray-500 font-medium">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {[
              ["G", "E", "2025", "Insulation + Boiler", "€8,000", "+€3,200"],
              ["F", "D", "2026", "Heat Pump + Windows", "€12,000", "+€5,800"],
              ["E", "C", "2028", "Solar PV + Insulation", "€15,000", "+€9,100"],
              ["D", "B", "2030", "Full Fabric + MVHR", "€22,000", "+€14,400"],
              ["C", "A", "2035", "EV Ready + Battery", "€9,000", "+€8,700"],
            ].map(([cur, tgt, yr, act, cost, npv]) => (
              <tr key={yr + cur} className="border-b border-gray-100 hover:bg-gray-50">
                <td className="py-1.5 px-2"><EPCBadge grade={cur} /></td>
                <td className="py-1.5 px-2"><EPCBadge grade={tgt} /></td>
                <td className="py-1.5 px-2 font-mono text-gray-600">{yr}</td>
                <td className="py-1.5 px-2 text-gray-600">{act}</td>
                <td className="py-1.5 px-2 font-mono text-gray-600">{cost}</td>
                <td className="py-1.5 px-2 font-mono text-emerald-600">{npv}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Section>
    </div>
  );
}

/* ══════════════════════════════════════════════════════════════════════════
   TAB 5 — RETROFIT PLANNER
══════════════════════════════════════════════════════════════════════════ */
function RetrofitPanel() {
  const [assetId, setAssetId] = useState("prop-003");
  const [budget, setBudget] = useState("30000");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const MEASURES = [
    { measure: "External Wall Insulation", cost: 9800, co2_save: 3.2, payback: 7.2, npv: 12400 },
    { measure: "Air Source Heat Pump", cost: 11200, co2_save: 4.8, payback: 8.9, npv: 15800 },
    { measure: "Roof Insulation", cost: 3200, co2_save: 1.1, payback: 4.1, npv: 6200 },
    { measure: "Triple Glazing", cost: 7400, co2_save: 1.4, payback: 9.8, npv: 5900 },
    { measure: "Solar PV (4kWp)", cost: 6800, co2_save: 2.2, payback: 6.4, npv: 11400 },
    { measure: "Battery Storage", cost: 5200, co2_save: 0.8, payback: 11.2, npv: 3100 },
  ];

  async function run() {
    setLoading(true); setError(null); setResult(null);
    try {
      const res = await axios.post(`${API_BASE}/api/v1/retrofit-planner/optimise`, {
        asset_id: assetId, budget_eur: parseFloat(budget),
      });
      setResult(res.data);
    } catch (e) {
      setError(e.response?.data?.detail || e.message || "Failed");
    } finally { setLoading(false); }
  }

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Retrofit Budget" value="€30K" sub="User defined" />
        <KpiCard label="Total CO₂ Saving" value="13.5 t/yr" sub="All measures combined" color="text-emerald-600" />
        <KpiCard label="Simple Payback" value="7.4 yrs" sub="Budget-optimised" />
        <KpiCard label="Total NPV" value="€54.8K" sub="20-year horizon" color="text-blue-600" />
      </div>

      <Section title="Retrofit Measures — Cost vs CO₂ Saving" icon={Wrench}>
        <ResponsiveContainer width="100%" height={240}>
          <BarChart data={MEASURES} layout="vertical" margin={{ left: 10, right: 30, top: 4, bottom: 4 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.04)" horizontal={false} />
            <XAxis type="number" tick={{ fontSize: 10 }} />
            <YAxis dataKey="measure" type="category" tick={{ fontSize: 10 }} width={160} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend iconSize={10} wrapperStyle={{ fontSize: "11px" }} />
            <Bar dataKey="cost" name="Cost (€)" fill="#6b7280" radius={[0, 2, 2, 0]} />
            <Bar dataKey="npv" name="NPV (€)" fill="#10b981" radius={[0, 2, 2, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Section>

      <Section title="Optimise Retrofit Plan" icon={Play}>
        <Row label="Asset ID"><Inp value={assetId} onChange={setAssetId} /></Row>
        <Row label="Budget (€)"><Inp value={budget} onChange={setBudget} type="number" /></Row>
        <Btn onClick={run} loading={loading}><Play className="h-3 w-3" /> Optimise</Btn>
        {error && <p className="mt-2 text-xs text-red-500">{error}</p>}
        {result && (
          <div className="mt-4 bg-white border border-gray-200 rounded-lg p-4 text-xs space-y-2">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[
                ["Selected Measures", result.selected_count ?? "—"],
                ["Total Cost", result.total_cost_eur ? `€${result.total_cost_eur.toLocaleString()}` : "—"],
                ["CO₂ Saving", result.co2_saving_tpa ? `${result.co2_saving_tpa} t/yr` : "—"],
                ["NPV", result.npv_eur ? `€${result.npv_eur.toLocaleString()}` : "—"],
              ].map(([l, v]) => (
                <div key={l}><span className="text-gray-500">{l}:</span> <span className="font-medium">{v}</span></div>
              ))}
            </div>
          </div>
        )}
      </Section>
    </div>
  );
}

const TABS = [
  { id: "residential", label: "Residential Assessment", icon: Home },
  { id: "rics", label: "RICS ESG", icon: Star },
  { id: "spatial", label: "Spatial Hazard", icon: MapPin },
  { id: "crrem", label: "CRREM Pathway", icon: TrendingDown },
  { id: "retrofit", label: "Retrofit Planner", icon: Wrench },
];

export default function ResidentialREPage() {
  const [tab, setTab] = useState("residential");

  return (
    <div className="p-6 max-w-[1280px] mx-auto space-y-5">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Residential Real Estate — Climate & ESG</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            EPC stranding · RICS ESG scoring · Spatial hazard overlay · CRREM decarbonisation pathway · Retrofit NPV optimiser
          </p>
        </div>
        <div className="flex gap-1.5">
          {["RICS", "CRREM", "EU MEPS", "GRESB"].map(b => (
            <span key={b} className="px-2 py-0.5 rounded border border-gray-300 text-[10px] font-medium text-gray-500">{b}</span>
          ))}
        </div>
      </div>

      <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
        {TABS.map(t => {
          const Icon = t.icon;
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                tab === t.id ? "bg-white text-gray-900 shadow-sm border border-gray-200" : "text-gray-500 hover:text-gray-700"
              }`}>
              <Icon className="h-3 w-3" />{t.label}
            </button>
          );
        })}
      </div>

      {tab === "residential" && <ResidentialPanel />}
      {tab === "rics" && <RICSPanel />}
      {tab === "spatial" && <SpatialHazardPanel />}
      {tab === "crrem" && <CRREMPanel />}
      {tab === "retrofit" && <RetrofitPanel />}

      <div className="text-[10px] text-gray-400 border-t border-gray-100 pt-4 space-y-0.5">
        <p><span className="font-semibold text-gray-500">CRREM:</span> Carbon Risk Real Estate Monitor v2.0 — sector pathways per country (residential/office/retail) aligned to Paris 1.5°C</p>
        <p><span className="font-semibold text-gray-500">EU MEPS:</span> Minimum Energy Performance Standards — country-level EPC thresholds per EU EPBD (Directive 2018/844)</p>
        <p><span className="font-semibold text-gray-500">RICS:</span> RICS Global Real Estate Sustainability Benchmark — 7 dimensions, green premium estimation per certification tier</p>
      </div>
    </div>
  );
}
