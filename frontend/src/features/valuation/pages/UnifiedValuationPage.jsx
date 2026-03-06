/**
 * Unified Asset Valuation Page
 * Covers all 7 asset classes with full methodology sets, ESG overlay,
 * sensitivity analysis, and validation summary.
 *
 * Standards: RICS Red Book PS1/VPS4, IVS 2024, USPAP, TEGoVA EVS
 */
import React, { useState, useCallback, useMemo } from "react";
import axios from "axios";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, ReferenceLine, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, WaterfallChart
} from "recharts";
import {
  Building2, Zap, Tractor, Layers, Home, Trees, MapPin,
  ChevronDown, ChevronUp, Info, AlertTriangle, CheckCircle,
  TrendingUp, TrendingDown, Calculator, RefreshCw, Download,
  Shield, Leaf, Flame, Droplets, Activity, Scale, Settings2
} from "lucide-react";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8001";

// ─── Asset class metadata ──────────────────────────────────────────────────
const ASSET_CLASSES = [
  {
    id: "infrastructure",
    label: "Infrastructure",
    icon: Layers,
    color: "#6366f1",
    bg: "bg-cyan-400/10",
    border: "border-cyan-400/20",
    text: "text-cyan-300",
    desc: "Regulated utilities, toll roads, rail, ports, airports, social infra",
    subtypes: [
      { v: "regulated_utility", l: "Regulated Utility (Water/Gas/Electricity)" },
      { v: "toll_road", l: "Toll Road" },
      { v: "rail", l: "Rail" },
      { v: "port", l: "Port" },
      { v: "airport", l: "Airport" },
      { v: "social_infra", l: "Social Infrastructure (PPP)" },
      { v: "telecom_tower", l: "Telecom Tower" },
      { v: "data_centre", l: "Data Centre" },
      { v: "bridge_tunnel", l: "Bridge / Tunnel" },
    ],
  },
  {
    id: "project",
    label: "Project Finance",
    icon: Building2,
    color: "#8b5cf6",
    bg: "bg-violet-50",
    border: "border-violet-200",
    text: "text-violet-700",
    desc: "PPP availability/demand, concessions, greenfield, brownfield, mining",
    subtypes: [
      { v: "ppp_availability", l: "PPP Availability Payment" },
      { v: "ppp_demand", l: "PPP Demand-Based" },
      { v: "concession", l: "Concession" },
      { v: "greenfield", l: "Greenfield" },
      { v: "brownfield", l: "Brownfield" },
      { v: "mining_project", l: "Mining Project" },
    ],
  },
  {
    id: "energy",
    label: "Energy & Power",
    icon: Zap,
    color: "#f59e0b",
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    text: "text-amber-400",
    desc: "Solar PV, wind, gas, nuclear, hydro, storage, hydrogen, geothermal",
    subtypes: [
      { v: "solar_pv", l: "Solar PV" },
      { v: "wind_onshore", l: "Wind Onshore" },
      { v: "wind_offshore", l: "Wind Offshore" },
      { v: "gas_ccgt", l: "Gas CCGT" },
      { v: "gas_ocgt", l: "Gas OCGT (Peaker)" },
      { v: "coal", l: "Coal" },
      { v: "nuclear", l: "Nuclear" },
      { v: "hydro", l: "Hydro" },
      { v: "biomass", l: "Biomass" },
      { v: "battery_storage", l: "Battery Storage (BESS)" },
      { v: "hydrogen", l: "Green Hydrogen" },
      { v: "geothermal", l: "Geothermal" },
      { v: "solar_csp", l: "Solar CSP" },
      { v: "offshore_wind_float", l: "Floating Offshore Wind" },
    ],
  },
  {
    id: "commercial",
    label: "Commercial RE",
    icon: Building2,
    color: "#0ea5e9",
    bg: "bg-sky-500/10",
    border: "border-sky-200",
    text: "text-sky-400",
    desc: "Office, retail, industrial, hotel, data centre, healthcare, mixed-use",
    subtypes: [
      { v: "office_prime", l: "Office — Prime" },
      { v: "office_secondary", l: "Office — Secondary" },
      { v: "retail_high_street", l: "Retail — High Street" },
      { v: "retail_shopping_centre", l: "Retail — Shopping Centre" },
      { v: "retail_park", l: "Retail — Retail Park" },
      { v: "industrial_logistics", l: "Industrial / Big Box Logistics" },
      { v: "light_industrial", l: "Light Industrial / Business Park" },
      { v: "hotel_full_service", l: "Hotel — Full Service" },
      { v: "hotel_limited", l: "Hotel — Limited Service" },
      { v: "data_centre", l: "Data Centre" },
      { v: "healthcare", l: "Healthcare / Life Sciences" },
      { v: "student_housing", l: "Student Housing (PBSA)" },
      { v: "senior_living", l: "Senior Living / Care Home" },
      { v: "mixed_use", l: "Mixed Use" },
    ],
  },
  {
    id: "residential",
    label: "Residential RE",
    icon: Home,
    color: "#10b981",
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    text: "text-emerald-400",
    desc: "Single-family, multifamily, BTR, affordable, social housing, student",
    subtypes: [
      { v: "single_family", l: "Single Family" },
      { v: "multifamily", l: "Multifamily / Apartment Block" },
      { v: "build_to_rent", l: "Build-to-Rent (BTR)" },
      { v: "affordable", l: "Affordable Housing" },
      { v: "social_housing", l: "Social Housing" },
      { v: "student", l: "Student Housing" },
    ],
  },
  {
    id: "agricultural",
    label: "Agricultural",
    icon: Tractor,
    color: "#84cc16",
    bg: "bg-lime-50",
    border: "border-lime-200",
    text: "text-lime-700",
    desc: "Arable, pasture, horticulture, plantation, forestry, aquaculture",
    subtypes: [
      { v: "arable", l: "Arable (Cereals/Oilseeds)" },
      { v: "permanent_pasture", l: "Permanent Pasture" },
      { v: "mixed_farming", l: "Mixed Farming" },
      { v: "horticulture", l: "Horticulture" },
      { v: "plantation", l: "Plantation (Fruit/Vines)" },
      { v: "forestry", l: "Forestry" },
      { v: "aquaculture", l: "Aquaculture" },
      { v: "organic_farm", l: "Organic Farm" },
    ],
  },
  {
    id: "land",
    label: "Development Land",
    icon: MapPin,
    color: "#f97316",
    bg: "bg-orange-500/10",
    border: "border-orange-500/20",
    text: "text-orange-400",
    desc: "Residential/commercial/industrial dev land, brownfield, carbon land",
    subtypes: [
      { v: "residential_dev", l: "Residential Development" },
      { v: "commercial_dev", l: "Commercial Development" },
      { v: "industrial_dev", l: "Industrial Development" },
      { v: "mixed_use_dev", l: "Mixed-Use Development" },
      { v: "brownfield", l: "Brownfield (Previously Developed)" },
      { v: "greenfield", l: "Greenfield (Agricultural → Dev)" },
      { v: "rural_bare", l: "Rural Bare Land" },
      { v: "strategic_land", l: "Strategic Land (Pre-Planning)" },
      { v: "carbon_land", l: "Carbon Land (Peatland / Rewilding)" },
    ],
  },
];

