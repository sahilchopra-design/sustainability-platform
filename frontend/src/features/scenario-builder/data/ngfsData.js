/**
 * NGFS Phase IV — Canonical parameter definitions, trajectory data, and scenario templates.
 * Source: NGFS Phase IV (2023), IPCC AR6, IEA WEO 2023, ECB PARIS Align.
 * Used by: ParameterConfigurator, TrajectoryVisualizer, NGFSDataBrowser, hooks.
 */

// ---------------------------------------------------------------------------
// NGFS Scenario Families
// ---------------------------------------------------------------------------

export const NGFS_FAMILIES = ['Orderly', 'Disorderly', 'Hot house world'];

export const NGFS_FAMILY_META = {
  Orderly: {
    color:       '#22d3ee',
    bgClass:     'bg-cyan-500/15',
    textClass:   'text-cyan-400',
    borderClass: 'border-cyan-500/30',
    description: 'Climate goals met with coordinated early action; low physical risk, managed transition.',
  },
  Disorderly: {
    color:       '#f59e0b',
    bgClass:     'bg-amber-500/15',
    textClass:   'text-amber-400',
    borderClass: 'border-amber-500/30',
    description: 'Late and abrupt policy shifts; higher transition risk, moderate physical risk.',
  },
  'Hot house world': {
    color:       '#f87171',
    bgClass:     'bg-red-500/15',
    textClass:   'text-red-400',
    borderClass: 'border-red-500/30',
    description: 'Insufficient climate action; high physical risk, low transition pressure.',
  },
};

// ---------------------------------------------------------------------------
// PARAMETER GROUPS — full NGFS Phase IV parameter catalogue
// ---------------------------------------------------------------------------

/**
 * Each parameter:
 *   id, key, label, group, unit, baseline (2024),
 *   min, max, step,
 *   trajectories: { Orderly, Disorderly, 'Hot house world' }
 *     — each is { 2025, 2030, 2035, 2040, 2045, 2050 }
 */
