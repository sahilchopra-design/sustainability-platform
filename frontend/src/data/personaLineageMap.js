/**
 * personaLineageMap.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Single source of truth for the complete lineage:
 *   Persona → Modules used → Form fields → API endpoint → DB tables → Migration
 *
 * Consumed by:
 *   - PersonaTemplatesPage  (Lineage tab)
 *   - DATA_CATALOG.md       (auto-generated reference)
 */

import { ALL_PERSONAS } from './personaSeeds';
import { MODULE_SCHEMAS } from './templateUtils';

// ─────────────────────────────────────────────────────────────────────────────
// MODULE REGISTRY — 30 modules × full metadata
// ─────────────────────────────────────────────────────────────────────────────
export const MODULE_REGISTRY = {
  // ── Core analytics ──────────────────────────────────────────────────────────
  portfolio: {
    label: 'Portfolio Analytics',
    route: '/portfolio-analytics',
    apiPrefix: '/api/pg/portfolios',
    dbTables: ['portfolios_pg', 'assets', 'analysis_runs'],
    migration: '001–005',
    category: 'Analytics',
    description: 'Portfolio CRUD, scenario comparison, VaR, TCFD dashboard',
  },
  scenario: {
    label: 'Scenario Analysis',
    route: '/scenarios',
    apiPrefix: '/api/v1/scenarios',
    dbTables: ['scenarios', 'scenario_versions', 'scenario_impacts'],
    migration: '001–005',
    category: 'Analytics',
    description: 'NGFS v4/v5 scenario library, impact calculations',
  },
  climate_risk: {
    label: 'Climate Risk Engine',
    route: '/climate-risk',
    apiPrefix: '/api/v1/climate-risk',
    dbTables: ['climate_assessment_runs', 'physical_risk_assessments', 'transition_risk_assessments'],
    migration: '010 / 043',
    category: 'Risk',
    description: 'Physical & transition risk per entity; NGFS scenario overlay',
  },
  financial_risk: {
    label: 'Financial Risk (ECL / PCAF)',
    route: '/financial-risk',
    apiPrefix: '/api/v1/ecl',
    dbTables: ['ecl_assessments', 'ecl_exposures', 'ecl_scenario_results', 'ecl_climate_overlays', 'pcaf_portfolios', 'pcaf_investees', 'pcaf_results', 'temperature_scores'],
    migration: '006',
    category: 'Risk',
    description: 'IFRS 9 ECL staging, PCAF financed emissions, temperature alignment',
  },
  stress_testing: {
    label: 'Stress Testing',
    route: '/stress-testing',
    apiPrefix: '/api/v1/stress-testing',
    dbTables: ['ecl_assessments', 'ecl_scenario_results', 'ecl_climate_overlays'],
    migration: '006',
    category: 'Risk',
    description: 'EBA GL/2017/16 ICAAP climate stress, adverse + severely adverse scenarios',
  },
  monte_carlo: {
    label: 'Monte Carlo Simulation',
    route: '/monte-carlo',
    apiPrefix: '/api/v1/monte-carlo',
    dbTables: ['analysis_runs'],
    migration: '001',
    category: 'Risk',
    description: 'P5/P95 VaR, tail risk, correlated scenario sampling',
  },

  // ── Emissions & carbon ──────────────────────────────────────────────────────
  carbon: {
    label: 'Carbon Calculator',
    route: '/carbon',
    apiPrefix: '/api/v1/carbon',
    dbTables: ['carbon_calculation_runs'],
    migration: '001',
    category: 'Emissions',
    description: 'Scope 1/2/3 GHG Protocol calculations; SBTi gap analysis',
  },
  supply_chain: {
    label: 'Supply Chain (Scope 3)',
    route: '/supply-chain',
    apiPrefix: '/api/v1/supply-chain',
    dbTables: ['sc_entities', 'scope3_assessments', 'scope3_activities', 'sbti_targets', 'sbti_trajectories', 'emission_factor_library', 'supply_chain_tiers'],
    migration: '007',
    category: 'Emissions',
    description: 'Scope 3 category-level, SBTi target setting, emission factor library',
  },
  dcm: {
    label: 'DCM Methodology Engine',
    route: '/dcm',
    apiPrefix: '/api/v1/dcm',
    dbTables: ['dcm_methodology_runs'],
    migration: '001',
    category: 'Emissions',
    description: '56 CDM/VCS/Gold Standard methodologies; carbon credit quantification',
  },

  // ── Regulatory ──────────────────────────────────────────────────────────────
  regulatory: {
    label: 'Regulatory Reporting',
    route: '/regulatory',
    apiPrefix: '/api/v1/regulatory',
    dbTables: ['regulatory_entities', 'sfdr_pai_disclosures', 'eu_taxonomy_assessments', 'eu_taxonomy_activities', 'tcfd_assessments', 'csrd_readiness', 'issb_assessments', 'brsr_disclosures', 'regulatory_action_plans'],
    migration: '009',
    category: 'Regulatory',
    description: 'SFDR PAI, EU Taxonomy, TCFD, CSRD, ISSB S1/S2, BRSR, SF Taxonomies',
  },
  gar_ets: {
    label: 'GAR & EU ETS',
    route: '/gar-ets',
    apiPrefix: '/api/v1/gar',
    dbTables: ['eu_ets_installations', 'eu_ets_allocations', 'eu_ets_compliance', 'eu_ets_price_forecasts', 'brsr_entity_disclosures', 'compiled_regulatory_reports'],
    migration: '044',
    category: 'Regulatory',
    description: 'EBA Pillar 3 GAR/BTAR, EU ETS Phase IV free allocation, ETS 2 readiness',
  },
  sfdr_pai: {
    label: 'SFDR PAI',
    route: '/regulatory',
    apiPrefix: '/api/v1/regulatory/sfdr-pai',
    dbTables: ['sfdr_pai_disclosures', 'regulatory_entities'],
    migration: '009',
    category: 'Regulatory',
    description: 'Article 4 RTS 18 mandatory PAI indicators; Article 8/9 fund disclosures',
  },
  double_materiality: {
    label: 'Double Materiality (DMA)',
    route: '/double-materiality',
    apiPrefix: '/api/v1/csrd/materiality',
    dbTables: ['csrd_materiality_topics', 'csrd_entity_registry', 'csrd_gap_tracker', 'csrd_disclosure_index'],
    migration: '013',
    category: 'Regulatory',
    description: 'EFRAG DMA — impact materiality + financial materiality, IRO identification',
  },
  eu_regulatory: {
    label: 'EU Regulatory Hub (EUDR / CSDDD)',
    route: '/eu-regulatory',
    apiPrefix: '/api/v1/eudr',
    dbTables: ['eudr_operators', 'eudr_due_diligence', 'eudr_commodity_lots', 'csddd_entities', 'csddd_assessments', 'csddd_adverse_impacts'],
    migration: '045 / 046',
    category: 'Regulatory',
    description: 'EUDR commodity due diligence (Annex I), CSDDD Art 2–29 compliance',
  },
  banking_capital: {
    label: 'Banking & Capital (Basel IV)',
    route: '/banking-capital',
    apiPrefix: '/api/v1/banking-capital',
    dbTables: ['fi_entities', 'fi_financials', 'fi_loan_books', 'fi_green_finance', 'fi_financed_emissions', 'fi_paris_alignment', 'fi_csrd_e1_climate', 'fi_csrd_s1_workforce', 'fi_csrd_g1_governance', 'fi_eu_taxonomy_kpis'],
    migration: '011',
    category: 'Regulatory',
    description: 'SA / IRB credit RWA, LCR, NSFR, CET1/AT1/T2, FRTB; FI CSRD ESRS',
  },
  sovereign_climate: {
    label: 'Sovereign Climate Risk',
    route: '/sovereign-climate',
    apiPrefix: '/api/v1/sovereign-climate-risk',
    dbTables: ['sovereign_climate_assessments', 'sovereign_portfolio_assessments'],
    migration: '046',
    category: 'Risk',
    description: '51-country profiles, NGFS scenario notch adjustments, portfolio climate VaR',
  },
  country_risk: {
    label: 'Country Risk',
    route: '/country-risk',
    apiPrefix: '/api/v1/country-risk',
    dbTables: ['sovereign_climate_assessments'],
    migration: '046',
    category: 'Risk',
    description: 'Sovereign risk composite scoring; ND-GAIN, NDC ambition, fiscal resilience',
  },

  // ── Nature & real estate ────────────────────────────────────────────────────
  nature_risk: {
    label: 'Nature Risk (TNFD LEAP)',
    route: '/nature-risk',
    apiPrefix: '/api/v1/nature-risk',
    dbTables: ['nature_assessments', 'nature_re_assessments', 'spatial_hazard_profiles'],
    migration: '010 / 043',
    category: 'Nature',
    description: 'TNFD LEAP 4-phase, water risk, biodiversity, BNG DEFRA Metric 4.0',
  },
  real_estate: {
    label: 'Real Estate (RICS / CRREM)',
    route: '/real-estate-assessment',
    apiPrefix: '/api/v1/real-estate',
    dbTables: ['residential_re_valuations', 'rics_esg_assessments', 'spatial_hazard_profiles', 'nature_re_assessments'],
    migration: '043',
    category: 'Nature',
    description: 'RICS ESG guidance, CRREM pathways, spatial hazard overlays',
  },
  residential_re: {
    label: 'Residential RE (CRREM / RICS)',
    route: '/residential-re',
    apiPrefix: '/api/v1/residential-re',
    dbTables: ['residential_re_valuations', 'rics_esg_assessments'],
    migration: '043',
    category: 'Nature',
    description: 'Mortgage book EPC/EUI, CRREM 2030/2050 targets, green mortgage tracking',
  },
  valuation: {
    label: 'Asset Valuation',
    route: '/valuation',
    apiPrefix: '/api/v1/valuation',
    dbTables: ['valuation_assets', 'unified_valuations', 'method_results', 'esg_adjustments', 'climate_valuation_adjustments', 'comparable_sales', 'audit_log'],
    migration: '010',
    category: 'Nature',
    description: 'Income / Cost / Sales comparison; ESG uplift, climate haircut adjustments',
  },

  // ── Energy & industry ───────────────────────────────────────────────────────
  energy_transition: {
    label: 'Energy Transition',
    route: '/energy-transition',
    apiPrefix: '/api/v1/energy-transition',
    dbTables: ['energy_generation_mix', 'energy_renewable_pipeline', 'energy_stranded_assets_register', 'energy_csrd_e1_climate'],
    migration: '012',
    category: 'Energy',
    description: 'Fleet transition optimiser, grid emission factors, avoided emissions, OGMP',
  },
  project_finance: {
    label: 'Project Finance',
    route: '/project-finance',
    apiPrefix: '/api/v1/project-finance',
    dbTables: ['valuation_assets', 'unified_valuations', 'method_results'],
    migration: '010',
    category: 'Energy',
    description: 'DSCR/LLCR, blended finance, green bond structuring, concessionality calc',
  },
  stranded_assets: {
    label: 'Stranded Assets',
    route: '/stranded-assets',
    apiPrefix: '/api/v1/stranded-assets',
    dbTables: ['energy_stranded_assets_register', 'ecl_assessments'],
    migration: '012 / 046',
    category: 'Energy',
    description: 'Carbon stranding risk for reserves, power plants, infrastructure, tech',
  },
  sector_assessments: {
    label: 'Sector Assessments',
    route: '/sector-assessments',
    apiPrefix: '/api/v1/sector',
    dbTables: ['data_centre_facilities', 'data_centre_assessments', 'cat_risk_properties', 'cat_risk_assessments', 'cat_risk_climate_scenarios', 'power_plants', 'power_plant_assessments', 'power_plant_trajectories'],
    migration: '008',
    category: 'Energy',
    description: 'Data centre PUE/WUE, CAT risk NatCat, power plant stranding trajectories',
  },
  energy_finance: {
    label: 'Energy Finance (LCOE / PPA)',
    route: '/energy-finance',
    apiPrefix: '/api/v1/energy-finance',
    dbTables: ['valuation_assets', 'unified_valuations'],
    migration: '010',
    category: 'Energy',
    description: 'Levelised cost modelling, PPA structuring, Wind/Solar/Battery financials',
  },
  green_hydrogen: {
    label: 'Green Hydrogen (RFNBO)',
    route: '/green-hydrogen',
    apiPrefix: '/api/v1/green-hydrogen',
    dbTables: [],
    migration: 'n/a',
    category: 'Energy',
    description: 'LCOH, electrolyser sizing, RFNBO additivity, H2 blending economics',
  },

  // ── Sustainability ───────────────────────────────────────────────────────────
  sustainability: {
    label: 'Sustainability (GRESB)',
    route: '/sustainability',
    apiPrefix: '/api/v1/sustainability',
    dbTables: ['regulatory_entities', 'sfdr_pai_disclosures'],
    migration: '009',
    category: 'ESG',
    description: 'GRESB, LEED, BREEAM, WELL, NABERS, CASBEE portfolio scoring',
  },
  asset_management: {
    label: 'Asset Management (PACTA)',
    route: '/asset-management',
    apiPrefix: '/api/v1/am',
    dbTables: ['am_assessments'],
    migration: '040',
    category: 'Analytics',
    description: 'ESG attribution, Paris alignment PACTA, green bond GBS/EU GBS screening',
  },
  technology_risk: {
    label: 'Technology Risk',
    route: '/technology-risk',
    apiPrefix: '/api/v1/factor-overlays/ecl-credit',
    dbTables: [],
    migration: 'Factor Overlay Engine',
    category: 'Risk',
    description: 'Automation disruption (19 NACE sectors), AI adoption, Fintech NIM compression',
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// PERSONA × MODULE matrix — which personas actively use which modules
// ─────────────────────────────────────────────────────────────────────────────
export function getPersonaModuleMatrix() {
  const moduleKeys = Object.keys(MODULE_REGISTRY);
  return ALL_PERSONAS.map(persona => {
    const activeModules = moduleKeys.filter(mk => !!persona.modules?.[mk]);
    return {
      personaId: persona.id,
      personaName: persona.name,
      institution: persona.institution,
      sector: persona.sector,
      role: persona.role,
      colour: persona.colour,
      logo: persona.logo,
      tagline: persona.tagline,
      activeModules,
      moduleCount: activeModules.length,
    };
  });
}

// ─────────────────────────────────────────────────────────────────────────────
// DB TABLE INDEX — which personas feed data into each table
// ─────────────────────────────────────────────────────────────────────────────
export function getDbTableIndex() {
  const index = {}; // tableName → { modules: Set, personas: Set }
  ALL_PERSONAS.forEach(persona => {
    Object.entries(persona.modules || {}).forEach(([moduleKey]) => {
      const reg = MODULE_REGISTRY[moduleKey];
      if (!reg) return;
      reg.dbTables.forEach(table => {
        if (!index[table]) index[table] = { modules: new Set(), personas: new Set(), migration: reg.migration, category: reg.category };
        index[table].modules.add(moduleKey);
        index[table].personas.add(persona.id);
      });
    });
  });
  // Convert Sets to arrays
  return Object.entries(index).map(([table, info]) => ({
    table,
    modules: [...info.modules],
    personas: [...info.personas],
    migration: info.migration,
    category: info.category,
  })).sort((a, b) => a.table.localeCompare(b.table));
}

// ─────────────────────────────────────────────────────────────────────────────
// Full lineage trace for a specific persona
// ─────────────────────────────────────────────────────────────────────────────
export function getPersonaLineage(personaId) {
  const persona = ALL_PERSONAS.find(p => p.id === personaId);
  if (!persona) return null;

  const moduleChains = Object.entries(persona.modules || {}).map(([moduleKey, moduleData]) => {
    const reg = MODULE_REGISTRY[moduleKey];
    const schema = MODULE_SCHEMAS?.[moduleKey];
    return {
      moduleKey,
      moduleLabel: reg?.label || moduleKey,
      route: reg?.route || '',
      apiEndpoint: schema?.apiEndpoint || reg?.apiPrefix || '',
      dbTables: reg?.dbTables || [],
      migration: reg?.migration || '',
      category: reg?.category || 'Other',
      sampleFields: Object.keys(moduleData || {}).slice(0, 6),
      fieldCount: Object.keys(moduleData || {}).length,
    };
  });

  return { persona, moduleChains };
}

// Category colour map for UI
export const CATEGORY_COLOURS = {
  Analytics:  { bg: 'bg-blue-100',    text: 'text-blue-800',    border: 'border-blue-200' },
  Risk:       { bg: 'bg-red-100',     text: 'text-red-800',     border: 'border-red-200' },
  Emissions:  { bg: 'bg-amber-100',   text: 'text-amber-800',   border: 'border-amber-200' },
  Regulatory: { bg: 'bg-purple-100',  text: 'text-purple-800',  border: 'border-purple-200' },
  Nature:     { bg: 'bg-emerald-100', text: 'text-emerald-800', border: 'border-emerald-200' },
  Energy:     { bg: 'bg-orange-100',  text: 'text-orange-800',  border: 'border-orange-200' },
  ESG:        { bg: 'bg-green-100',   text: 'text-green-800',   border: 'border-green-200' },
};