// ─── Input field definitions per asset class ──────────────────────────────
const FIELDS = {
  infrastructure: [
    { k: "regulated_asset_base_value", l: "Regulated Asset Base (RAB)", type: "number", unit: "£", hint: "Total RAB value as determined by regulator" },
    { k: "allowed_return_on_rab_pct", l: "Allowed Return on RAB (%)", type: "number", unit: "%" },
    { k: "annual_revenue", l: "Annual Revenue", type: "number", unit: "£" },
    { k: "annual_opex", l: "Annual OPEX", type: "number", unit: "£" },
    { k: "annual_capex", l: "Annual CAPEX", type: "number", unit: "£" },
    { k: "discount_rate_pct", l: "Discount Rate (WACC %)", type: "number", unit: "%" },
    { k: "projection_years", l: "Projection Period (Years)", type: "number" },
    { k: "terminal_growth_pct", l: "Terminal Growth Rate (%)", type: "number", unit: "%" },
    { k: "replacement_cost", l: "Replacement Cost (New)", type: "number", unit: "£" },
    { k: "asset_age_years", l: "Asset Age (Years)", type: "number" },
    { k: "useful_life_years", l: "Useful Economic Life (Years)", type: "number" },
    { k: "regulatory_risk_premium_bps", l: "Regulatory Risk Premium (bps)", type: "number" },
  ],
  project: [
    { k: "total_project_cost", l: "Total Project Cost", type: "number", unit: "£" },
    { k: "equity_contribution_pct", l: "Equity Contribution (%)", type: "number", unit: "%" },
    { k: "annual_revenue", l: "Annual Revenue (Availability / Demand)", type: "number", unit: "£" },
    { k: "annual_opex", l: "Annual OPEX", type: "number", unit: "£" },
    { k: "annual_debt_service", l: "Annual Debt Service", type: "number", unit: "£" },
    { k: "concession_years", l: "Concession Term (Years)", type: "number" },
    { k: "construction_years", l: "Construction Period (Years)", type: "number" },
    { k: "debt_interest_rate_pct", l: "Senior Debt Interest Rate (%)", type: "number", unit: "%" },
    { k: "equity_irr_target_pct", l: "Equity IRR Target (%)", type: "number", unit: "%" },
    { k: "project_irr_target_pct", l: "Project IRR Target (%)", type: "number", unit: "%" },
    { k: "dscr_minimum", l: "Minimum DSCR", type: "number" },
    { k: "senior_debt_pct", l: "Senior Debt (%)", type: "number", unit: "%" },
  ],
  energy: [
    { k: "nameplate_capacity_mw", l: "Nameplate Capacity (MW)", type: "number", unit: "MW" },
    { k: "capacity_factor_pct", l: "Capacity Factor (%)", type: "number", unit: "%" },
    { k: "annual_generation_mwh", l: "Annual Generation (MWh)", type: "number", unit: "MWh", hint: "If 0, computed from MW × CF" },
    { k: "ppa_price_usd_mwh", l: "PPA Price ($/MWh)", type: "number", unit: "$/MWh" },
    { k: "merchant_price_usd_mwh", l: "Merchant Price ($/MWh)", type: "number", unit: "$/MWh" },
    { k: "ppa_coverage_pct", l: "PPA Coverage (%)", type: "number", unit: "%" },
    { k: "ppa_duration_years", l: "PPA Duration (Years)", type: "number" },
    { k: "annual_opex_usd_kw", l: "Annual OPEX ($/kW-year)", type: "number", unit: "$/kW-yr" },
    { k: "annual_degradation_pct", l: "Annual Degradation (%/yr)", type: "number", unit: "%" },
    { k: "construction_cost_usd_kw", l: "Construction Cost ($/kW)", type: "number", unit: "$/kW" },
    { k: "discount_rate_pct", l: "Discount Rate (%)", type: "number", unit: "%" },
    { k: "asset_life_years", l: "Asset Life (Years)", type: "number" },
    { k: "eu_ets_price_eur_tco2", l: "EU ETS Carbon Price (€/tCO₂)", type: "number", unit: "€/t" },
    { k: "annual_co2_tonnes", l: "Annual CO₂ Emissions (t)", type: "number", unit: "t", hint: "Thermal plants only" },
  ],
  commercial: [
    { k: "gross_floor_area_m2", l: "Gross Floor Area (m²)", type: "number", unit: "m²" },
    { k: "net_lettable_area_m2", l: "Net Lettable Area (m²)", type: "number", unit: "m²", hint: "If 0, = 85% of GFA" },
    { k: "passing_rent_psm_pa", l: "Passing Rent (£/m²/yr)", type: "number", unit: "£/m²/yr" },
    { k: "market_rent_psm_pa", l: "Market Rent / ERV (£/m²/yr)", type: "number", unit: "£/m²/yr" },
    { k: "occupancy_rate_pct", l: "Occupancy Rate (%)", type: "number", unit: "%" },
    { k: "management_fee_pct", l: "Management Fee (% of gross rent)", type: "number", unit: "%" },
    { k: "capex_reserve_psm", l: "CapEx Reserve (£/m²/yr)", type: "number", unit: "£/m²/yr" },
    { k: "initial_yield_pct", l: "Initial Yield / Cap Rate (%)", type: "number", unit: "%", hint: "0 = use JLL market default" },
    { k: "discount_rate_pct", l: "Discount Rate (%)", type: "number", unit: "%" },
    { k: "exit_yield_pct", l: "Exit Yield (%)", type: "number", unit: "%", hint: "0 = initial yield + 0.25%" },
    { k: "rent_growth_pct_pa", l: "Rent Growth (% p.a.)", type: "number", unit: "%" },
    { k: "lease_term_years", l: "Lease Term (Years)", type: "number" },
    { k: "void_period_months", l: "Void Period (Months)", type: "number" },
    { k: "lease_incentive_months", l: "Lease Incentive / Rent-Free (Months)", type: "number" },
    { k: "projection_years", l: "Projection Period (Years)", type: "number" },
    { k: "year_built", l: "Year Built", type: "number" },
    { k: "last_refurbishment_year", l: "Last Refurbishment Year", type: "number", hint: "Optional" },
    { k: "land_value_pct", l: "Land Value (% of total)", type: "number", unit: "%" },
  ],
  residential: [
    { k: "units", l: "Number of Units", type: "number" },
    { k: "avg_unit_size_m2", l: "Average Unit Size (m²)", type: "number", unit: "m²" },
    { k: "avg_monthly_rent_per_unit", l: "Average Monthly Rent per Unit", type: "number", unit: "£/unit/mo" },
    { k: "occupancy_rate_pct", l: "Occupancy Rate (%)", type: "number", unit: "%" },
    { k: "annual_opex_per_unit", l: "Annual OPEX per Unit", type: "number", unit: "£/unit/yr" },
    { k: "capex_reserve_pct", l: "CapEx Reserve (% of gross revenue)", type: "number", unit: "%" },
    { k: "gross_yield_market_pct", l: "Market Gross Yield (%)", type: "number", unit: "%", hint: "0 = use market default" },
    { k: "discount_rate_pct", l: "Discount Rate (%)", type: "number", unit: "%" },
    { k: "exit_yield_pct", l: "Exit Yield (%)", type: "number", unit: "%" },
    { k: "rent_growth_pct_pa", l: "Rent Growth (% p.a.)", type: "number", unit: "%" },
    { k: "projection_years", l: "Projection Period (Years)", type: "number" },
  ],
  agricultural: [
    { k: "area_hectares", l: "Area (Hectares)", type: "number", unit: "ha" },
    { k: "soil_quality_score", l: "Soil Quality Score (1–5)", type: "number", hint: "1=poor, 3=average, 5=excellent" },
    { k: "annual_crop_yield_tonnes_ha", l: "Annual Crop Yield (t/ha)", type: "number", unit: "t/ha" },
    { k: "commodity_price_usd_tonne", l: "Commodity Price ($/tonne)", type: "number", unit: "$/t" },
    { k: "annual_opex_usd_ha", l: "Annual OPEX ($/ha)", type: "number", unit: "$/ha" },
    { k: "agricultural_subsidy_usd_ha", l: "Agricultural Subsidy ($/ha)", type: "number", unit: "$/ha" },
    { k: "comparable_land_price_usd_ha", l: "Comparable Land Price ($/ha)", type: "number", unit: "$/ha", hint: "0 = use market default" },
    { k: "discount_rate_pct", l: "Discount Rate (%)", type: "number", unit: "%" },
    { k: "projection_years", l: "Projection Period (Years)", type: "number" },
    { k: "estimated_timber_volume_m3_ha", l: "Timber Volume (m³/ha)", type: "number", unit: "m³/ha", hint: "Forestry only" },
    { k: "standing_timber_value_usd_m3", l: "Standing Timber Value ($/m³)", type: "number", unit: "$/m³", hint: "Forestry only" },
    { k: "carbon_sequestration_tco2e_ha_yr", l: "Carbon Sequestration (tCO₂e/ha/yr)", type: "number", unit: "t/ha/yr" },
    { k: "carbon_credit_price_usd", l: "Carbon Credit Price ($/tCO₂e)", type: "number", unit: "$/t" },
  ],
  land: [
    { k: "site_area_hectares", l: "Site Area (Hectares)", type: "number", unit: "ha" },
    { k: "gross_development_value", l: "GDV — Gross Development Value", type: "number", unit: "£", hint: "Total value of completed development" },
    { k: "total_development_cost", l: "Total Development Cost", type: "number", unit: "£", hint: "Hard + soft construction costs" },
    { k: "developer_profit_pct", l: "Developer's Profit (% of GDV)", type: "number", unit: "%" },
    { k: "finance_cost_pct", l: "Finance Cost (% p.a.)", type: "number", unit: "%" },
    { k: "development_period_years", l: "Development Period (Years)", type: "number" },
    { k: "planning_risk_discount_pct", l: "Planning Risk Discount (%)", type: "number", unit: "%" },
    { k: "remediation_cost", l: "Remediation Cost (Brownfield)", type: "number", unit: "£" },
    { k: "existing_use_value_ha", l: "Existing Use Value (£/ha)", type: "number", unit: "£/ha", hint: "Strategic land EUV" },
    { k: "planning_uplift_multiple", l: "Planning Uplift Multiple", type: "number", hint: "EUV × this = strategic land value" },
    { k: "carbon_sequestration_potential_tco2e_ha", l: "Carbon Sequestration (tCO₂e/ha)", type: "number", unit: "t/ha", hint: "Carbon land only" },
  ],
};