export const PARAMETER_GROUPS = {
  carbon: {
    id:    'carbon',
    label: 'Carbon & Emissions',
    icon:  'leaf',
    color: '#22d3ee',
    params: [
      {
        id: 'carbon_price_usd',
        key: 'carbon_price_usd',
        label: 'Carbon Price',
        unit: '$/tCO2e',
        baseline: 50,
        min: 0,
        max: 500,
        step: 5,
        description: 'Implicit / explicit economy-wide carbon price. NGFS Phase IV central path.',
        trajectories: {
          Orderly:           { 2025: 65,  2030: 120, 2035: 155, 2040: 180, 2045: 190, 2050: 200 },
          Disorderly:        { 2025: 55,  2030: 90,  2035: 150, 2040: 200, 2045: 260, 2050: 300 },
          'Hot house world': { 2025: 25,  2030: 30,  2035: 35,  2040: 38,  2045: 42,  2050: 45  },
        },
      },
      {
        id: 'ghg_emissions_gton',
        key: 'ghg_emissions_gton',
        label: 'Global GHG Emissions',
        unit: 'GtCO2e/yr',
        baseline: 57,
        min: 0,
        max: 70,
        step: 1,
        description: 'Total annual global GHG emissions (Gt CO2e).',
        trajectories: {
          Orderly:           { 2025: 55, 2030: 45, 2035: 35, 2040: 25, 2045: 15, 2050: 5  },
          Disorderly:        { 2025: 57, 2030: 52, 2035: 40, 2040: 28, 2045: 15, 2050: 5  },
          'Hot house world': { 2025: 57, 2030: 58, 2035: 60, 2040: 61, 2045: 62, 2050: 63 },
        },
      },
      {
        id: 'renewable_share_pct',
        key: 'renewable_share_pct',
        label: 'Renewable Energy Share',
        unit: '%',
        baseline: 30,
        min: 0,
        max: 100,
        step: 1,
        description: 'Share of renewables in primary energy supply.',
        trajectories: {
          Orderly:           { 2025: 35, 2030: 50, 2035: 65, 2040: 78, 2045: 88, 2050: 95 },
          Disorderly:        { 2025: 32, 2030: 42, 2035: 58, 2040: 72, 2045: 83, 2050: 90 },
          'Hot house world': { 2025: 31, 2030: 35, 2035: 38, 2040: 42, 2045: 46, 2050: 50 },
        },
      },
    ],
  },

  macro: {
    id:    'macro',
    label: 'Macro Economy',
    icon:  'trending-up',
    color: '#a78bfa',
    params: [
      {
        id: 'gdp_growth_pct',
        key: 'gdp_growth_pct',
        label: 'GDP Growth',
        unit: '% p.a.',
        baseline: 2.8,
        min: -5,
        max: 8,
        step: 0.1,
        description: 'Annual real GDP growth rate (global weighted average).',
        trajectories: {
          Orderly:           { 2025: 2.8, 2030: 2.6, 2035: 2.5, 2040: 2.4, 2045: 2.4, 2050: 2.3 },
          Disorderly:        { 2025: 2.4, 2030: 1.8, 2035: 2.0, 2040: 2.2, 2045: 2.3, 2050: 2.3 },
          'Hot house world': { 2025: 2.7, 2030: 2.3, 2035: 1.8, 2040: 1.4, 2045: 1.0, 2050: 0.6 },
        },
      },
      {
        id: 'inflation_pct',
        key: 'inflation_pct',
        label: 'Inflation Rate',
        unit: '%',
        baseline: 3.2,
        min: -1,
        max: 15,
        step: 0.1,
        description: 'Annual CPI inflation rate.',
        trajectories: {
          Orderly:           { 2025: 2.8, 2030: 2.2, 2035: 2.0, 2040: 2.0, 2045: 2.0, 2050: 2.0 },
          Disorderly:        { 2025: 3.5, 2030: 4.2, 2035: 3.0, 2040: 2.5, 2045: 2.2, 2050: 2.0 },
          'Hot house world': { 2025: 3.0, 2030: 3.5, 2035: 4.0, 2040: 4.5, 2045: 5.0, 2050: 5.5 },
        },
      },
      {
        id: 'interest_rate_pct',
        key: 'interest_rate_pct',
        label: 'Policy Interest Rate',
        unit: '%',
        baseline: 4.5,
        min: 0,
        max: 15,
        step: 0.25,
        description: 'Central bank benchmark policy rate.',
        trajectories: {
          Orderly:           { 2025: 3.5, 2030: 3.0, 2035: 2.8, 2040: 2.8, 2045: 2.8, 2050: 2.8 },
          Disorderly:        { 2025: 4.5, 2030: 5.5, 2035: 4.0, 2040: 3.5, 2045: 3.0, 2050: 3.0 },
          'Hot house world': { 2025: 4.0, 2030: 4.5, 2035: 5.0, 2040: 5.5, 2045: 6.0, 2050: 6.5 },
        },
      },
    ],
  },

  physical: {
    id:    'physical',
    label: 'Physical Climate',
    icon:  'thermometer',
    color: '#f87171',
    params: [
      {
        id: 'temperature_rise_c',
        key: 'temperature_rise_c',
        label: 'Global Temperature Rise',
        unit: '°C above pre-industrial',
        baseline: 1.2,
        min: 0,
        max: 5,
        step: 0.1,
        description: 'GMST warming above 1850–1900 baseline.',
        trajectories: {
          Orderly:           { 2025: 1.3, 2030: 1.5, 2035: 1.6, 2040: 1.6, 2045: 1.6, 2050: 1.6 },
          Disorderly:        { 2025: 1.3, 2030: 1.5, 2035: 1.7, 2040: 1.7, 2045: 1.7, 2050: 1.7 },
          'Hot house world': { 2025: 1.3, 2030: 1.6, 2035: 1.9, 2040: 2.3, 2045: 2.8, 2050: 3.3 },
        },
      },
      {
        id: 'sea_level_rise_mm',
        key: 'sea_level_rise_mm',
        label: 'Sea Level Rise',
        unit: 'mm above 2000',
        baseline: 80,
        min: 0,
        max: 600,
        step: 10,
        description: 'Global mean sea level rise vs year 2000 baseline.',
        trajectories: {
          Orderly:           { 2025: 90,  2030: 110, 2035: 135, 2040: 160, 2045: 185, 2050: 210 },
          Disorderly:        { 2025: 92,  2030: 115, 2035: 145, 2040: 175, 2045: 210, 2050: 250 },
          'Hot house world': { 2025: 95,  2030: 125, 2035: 170, 2040: 230, 2045: 310, 2050: 400 },
        },
      },
      {
        id: 'extreme_heat_freq',
        key: 'extreme_heat_freq',
        label: 'Extreme Heat Events',
        unit: 'x baseline frequency',
        baseline: 1.0,
        min: 0.5,
        max: 10,
        step: 0.1,
        description: 'Frequency of heat waves (≥35°C) relative to 1980–2010 baseline.',
        trajectories: {
          Orderly:           { 2025: 1.3, 2030: 1.6, 2035: 1.8, 2040: 2.0, 2045: 2.1, 2050: 2.2 },
          Disorderly:        { 2025: 1.3, 2030: 1.7, 2035: 2.0, 2040: 2.3, 2045: 2.5, 2050: 2.7 },
          'Hot house world': { 2025: 1.4, 2030: 2.0, 2035: 2.8, 2040: 3.9, 2045: 5.2, 2050: 6.8 },
        },
      },
    ],
  },

  transition: {
    id:    'transition',
    label: 'Transition & Policy',
    icon:  'zap',
    color: '#34d399',
    params: [
      {
        id: 'policy_stringency',
        key: 'policy_stringency',
        label: 'Climate Policy Stringency',
        unit: 'index (0–100)',
        baseline: 40,
        min: 0,
        max: 100,
        step: 1,
        description: 'Composite index of climate policy ambition (ETS, regulations, subsidies).',
        trajectories: {
          Orderly:           { 2025: 55, 2030: 72, 2035: 82, 2040: 90, 2045: 95, 2050: 98 },
          Disorderly:        { 2025: 42, 2030: 55, 2035: 80, 2040: 92, 2045: 96, 2050: 98 },
          'Hot house world': { 2025: 38, 2030: 35, 2035: 33, 2040: 32, 2045: 31, 2050: 30 },
        },
      },
      {
        id: 'fossil_fuel_divestment_pct',
        key: 'fossil_fuel_divestment_pct',
        label: 'Fossil Fuel Divestment',
        unit: '% of peak reserves stranded',
        baseline: 5,
        min: 0,
        max: 80,
        step: 1,
        description: 'Share of fossil fuel reserves stranded relative to peak 2019 reserves.',
        trajectories: {
          Orderly:           { 2025: 8,  2030: 20, 2035: 35, 2040: 48, 2045: 58, 2050: 65 },
          Disorderly:        { 2025: 6,  2030: 15, 2035: 35, 2040: 52, 2045: 64, 2050: 72 },
          'Hot house world': { 2025: 5,  2030: 8,  2035: 10, 2040: 12, 2045: 14, 2050: 16 },
        },
      },
      {
        id: 'ev_penetration_pct',
        key: 'ev_penetration_pct',
        label: 'EV Penetration (New Sales)',
        unit: '% of new car sales',
        baseline: 18,
        min: 0,
        max: 100,
        step: 1,
        description: 'Share of BEV+PHEV in new passenger car registrations globally.',
        trajectories: {
          Orderly:           { 2025: 28, 2030: 55, 2035: 78, 2040: 92, 2045: 98, 2050: 99 },
          Disorderly:        { 2025: 24, 2030: 45, 2035: 72, 2040: 88, 2045: 96, 2050: 99 },
          'Hot house world': { 2025: 20, 2030: 28, 2035: 35, 2040: 42, 2045: 50, 2050: 58 },
        },
      },
    ],
  },

  financial: {
    id:    'financial',
    label: 'Financial Markets',
    icon:  'dollar-sign',
    color: '#fbbf24',
    params: [
      {
        id: 'credit_spread_bps',
        key: 'credit_spread_bps',
        label: 'IG Credit Spread (IG)',
        unit: 'bps',
        baseline: 110,
        min: 50,
        max: 600,
        step: 5,
        description: 'Option-adjusted spread for investment-grade corporate bonds (ICE BofA IG).',
        trajectories: {
          Orderly:           { 2025: 100, 2030: 90,  2035: 85,  2040: 82,  2045: 80,  2050: 78  },
          Disorderly:        { 2025: 130, 2030: 180, 2035: 140, 2040: 110, 2045: 95,  2050: 85  },
          'Hot house world': { 2025: 115, 2030: 140, 2035: 180, 2040: 220, 2045: 270, 2050: 320 },
        },
      },
      {
        id: 'equity_risk_premium_pct',
        key: 'equity_risk_premium_pct',
        label: 'Equity Risk Premium',
        unit: '%',
        baseline: 5.2,
        min: 1,
        max: 15,
        step: 0.1,
        description: 'Equity risk premium (implied ERP via DDM on MSCI World).',
        trajectories: {
          Orderly:           { 2025: 5.0, 2030: 4.8, 2035: 4.6, 2040: 4.5, 2045: 4.5, 2050: 4.4 },
          Disorderly:        { 2025: 5.5, 2030: 6.5, 2035: 6.0, 2040: 5.5, 2045: 5.2, 2050: 5.0 },
          'Hot house world': { 2025: 5.2, 2030: 5.8, 2035: 6.5, 2040: 7.5, 2045: 8.5, 2050: 9.5 },
        },
      },
    ],
  },
};

