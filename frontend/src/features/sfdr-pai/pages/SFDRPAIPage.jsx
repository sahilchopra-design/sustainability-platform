/**
 * SFDRPAIPage.jsx
 * Route: /sfdr-pai
 *
 * Comprehensive SFDR Principal Adverse Impact (PAI) module.
 * Implements the full RTS Annex I Table 1 (18 mandatory indicators),
 * Tables 2-3 (38 additional), DNSH assessment, period comparison,
 * entity classification (Article 6/8/9), and disclosure readiness.
 *
 * Tabs:
 *   1. PAI Dashboard        - Overview of all 18 mandatory PAIs with KPI cards, RAG heatmap, benchmark bars
 *   2. PAI Calculations     - Per-indicator deep dive, holdings breakdown, DQS distribution
 *   3. DNSH Assessment      - Do No Significant Harm matrix across 6 EU Taxonomy objectives
 *   4. Period Comparison     - YoY trend analysis, side-by-side bars, summary statistics
 *   5. Entity Classification - Article 6/8/9 classification, RTS statement preview, cross-framework mapping
 */
import React, { useState, useMemo } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell, RadarChart, Radar,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, LineChart, Line,
} from 'recharts';
import {
  BarChart3, Activity, ShieldCheck, TrendingUp, FileText,
  ChevronDown, ChevronRight, AlertTriangle, CheckCircle2,
  XCircle, Info, ArrowUpRight, ArrowDownRight, Minus,
  Building2, Leaf, Droplets, Recycle, Wind, Bug,
} from 'lucide-react';
import DemoBanner from '../../../components/shared/DemoBanner';

/* ============================================================================
   DESIGN TOKENS
   ============================================================================ */
const CHART_COLORS = ['#111111', '#6b7280', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#3b82f6', '#ec4899'];
const DQS_COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#f97316', '#ef4444'];
const DNSH_PASS = '#10b981';
const DNSH_FAIL = '#ef4444';
const DNSH_NA = '#d1d5db';

const TOOLTIP_STYLE = { backgroundColor: '#ffffff', border: '1px solid rgba(0,0,0,0.08)', color: '#111' };

/* ============================================================================
   DETERMINISTIC SEED RANDOM
   ============================================================================ */
function seededRandom(seed) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

/* ============================================================================
   SHARED UI COMPONENTS
   ============================================================================ */
function Card({ title, subtitle, badge, children, className = '' }) {
  return (
    <div className={`bg-white rounded-xl border border-gray-200 shadow-sm ${className}`}>
      {(title || subtitle) && (
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            {title && <h2 className="text-sm font-semibold text-gray-900">{title}</h2>}
            {subtitle && <p className="text-xs text-gray-500 mt-0.5">{subtitle}</p>}
          </div>
          {badge && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-gray-100 text-gray-700 border border-gray-200">
              {badge}
            </span>
          )}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  );
}

function StatCard({ label, value, sub, icon: Icon, accent }) {
  const colorMap = {
    green: 'text-emerald-600',
    red: 'text-red-600',
    amber: 'text-amber-600',
    black: 'text-gray-900',
  };
  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
      <div className="flex items-center justify-between mb-2">
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        {Icon && <Icon className="w-4 h-4 text-gray-400" />}
      </div>
      <p className={`text-2xl font-bold ${colorMap[accent] || 'text-gray-900'}`}>
        {typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 1 }) : value}
      </p>
      {sub && <p className="text-[11px] text-gray-500 mt-1">{sub}</p>}
    </div>
  );
}

function TabPill({ tabs, active, onChange }) {
  return (
    <div className="inline-flex bg-[#f0f0f0] rounded-lg p-1 border border-gray-200 flex-wrap gap-0.5">
      {tabs.map(t => (
        <button key={t.id} onClick={() => onChange(t.id)}
          className={`px-4 py-1.5 rounded-md text-xs font-medium transition-all flex items-center gap-1.5 ${
            active === t.id
              ? 'bg-white text-gray-900 shadow-sm border border-gray-300'
              : 'text-gray-500 hover:text-gray-600'
          }`}>
          {t.icon}{t.label}
        </button>
      ))}
    </div>
  );
}

function RAGDot({ status }) {
  const map = {
    green: 'bg-emerald-500',
    amber: 'bg-amber-400',
    red: 'bg-red-500',
    gray: 'bg-gray-300',
  };
  return <span className={`inline-block w-2.5 h-2.5 rounded-full ${map[status] || map.gray}`} />;
}

function TrendArrow({ trend }) {
  if (trend === 'improved') return <ArrowDownRight className="w-3.5 h-3.5 text-emerald-600" />;
  if (trend === 'deteriorated') return <ArrowUpRight className="w-3.5 h-3.5 text-red-600" />;
  return <Minus className="w-3.5 h-3.5 text-gray-500" />;
}