// ─── ESG field definitions (shared) ─────────────────────────────────────
const ESG_FIELDS = [
  { k: "epc_rating", l: "EPC Rating", type: "select", opts: ["A","B","C","D","E","F","G"] },
  { k: "energy_intensity_kwh_m2", l: "Energy Intensity (kWh/m²/yr)", type: "number", unit: "kWh/m²" },
  { k: "carbon_intensity_kgco2_m2", l: "Carbon Intensity (kgCO₂/m²/yr)", type: "number", unit: "kg/m²" },
  { k: "flood_risk", l: "Flood Risk", type: "select", opts: ["none","low","medium","high","extreme"] },
  { k: "physical_risk_score", l: "Physical Risk Score (0–100)", type: "number" },
  { k: "transition_risk_score", l: "Transition Risk Score (0–100)", type: "number" },
  { k: "water_stress_score", l: "Water Stress (WRI Aqueduct 0–5)", type: "number" },
  { k: "biodiversity_sensitivity", l: "Biodiversity Sensitivity", type: "select", opts: ["low","medium","high","critical"] },
  { k: "has_green_certification", l: "Green Certification", type: "boolean" },
  { k: "certification_type", l: "Certification Type", type: "select", opts: ["","BREEAM_Outstanding","BREEAM_Excellent","BREEAM_VeryGood","LEED_Platinum","LEED_Gold","NABERS_5","NABERS_4","GreenStar_6","GreenStar_5","EDGE_Plus","HQE_Exceptional"] },
  { k: "sbti_aligned", l: "SBTi Aligned", type: "boolean" },
  { k: "climate_scenario", l: "Climate Scenario", type: "select", opts: ["nze_1_5c","below_2c","ndc_2_5c","current_policies_3c"] },
];

const SCENARIO_LABELS = {
  nze_1_5c: "Net Zero 1.5°C",
  below_2c: "Below 2°C",
  ndc_2_5c: "NDC ~2.5°C",
  current_policies_3c: "Current Policies 3°C+",
};

const COUNTRY_OPTIONS = [
  { v: "GB", l: "United Kingdom" }, { v: "US", l: "United States" },
  { v: "DE", l: "Germany" }, { v: "FR", l: "France" }, { v: "NL", l: "Netherlands" },
  { v: "AU", l: "Australia" }, { v: "SG", l: "Singapore" }, { v: "JP", l: "Japan" },
  { v: "CA", l: "Canada" }, { v: "AE", l: "UAE" },
];

const METHOD_COLORS = {
  income_dcf: "#6366f1", direct_capitalisation: "#0ea5e9", regulated_asset_base: "#8b5cf6",
  project_finance_dcf: "#a855f7", energy_yield_dcf: "#f59e0b", replacement_cost: "#64748b",
  sales_comparison: "#10b981", residual_land_value: "#f97316", hedonic_pricing: "#ec4899",
  timber_carbon_value: "#84cc16", nav_approach: "#06b6d4",
};

const METHOD_LABELS = {
  income_dcf: "Income DCF", direct_capitalisation: "Direct Cap.", regulated_asset_base: "RAB",
  project_finance_dcf: "PF DCF", energy_yield_dcf: "Energy Yield DCF",
  replacement_cost: "Replacement Cost", sales_comparison: "Sales Comparison",
  residual_land_value: "Residual Land", hedonic_pricing: "Hedonic / Planning",
  timber_carbon_value: "Timber + Carbon", nav_approach: "NAV (EV/EBITDA)",
};

// ─── Utility helpers ──────────────────────────────────────────────────────
const fmt = (v, decimals = 0) =>
  v == null ? "—" : new Intl.NumberFormat("en-GB", {
    minimumFractionDigits: decimals, maximumFractionDigits: decimals
  }).format(v);

const fmtCcy = (v, currency = "GBP") => {
  if (v == null) return "—";
  const symbol = currency === "USD" ? "$" : currency === "EUR" ? "€" : currency === "AUD" ? "A$" : "£";
  if (Math.abs(v) >= 1e9) return `${symbol}${fmt(v / 1e9, 2)}bn`;
  if (Math.abs(v) >= 1e6) return `${symbol}${fmt(v / 1e6, 2)}m`;
  if (Math.abs(v) >= 1e3) return `${symbol}${fmt(v / 1e3, 1)}k`;
  return `${symbol}${fmt(v, 0)}`;
};

const confidenceColor = (c) => ({
  high: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  medium: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  low: "text-red-500 bg-red-500/10 border-red-500/20",
}[c] || "text-white/40 bg-white/[0.02] border-white/[0.06]");