// Flat list for quick lookup
export const ALL_PARAMETERS = Object.values(PARAMETER_GROUPS).flatMap(g =>
  g.params.map(p => ({ ...p, groupId: g.id, groupLabel: g.label }))
);

// ---------------------------------------------------------------------------
// Scenario Templates
// ---------------------------------------------------------------------------

export const SCENARIO_TEMPLATES = [
  {
    id: 'tpl-ngfs-orderly',
    name: 'NGFS Orderly (Net Zero 2050)',
    description: 'NGFS Phase IV Net Zero 2050 — coordinated early action with 1.5°C limit. Default for stress-testing under Basel III Pillar 2.',
    category: 'ngfs',
    ngfsFamily: 'Orderly',
    tags: ['NGFS', 'Net Zero', 'Basel III', 'TCFD'],
    isOfficial: true,
    author: 'NGFS / IPCC',
    usageCount: 1247,
    createdAt: '2023-09-01',
    parameterOverrides: {},
  },
  {
    id: 'tpl-ngfs-disorderly',
    name: 'NGFS Disorderly (Divergent Net Zero)',
    description: 'NGFS Phase IV Divergent Net Zero — late and fragmented policy, higher transition risk. EBA GL/2022/16 adverse scenario.',
    category: 'ngfs',
    ngfsFamily: 'Disorderly',
    tags: ['NGFS', 'EBA', 'Adverse', 'Transition Risk'],
    isOfficial: true,
    author: 'NGFS / IPCC',
    usageCount: 986,
    createdAt: '2023-09-01',
    parameterOverrides: {},
  },
  {
    id: 'tpl-ngfs-hothouse',
    name: 'NGFS Hot House World',
    description: 'NGFS Phase IV Current Policies — insufficient action, 3°C+ warming, severe physical risk. TCFD severe stress scenario.',
    category: 'ngfs',
    ngfsFamily: 'Hot house world',
    tags: ['NGFS', 'Physical Risk', 'TCFD', 'Severe'],
    isOfficial: true,
    author: 'NGFS / IPCC',
    usageCount: 874,
    createdAt: '2023-09-01',
    parameterOverrides: {},
  },
  {
    id: 'tpl-early-aggressive',
    name: 'Early Aggressive Transition',
    description: 'Accelerated decarbonisation: carbon price reaches $300/tCO2e by 2035, EV penetration 90% by 2040. Stress-tests fossil-exposed portfolios.',
    category: 'custom',
    ngfsFamily: 'Disorderly',
    tags: ['Custom', 'Stranded Assets', 'High Carbon Price', 'Energy Transition'],
    isOfficial: false,
    author: 'A2 Intelligence',
    usageCount: 312,
    createdAt: '2024-06-15',
    parameterOverrides: {
      carbon_price_usd: { 2030: 180, 2035: 300, 2040: 350, 2045: 380, 2050: 400 },
      ev_penetration_pct: { 2030: 65, 2035: 90, 2040: 98, 2050: 100 },
    },
  },
  {
    id: 'tpl-delayed-warming',
    name: 'Delayed Policy — High Physical',
    description: 'Low policy ambition through 2035 followed by crash transition; combines severe physical risk exposure with elevated transition shock.',
    category: 'stress',
    ngfsFamily: 'Hot house world',
    tags: ['Stress', 'Physical Risk', 'Tail Risk', 'CRREM'],
    isOfficial: false,
    author: 'A2 Intelligence',
    usageCount: 198,
    createdAt: '2024-08-20',
    parameterOverrides: {
      temperature_rise_c: { 2040: 2.8, 2050: 4.0 },
      carbon_price_usd:   { 2035: 80, 2040: 220, 2050: 350 },
    },
  },
  {
    id: 'tpl-eba-baseline',
    name: 'EBA Baseline (GL/2022/16)',
    description: 'EBA Guidelines baseline scenario for climate stress testing of EU credit institutions. Aligns with ECB PARIS Align methodology.',
    category: 'regulatory',
    ngfsFamily: 'Orderly',
    tags: ['EBA', 'Regulatory', 'EU', 'PARIS Align', 'ECB'],
    isOfficial: true,
    author: 'EBA / ECB',
    usageCount: 521,
    createdAt: '2023-12-01',
    parameterOverrides: {},
  },
  {
    id: 'tpl-eba-adverse',
    name: 'EBA Adverse (GL/2022/16)',
    description: 'EBA adverse stress scenario with disorderly transition shock + elevated physical risk. Required for EU climate stress testing.',
    category: 'regulatory',
    ngfsFamily: 'Disorderly',
    tags: ['EBA', 'Regulatory', 'EU', 'Adverse', 'Stress Test'],
    isOfficial: true,
    author: 'EBA / ECB',
    usageCount: 489,
    createdAt: '2023-12-01',
    parameterOverrides: {
      carbon_price_usd:  { 2030: 150, 2035: 250, 2040: 320, 2050: 400 },
      credit_spread_bps: { 2025: 160, 2030: 220, 2040: 180, 2050: 140 },
    },
  },
  {
    id: 'tpl-real-estate-crrem',
    name: 'CRREM 1.5°C Pathway',
    description: 'Carbon Risk Real Estate Monitor 1.5°C energy intensity pathway for EU real estate portfolios. Aligned with GRESB & CRREM v2.0.',
    category: 'regulatory',
    ngfsFamily: 'Orderly',
    tags: ['CRREM', 'Real Estate', 'Energy Intensity', 'GRESB', '1.5°C'],
    isOfficial: true,
    author: 'CRREM / GRESB',
    usageCount: 267,
    createdAt: '2024-01-15',
    parameterOverrides: {
      renewable_share_pct: { 2030: 65, 2040: 90, 2050: 100 },
    },
  },
];