function Badge({ label, variant = 'neutral' }) {
  const styles = {
    green: 'bg-emerald-50 text-emerald-600 border-emerald-200',
    red: 'bg-red-50 text-red-600 border-red-200',
    amber: 'bg-amber-50 text-amber-600 border-amber-200',
    neutral: 'bg-gray-50 text-gray-500 border-gray-200',
    blue: 'bg-blue-50 text-blue-600 border-blue-200',
  };
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border ${styles[variant]}`}>
      {label}
    </span>
  );
}

/* ============================================================================
   MANDATORY PAI INDICATOR DEFINITIONS (Table 1, Annex I)
   ============================================================================ */
const PAI_INDICATORS = [
  { id: 1,  name: 'GHG Emissions', short: 'GHG', unit: 'tCO2e', category: 'climate', formula: 'Sum of Scope 1 + Scope 2 + Scope 3 across all investee companies, weighted by ownership share', requiredData: ['Scope 1 emissions', 'Scope 2 emissions', 'Scope 3 emissions', 'Enterprise value', 'Ownership share'] },
  { id: 2,  name: 'Carbon Footprint', short: 'CF', unit: 'tCO2e/EUR M', category: 'climate', formula: 'Total financed emissions / Current value of all investments (EUR M)', requiredData: ['Total financed emissions', 'Portfolio AUM'] },
  { id: 3,  name: 'GHG Intensity of Investees', short: 'GHG Int.', unit: 'tCO2e/EUR M rev', category: 'climate', formula: 'Sum (investee emissions / investee revenue) x ownership weight', requiredData: ['Scope 1+2 emissions', 'Revenue', 'Ownership share'] },
  { id: 4,  name: 'Fossil Fuel Exposure', short: 'Fossil', unit: '%', category: 'climate', formula: 'Share of investments in companies active in fossil fuel sector (NACE B.05-B.06, D.35.1)', requiredData: ['NACE codes', 'Revenue breakdown', 'Market value'] },
  { id: 5,  name: 'Non-Renewable Energy Share', short: 'Non-RE', unit: '%', category: 'climate', formula: 'Weighted average share of non-renewable energy consumption and production', requiredData: ['Energy consumption by source', 'Energy production by source'] },
  { id: 6,  name: 'Energy Consumption Intensity', short: 'ECI', unit: 'GWh/EUR M', category: 'climate', formula: 'Energy consumption per unit of revenue, per high-impact NACE sector', requiredData: ['Energy consumption (GWh)', 'Revenue', 'NACE sector codes'] },
  { id: 7,  name: 'Activities Affecting Biodiversity', short: 'Bio', unit: 'share %', category: 'environment', formula: 'Share of investments in companies with sites/operations in or near biodiversity-sensitive areas', requiredData: ['Facility locations', 'Proximity to protected areas', 'Impact assessment'] },
  { id: 8,  name: 'Emissions to Water', short: 'Water', unit: 'tonnes', category: 'environment', formula: 'Weighted average of tonnes of emissions to water generated by investee companies', requiredData: ['Pollutant discharge data', 'Water body classifications'] },
  { id: 9,  name: 'Hazardous Waste Ratio', short: 'HazWaste', unit: 'tonnes', category: 'environment', formula: 'Weighted average of tonnes of hazardous waste and radioactive waste generated', requiredData: ['Waste generation data', 'Waste classification', 'Disposal method'] },
  { id: 10, name: 'UNGC/OECD Violations', short: 'UNGC', unit: 'share %', category: 'social', formula: 'Share of investments in companies that have been involved in violations of UNGC principles or OECD Guidelines', requiredData: ['Controversy data', 'UNGC signatory status', 'OECD compliance records'] },
  { id: 11, name: 'Lack of Compliance Processes', short: 'Compliance', unit: 'share %', category: 'social', formula: 'Share of investments in companies without policies to monitor compliance with UNGC/OECD', requiredData: ['Policy documentation', 'Compliance framework status'] },
  { id: 12, name: 'Unadjusted Gender Pay Gap', short: 'PayGap', unit: '%', category: 'social', formula: 'Weighted average of unadjusted gender pay gap of investee companies', requiredData: ['Male/female average compensation data'] },
  { id: 13, name: 'Board Gender Diversity', short: 'BoardDiv', unit: '%', category: 'social', formula: 'Weighted average ratio of female-to-male board members', requiredData: ['Board composition data'] },
  { id: 14, name: 'Controversial Weapons Exposure', short: 'Weapons', unit: 'share %', category: 'social', formula: 'Share of investments in companies involved in controversial weapons (anti-personnel mines, cluster munitions, chemical, biological)', requiredData: ['Revenue screening', 'Weapons involvement flags'] },
  { id: 15, name: 'GHG Intensity of Countries', short: 'SovGHG', unit: 'tCO2e/EUR M GDP', category: 'sovereign', formula: 'GHG intensity of investee countries, weighted by sovereign bond allocation', requiredData: ['Country GHG emissions', 'GDP data', 'Sovereign bond holdings'] },
  { id: 16, name: 'Investee Countries Social Violations', short: 'SovSocial', unit: 'count', category: 'sovereign', formula: 'Number of investee countries subject to social violations (ICCPR, ILO, UDHR)', requiredData: ['Country human rights records', 'Treaty ratification status'] },
  { id: 17, name: 'Exposure to Fossil Fuels (RE)', short: 'RE Fossil', unit: '%', category: 'real_estate', formula: 'Share of real estate investments involved in extraction, storage, transport or manufacture of fossil fuels', requiredData: ['Property use classification', 'Tenant activities'] },
  { id: 18, name: 'Energy-Inefficient Real Estate', short: 'EPC', unit: '%', category: 'real_estate', formula: 'Share of real estate investments in energy-inefficient real estate assets (EPC below C)', requiredData: ['EPC certificates', 'Property energy ratings'] },
];

const PAI_CATEGORIES = [
  { key: 'climate', label: 'Climate & GHG', icon: Wind, ids: [1,2,3,4,5,6] },
  { key: 'environment', label: 'Environment', icon: Leaf, ids: [7,8,9] },
  { key: 'social', label: 'Social & Governance', icon: Building2, ids: [10,11,12,13,14] },
  { key: 'sovereign', label: 'Sovereign', icon: Activity, ids: [15,16] },
  { key: 'real_estate', label: 'Real Estate', icon: Building2, ids: [17,18] },
];

/* ============================================================================
   EU TAXONOMY OBJECTIVES (for DNSH)
   ============================================================================ */
const TAXONOMY_OBJECTIVES = [
  { key: 'CCM', label: 'Climate Change Mitigation', icon: Wind },
  { key: 'CCA', label: 'Climate Change Adaptation', icon: AlertTriangle },
  { key: 'WTR', label: 'Water & Marine Resources', icon: Droplets },
  { key: 'CE',  label: 'Circular Economy', icon: Recycle },
  { key: 'POL', label: 'Pollution Prevention', icon: Bug },
  { key: 'BIO', label: 'Biodiversity & Ecosystems', icon: Leaf },
];

/* ============================================================================
   DEMO DATA GENERATION
   ============================================================================ */
const SECTORS = [
  'Energy', 'Utilities', 'Materials', 'Industrials', 'Consumer Discretionary',
  'Consumer Staples', 'Health Care', 'Financials', 'Information Technology', 'Real Estate',
];

const COMPANY_NAMES = [
  'NordEnergy AG', 'CleanPower Corp', 'EuroSteel GmbH', 'HeliosTech SA', 'MedPharm Holdings',
  'GreenBuild Inc', 'AtlanticShipping Ltd', 'SolarWind PLC', 'AgriChem SpA', 'DataVault Systems',
  'TransitLink SE', 'AquaPure Tech', 'ForestProducts Oy', 'BioGenix Labs', 'TerraMineral Corp',
  'CyberSecure Ltd', 'FoodChain Global', 'RetailStar NV', 'InsureSafe Group', 'PropVest REIT',
  'ChemSynth AG', 'WindTurbine AS', 'OceanLogistics SA', 'PharmaVita Inc', 'SmartGrid Holdings',
  'CarbonCapture Ltd', 'EcoPaper AB', 'FinTrust Bank', 'AutoDrive Corp', 'RenewableFuels GmbH',
];

function generateDemoData() {
  const rng = seededRandom(20260309);

  // Generate 30 holdings
  const holdings = COMPANY_NAMES.map((name, idx) => {
    const sector = SECTORS[idx % SECTORS.length];
    const weight = 1.5 + rng() * 6.0;
    const marketValue = 10 + rng() * 90;
    return {
      id: idx + 1,
      name,
      sector,
      weight: Math.round(weight * 100) / 100,
      marketValue: Math.round(marketValue * 10) / 10,
      isin: `XX${String(1000000 + idx * 17389).slice(0, 7)}${idx}`,
      scope1: Math.round(rng() * 50000),
      scope2: Math.round(rng() * 30000),
      scope3: Math.round(rng() * 120000),
      revenue: Math.round(500 + rng() * 9500),
      energyConsumption: Math.round(50 + rng() * 500),
      renewableShare: Math.round(rng() * 100),
      genderPayGap: Math.round(5 + rng() * 30),
      boardFemaleRatio: Math.round(10 + rng() * 50),
      hasUNGCViolation: rng() < 0.12,
      hasComplianceProcess: rng() > 0.15,
      controversialWeapons: rng() < 0.05,
      fossilFuelActive: rng() < 0.2,
      nearBiodiversityArea: rng() < 0.18,
      waterEmissions: Math.round(rng() * 200),
      hazardousWaste: Math.round(rng() * 1500),
      epcRating: ['A', 'B', 'C', 'D', 'E', 'F', 'G'][Math.floor(rng() * 7)],
      dqs: Math.ceil(rng() * 5),
      dataMethod: ['reported', 'estimated', 'proxy'][Math.floor(rng() * 3)],
    };
  });

  // Compute PAI values
  const totalAUM = holdings.reduce((s, h) => s + h.marketValue, 0);
  const paiValues = {};
  const rng2 = seededRandom(42);

  PAI_INDICATORS.forEach(pai => {
    let value, benchmark, priorValue;
    switch (pai.id) {
      case 1:
        value = Math.round(holdings.reduce((s, h) => s + (h.scope1 + h.scope2 + h.scope3) * (h.weight / 100), 0));
        benchmark = Math.round(value * (0.85 + rng2() * 0.3));
        priorValue = Math.round(value * (1.02 + rng2() * 0.1));
        break;
      case 2:
        value = Math.round(holdings.reduce((s, h) => s + (h.scope1 + h.scope2) * (h.weight / 100), 0) / (totalAUM / 1000000) * 100) / 100;
        benchmark = Math.round(value * (0.9 + rng2() * 0.2) * 100) / 100;
        priorValue = Math.round(value * (1.05 + rng2() * 0.08) * 100) / 100;
        break;
      case 3:
        value = Math.round(holdings.reduce((s, h) => s + ((h.scope1 + h.scope2) / h.revenue) * h.weight, 0) * 100) / 100;
        benchmark = Math.round(value * (0.8 + rng2() * 0.4) * 100) / 100;
        priorValue = Math.round(value * (1.03 + rng2() * 0.06) * 100) / 100;
        break;
      case 4:
        value = Math.round(holdings.filter(h => h.fossilFuelActive).reduce((s, h) => s + h.weight, 0) * 100) / 100;
        benchmark = Math.round((8 + rng2() * 10) * 100) / 100;
        priorValue = Math.round(value * (1.0 + rng2() * 0.15) * 100) / 100;
        break;
      case 5:
        value = Math.round(holdings.reduce((s, h) => s + (100 - h.renewableShare) * (h.weight / 100), 0) * 100) / 100;
        benchmark = Math.round((55 + rng2() * 15) * 100) / 100;
        priorValue = Math.round(value * (1.02 + rng2() * 0.05) * 100) / 100;
        break;
      case 6:
        value = Math.round(holdings.reduce((s, h) => s + h.energyConsumption * (h.weight / 100) / (h.revenue / 1000), 0) * 1000) / 1000;
        benchmark = Math.round(value * (0.85 + rng2() * 0.3) * 1000) / 1000;
        priorValue = Math.round(value * (1.04 + rng2() * 0.06) * 1000) / 1000;
        break;
      case 7:
        value = Math.round(holdings.filter(h => h.nearBiodiversityArea).reduce((s, h) => s + h.weight, 0) * 100) / 100;
        benchmark = Math.round((4 + rng2() * 8) * 100) / 100;
        priorValue = Math.round(value * (0.98 + rng2() * 0.1) * 100) / 100;
        break;
      case 8:
        value = Math.round(holdings.reduce((s, h) => s + h.waterEmissions * (h.weight / 100), 0));
        benchmark = Math.round(value * (0.7 + rng2() * 0.6));
        priorValue = Math.round(value * (1.01 + rng2() * 0.08));
        break;
      case 9:
        value = Math.round(holdings.reduce((s, h) => s + h.hazardousWaste * (h.weight / 100), 0));
        benchmark = Math.round(value * (0.75 + rng2() * 0.5));
        priorValue = Math.round(value * (1.03 + rng2() * 0.07));
        break;
      case 10:
        value = Math.round(holdings.filter(h => h.hasUNGCViolation).reduce((s, h) => s + h.weight, 0) * 100) / 100;
        benchmark = Math.round((3 + rng2() * 6) * 100) / 100;
        priorValue = Math.round(value * (0.95 + rng2() * 0.15) * 100) / 100;
        break;
      case 11:
        value = Math.round(holdings.filter(h => !h.hasComplianceProcess).reduce((s, h) => s + h.weight, 0) * 100) / 100;
        benchmark = Math.round((10 + rng2() * 15) * 100) / 100;
        priorValue = Math.round(value * (1.0 + rng2() * 0.12) * 100) / 100;
        break;
      case 12:
        value = Math.round(holdings.reduce((s, h) => s + h.genderPayGap * (h.weight / 100), 0) * 100) / 100;
        benchmark = Math.round((12 + rng2() * 8) * 100) / 100;
        priorValue = Math.round(value * (1.01 + rng2() * 0.05) * 100) / 100;
        break;
      case 13:
        value = Math.round(holdings.reduce((s, h) => s + h.boardFemaleRatio * (h.weight / 100), 0) * 100) / 100;
        benchmark = Math.round((30 + rng2() * 12) * 100) / 100;
        priorValue = Math.round(value * (0.96 + rng2() * 0.06) * 100) / 100;
        break;
      case 14:
        value = Math.round(holdings.filter(h => h.controversialWeapons).reduce((s, h) => s + h.weight, 0) * 100) / 100;
        benchmark = Math.round((0.5 + rng2() * 2) * 100) / 100;
        priorValue = Math.round(value * (0.98 + rng2() * 0.08) * 100) / 100;
        break;
      case 15:
        value = Math.round((180 + rng2() * 120) * 100) / 100;
        benchmark = Math.round((200 + rng2() * 100) * 100) / 100;
        priorValue = Math.round(value * (1.02 + rng2() * 0.06) * 100) / 100;
        break;
      case 16:
        value = Math.round(1 + rng2() * 4);
        benchmark = Math.round(2 + rng2() * 3);
        priorValue = Math.round(value + (rng2() > 0.5 ? 1 : -1) * Math.round(rng2()));
        break;
      case 17:
        value = Math.round((2 + rng2() * 8) * 100) / 100;
        benchmark = Math.round((5 + rng2() * 6) * 100) / 100;
        priorValue = Math.round(value * (0.97 + rng2() * 0.1) * 100) / 100;
        break;
      case 18:
        value = Math.round((15 + rng2() * 30) * 100) / 100;
        benchmark = Math.round((20 + rng2() * 20) * 100) / 100;
        priorValue = Math.round(value * (1.01 + rng2() * 0.08) * 100) / 100;
        break;
      default:
        value = Math.round(rng2() * 100 * 100) / 100;
        benchmark = Math.round(rng2() * 100 * 100) / 100;
        priorValue = Math.round(value * (0.95 + rng2() * 0.15) * 100) / 100;
    }

    const pctChange = priorValue !== 0 ? Math.round(((value - priorValue) / Math.abs(priorValue)) * 10000) / 100 : 0;
    const isLowerBetter = ![13].includes(pai.id);
    let trend;
    if (Math.abs(pctChange) < 1.5) trend = 'stable';
    else if (isLowerBetter) trend = value < priorValue ? 'improved' : 'deteriorated';
    else trend = value > priorValue ? 'improved' : 'deteriorated';

    const coverage = Math.round(65 + rng2() * 33);
    const benchmarkPercentile = Math.round(20 + rng2() * 70);
    const ragStatus = benchmarkPercentile >= 60 ? 'green' : benchmarkPercentile >= 35 ? 'amber' : 'red';

    paiValues[pai.id] = {
      ...pai,
      value,
      benchmark,
      priorValue,
      pctChange,
      trend,
      coverage,
      benchmarkPercentile,
      ragStatus,
      dqsDistribution: [
        Math.round(rng2() * 20),
        Math.round(rng2() * 25),
        Math.round(15 + rng2() * 20),
        Math.round(10 + rng2() * 15),
        Math.round(5 + rng2() * 10),
      ],
    };
  });

  // DNSH matrix
  const rng3 = seededRandom(7777);
  const dnshMatrix = PAI_INDICATORS.map(pai => {
    const row = { paiId: pai.id, paiName: pai.name };
    TAXONOMY_OBJECTIVES.forEach(obj => {
      const r = rng3();
      row[obj.key] = r < 0.15 ? 'fail' : r < 0.3 ? 'not_applicable' : 'pass';
    });
    return row;
  });

  // Entity classification
  const classification = {
    article: 9,
    label: 'Article 9 (Dark Green)',
    rationale: 'Product has sustainable investment as its objective, meets all mandatory PAI disclosure requirements, and all DNSH criteria are satisfied for taxonomy-aligned investments.',
    sustainableInvestmentPct: 82.4,
    taxonomyAlignedPct: 67.2,
    minimumSafeguards: true,
    dnshCompliance: true,
  };

  // Cross-framework mapping
  const crossFramework = [
    { sfdr: 'PAI 1-3 (GHG Emissions)', csrd: 'ESRS E1-6, E1-4', taxonomy: 'CCM Art. 10', ghgProtocol: 'Scope 1/2/3' },
    { sfdr: 'PAI 4 (Fossil Fuel)', csrd: 'ESRS E1-4', taxonomy: 'CCM DNSH', ghgProtocol: 'Sector screening' },
    { sfdr: 'PAI 5-6 (Energy)', csrd: 'ESRS E1-5', taxonomy: 'CCM Art. 10(1)', ghgProtocol: 'Scope 2 location/market' },
    { sfdr: 'PAI 7 (Biodiversity)', csrd: 'ESRS E4-5', taxonomy: 'BIO Art. 15', ghgProtocol: 'N/A' },
    { sfdr: 'PAI 8-9 (Pollution/Waste)', csrd: 'ESRS E2-3, E5-4', taxonomy: 'POL/CE DNSH', ghgProtocol: 'N/A' },
    { sfdr: 'PAI 10-11 (UNGC/OECD)', csrd: 'ESRS S1-17', taxonomy: 'Min. Safeguards', ghgProtocol: 'N/A' },
    { sfdr: 'PAI 12-14 (Social)', csrd: 'ESRS S1-16, G1-1', taxonomy: 'Min. Safeguards', ghgProtocol: 'N/A' },
    { sfdr: 'PAI 15-16 (Sovereign)', csrd: 'ESRS S3-4', taxonomy: 'N/A', ghgProtocol: 'National inventories' },
    { sfdr: 'PAI 17-18 (Real Estate)', csrd: 'ESRS E1-5', taxonomy: 'CCM 7.7', ghgProtocol: 'Scope 1/2' },
  ];

  // RTS statement sections
  const rtsStatement = [
    { section: 1, title: 'Summary', content: 'This financial product considers principal adverse impacts on sustainability factors. All 18 mandatory PAI indicators under Annex I Table 1 are monitored and disclosed.' },
    { section: 2, title: 'Description of PAIs', content: 'Quantitative assessment of all mandatory indicators is conducted on a quarterly basis using investee-reported data, supplemented by estimated and proxy values where primary data is unavailable.' },
    { section: 3, title: 'Description of Policies', content: 'ESG integration policy applies sector-based exclusions (controversial weapons, thermal coal >5%), engagement escalation triggers, and best-in-class tilts across PAI indicators.' },
    { section: 4, title: 'Engagement Policies', content: 'Active ownership programme targets bottom-quintile PAI performers with structured engagement milestones over 24-month cycles. 78% of flagged companies showed improvement in the reference period.' },
    { section: 5, title: 'References to Standards', content: 'Alignment with UNGC principles, OECD Guidelines for MNEs, ILO core conventions, and the International Bill of Human Rights. EU Taxonomy alignment verified for sustainable investments.' },
    { section: 6, title: 'Historical Comparison', content: 'Year-on-year comparison shows improvement in 11 of 18 mandatory indicators. Carbon footprint reduced by 8.2%, gender pay gap narrowed by 1.4 percentage points.' },
    { section: 7, title: 'Appendix — Data Sources', content: 'Data sourced from CDP (climate), ISS ESG (controversies), Bloomberg (financials), Sustainalytics (risk ratings), S&P Trucost (emissions), and direct company disclosures.' },
  ];

  // Disclosure readiness
  const disclosureFields = [
    { field: 'PAI 1-6 Climate metrics', populated: true },
    { field: 'PAI 7-9 Environment metrics', populated: true },
    { field: 'PAI 10-14 Social metrics', populated: true },
    { field: 'PAI 15-16 Sovereign metrics', populated: true },
    { field: 'PAI 17-18 Real estate metrics', populated: false },
    { field: 'Historical comparison (2 years)', populated: true },
    { field: 'Engagement policy description', populated: true },
    { field: 'EU Taxonomy alignment %', populated: true },
    { field: 'Minimum safeguards check', populated: true },
    { field: 'DNSH assessment per objective', populated: true },
    { field: 'Data quality methodology', populated: true },
    { field: 'Third-party assurance report', populated: false },
  ];

  const materialPAIs = Object.values(paiValues).filter(p => p.ragStatus === 'red').length;
  const avgCoverage = Math.round(Object.values(paiValues).reduce((s, p) => s + p.coverage, 0) / 18);

  return {
    holdings,
    paiValues,
    dnshMatrix,
    classification,
    crossFramework,
    rtsStatement,
    disclosureFields,
    totalAUM,
    materialPAIs,
    avgCoverage,
  };
}

/* ============================================================================
   MAIN COMPONENT
   ============================================================================ */
export default function SFDRPAIPage() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedPAI, setSelectedPAI] = useState(1);
  const [compPeriodA, setCompPeriodA] = useState('2025');
  const [compPeriodB, setCompPeriodB] = useState('2024');

  const data = useMemo(() => generateDemoData(), []);

  const tabs = [
    { id: 'dashboard',      label: 'PAI Dashboard',          icon: <BarChart3 className="w-3.5 h-3.5" /> },
    { id: 'calculations',   label: 'PAI Calculations',       icon: <Activity className="w-3.5 h-3.5" /> },
    { id: 'dnsh',           label: 'DNSH Assessment',        icon: <ShieldCheck className="w-3.5 h-3.5" /> },
    { id: 'comparison',     label: 'Period Comparison',       icon: <TrendingUp className="w-3.5 h-3.5" /> },
    { id: 'classification', label: 'Entity Classification',   icon: <FileText className="w-3.5 h-3.5" /> },
  ];

  return (
    <div className="min-h-screen bg-white">
      <DemoBanner message="PAI indicator values, DQS distributions, and benchmark comparisons display deterministic sample data. Upload your fund holdings to calculate live PAI disclosures." />
      {/* Header */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-[1440px] mx-auto px-6 py-5">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-lg font-bold text-gray-900">SFDR Principal Adverse Impact (PAI)</h1>
              <p className="text-xs text-gray-500 mt-1">
                Regulation (EU) 2019/2088 &middot; RTS Annex I Table 1 &middot; 18 Mandatory Indicators
              </p>
            </div>
            <div className="flex items-center gap-3">
              <Badge label={data.classification.label} variant="green" />
              <button className="px-4 py-2 bg-[#164E8A] text-white rounded-lg text-xs font-medium hover:bg-gray-800 transition">
                Export PAI Statement
              </button>
            </div>
          </div>
          <div className="mt-4">
            <TabPill tabs={tabs} active={activeTab} onChange={setActiveTab} />
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-[1440px] mx-auto px-6 py-6 space-y-6">
        {activeTab === 'dashboard' && (
          <DashboardTab data={data} />
        )}
        {activeTab === 'calculations' && (
          <CalculationsTab data={data} selectedPAI={selectedPAI} setSelectedPAI={setSelectedPAI} />
        )}
        {activeTab === 'dnsh' && (
          <DNSHTab data={data} />
        )}
        {activeTab === 'comparison' && (
          <ComparisonTab data={data} periodA={compPeriodA} periodB={compPeriodB} setPeriodA={setCompPeriodA} setPeriodB={setCompPeriodB} />
        )}
        {activeTab === 'classification' && (
          <ClassificationTab data={data} />
        )}
      </div>
    </div>
  );
}

/* ============================================================================
   TAB 1: PAI DASHBOARD
   ============================================================================ */
function DashboardTab({ data }) {
  const { paiValues, totalAUM, materialPAIs, avgCoverage, classification } = data;
  const paiList = Object.values(paiValues);

  const barChartData = PAI_INDICATORS.map(pai => ({
    name: `PAI ${pai.id}`,
    short: pai.short,
    value: paiValues[pai.id].value,
    benchmark: paiValues[pai.id].benchmark,
  }));

  // Data quality heatmap data
  const qualityDimensions = ['Completeness', 'Accuracy', 'Timeliness', 'Methodology', 'Consistency'];
  const rng = seededRandom(99);
  const heatmapData = PAI_INDICATORS.map(pai => {
    const row = { indicator: `PAI ${pai.id}` };
    qualityDimensions.forEach(dim => {
      row[dim] = Math.round(40 + rng() * 58);
    });
    return row;
  });

  return (
    <>
      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Entity Classification"
          value={`Article ${classification.article}`}
          sub={classification.article === 9 ? 'Dark Green Product' : classification.article === 8 ? 'Light Green Product' : 'No Sustainability Claim'}
          icon={FileText}
          accent="green"
        />
        <StatCard
          label="Data Coverage"
          value={`${avgCoverage}%`}
          sub="Weighted avg across 18 PAIs"
          icon={Activity}
          accent="black"
        />
        <StatCard
          label="Material PAIs"
          value={materialPAIs}
          sub="Below sector median (red RAG)"
          icon={AlertTriangle}
          accent={materialPAIs > 3 ? 'red' : 'amber'}
        />
        <StatCard
          label="Portfolio AUM"
          value={`EUR ${Math.round(totalAUM)}M`}
          sub="30 holdings across 10 sectors"
          icon={Building2}
          accent="black"
        />
      </div>

      {/* Benchmark Comparison Bar Chart */}
      <Card title="Mandatory PAI Indicators vs Sector Benchmark" subtitle="All 18 Table 1 indicators - normalised values with sector median overlay" badge="Annex I Table 1">
        <ResponsiveContainer width="100%" height={380}>
          <BarChart data={barChartData} margin={{ top: 10, right: 20, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.5)' }} angle={-45} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.4)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="value" name="Portfolio" fill="#111111" radius={[3, 3, 0, 0]} />
            <Bar dataKey="benchmark" name="Sector Median" fill="#d1d5db" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* RAG Traffic Light + Summary Table */}
      <Card title="PAI Summary Table" subtitle="RAG status based on benchmark percentile ranking" badge="18 Indicators">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">ID</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Indicator</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Category</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">Value</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Unit</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">RAG</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">Trend</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">Coverage</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">DQS</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">Benchmark %ile</th>
              </tr>
            </thead>
            <tbody>
              {paiList.map(p => (
                <tr key={p.id} className="border-b border-gray-100 hover:bg-[#f5f6f8] transition">
                  <td className="py-2.5 px-3 text-xs font-mono text-gray-500">{p.id}</td>
                  <td className="py-2.5 px-3 text-xs font-medium text-gray-800">{p.name}</td>
                  <td className="py-2.5 px-3">
                    <Badge
                      label={p.category === 'climate' ? 'Climate' : p.category === 'environment' ? 'Env.' : p.category === 'social' ? 'Social' : p.category === 'sovereign' ? 'Sovereign' : 'Real Estate'}
                      variant={p.category === 'climate' ? 'blue' : p.category === 'environment' ? 'green' : p.category === 'social' ? 'amber' : 'neutral'}
                    />
                  </td>
                  <td className="py-2.5 px-3 text-xs text-right font-mono text-gray-700">{p.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</td>
                  <td className="py-2.5 px-3 text-[10px] text-gray-500">{p.unit}</td>
                  <td className="py-2.5 px-3 text-center"><RAGDot status={p.ragStatus} /></td>
                  <td className="py-2.5 px-3 text-center flex items-center justify-center gap-1">
                    <TrendArrow trend={p.trend} />
                    <span className={`text-[10px] ${p.trend === 'improved' ? 'text-emerald-600' : p.trend === 'deteriorated' ? 'text-red-600' : 'text-gray-500'}`}>
                      {p.pctChange > 0 ? '+' : ''}{p.pctChange}%
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-xs text-right text-gray-500">{p.coverage}%</td>
                  <td className="py-2.5 px-3 text-xs text-right">
                    <span className={`font-mono ${p.dqsDistribution[0] > 15 ? 'text-emerald-600' : 'text-amber-600'}`}>
                      {Math.round(p.dqsDistribution.reduce((s, v, i) => s + v * (i + 1), 0) / p.dqsDistribution.reduce((s, v) => s + v, 0) * 10) / 10}
                    </span>
                  </td>
                  <td className="py-2.5 px-3 text-xs text-right font-mono text-gray-600">P{p.benchmarkPercentile}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Data Quality Heatmap */}
      <Card title="Data Quality Heatmap" subtitle="Score by indicator and quality dimension (0-100)" badge="PCAF DQS">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Indicator</th>
                {qualityDimensions.map(dim => (
                  <th key={dim} className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">{dim}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {heatmapData.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-100">
                  <td className="py-2 px-3 text-xs font-medium text-gray-700">{row.indicator}</td>
                  {qualityDimensions.map(dim => {
                    const val = row[dim];
                    const bg = val >= 80 ? 'bg-emerald-100 text-emerald-700' : val >= 60 ? 'bg-blue-50 text-blue-700' : val >= 40 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700';
                    return (
                      <td key={dim} className="py-2 px-3 text-center">
                        <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${bg}`}>{val}</span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