// ─── Input form component ─────────────────────────────────────────────────
function InputField({ field, value, onChange }) {
  const cls = "w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50 bg-[#0d1424]";
  if (field.type === "boolean") {
    return (
      <div className="flex items-center gap-2">
        <input
          type="checkbox"
          id={field.k}
          checked={!!value}
          onChange={(e) => onChange(field.k, e.target.checked)}
          className="w-4 h-4 accent-indigo-600"
        />
        <label htmlFor={field.k} className="text-sm text-white/60">{field.l}</label>
      </div>
    );
  }
  if (field.type === "select") {
    return (
      <div>
        <label className="block text-xs font-medium text-white/40 mb-1">{field.l}</label>
        <select value={value ?? ""} onChange={(e) => onChange(field.k, e.target.value)} className={cls}>
          {field.opts.map(o => <option key={o} value={o}>{o || "(none)"}</option>)}
        </select>
      </div>
    );
  }
  return (
    <div>
      <label className="block text-xs font-medium text-white/40 mb-1">
        {field.l} {field.unit && <span className="text-white/30">({field.unit})</span>}
      </label>
      {field.hint && <p className="text-xs text-white/30 mb-1">{field.hint}</p>}
      <input
        type="number"
        value={value ?? ""}
        onChange={(e) => onChange(field.k, e.target.value === "" ? "" : parseFloat(e.target.value))}
        className={cls}
        step="any"
      />
    </div>
  );
}

// ─── Collapsible section ──────────────────────────────────────────────────
function Section({ title, children, defaultOpen = true }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="border border-white/[0.06] rounded-lg overflow-hidden mb-4">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white/[0.02] hover:bg-white/[0.06] transition-colors"
      >
        <span className="font-medium text-sm text-white/70">{title}</span>
        {open ? <ChevronUp className="h-4 w-4 text-white/30" /> : <ChevronDown className="h-4 w-4 text-white/30" />}
      </button>
      {open && <div className="p-4 bg-[#0d1424]">{children}</div>}
    </div>
  );
}

// ─── Method result card ───────────────────────────────────────────────────
function MethodCard({ method, value, weight, confidence, narrative, basis, currency, isReconciled = false }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className={`border rounded-lg p-4 ${isReconciled ? "border-cyan-400/20 bg-cyan-400/10" : "border-white/[0.06] bg-[#0d1424]"}`}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className={`text-xs font-semibold px-2 py-0.5 rounded border ${confidenceColor(confidence)}`}>
              {confidence?.toUpperCase()}
            </span>
            <span className="text-sm font-medium text-white/70">
              {isReconciled ? "Reconciled Value" : (METHOD_LABELS[method] || method)}
            </span>
            {!isReconciled && (
              <span className="text-xs text-white/30">Weight: {(weight * 100).toFixed(0)}%</span>
            )}
          </div>
          <div className="text-xl font-bold text-white mt-1">{fmtCcy(value, currency)}</div>
        </div>
        {narrative && (
          <button onClick={() => setExpanded(!expanded)} className="text-white/30 hover:text-white/60 mt-1">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </button>
        )}
      </div>
      {expanded && (
        <div className="mt-3 pt-3 border-t border-white/[0.06] text-xs text-white/60 space-y-1">
          {narrative && <p>{narrative}</p>}
          {basis && <p className="text-white/30 italic">Basis: {basis}</p>}
        </div>
      )}
    </div>
  );
}