// ---------------------------------------------------------------------------
// NGFS Variable Catalogue (for NGFSDataBrowser)
// ---------------------------------------------------------------------------

export const NGFS_VARIABLES = [
  { id: 'v-carbon-price',   name: 'Carbon Price',             family: 'all',              region: 'Global',  unit: '$/tCO2e',         paramId: 'carbon_price_usd',         source: 'NGFS/REMIND-MAgPIE', lastUpdated: '2023-09' },
  { id: 'v-ghg',            name: 'GHG Emissions',            family: 'all',              region: 'Global',  unit: 'GtCO2e/yr',       paramId: 'ghg_emissions_gton',       source: 'NGFS/GCAM',          lastUpdated: '2023-09' },
  { id: 'v-renewable',      name: 'Renewable Share',          family: 'all',              region: 'Global',  unit: '%',               paramId: 'renewable_share_pct',      source: 'NGFS/IEA',           lastUpdated: '2023-09' },
  { id: 'v-gdp',            name: 'GDP Growth',               family: 'all',              region: 'Global',  unit: '% p.a.',          paramId: 'gdp_growth_pct',           source: 'NGFS/IMF',           lastUpdated: '2023-09' },
  { id: 'v-temp',           name: 'Temperature Rise',         family: 'all',              region: 'Global',  unit: '°C',              paramId: 'temperature_rise_c',       source: 'NGFS/MAGICC',        lastUpdated: '2023-09' },
  { id: 'v-sea-level',      name: 'Sea Level Rise',           family: 'Hot house world',  region: 'Global',  unit: 'mm',              paramId: 'sea_level_rise_mm',        source: 'NGFS/IPCC AR6',      lastUpdated: '2023-09' },
  { id: 'v-policy',         name: 'Policy Stringency Index',  family: 'all',              region: 'Global',  unit: 'Index 0–100',     paramId: 'policy_stringency',        source: 'NGFS/Climate Policy Radar', lastUpdated: '2023-09' },
  { id: 'v-ev',             name: 'EV Penetration',           family: 'Orderly',          region: 'Global',  unit: '%',               paramId: 'ev_penetration_pct',       source: 'NGFS/IEA EV Outlook',lastUpdated: '2023-09' },
  { id: 'v-credit-spread',  name: 'IG Credit Spread',         family: 'all',              region: 'Global',  unit: 'bps',             paramId: 'credit_spread_bps',        source: 'ECB PARIS Align',    lastUpdated: '2023-12' },
];