/* ============================================================================
   TAB 2: PAI CALCULATIONS
   ============================================================================ */
function CalculationsTab({ data, selectedPAI, setSelectedPAI }) {
  const { paiValues, holdings } = data;
  const indicator = paiValues[selectedPAI];
  const paiDef = PAI_INDICATORS.find(p => p.id === selectedPAI);

  // Compute top 10 contributors
  const holdingContributions = useMemo(() => {
    const rng = seededRandom(selectedPAI * 1000);
    return holdings
      .map(h => ({
        name: h.name,
        sector: h.sector,
        weight: h.weight,
        contribution: Math.round(h.weight * (5 + rng() * 20) * 100) / 100,
        method: h.dataMethod,
        dqs: h.dqs,
      }))
      .sort((a, b) => b.contribution - a.contribution)
      .slice(0, 10);
  }, [selectedPAI, holdings]);

  // Estimation method distribution
  const methodDist = useMemo(() => {
    const counts = { reported: 0, estimated: 0, proxy: 0 };
    holdings.forEach(h => { counts[h.dataMethod] = (counts[h.dataMethod] || 0) + 1; });
    return [
      { name: 'Reported', value: counts.reported, fill: '#10b981' },
      { name: 'Estimated', value: counts.estimated, fill: '#3b82f6' },
      { name: 'Proxy', value: counts.proxy, fill: '#f59e0b' },
    ];
  }, [holdings]);

  // DQS distribution for selected PAI
  const dqsData = indicator.dqsDistribution.map((v, i) => ({
    name: `DQS ${i + 1}`,
    value: v,
    label: ['Reported', 'Vendor verified', 'Modelled', 'Estimated', 'Proxy'][i],
  }));

  return (
    <>
      {/* Indicator Selector */}
      <Card title="Select PAI Indicator" subtitle="Choose from 18 mandatory indicators for detailed analysis">
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2">
          {PAI_INDICATORS.map(pai => (
            <button
              key={pai.id}
              onClick={() => setSelectedPAI(pai.id)}
              className={`px-3 py-2.5 rounded-lg border text-left transition-all ${
                selectedPAI === pai.id
                  ? 'bg-[#164E8A] text-white border-black'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-black/20 hover:text-gray-800'
              }`}
            >
              <span className="text-[10px] font-mono block opacity-60">PAI {pai.id}</span>
              <span className="text-xs font-medium block truncate">{pai.short}</span>
            </button>
          ))}
        </div>
      </Card>

      {/* Selected Indicator Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title={`PAI ${indicator.id}: ${indicator.name}`} subtitle={indicator.unit} badge={indicator.category.toUpperCase()} className="lg:col-span-2">
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-[#f5f6f8] rounded-lg p-3">
                <p className="text-[10px] text-gray-500 mb-1">Current Value</p>
                <p className="text-lg font-bold text-gray-900">{indicator.value.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
                <p className="text-[10px] text-gray-500">{indicator.unit}</p>
              </div>
              <div className="bg-[#f5f6f8] rounded-lg p-3">
                <p className="text-[10px] text-gray-500 mb-1">Benchmark</p>
                <p className="text-lg font-bold text-gray-700">{indicator.benchmark.toLocaleString(undefined, { maximumFractionDigits: 2 })}</p>
                <p className="text-[10px] text-gray-500">Sector median</p>
              </div>
              <div className="bg-[#f5f6f8] rounded-lg p-3">
                <p className="text-[10px] text-gray-500 mb-1">Percentile</p>
                <p className="text-lg font-bold text-gray-700">P{indicator.benchmarkPercentile}</p>
                <RAGDot status={indicator.ragStatus} />
              </div>
              <div className="bg-[#f5f6f8] rounded-lg p-3">
                <p className="text-[10px] text-gray-500 mb-1">Coverage</p>
                <p className="text-lg font-bold text-gray-700">{indicator.coverage}%</p>
                <p className="text-[10px] text-gray-500">Holdings covered</p>
              </div>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-gray-600 mb-2">Formula</h3>
              <p className="text-xs text-gray-500 leading-relaxed">{paiDef.formula}</p>
            </div>

            <div className="border border-gray-200 rounded-lg p-4">
              <h3 className="text-xs font-semibold text-gray-600 mb-2">Required Data Points</h3>
              <div className="flex flex-wrap gap-2">
                {paiDef.requiredData.map((dp, i) => (
                  <span key={i} className="inline-flex items-center px-2 py-1 rounded bg-[#f5f6f8] text-[10px] text-gray-500 border border-gray-200">{dp}</span>
                ))}
              </div>
            </div>
          </div>
        </Card>

        {/* DQS Pie Chart */}
        <Card title="Data Quality Distribution" subtitle="PCAF DQS levels for this indicator" badge="DQS">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={dqsData} dataKey="value" nameKey="label" cx="50%" cy="50%" outerRadius={80} innerRadius={40} strokeWidth={1} stroke="#fff">
                {dqsData.map((_, i) => (
                  <Cell key={i} fill={DQS_COLORS[i]} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 10 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="mt-3 space-y-1.5">
            {dqsData.map((d, i) => (
              <div key={i} className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full" style={{ backgroundColor: DQS_COLORS[i] }} />
                  <span className="text-gray-500">{d.label}</span>
                </div>
                <span className="font-mono text-gray-500">{d.value}%</span>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Top 10 Holdings Breakdown */}
      <Card title="Top 10 Holdings by Contribution" subtitle={`Holdings contributing most to PAI ${selectedPAI}`} badge="Holdings">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">#</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Company</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Sector</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">Weight %</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">Contribution</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">Method</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">DQS</th>
              </tr>
            </thead>
            <tbody>
              {holdingContributions.map((h, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-[#f5f6f8] transition">
                  <td className="py-2.5 px-3 text-xs font-mono text-gray-500">{idx + 1}</td>
                  <td className="py-2.5 px-3 text-xs font-medium text-gray-800">{h.name}</td>
                  <td className="py-2.5 px-3 text-xs text-gray-500">{h.sector}</td>
                  <td className="py-2.5 px-3 text-xs text-right font-mono text-gray-600">{h.weight}%</td>
                  <td className="py-2.5 px-3 text-xs text-right font-mono text-gray-700 font-semibold">{h.contribution.toLocaleString()}</td>
                  <td className="py-2.5 px-3 text-center">
                    <Badge
                      label={h.method}
                      variant={h.method === 'reported' ? 'green' : h.method === 'estimated' ? 'blue' : 'amber'}
                    />
                  </td>
                  <td className="py-2.5 px-3 text-center">
                    <span className={`text-xs font-mono font-bold ${h.dqs <= 2 ? 'text-emerald-600' : h.dqs <= 3 ? 'text-blue-600' : 'text-amber-600'}`}>
                      {h.dqs}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Estimation Method Distribution */}
      <Card title="Estimation Method Distribution" subtitle="Proportion of holdings by data source type" badge="30 Holdings">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-center">
          <ResponsiveContainer width="100%" height={240}>
            <PieChart>
              <Pie data={methodDist} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} innerRadius={50} strokeWidth={2} stroke="#fff">
                {methodDist.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-3">
            {methodDist.map((m, i) => (
              <div key={i} className="flex items-center justify-between p-3 bg-[#f5f6f8] rounded-lg">
                <div className="flex items-center gap-3">
                  <span className="w-3 h-3 rounded-full" style={{ backgroundColor: m.fill }} />
                  <span className="text-xs font-medium text-gray-700">{m.name}</span>
                </div>
                <div className="text-right">
                  <span className="text-sm font-bold text-gray-900">{m.value}</span>
                  <span className="text-xs text-gray-500 ml-1">holdings</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </Card>
    </>
  );
}

/* ============================================================================
   TAB 3: DNSH ASSESSMENT
   ============================================================================ */
function DNSHTab({ data }) {
  const { dnshMatrix, holdings } = data;

  // Overall compliance
  const totalCells = dnshMatrix.length * TAXONOMY_OBJECTIVES.length;
  const passCells = dnshMatrix.reduce((s, row) => s + TAXONOMY_OBJECTIVES.filter(o => row[o.key] === 'pass').length, 0);
  const failCells = dnshMatrix.reduce((s, row) => s + TAXONOMY_OBJECTIVES.filter(o => row[o.key] === 'fail').length, 0);
  const naCells = totalCells - passCells - failCells;
  const overallScore = Math.round((passCells / (passCells + failCells)) * 100);

  // Risk flags: PAIs with at least one fail
  const flaggedPAIs = dnshMatrix.filter(row => TAXONOMY_OBJECTIVES.some(o => row[o.key] === 'fail'));

  // Per-objective summary
  const objectiveSummary = TAXONOMY_OBJECTIVES.map(obj => {
    const passes = dnshMatrix.filter(r => r[obj.key] === 'pass').length;
    const fails = dnshMatrix.filter(r => r[obj.key] === 'fail').length;
    const na = dnshMatrix.filter(r => r[obj.key] === 'not_applicable').length;
    return { ...obj, passes, fails, na, pct: Math.round((passes / (passes + fails || 1)) * 100) };
  });

  const objectiveBarData = objectiveSummary.map(o => ({
    name: o.key,
    Pass: o.passes,
    Fail: o.fails,
    'N/A': o.na,
  }));

  return (
    <>
      {/* KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard label="Overall DNSH Score" value={`${overallScore}%`} sub="Pass rate (excl. N/A)" icon={ShieldCheck} accent="green" />
        <StatCard label="Pass Cells" value={passCells} sub={`of ${totalCells} total assessments`} icon={CheckCircle2} accent="green" />
        <StatCard label="Fail Cells" value={failCells} sub="Require remediation" icon={XCircle} accent="red" />
        <StatCard label="Flagged PAIs" value={flaggedPAIs.length} sub="With at least one failure" icon={AlertTriangle} accent="amber" />
      </div>

      {/* Objective Compliance Bar */}
      <Card title="Compliance by EU Taxonomy Objective" subtitle="Pass / Fail / N/A distribution per objective" badge="6 Objectives">
        <ResponsiveContainer width="100%" height={280}>
          <BarChart data={objectiveBarData} margin={{ top: 10, right: 20, left: 0, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
            <XAxis dataKey="name" tick={{ fontSize: 11, fill: 'rgba(0,0,0,0.5)' }} />
            <YAxis tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.4)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="Pass" stackId="a" fill={DNSH_PASS} radius={[0, 0, 0, 0]} />
            <Bar dataKey="Fail" stackId="a" fill={DNSH_FAIL} />
            <Bar dataKey="N/A" stackId="a" fill={DNSH_NA} radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* DNSH Matrix */}
      <Card title="DNSH Assessment Matrix" subtitle="PAI indicators x EU Taxonomy objectives" badge="18 x 6">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">PAI</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Indicator</th>
                {TAXONOMY_OBJECTIVES.map(obj => (
                  <th key={obj.key} className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">
                    <div className="flex flex-col items-center gap-0.5">
                      <obj.icon className="w-3.5 h-3.5 text-gray-500" />
                      <span>{obj.key}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {dnshMatrix.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-[#f5f6f8] transition">
                  <td className="py-2.5 px-3 text-xs font-mono text-gray-500">{row.paiId}</td>
                  <td className="py-2.5 px-3 text-xs font-medium text-gray-700 max-w-[180px] truncate">{row.paiName}</td>
                  {TAXONOMY_OBJECTIVES.map(obj => {
                    const status = row[obj.key];
                    const cellClass = status === 'pass'
                      ? 'bg-emerald-50 text-emerald-600'
                      : status === 'fail'
                      ? 'bg-red-50 text-red-600'
                      : 'bg-gray-50 text-gray-500';
                    const icon = status === 'pass'
                      ? <CheckCircle2 className="w-3.5 h-3.5" />
                      : status === 'fail'
                      ? <XCircle className="w-3.5 h-3.5" />
                      : <Minus className="w-3 h-3" />;
                    return (
                      <td key={obj.key} className="py-2.5 px-3 text-center">
                        <span className={`inline-flex items-center justify-center w-7 h-7 rounded-md ${cellClass}`}>
                          {icon}
                        </span>
                      </td>
                    );
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Risk Flags */}
      {flaggedPAIs.length > 0 && (
        <Card title="Risk Flags" subtitle="PAI indicators with at least one DNSH failure requiring remediation" badge={`${flaggedPAIs.length} Flagged`}>
          <div className="space-y-3">
            {flaggedPAIs.map((row, idx) => {
              const failedObjs = TAXONOMY_OBJECTIVES.filter(o => row[o.key] === 'fail');
              return (
                <div key={idx} className="flex items-start gap-3 p-3 bg-red-50 border border-red-100 rounded-lg">
                  <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                  <div>
                    <p className="text-xs font-semibold text-red-700">PAI {row.paiId}: {row.paiName}</p>
                    <p className="text-[10px] text-red-500 mt-0.5">
                      Failed objectives: {failedObjs.map(o => o.key).join(', ')}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>
        </Card>
      )}

      {/* Per-Objective Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {objectiveSummary.map(obj => (
          <div key={obj.key} className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <div className="flex items-center gap-2 mb-3">
              <obj.icon className="w-4 h-4 text-gray-500" />
              <h3 className="text-xs font-semibold text-gray-700">{obj.label}</h3>
            </div>
            <div className="flex items-end gap-4 mb-3">
              <div>
                <p className="text-2xl font-bold text-gray-900">{obj.pct}%</p>
                <p className="text-[10px] text-gray-500">Pass rate</p>
              </div>
              <div className="flex-1">
                <div className="flex gap-1 h-4">
                  <div className="bg-emerald-400 rounded-l" style={{ width: `${(obj.passes / 18) * 100}%` }} />
                  <div className="bg-red-400" style={{ width: `${(obj.fails / 18) * 100}%` }} />
                  <div className="bg-gray-200 rounded-r" style={{ width: `${(obj.na / 18) * 100}%` }} />
                </div>
              </div>
            </div>
            <div className="flex gap-4 text-[10px] text-gray-500">
              <span><span className="font-semibold text-emerald-600">{obj.passes}</span> pass</span>
              <span><span className="font-semibold text-red-600">{obj.fails}</span> fail</span>
              <span><span className="font-semibold text-gray-500">{obj.na}</span> n/a</span>
            </div>
          </div>
        ))}
      </div>
    </>
  );
}

/* ============================================================================
   TAB 4: PERIOD COMPARISON
   ============================================================================ */
function ComparisonTab({ data, periodA, periodB, setPeriodA, setPeriodB }) {
  const { paiValues } = data;
  const paiList = Object.values(paiValues);

  const compData = PAI_INDICATORS.map(pai => ({
    name: `PAI ${pai.id}`,
    short: pai.short,
    current: paiValues[pai.id].value,
    prior: paiValues[pai.id].priorValue,
    pctChange: paiValues[pai.id].pctChange,
    trend: paiValues[pai.id].trend,
  }));

  const improved = paiList.filter(p => p.trend === 'improved').length;
  const deteriorated = paiList.filter(p => p.trend === 'deteriorated').length;
  const stable = paiList.filter(p => p.trend === 'stable').length;

  const summaryPie = [
    { name: 'Improved', value: improved, fill: '#10b981' },
    { name: 'Deteriorated', value: deteriorated, fill: '#ef4444' },
    { name: 'Stable', value: stable, fill: '#d1d5db' },
  ];

  const periods = ['2025', '2024', '2023', '2022'];

  return (
    <>
      {/* Period Selectors */}
      <Card title="Period Selection" subtitle="Select two reporting periods for year-on-year comparison">
        <div className="flex items-center gap-6">
          <div>
            <label className="block text-xs text-gray-500 mb-1">Current Period</label>
            <select
              value={periodA}
              onChange={e => setPeriodA(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none focus:ring-1 focus:ring-black/30"
            >
              {periods.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <span className="text-gray-400 text-lg mt-5">vs</span>
          <div>
            <label className="block text-xs text-gray-500 mb-1">Prior Period</label>
            <select
              value={periodB}
              onChange={e => setPeriodB(e.target.value)}
              className="border border-gray-200 rounded-lg px-3 py-2 text-sm bg-[#f5f6f8] text-gray-700 focus:outline-none focus:ring-1 focus:ring-black/30"
            >
              {periods.map(p => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
        </div>
      </Card>

      {/* Summary KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard label="Improved" value={improved} sub={`of 18 indicators (${Math.round(improved / 18 * 100)}%)`} icon={ArrowDownRight} accent="green" />
        <StatCard label="Deteriorated" value={deteriorated} sub={`of 18 indicators (${Math.round(deteriorated / 18 * 100)}%)`} icon={ArrowUpRight} accent="red" />
        <StatCard label="Stable" value={stable} sub={`of 18 indicators (${Math.round(stable / 18 * 100)}%)`} icon={Minus} accent="black" />
      </div>

      {/* Side-by-Side Bar Chart */}
      <Card title={`Period Comparison: ${periodA} vs ${periodB}`} subtitle="Current and prior period values per indicator" badge="18 Indicators">
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={compData} margin={{ top: 10, right: 20, left: 0, bottom: 60 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
            <XAxis dataKey="name" tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.5)' }} angle={-45} textAnchor="end" interval={0} />
            <YAxis tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.4)' }} />
            <Tooltip contentStyle={TOOLTIP_STYLE} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar dataKey="current" name={periodA} fill="#111111" radius={[3, 3, 0, 0]} />
            <Bar dataKey="prior" name={periodB} fill="#d1d5db" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </Card>

      {/* Trend Summary Pie */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Trend Distribution" subtitle="Proportion of improved / deteriorated / stable">
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={summaryPie} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={95} innerRadius={55} strokeWidth={2} stroke="#fff">
                {summaryPie.map((entry, i) => (
                  <Cell key={i} fill={entry.fill} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 11 }} />
            </PieChart>
          </ResponsiveContainer>
        </Card>

        {/* Percentage Change Table */}
        <Card title="Change Detail" subtitle="Percentage change per indicator">
          <div className="overflow-y-auto max-h-[300px]">
            <table className="w-full text-left">
              <thead className="sticky top-0 bg-white">
                <tr className="border-b border-gray-200">
                  <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">PAI</th>
                  <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">Indicator</th>
                  <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-right">Change</th>
                  <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider text-center">Trend</th>
                </tr>
              </thead>
              <tbody>
                {compData.map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-100 hover:bg-[#f5f6f8] transition">
                    <td className="py-2 px-3 text-xs font-mono text-gray-500">{row.name}</td>
                    <td className="py-2 px-3 text-xs text-gray-700">{row.short}</td>
                    <td className={`py-2 px-3 text-xs text-right font-mono font-semibold ${
                      row.trend === 'improved' ? 'text-emerald-600' : row.trend === 'deteriorated' ? 'text-red-600' : 'text-gray-500'
                    }`}>
                      {row.pctChange > 0 ? '+' : ''}{row.pctChange}%
                    </td>
                    <td className="py-2 px-3 text-center">
                      <div className="flex items-center justify-center gap-1">
                        <TrendArrow trend={row.trend} />
                        <Badge
                          label={row.trend}
                          variant={row.trend === 'improved' ? 'green' : row.trend === 'deteriorated' ? 'red' : 'neutral'}
                        />
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* Trend over time line chart (synthetic multi-year) */}
      <Card title="Multi-Year Trend — Selected Indicators" subtitle="Synthetic trajectory for PAI 1, 2, 4, 12, 13" badge="5-Year View">
        <MultiYearTrendChart paiValues={paiValues} />
      </Card>
    </>
  );
}

function MultiYearTrendChart({ paiValues }) {
  const rng = seededRandom(5555);
  const years = [2021, 2022, 2023, 2024, 2025];
  const tracked = [1, 2, 4, 12, 13];
  const lineColors = ['#111111', '#6b7280', '#10b981', '#f59e0b', '#3b82f6'];

  const lineData = years.map((year, yi) => {
    const row = { year };
    tracked.forEach(id => {
      const base = paiValues[id].value;
      const factor = 1.3 - yi * 0.08 + (rng() - 0.5) * 0.1;
      row[`PAI ${id}`] = Math.round(base * factor * 100) / 100;
    });
    return row;
  });

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={lineData} margin={{ top: 10, right: 20, left: 0, bottom: 10 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.06)" />
        <XAxis dataKey="year" tick={{ fontSize: 11, fill: 'rgba(0,0,0,0.5)' }} />
        <YAxis tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.4)' }} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Legend wrapperStyle={{ fontSize: 11 }} />
        {tracked.map((id, i) => (
          <Line key={id} type="monotone" dataKey={`PAI ${id}`} stroke={lineColors[i]} strokeWidth={2} dot={{ r: 3 }} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  );
}

/* ============================================================================
   TAB 5: ENTITY CLASSIFICATION & DISCLOSURE
   ============================================================================ */
function ClassificationTab({ data }) {
  const { classification, crossFramework, rtsStatement, disclosureFields, paiValues } = data;

  const populatedCount = disclosureFields.filter(f => f.populated).length;
  const readinessScore = Math.round((populatedCount / disclosureFields.length) * 100);

  // Requirements checklist per article
  const artRequirements = {
    6: [
      { req: 'Pre-contractual disclosure of sustainability risk integration', met: true },
      { req: 'Website disclosure of sustainability risk policy', met: true },
      { req: 'Explanation of no-sustainability-consideration decision', met: false },
    ],
    8: [
      { req: 'All Article 6 requirements', met: true },
      { req: 'Environmental/social characteristics promotion', met: true },
      { req: 'Proportion of taxonomy-aligned investments', met: true },
      { req: 'DNSH assessment for sustainable investments', met: true },
      { req: 'Periodic report with E/S characteristic performance', met: true },
      { req: 'Index benchmark methodology (if applicable)', met: false },
    ],
    9: [
      { req: 'All Article 8 requirements', met: true },
      { req: 'Sustainable investment as objective', met: true },
      { req: 'Taxonomy alignment at minimum 0%', met: true },
      { req: 'EU taxonomy alignment > 0% reported', met: true },
      { req: 'DNSH across all EU Taxonomy objectives', met: true },
      { req: 'Minimum safeguards compliance', met: true },
      { req: 'PAI consideration mandatory', met: true },
      { req: 'Index benchmark with Paris-aligned methodology', met: false },
    ],
  };

  const currentReqs = artRequirements[classification.article] || [];
  const reqsMet = currentReqs.filter(r => r.met).length;

  // Radar for classification dimensions
  const classRadarData = [
    { dimension: 'E/S Characteristics', value: 88 },
    { dimension: 'Taxonomy Alignment', value: Math.round(classification.taxonomyAlignedPct) },
    { dimension: 'Sustainable Inv %', value: Math.round(classification.sustainableInvestmentPct) },
    { dimension: 'DNSH Compliance', value: classification.dnshCompliance ? 95 : 40 },
    { dimension: 'Min Safeguards', value: classification.minimumSafeguards ? 92 : 30 },
    { dimension: 'PAI Disclosure', value: readinessScore },
  ];

  return (
    <>
      {/* Classification Summary */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="Entity Classification" subtitle="SFDR Article determination" badge={`Article ${classification.article}`} className="lg:col-span-1">
          <div className="text-center py-4">
            <div className={`inline-flex items-center justify-center w-24 h-24 rounded-full mb-4 ${
              classification.article === 9 ? 'bg-emerald-50 border-2 border-emerald-200' :
              classification.article === 8 ? 'bg-blue-50 border-2 border-blue-200' :
              'bg-gray-50 border-2 border-gray-200'
            }`}>
              <span className={`text-3xl font-bold ${
                classification.article === 9 ? 'text-emerald-600' :
                classification.article === 8 ? 'text-blue-600' :
                'text-gray-600'
              }`}>{classification.article}</span>
            </div>
            <p className="text-sm font-semibold text-gray-800">{classification.label}</p>
            <p className="text-xs text-gray-500 mt-2 leading-relaxed">{classification.rationale}</p>
          </div>
          <div className="space-y-2 mt-4 border-t border-gray-200 pt-4">
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Sustainable Investment %</span>
              <span className="font-semibold text-gray-700">{classification.sustainableInvestmentPct}%</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Taxonomy-Aligned %</span>
              <span className="font-semibold text-gray-700">{classification.taxonomyAlignedPct}%</span>
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">Minimum Safeguards</span>
              <Badge label={classification.minimumSafeguards ? 'Met' : 'Not Met'} variant={classification.minimumSafeguards ? 'green' : 'red'} />
            </div>
            <div className="flex justify-between text-xs">
              <span className="text-gray-500">DNSH Compliance</span>
              <Badge label={classification.dnshCompliance ? 'Passed' : 'Failed'} variant={classification.dnshCompliance ? 'green' : 'red'} />
            </div>
          </div>
        </Card>

        <Card title="Classification Dimensions" subtitle="Radar overview of key compliance areas" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={320}>
            <RadarChart data={classRadarData} cx="50%" cy="50%" outerRadius={110}>
              <PolarGrid stroke="rgba(0,0,0,0.08)" />
              <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 10, fill: 'rgba(0,0,0,0.5)' }} />
              <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 9, fill: 'rgba(0,0,0,0.3)' }} />
              <Radar name="Score" dataKey="value" stroke="#111111" fill="#111111" fillOpacity={0.15} strokeWidth={2} />
              <Tooltip contentStyle={TOOLTIP_STYLE} />
            </RadarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Requirements Checklist */}
      <Card title={`Article ${classification.article} Requirements Checklist`} subtitle={`${reqsMet} of ${currentReqs.length} requirements met`} badge={`${Math.round(reqsMet / currentReqs.length * 100)}%`}>
        <div className="space-y-2">
          {currentReqs.map((r, i) => (
            <div key={i} className={`flex items-start gap-3 p-3 rounded-lg ${r.met ? 'bg-emerald-50 border border-emerald-100' : 'bg-red-50 border border-red-100'}`}>
              {r.met ? <CheckCircle2 className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" /> : <XCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />}
              <p className={`text-xs ${r.met ? 'text-emerald-700' : 'text-red-700'}`}>{r.req}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* RTS PAI Statement Preview */}
      <Card title="PAI Statement Preview" subtitle="7-section RTS template per Annex I" badge="Article 4 RTS">
        <div className="space-y-4">
          {rtsStatement.map(s => (
            <div key={s.section} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-[#164E8A] text-white text-[10px] font-bold">{s.section}</span>
                <h3 className="text-xs font-semibold text-gray-700">{s.title}</h3>
              </div>
              <p className="text-xs text-gray-500 leading-relaxed">{s.content}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Cross-Framework Mapping */}
      <Card title="Cross-Framework Mapping" subtitle="SFDR PAI indicators mapped to CSRD ESRS, EU Taxonomy, and GHG Protocol" badge="Interoperability">
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-gray-200">
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">SFDR PAI</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">CSRD ESRS</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">EU Taxonomy</th>
                <th className="py-2 px-3 text-[10px] font-semibold text-gray-500 uppercase tracking-wider">GHG Protocol</th>
              </tr>
            </thead>
            <tbody>
              {crossFramework.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-[#f5f6f8] transition">
                  <td className="py-2.5 px-3 text-xs font-medium text-gray-700">{row.sfdr}</td>
                  <td className="py-2.5 px-3 text-xs text-gray-500">{row.csrd}</td>
                  <td className="py-2.5 px-3 text-xs text-gray-500">{row.taxonomy}</td>
                  <td className="py-2.5 px-3 text-xs text-gray-500">{row.ghgProtocol}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Disclosure Readiness */}
      <Card title="Disclosure Readiness" subtitle="Required disclosure fields population status" badge={`${readinessScore}%`}>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Progress bar */}
          <div>
            <div className="mb-4">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-500">Overall Readiness</span>
                <span className="text-sm font-bold text-gray-900">{readinessScore}%</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-3">
                <div
                  className="bg-[#164E8A] rounded-full h-3 transition-all"
                  style={{ width: `${readinessScore}%` }}
                />
              </div>
            </div>
            <div className="space-y-2">
              {disclosureFields.map((f, i) => (
                <div key={i} className="flex items-center justify-between p-2 rounded-lg bg-[#f5f6f8]">
                  <div className="flex items-center gap-2">
                    {f.populated
                      ? <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                      : <XCircle className="w-3.5 h-3.5 text-red-400" />
                    }
                    <span className="text-xs text-gray-600">{f.field}</span>
                  </div>
                  <Badge label={f.populated ? 'Complete' : 'Missing'} variant={f.populated ? 'green' : 'red'} />
                </div>
              ))}
            </div>
          </div>

          {/* Readiness by category */}
          <div>
            <h3 className="text-xs font-semibold text-gray-600 mb-3">Readiness by PAI Category</h3>
            {PAI_CATEGORIES.map(cat => {
              const catPais = cat.ids.map(id => paiValues[id]);
              const avgCov = Math.round(catPais.reduce((s, p) => s + p.coverage, 0) / catPais.length);
              const Icon = cat.icon;
              return (
                <div key={cat.key} className="flex items-center gap-3 mb-3 p-3 bg-[#f5f6f8] rounded-lg">
                  <Icon className="w-4 h-4 text-gray-500 flex-shrink-0" />
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-xs font-medium text-gray-600">{cat.label}</span>
                      <span className="text-xs font-mono text-gray-500">{avgCov}%</span>
                    </div>
                    <div className="w-full bg-gray-100 rounded-full h-1.5">
                      <div
                        className={`rounded-full h-1.5 transition-all ${avgCov >= 80 ? 'bg-emerald-500' : avgCov >= 60 ? 'bg-blue-500' : 'bg-amber-500'}`}
                        style={{ width: `${avgCov}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            })}

            {/* Peer sector comparison */}
            <h3 className="text-xs font-semibold text-gray-600 mb-3 mt-6">Peer Sector Benchmarking</h3>
            <PeerBenchmarkMini paiValues={paiValues} />
          </div>
        </div>
      </Card>
    </>
  );
}

/* ============================================================================
   PEER BENCHMARK MINI COMPONENT
   ============================================================================ */
function PeerBenchmarkMini({ paiValues }) {
  const rng = seededRandom(8888);
  const sectors = ['Financials', 'Utilities', 'Energy', 'Industrials', 'Health Care', 'Technology', 'Consumer', 'Real Estate'];

  const benchData = sectors.map(sector => ({
    sector,
    percentile: Math.round(20 + rng() * 70),
    peerCount: Math.round(15 + rng() * 85),
  }));

  return (
    <div className="space-y-2">
      {benchData.map((s, i) => (
        <div key={i} className="flex items-center gap-3 p-2 bg-white border border-gray-200 rounded-lg">
          <span className="text-xs text-gray-500 w-24 truncate">{s.sector}</span>
          <div className="flex-1 relative">
            <div className="w-full bg-gray-100 rounded-full h-2">
              <div
                className={`rounded-full h-2 ${s.percentile >= 60 ? 'bg-emerald-500' : s.percentile >= 35 ? 'bg-amber-400' : 'bg-red-400'}`}
                style={{ width: `${s.percentile}%` }}
              />
            </div>
          </div>
          <span className="text-[10px] font-mono text-gray-500 w-10 text-right">P{s.percentile}</span>
        </div>
      ))}
    </div>
  );
}