// ─── ESG Waterfall Chart ──────────────────────────────────────────────────
function ESGWaterfallChart({ breakdown, preEsg, finalValue, currency }) {
  const bars = [
    { name: "Pre-ESG", value: preEsg, fill: "#6366f1", isBase: true },
    { name: "Green Premium", value: (preEsg * breakdown.green_premium_pct) / 100, fill: "#10b981" },
    { name: "Brown Discount", value: -(preEsg * Math.abs(breakdown.brown_discount_pct)) / 100, fill: "#ef4444" },
    { name: "Physical Risk", value: -(preEsg * Math.abs(breakdown.physical_risk_pct)) / 100, fill: "#f97316" },
    { name: "Transition Risk", value: -(preEsg * Math.abs(breakdown.transition_risk_pct)) / 100, fill: "#f59e0b" },
    { name: "Biodiversity", value: (preEsg * breakdown.biodiversity_pct) / 100, fill: "#84cc16" },
    { name: "Final Value", value: finalValue, fill: "#0ea5e9", isFinal: true },
  ].filter(b => b.isBase || b.isFinal || Math.abs(b.value) > 0.01);

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={bars} margin={{ top: 10, right: 10, left: 30, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} />
        <YAxis tick={{ fontSize: 10 }} tickFormatter={v => fmtCcy(v, currency)} width={70} />
        <Tooltip formatter={(v) => fmtCcy(v, currency)} />
        <Bar dataKey="value" radius={[4, 4, 0, 0]}>
          {bars.map((entry, i) => <Cell key={i} fill={entry.fill} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Method comparison chart ───────────────────────────────────────────────
function MethodComparisonChart({ methodResults, finalValue, currency }) {
  const data = [
    ...methodResults.map(m => ({
      name: METHOD_LABELS[m.method] || m.method,
      value: m.indicated_value,
      fill: METHOD_COLORS[m.method] || "#94a3b8",
    })),
    { name: "Reconciled", value: finalValue, fill: "#6366f1" },
  ];

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={data} layout="vertical" margin={{ top: 5, right: 30, left: 90, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
        <XAxis type="number" tickFormatter={v => fmtCcy(v, currency)} tick={{ fontSize: 10 }} />
        <YAxis type="category" dataKey="name" tick={{ fontSize: 11 }} width={90} />
        <Tooltip formatter={(v) => fmtCcy(v, currency)} />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((d, i) => <Cell key={i} fill={d.fill} />)}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

// ─── Main Page ──────────────────────────────────────────────────────────────
export default function UnifiedValuationPage() {
  const [selectedClass, setSelectedClass] = useState("commercial");
  const [inputs, setInputs] = useState({});
  const [esgInputs, setEsgInputs] = useState({
    epc_rating: "D", flood_risk: "none", biodiversity_sensitivity: "low",
    climate_scenario: "below_2c", has_green_certification: false, sbti_aligned: false,
    energy_intensity_kwh_m2: 0, carbon_intensity_kgco2_m2: 0, physical_risk_score: 0,
    transition_risk_score: 0, water_stress_score: 0, certification_type: "",
    assessment_year: 2024, target_year: 2035,
  });
  const [meta, setMeta] = useState({
    assetName: "New Asset",
    countryIso: "GB",
    currency: "GBP",
    valuationStandard: "RICS_Red_Book",
    subtype: "",
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("inputs");
  const [showValidation, setShowValidation] = useState(false);

  const acMeta = ASSET_CLASSES.find(a => a.id === selectedClass);
  const fields = FIELDS[selectedClass] || [];

  const handleClassChange = useCallback((classId) => {
    setSelectedClass(classId);
    setInputs({});
    setResult(null);
    setError(null);
    const ac = ASSET_CLASSES.find(a => a.id === classId);
    setMeta(m => ({ ...m, subtype: ac?.subtypes[0]?.v || "" }));
  }, []);

  const handleInputChange = useCallback((key, value) => {
    setInputs(p => ({ ...p, [key]: value }));
  }, []);

  const handleEsgChange = useCallback((key, value) => {
    setEsgInputs(p => ({ ...p, [key]: value }));
  }, []);

  const handleMetaChange = useCallback((key, value) => {
    setMeta(p => ({ ...p, [key]: value }));
  }, []);

  const runValuation = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const payload = {
        asset_class: selectedClass,
        asset_name: meta.assetName,
        country_iso: meta.countryIso,
        currency: meta.currency,
        valuation_standard: meta.valuationStandard,
        esg: esgInputs,
        inputs: { ...inputs, subtype: meta.subtype },
      };
      const res = await axios.post(`${API_BASE}/api/v1/valuation/calculate`, payload);
      setResult(res.data);
      setActiveTab("results");
    } catch (err) {
      setError(err.response?.data?.detail || err.message || "Valuation failed.");
    } finally {
      setLoading(false);
    }
  };

  const esgAdjPct = result?.esg_adjustment_pct ?? 0;
  const esgColor = esgAdjPct > 0 ? "text-emerald-400" : esgAdjPct < 0 ? "text-red-500" : "text-white/40";

  return (
    <div className="min-h-screen bg-white/[0.02]">
      {/* ── Header ── */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-cyan-400/10 rounded-lg">
              <Scale className="h-6 w-6 text-cyan-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">Unified Asset Valuation Engine</h1>
              <p className="text-sm text-white/40">
                All asset classes · RICS Red Book PS1/VPS4 · IVS 2024 · USPAP · TEGoVA EVS · ESG Climate Overlay
              </p>
            </div>
          </div>
          <div className="flex gap-2 flex-wrap">
            {["RICS PS1/VPS4", "IVS 2024", "ESG Overlay", "CRREM v2"].map(b => (
              <span key={b} className="text-xs px-2 py-1 bg-cyan-400/10 text-cyan-300 border border-cyan-400/20 rounded-full font-medium">{b}</span>
            ))}
          </div>
        </div>
      </div>

      {/* ── Asset Class Selector ── */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6 py-3">
        <p className="text-xs font-medium text-white/30 mb-2 uppercase tracking-wide">Select Asset Class</p>
        <div className="flex gap-2 flex-wrap">
          {ASSET_CLASSES.map(ac => {
            const Icon = ac.icon;
            const active = selectedClass === ac.id;
            return (
              <button
                key={ac.id}
                onClick={() => handleClassChange(ac.id)}
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                  active
                    ? `${ac.bg} ${ac.text} ${ac.border} `
                    : "bg-[#0d1424] text-white/60 border-white/[0.06] hover:bg-white/[0.02]"
                }`}
              >
                <Icon className="h-4 w-4" />
                {ac.label}
              </button>
            );
          })}
        </div>
        {acMeta && (
          <p className="text-xs text-white/30 mt-2">{acMeta.desc}</p>
        )}
      </div>

      {/* ── Tab Nav ── */}
      <div className="bg-[#0d1424] border-b border-white/[0.06] px-6">
        <div className="flex gap-0">
          {[
            { id: "inputs", label: "Input Parameters" },
            { id: "esg", label: "ESG & Climate" },
            { id: "results", label: "Valuation Results", disabled: !result },
            { id: "validation", label: "Validation Summary", disabled: !result },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => !tab.disabled && setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? "border-cyan-400/20 text-cyan-400"
                  : tab.disabled
                  ? "border-transparent text-white/20 cursor-not-allowed"
                  : "border-transparent text-white/40 hover:text-white/70 hover:border-white/[0.08]"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="p-6 max-w-7xl mx-auto">
        {/* ── INPUTS TAB ── */}
        {activeTab === "inputs" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Asset meta + asset inputs */}
            <div className="lg:col-span-2 space-y-4">
              {/* Asset Identification */}
              <Section title="Asset Identification" defaultOpen={true}>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                  <div className="col-span-2 md:col-span-1">
                    <label className="block text-xs font-medium text-white/40 mb-1">Asset Name</label>
                    <input
                      type="text"
                      value={meta.assetName}
                      onChange={e => handleMetaChange("assetName", e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1">Subtype</label>
                    <select
                      value={meta.subtype}
                      onChange={e => handleMetaChange("subtype", e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                    >
                      {acMeta?.subtypes.map(s => (
                        <option key={s.v} value={s.v}>{s.l}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1">Country</label>
                    <select
                      value={meta.countryIso}
                      onChange={e => handleMetaChange("countryIso", e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                    >
                      {COUNTRY_OPTIONS.map(c => <option key={c.v} value={c.v}>{c.l}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1">Currency</label>
                    <select
                      value={meta.currency}
                      onChange={e => handleMetaChange("currency", e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                    >
                      <option value="GBP">GBP £</option>
                      <option value="USD">USD $</option>
                      <option value="EUR">EUR €</option>
                      <option value="AUD">AUD A$</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1">Valuation Standard</label>
                    <select
                      value={meta.valuationStandard}
                      onChange={e => handleMetaChange("valuationStandard", e.target.value)}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50"
                    >
                      <option value="RICS_Red_Book">RICS Red Book (PS1/VPS4)</option>
                      <option value="IVS_2024">IVS 2024 (IVSC)</option>
                      <option value="USPAP">USPAP</option>
                      <option value="TEGoVA_EVS">TEGoVA EVS</option>
                    </select>
                  </div>
                </div>
              </Section>

              {/* Asset-specific inputs */}
              <Section title={`${acMeta?.label || "Asset"} Input Parameters`} defaultOpen={true}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {fields.map(f => (
                    <InputField
                      key={f.k}
                      field={f}
                      value={inputs[f.k]}
                      onChange={handleInputChange}
                    />
                  ))}
                </div>
              </Section>
            </div>

            {/* Right: Run panel + methodology info */}
            <div className="space-y-4">
              {/* Run Valuation */}
              <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-5 ">
                <h3 className="font-semibold text-white/90 mb-3 flex items-center gap-2">
                  <Calculator className="h-4 w-4 text-cyan-400" />
                  Run Valuation
                </h3>
                <p className="text-xs text-white/40 mb-4">
                  The engine will apply all standard methodologies for the selected asset class,
                  reconcile results by weight, and apply the ESG climate overlay.
                </p>

                {/* ESG quick preview */}
                <div className="bg-white/[0.02] rounded-lg p-3 mb-4 text-xs space-y-1">
                  <div className="flex justify-between">
                    <span className="text-white/40">EPC Rating</span>
                    <span className="font-medium text-white/70">{esgInputs.epc_rating}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Flood Risk</span>
                    <span className="font-medium text-white/70 capitalize">{esgInputs.flood_risk}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Climate Scenario</span>
                    <span className="font-medium text-white/70">{SCENARIO_LABELS[esgInputs.climate_scenario]}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-white/40">Green Cert.</span>
                    <span className="font-medium text-white/70">
                      {esgInputs.has_green_certification ? (esgInputs.certification_type || "Yes") : "None"}
                    </span>
                  </div>
                </div>

                <button
                  onClick={runValuation}
                  disabled={loading}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-cyan-400 hover:bg-cyan-300 disabled:bg-cyan-400/40 text-white text-sm font-semibold rounded-lg transition-colors shadow"
                >
                  {loading ? (
                    <><RefreshCw className="h-4 w-4 animate-spin" /> Calculating...</>
                  ) : (
                    <><Calculator className="h-4 w-4" /> Run Valuation</>
                  )}
                </button>

                {error && (
                  <div className="mt-3 p-3 bg-red-500/10 border border-red-500/20 rounded-lg text-xs text-red-400">
                    <AlertTriangle className="h-3 w-3 inline mr-1" />{error}
                  </div>
                )}

                {result && (
                  <div className="mt-3 p-3 bg-emerald-500/10 border border-emerald-500/20 rounded-lg text-center">
                    <div className="text-xs text-emerald-400 font-medium mb-1">Reconciled Value</div>
                    <div className="text-2xl font-bold text-emerald-400">{fmtCcy(result.final_value, result.currency)}</div>
                    <div className="text-xs text-white/40 mt-1">
                      Range: {fmtCcy(result.value_range_low, result.currency)} – {fmtCcy(result.value_range_high, result.currency)}
                    </div>
                    <button onClick={() => setActiveTab("results")} className="mt-2 text-xs text-cyan-400 hover:underline font-medium">
                      View Full Results →
                    </button>
                  </div>
                )}
              </div>

              {/* Methodology Info */}
              <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-5">
                <h3 className="font-semibold text-white/90 mb-3 flex items-center gap-2">
                  <Info className="h-4 w-4 text-blue-500" />
                  Methodologies Applied
                </h3>
                <div className="space-y-2 text-xs text-white/60">
                  {selectedClass === "infrastructure" && (
                    <>
                      <p><span className="font-medium text-white/70">Regulated Asset Base (RAB):</span> WACC-based valuation using regulator-allowed returns, regulatory period, and depreciation of RAB.</p>
                      <p><span className="font-medium text-white/70">Income DCF:</span> 30-year discounted cashflow with EBITDA-style revenues, capex, depreciation, and Gordon growth terminal.</p>
                      <p><span className="font-medium text-white/70">Replacement Cost:</span> Depreciated replacement cost based on asset age and useful life. Verification method.</p>
                    </>
                  )}
                  {selectedClass === "project" && (
                    <>
                      <p><span className="font-medium text-white/70">Project Finance DCF:</span> Equity IRR analysis with DSCR validation, construction ramp-up, concession term, senior/mezzanine debt waterfall.</p>
                      <p><span className="font-medium text-white/70">Replacement Cost:</span> Total project cost less depreciation as verification.</p>
                    </>
                  )}
                  {selectedClass === "energy" && (
                    <>
                      <p><span className="font-medium text-white/70">Energy Yield DCF:</span> PPA blended merchant revenue model with annual generation, degradation factor, OPEX escalation, EU ETS carbon cost for thermal, decommissioning.</p>
                      <p><span className="font-medium text-white/70">Replacement Cost:</span> $/kW construction cost with age depreciation.</p>
                      <p><span className="font-medium text-white/70">NAV (EV/EBITDA):</span> Sector multiple valuation using industry EV/EBITDA multiples by technology type.</p>
                    </>
                  )}
                  {selectedClass === "commercial" && (
                    <>
                      <p><span className="font-medium text-white/70">Direct Capitalisation:</span> NOI ÷ Cap Rate. JLL/CBRE Q1-2024 market yields used if none provided.</p>
                      <p><span className="font-medium text-white/70">Income DCF:</span> 10-year rent cashflow model with lease renewal cycles, void periods, rent-free incentives, exit yield terminal.</p>
                      <p><span className="font-medium text-white/70">Replacement Cost:</span> BCIS/RS Means build cost per m² × age depreciation + land value.</p>
                    </>
                  )}
                  {selectedClass === "residential" && (
                    <>
                      <p><span className="font-medium text-white/70">Direct Capitalisation:</span> Annual gross rent ÷ gross market yield. BTR/PRS market standards.</p>
                      <p><span className="font-medium text-white/70">Income DCF:</span> 10-year net rental income with exit yield capitalisation.</p>
                      <p><span className="font-medium text-white/70">Sales Comparison:</span> Adjusted comparable transactions (if provided).</p>
                    </>
                  )}
                  {selectedClass === "agricultural" && (
                    <>
                      <p><span className="font-medium text-white/70">Income DCF:</span> 20-year crop revenue less OPEX, adjusted for soil quality score (CAAV methodology).</p>
                      <p><span className="font-medium text-white/70">Comparable Sales:</span> CAAV/APHA $/ha evidence by land class and country.</p>
                      <p><span className="font-medium text-white/70">Timber + Carbon:</span> Standing timber valuation + capitalised carbon credit income (Woodland Carbon Code / REDD+).</p>
                    </>
                  )}
                  {selectedClass === "land" && (
                    <>
                      <p><span className="font-medium text-white/70">Residual Land Value:</span> GDV − Build Cost − Developer Profit − Finance Cost − Remediation, PV'd at development start.</p>
                      <p><span className="font-medium text-white/70">Comparable Sales:</span> Land sales £/ha evidence.</p>
                      <p><span className="font-medium text-white/70">Planning Uplift:</span> Existing Use Value × planning uplift multiple (RICS Hope Value / NPPF).</p>
                      <p><span className="font-medium text-white/70">Carbon Land:</span> Capitalised annual carbon sequestration revenue (peatland / rewilding).</p>
                    </>
                  )}
                  <div className="mt-3 pt-2 border-t border-white/[0.04] text-white/30">
                    ESG Climate Overlay applied to all methods per RICS VPS4 / IVS ESG guidance.
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── ESG TAB ── */}
        {activeTab === "esg" && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2">
              <Section title="ESG & Climate Risk Inputs" defaultOpen={true}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {ESG_FIELDS.map(f => (
                    <InputField key={f.k} field={f} value={esgInputs[f.k]} onChange={handleEsgChange} />
                  ))}
                </div>
              </Section>
              <Section title="Assessment Timeline" defaultOpen={true}>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1">Assessment Year</label>
                    <input type="number" value={esgInputs.assessment_year} onChange={e => handleEsgChange("assessment_year", parseInt(e.target.value))}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50" />
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-white/40 mb-1">Target Year (ESG horizon)</label>
                    <input type="number" value={esgInputs.target_year} onChange={e => handleEsgChange("target_year", parseInt(e.target.value))}
                      className="w-full px-3 py-1.5 text-sm border border-white/[0.06] rounded-md focus:outline-none focus:ring-2 focus:ring-cyan-400/50" />
                  </div>
                </div>
              </Section>
            </div>
            <div>
              <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-5">
                <h3 className="font-semibold text-white/90 mb-3 flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-emerald-500" />
                  ESG Overlay Logic
                </h3>
                <div className="space-y-2 text-xs text-white/60">
                  <p><span className="font-medium text-emerald-400">Green Premiums:</span> BREEAM Outstanding +10%, Excellent +7%, VeryGood +4%; LEED Platinum +10%, Gold +7%; NABERS 5+ +8%; GreenStar 6 +9%.</p>
                  <p><span className="font-medium text-red-400">EPC Brown Discounts:</span> A −5%, B −2%, C 0%, D +2%, E +5%, F +8%, G +10% above baseline.</p>
                  <p><span className="font-medium text-orange-400">Flood Risk Discounts:</span> Low −2%, Medium −5%, High −12%, Extreme −20%.</p>
                  <p><span className="font-medium text-amber-400">Physical Risk:</span> Score-based discount up to −15% for extreme risk under NGFS 3°C+ scenario.</p>
                  <p><span className="font-medium text-blue-300">Transition Risk:</span> Penalty for high transition risk per CRREM stranding analysis.</p>
                  <p><span className="font-medium text-lime-600">Biodiversity:</span> Up to +3% premium for low biodiversity sensitivity (green certification); discount for critical.</p>
                  <p className="mt-2 text-white/30 italic">Sources: MSCI Real Estate Green Premium Report 2023; RICS VPS4 (2024); CRREM v2.0</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── RESULTS TAB ── */}
        {activeTab === "results" && result && (
          <div className="space-y-6">
            {/* Hero card */}
            <div className="bg-gradient-to-br from-indigo-600 to-indigo-800 rounded-2xl p-6 text-white shadow-lg">
              <div className="flex items-start justify-between flex-wrap gap-4">
                <div>
                  <p className="text-cyan-200/60 text-sm mb-1">{result.asset_name} · {result.asset_class?.toUpperCase()} · {result.currency}</p>
                  <div className="text-4xl font-bold">{fmtCcy(result.final_value, result.currency)}</div>
                  <p className="text-cyan-200/60 text-sm mt-1">
                    Value Range: {fmtCcy(result.value_range_low, result.currency)} – {fmtCcy(result.value_range_high, result.currency)}
                  </p>
                  {result.material_uncertainty && (
                    <div className="mt-2 flex items-center gap-1 text-amber-300 text-xs">
                      <AlertTriangle className="h-3 w-3" /> Material Uncertainty applies — RICS VPS4 §10
                    </div>
                  )}
                </div>
                <div className="space-y-2 text-sm min-w-40">
                  <div className="flex justify-between gap-4">
                    <span className="text-cyan-200/60">Pre-ESG Value</span>
                    <span className="font-semibold">{fmtCcy(result.reconciled_value_pre_esg, result.currency)}</span>
                  </div>
                  <div className="flex justify-between gap-4">
                    <span className="text-cyan-200/60">ESG Adjustment</span>
                    <span className={`font-semibold ${esgAdjPct >= 0 ? "text-emerald-300" : "text-red-300"}`}>
                      {esgAdjPct >= 0 ? "+" : ""}{fmt(esgAdjPct, 2)}%
                    </span>
                  </div>
                  {result.value_per_m2 != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">Per m²</span>
                      <span className="font-semibold">{fmtCcy(result.value_per_m2, result.currency)}</span>
                    </div>
                  )}
                  {result.value_per_unit != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">Per Unit</span>
                      <span className="font-semibold">{fmtCcy(result.value_per_unit, result.currency)}</span>
                    </div>
                  )}
                  {result.value_per_ha != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">Per Hectare</span>
                      <span className="font-semibold">{fmtCcy(result.value_per_ha, result.currency)}</span>
                    </div>
                  )}
                  {result.value_per_kw != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">Per kW</span>
                      <span className="font-semibold">{fmtCcy(result.value_per_kw, result.currency)}</span>
                    </div>
                  )}
                  {result.yield_pct != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">Implied Yield</span>
                      <span className="font-semibold">{fmt(result.yield_pct, 2)}%</span>
                    </div>
                  )}
                  {result.irr_pct != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">Project IRR</span>
                      <span className="font-semibold">{fmt(result.irr_pct, 2)}%</span>
                    </div>
                  )}
                  {result.dscr != null && (
                    <div className="flex justify-between gap-4">
                      <span className="text-cyan-200/60">DSCR</span>
                      <span className="font-semibold">{fmt(result.dscr, 2)}×</span>
                    </div>
                  )}
                </div>
              </div>
              <div className="mt-4 flex items-center gap-2">
                <Shield className="h-4 w-4 text-emerald-300" />
                <span className="text-xs text-cyan-200/60">
                  {result.validation_summary?.compliance?.standard} · RICS PS1 Compliant ·
                  ESG Addressed per VPS4 · Valuation Date: {result.valuation_date}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Method results */}
              <div>
                <h3 className="font-semibold text-white/90 mb-3 text-sm flex items-center gap-2">
                  <BarChart2 className="h-4 w-4 text-cyan-400" />
                  Method Comparison
                </h3>
                <MethodComparisonChart
                  methodResults={result.method_results}
                  finalValue={result.final_value}
                  currency={result.currency}
                />
                <div className="mt-4 space-y-3">
                  {result.method_results.map(m => (
                    <MethodCard
                      key={m.method}
                      method={m.method}
                      value={m.indicated_value}
                      weight={m.weight}
                      confidence={m.confidence}
                      narrative={m.narrative}
                      basis={m.methodology_basis}
                      currency={result.currency}
                    />
                  ))}
                  <MethodCard
                    isReconciled={true}
                    method="reconciled"
                    value={result.final_value}
                    confidence="high"
                    currency={result.currency}
                    narrative={`Weighted reconciliation of ${result.method_results.length} methods, then ESG overlay applied (${esgAdjPct >= 0 ? "+" : ""}${fmt(esgAdjPct, 2)}%).`}
                  />
                </div>
              </div>

              {/* ESG breakdown */}
              <div>
                <h3 className="font-semibold text-white/90 mb-3 text-sm flex items-center gap-2">
                  <Leaf className="h-4 w-4 text-emerald-500" />
                  ESG Adjustment Waterfall
                </h3>
                <ESGWaterfallChart
                  breakdown={result.esg_breakdown}
                  preEsg={result.reconciled_value_pre_esg}
                  finalValue={result.final_value}
                  currency={result.currency}
                />

                {/* ESG breakdown table */}
                <div className="mt-4 border border-white/[0.06] rounded-lg overflow-hidden">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-white/[0.02] border-b border-white/[0.06]">
                        <th className="text-left px-4 py-2 text-xs font-medium text-white/40">ESG Factor</th>
                        <th className="text-right px-4 py-2 text-xs font-medium text-white/40">Impact (%)</th>
                        <th className="text-right px-4 py-2 text-xs font-medium text-white/40">Value Impact</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {[
                        { l: "Green Premium", v: result.esg_breakdown.green_premium_pct, pos: true, icon: Leaf, color: "text-emerald-400" },
                        { l: "EPC/Brown Discount", v: result.esg_breakdown.brown_discount_pct, pos: false, icon: Flame, color: "text-red-500" },
                        { l: "Physical Climate Risk", v: result.esg_breakdown.physical_risk_pct, pos: false, icon: Droplets, color: "text-orange-500" },
                        { l: "Transition Risk", v: result.esg_breakdown.transition_risk_pct, pos: false, icon: TrendingDown, color: "text-amber-400" },
                        { l: "Biodiversity", v: result.esg_breakdown.biodiversity_pct, pos: true, icon: Trees, color: "text-lime-600" },
                      ].map(row => {
                        const Icon = row.icon;
                        const impact = (result.reconciled_value_pre_esg * row.v) / 100;
                        return (
                          <tr key={row.l} className="hover:bg-white/[0.02]">
                            <td className="px-4 py-2 flex items-center gap-2 text-white/70">
                              <Icon className={`h-3.5 w-3.5 ${row.color}`} />{row.l}
                            </td>
                            <td className={`px-4 py-2 text-right font-medium ${row.v > 0 ? "text-emerald-400" : row.v < 0 ? "text-red-500" : "text-white/30"}`}>
                              {row.v >= 0 ? "+" : ""}{fmt(row.v, 2)}%
                            </td>
                            <td className={`px-4 py-2 text-right font-medium ${impact > 0 ? "text-emerald-400" : impact < 0 ? "text-red-500" : "text-white/30"}`}>
                              {fmtCcy(Math.abs(impact), result.currency)}
                            </td>
                          </tr>
                        );
                      })}
                      <tr className="bg-white/[0.02] font-semibold">
                        <td className="px-4 py-2 text-white/90">Net ESG Adjustment</td>
                        <td className={`px-4 py-2 text-right ${esgAdjPct >= 0 ? "text-emerald-400" : "text-red-500"}`}>
                          {esgAdjPct >= 0 ? "+" : ""}{fmt(esgAdjPct, 2)}%
                        </td>
                        <td className={`px-4 py-2 text-right ${(result.final_value - result.reconciled_value_pre_esg) >= 0 ? "text-emerald-400" : "text-red-500"}`}>
                          {fmtCcy(Math.abs(result.final_value - result.reconciled_value_pre_esg), result.currency)}
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* ESG narrative */}
                {result.esg_breakdown.narrative && (
                  <div className="mt-3 p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-300">
                    <Info className="h-3 w-3 inline mr-1" />{result.esg_breakdown.narrative}
                  </div>
                )}

                {/* Key metrics */}
                {result.method_results.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-white/70 mb-2">Key Metrics by Method</h4>
                    <div className="space-y-2">
                      {result.method_results.map(m => (
                        <div key={m.method} className="bg-[#0d1424] border border-white/[0.06] rounded-lg p-3">
                          <div className="text-xs font-medium text-white/60 mb-2">{METHOD_LABELS[m.method] || m.method}</div>
                          <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                            {Object.entries(m.key_metrics || {}).map(([k, v]) => (
                              <div key={k} className="flex justify-between gap-2">
                                <span className="text-white/30 truncate">{k.replace(/_/g, " ")}</span>
                                <span className="text-white/70 font-medium whitespace-nowrap">
                                  {typeof v === "number" ? (v > 1000 ? fmtCcy(v, result.currency) : fmt(v, 2)) : String(v)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* ── VALIDATION SUMMARY TAB ── */}
        {activeTab === "validation" && result && (
          <div className="space-y-4 max-w-4xl">
            <div className="bg-[#0d1424] border border-white/[0.06] rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <CheckCircle className="h-5 w-5 text-emerald-500" />
                <h2 className="text-lg font-semibold text-white/90">Valuation Validation Summary</h2>
              </div>
              <p className="text-sm text-white/40 mb-5">
                This validation summary documents the methodology, inputs, outputs, and compliance status in accordance with RICS PS2 (Inspections), RICS VPS4 (ESG), and IVS 103 (Reporting).
              </p>

              {/* Compliance badges */}
              <div className="flex gap-2 flex-wrap mb-6">
                {[
                  { l: "RICS PS1 Compliant", ok: result.validation_summary?.compliance?.rics_ps1_compliant },
                  { l: "VPS4 ESG Addressed", ok: result.validation_summary?.compliance?.rics_vps4_esg_addressed },
                  { l: "IVS ESG Addressed", ok: result.validation_summary?.compliance?.ivs_esg_addressed },
                  { l: "Material Uncertainty", ok: result.validation_summary?.material_uncertainty, warn: true },
                ].map(b => (
                  <span key={b.l} className={`flex items-center gap-1 px-3 py-1 rounded-full text-xs font-medium border ${
                    b.warn
                      ? (b.ok ? "bg-amber-500/10 text-amber-400 border-amber-500/20" : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20")
                      : (b.ok ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/20" : "bg-red-500/10 text-red-400 border-red-500/20")
                  }`}>
                    {b.warn ? (b.ok ? <AlertTriangle className="h-3 w-3" /> : <CheckCircle className="h-3 w-3" />) :
                      (b.ok ? <CheckCircle className="h-3 w-3" /> : <AlertTriangle className="h-3 w-3" />)}
                    {b.l}
                  </span>
                ))}
              </div>

              {/* Summary table */}
              <div className="grid grid-cols-2 gap-x-8 gap-y-3 text-sm mb-6">
                {[
                  ["Valuation Standard", result.validation_summary?.compliance?.standard],
                  ["Valuation Date", result.validation_summary?.valuation_date],
                  ["Asset Class", result.asset_class],
                  ["Asset Name", result.asset_name],
                  ["Currency", result.currency],
                  ["Methods Applied", result.validation_summary?.methods_applied?.join(", ")],
                  ["Pre-ESG Reconciled", fmtCcy(result.reconciled_value_pre_esg, result.currency)],
                  ["ESG Adjustment", `${esgAdjPct >= 0 ? "+" : ""}${fmt(esgAdjPct, 2)}%`],
                  ["Final Value", fmtCcy(result.final_value, result.currency)],
                  ["Value Range", `${fmtCcy(result.value_range_low, result.currency)} – ${fmtCcy(result.value_range_high, result.currency)}`],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between border-b border-white/[0.04] pb-2">
                    <span className="text-white/40">{k}</span>
                    <span className="font-medium text-white/90 text-right max-w-xs truncate">{v ?? "—"}</span>
                  </div>
                ))}
              </div>

              {/* Method details */}
              <h4 className="font-semibold text-white/70 mb-3">Method Detail</h4>
              <div className="space-y-3 mb-6">
                {result.validation_summary?.method_details?.map(m => (
                  <div key={m.method} className="border border-white/[0.06] rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-white/70">{METHOD_LABELS[m.method] || m.method}</span>
                      <div className="flex items-center gap-2">
                        <span className={`text-xs px-2 py-0.5 rounded border font-medium ${confidenceColor(m.confidence)}`}>
                          {m.confidence?.toUpperCase()}
                        </span>
                        <span className="text-xs text-white/30">Weight: {fmt(m.weight * 100, 0)}%</span>
                        <span className="text-sm font-bold text-white/90">{fmtCcy(m.indicated_value, result.currency)}</span>
                      </div>
                    </div>
                    <p className="text-xs text-white/30 italic mb-2">Basis: {m.basis}</p>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
                      {Object.entries(m.key_metrics || {}).map(([k, v]) => (
                        <div key={k} className="bg-white/[0.02] px-2 py-1 rounded">
                          <span className="text-white/30">{k.replace(/_/g, " ")}: </span>
                          <span className="font-medium text-white/70">
                            {typeof v === "number" ? (v > 1000 ? fmtCcy(v, result.currency) : fmt(v, 2)) : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>

              {/* Data sources */}
              <h4 className="font-semibold text-white/70 mb-2">Data Sources & References</h4>
              <ul className="space-y-1">
                {result.validation_summary?.data_sources?.map(ds => (
                  <li key={ds} className="flex items-start gap-2 text-xs text-white/60">
                    <CheckCircle className="h-3 w-3 text-emerald-400 mt-0.5 flex-shrink-0" />
                    {ds}
                  </li>
                ))}
              </ul>

              {/* Material uncertainty clause */}
              {result.validation_summary?.material_uncertainty && (
                <div className="mt-4 p-4 bg-amber-500/10 border border-amber-500/20 rounded-lg">
                  <div className="flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 text-amber-500 flex-shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-medium text-amber-400">Material Uncertainty Clause (RICS VPS4 §10)</p>
                      <p className="text-xs text-amber-400 mt-1">
                        Due to limited comparable market evidence or one or more methods returning low confidence,
                        less certainty should be attached to this valuation than would normally be the case.
                        The valuation reflects current market conditions and the information available at the valuation date.
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* No results yet placeholder */}
        {(activeTab === "results" || activeTab === "validation") && !result && (
          <div className="text-center py-20 text-white/30">
            <Calculator className="h-12 w-12 mx-auto mb-4 opacity-30" />
            <p className="text-lg font-medium">No valuation run yet</p>
            <p className="text-sm mt-1">Complete the input parameters and click "Run Valuation"</p>
            <button onClick={() => setActiveTab("inputs")} className="mt-4 px-4 py-2 bg-cyan-400 text-white text-sm rounded-lg hover:bg-cyan-300 transition-colors">
              Go to Inputs
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