// ---------------------------------------------------------------------------
// Helper utilities
// ---------------------------------------------------------------------------

/**
 * Build a trajectory array for a parameter + NGFS family + optional overrides.
 * Returns array of { year, value } for 2025–2050 in 5-year steps.
 */
export function buildTrajectory(paramId, ngfsFamily, overrides = {}) {
  const param = ALL_PARAMETERS.find(p => p.id === paramId);
  if (!param) return [];
  const base = param.trajectories?.[ngfsFamily] || {};
  const years = [2025, 2030, 2035, 2040, 2045, 2050];
  return years.map(yr => ({
    year: yr,
    value: overrides[yr] !== undefined ? overrides[yr] : (base[yr] ?? param.baseline),
    isEdited: overrides[yr] !== undefined,
  }));
}

/**
 * Build initial scenario parameters for a given template.
 */
export function buildScenarioParams(template) {
  return ALL_PARAMETERS.map(p => ({
    ...p,
    value:      template.ngfsFamily ? (p.trajectories?.[template.ngfsFamily]?.[2050] ?? p.baseline) : p.baseline,
    trajectory: buildTrajectory(p.id, template.ngfsFamily || 'Orderly', template.parameterOverrides?.[p.id] || {}),
  }));
}

/**
 * Get a default empty scenario state.
 */
export function emptyScenario() {
  return {
    id:             null,
    name:           'Unnamed Scenario',
    description:    '',
    category:       'custom',
    ngfsFamily:     'Orderly',
    timeHorizon:    2050,
    status:         'draft',
    tags:           [],
    baseTemplateId: null,
    parameters:     buildScenarioParams({ ngfsFamily: 'Orderly', parameterOverrides: {} }),
    versions:       [],
    createdAt:      new Date().toISOString(),
    updatedAt:      new Date().toISOString(),
  };
}
