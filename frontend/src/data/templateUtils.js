/**
 * templateUtils.js
 * ─────────────────────────────────────────────────────────────────────────────
 * Generates downloadable CSV / JSON templates for each module, pre-filled with
 * every persona's data for that module.  Used by PersonaTemplatesPage.
 *
 * Usage:
 *   import { downloadCsvTemplate, downloadJsonTemplate, MODULE_SCHEMAS } from './templateUtils';
 *   downloadCsvTemplate('climate_risk');
 */

import { ALL_PERSONAS } from './personaSeeds';

// ─────────────────────────────────────────────────────────────────────────────
// Schema: every field a module accepts, with header label + default value
// ─────────────────────────────────────────────────────────────────────────────
export const MODULE_SCHEMAS = {
  climate_risk: {
    label: 'Climate Risk Engine',
    description: 'Physical & transition risk assessment per entity',
    apiEndpoint: '/api/v1/climate-risk/physical',
    dbTables: ['climate_assessment_runs', 'physical_risk_assessments', 'transition_risk_assessments'],
    migration: '010 / 043',
    fields: [
      { key: 'entity_id',              label: 'Entity ID',                    default: 'ENT-001',     type: 'string' },
      { key: 'entity_name',            label: 'Entity Name',                  default: '',            type: 'string' },
      { key: 'entity_type',            label: 'Entity Type',                  default: 'counterparty',type: 'enum', options: ['counterparty','asset','security','fund','portfolio'] },
      { key: 'sector_nace',            label: 'NACE Sector Code',             default: 'K64',         type: 'string' },
      { key: 'latitude',               label: 'Latitude',                     default: '',            type: 'number' },
      { key: 'longitude',              label: 'Longitude',                    default: '',            type: 'number' },
      { key: 'country',                label: 'Country ISO2',                 default: 'DE',          type: 'string' },
      { key: 'asset_value_eur',        label: 'Asset Value (EUR)',            default: '',            type: 'number' },
      { key: 'annual_revenue_eur',     label: 'Annual Revenue (EUR)',         default: '',            type: 'number' },
      { key: 'carbon_intensity_tco2_eur', label: 'Carbon Intensity (tCO2/EUR)', default: '',         type: 'number' },
      { key: 'flood_zone',             label: 'In Flood Zone (true/false)',   default: 'false',       type: 'boolean' },
      { key: 'capex_green_pct',        label: 'Green CapEx %',                default: '',            type: 'number' },
      { key: 'scenario',               label: 'NGFS Scenario',                default: 'net_zero_2050', type: 'enum', options: ['net_zero_2050','below_2c','delayed_transition','current_policies','nationally_determined'] },
      { key: 'time_horizon',           label: 'Time Horizon (years)',         default: '10',          type: 'enum', options: ['5','10','20','30'] },
      { key: 'physicalRiskScore',      label: 'Physical Risk Score (0–10)',   default: '',            type: 'number' },
      { key: 'transitionRiskScore',    label: 'Transition Risk Score (0–10)', default: '',            type: 'number' },
    ],
  },

  gar_ets: {
    label: 'GAR & EU ETS',
    description: 'Green Asset Ratio and EU ETS compliance',
    apiEndpoint: '/api/v1/gar/calculate',
    dbTables: ['eu_ets_installations', 'eu_ets_allocations', 'eu_ets_compliance', 'compiled_regulatory_reports'],
    migration: '044',
    fields: [
      { key: 'installationId',         label: 'Installation ID',             default: 'INST-001',    type: 'string' },
      { key: 'sector',                 label: 'ETS Sector',                  default: 'Iron & Steel',type: 'string' },
      { key: 'benchmark',              label: 'Benchmark Product',           default: 'hot_metal',   type: 'string' },
      { key: 'hal',                    label: 'Historical Activity Level (t/yr)', default: '',       type: 'number' },
      { key: 'year',                   label: 'Compliance Year',             default: '2025',        type: 'number' },
      { key: 'carbonLeakage',          label: 'Carbon Leakage Sector (true/false)', default: 'true', type: 'boolean' },
      { key: 'carbonPrice',            label: 'EUA Price (€/t)',             default: '80',          type: 'number' },
      { key: 'totalAssets',            label: 'Total Assets (EUR)',          default: '',            type: 'number' },
      { key: 'taxonomyEligiblePct',    label: 'Taxonomy Eligible %',         default: '',            type: 'number' },
      { key: 'taxonomyAlignedPct',     label: 'Taxonomy Aligned % (GAR)',    default: '',            type: 'number' },
      { key: 'residentialMortgages',   label: 'Residential Mortgages (EUR)', default: '',            type: 'number' },
      { key: 'commercialRE',           label: 'Commercial RE Loans (EUR)',   default: '',            type: 'number' },
      { key: 'corporateLoans',         label: 'Corporate Loans (EUR)',       default: '',            type: 'number' },
      { key: 'smeLoans',               label: 'SME Loans (EUR)',             default: '',            type: 'number' },
      { key: 'greenBondHoldings',      label: 'Green Bond Holdings (EUR)',   default: '',            type: 'number' },
    ],
  },

  energy_transition: {
    label: 'Energy Transition',
    description: 'Fleet transition, grid emission factors, avoided emissions',
    apiEndpoint: '/api/v1/energy-transition/fleet',
    dbTables: ['energy_generation_mix', 'energy_renewable_pipeline', 'energy_stranded_assets_register'],
    migration: '012',
    fields: [
      { key: 'country',                label: 'Country ISO2',                default: 'DE',          type: 'string' },
      { key: 'scenario',               label: 'NGFS Scenario',               default: 'net_zero_2050', type: 'enum', options: ['net_zero_2050','below_2c','delayed_transition','current_policies'] },
      { key: 'targetYear',             label: 'Target Year',                 default: '2040',        type: 'number' },
      { key: 'plant_name',             label: 'Plant Name',                  default: '',            type: 'string' },
      { key: 'plant_type',             label: 'Plant Type',                  default: 'coal',        type: 'enum', options: ['coal','gas','oil','nuclear','solar','wind_onshore','wind_offshore','hydro','biomass','ccgt'] },
      { key: 'capacity_mw',            label: 'Installed Capacity (MW)',     default: '',            type: 'number' },
      { key: 'capacity_factor',        label: 'Capacity Factor (0–1)',       default: '0.35',        type: 'number' },
      { key: 'book_value_m',           label: 'Book Value (EUR M)',          default: '',            type: 'number' },
      { key: 'remaining_life_yr',      label: 'Remaining Asset Life (yrs)',  default: '',            type: 'number' },
      { key: 'co2_intensity',          label: 'CO2 Intensity (tCO2/MWh)',    default: '',            type: 'number' },
    ],
  },

  project_finance: {
    label: 'Project Finance',
    description: 'DSCR, LLCR, blended finance, green bond structuring',
    apiEndpoint: '/api/v1/project-finance/assess',
    dbTables: ['valuation_assets', 'unified_valuations', 'method_results'],
    migration: '010',
    fields: [
      { key: 'projectName',            label: 'Project Name',                default: '',            type: 'string' },
      { key: 'projectType',            label: 'Project Type',                default: 'solar',       type: 'enum', options: ['solar','wind_onshore','wind_offshore','hydro','geothermal','battery_storage','green_hydrogen','other_renewables'] },
      { key: 'country',                label: 'Country ISO2',                default: 'DE',          type: 'string' },
      { key: 'capexM',                 label: 'Total CapEx (EUR M)',          default: '',            type: 'number' },
      { key: 'capacityMW',             label: 'Installed Capacity (MW)',      default: '',            type: 'number' },
      { key: 'debtPct',                label: 'Debt / Total Funding (%)',     default: '70',          type: 'number' },
      { key: 'interestRate',           label: 'Interest Rate (%)',            default: '4.5',         type: 'number' },
      { key: 'loanTermYears',          label: 'Loan Tenor (years)',           default: '18',          type: 'number' },
      { key: 'ppaPrice',               label: 'PPA Price (USD/MWh)',          default: '',            type: 'number' },
      { key: 'ppaTerm',                label: 'PPA Tenor (years)',            default: '15',          type: 'number' },
      { key: 'opexM',                  label: 'Annual OpEx (EUR M)',          default: '',            type: 'number' },
      { key: 'constructionYears',      label: 'Construction Period (years)',  default: '2',           type: 'number' },
    ],
  },

  nature_risk: {
    label: 'Nature Risk (TNFD LEAP)',
    description: 'TNFD LEAP assessment, water risk, biodiversity net gain',
    apiEndpoint: '/api/v1/nature-risk/leap',
    dbTables: ['nature_assessments', 'nature_re_assessments', 'spatial_hazard_profiles'],
    migration: '010 / 043',
    fields: [
      { key: 'entity',                 label: 'Entity / Site Name',          default: '',            type: 'string' },
      { key: 'sector',                 label: 'Sector (NACE)',                default: '',            type: 'string' },
      { key: 'tnfdLeapPhase',          label: 'TNFD LEAP Phase',             default: 'locate',      type: 'enum', options: ['locate','evaluate','assess','prepare'] },
      { key: 'country',                label: 'Country ISO2',                default: '',            type: 'string' },
      { key: 'latitude',               label: 'Latitude',                    default: '',            type: 'number' },
      { key: 'longitude',              label: 'Longitude',                   default: '',            type: 'number' },
      { key: 'exposedSectors',         label: 'Exposed Sectors (comma-sep)', default: '',            type: 'string' },
      { key: 'waterRiskScore',         label: 'Water Risk Score (0–10)',      default: '',            type: 'number' },
      { key: 'biodiversityRiskScore',  label: 'Biodiversity Risk Score (0–10)', default: '',         type: 'number' },
      { key: 'physicalRiskScore',      label: 'Physical Risk Score (0–10)',   default: '',            type: 'number' },
      { key: 'transitionRiskScore',    label: 'Transition Risk Score (0–10)', default: '',           type: 'number' },
    ],
  },

  sustainability: {
    label: 'Sustainability (GRESB / LEED / BREEAM)',
    description: 'Portfolio sustainability scoring and green building certifications',
    apiEndpoint: '/api/v1/sustainability/gresb',
    dbTables: ['regulatory_entities', 'sfdr_pai_disclosures'],
    migration: '009',
    fields: [
      { key: 'portfolio_name',         label: 'Portfolio Name',              default: '',            type: 'string' },
      { key: 'entity_type',            label: 'Entity Type',                 default: 'standing_investments', type: 'enum', options: ['standing_investments','development'] },
      { key: 'region',                 label: 'Region',                      default: 'europe',      type: 'enum', options: ['europe','north_america','asia_pacific','global'] },
      { key: 'total_aum',              label: 'Total AUM (EUR)',              default: '',            type: 'number' },
      { key: 'num_assets',             label: 'Number of Assets',            default: '',            type: 'number' },
      { key: 'score_management',       label: 'GRESB Score: Management',     default: '',            type: 'number' },
      { key: 'score_policy',           label: 'GRESB Score: Policy',         default: '',            type: 'number' },
      { key: 'score_risk_management',  label: 'GRESB Score: Risk Mgmt',      default: '',            type: 'number' },
      { key: 'score_stakeholder',      label: 'GRESB Score: Stakeholder Eng.',default: '',           type: 'number' },
      { key: 'score_performance',      label: 'GRESB Score: Performance Ind.',default: '',           type: 'number' },
    ],
  },

  financial_risk: {
    label: 'Financial Risk (ECL / PCAF)',
    description: 'IFRS 9 Expected Credit Loss and PCAF financed emissions',
    apiEndpoint: '/api/v1/ecl/calculate',
    dbTables: ['ecl_assessments', 'ecl_exposures', 'ecl_scenario_results', 'ecl_climate_overlays', 'pcaf_portfolios', 'pcaf_investees', 'pcaf_results'],
    migration: '006',
    fields: [
      { key: 'entityName',             label: 'Entity Name',                 default: '',            type: 'string' },
      { key: 'exposure',               label: 'Gross Exposure (EUR)',         default: '',            type: 'number' },
      { key: 'pd',                     label: 'Probability of Default (0–1)', default: '',           type: 'number' },
      { key: 'lgd',                    label: 'Loss Given Default (0–1)',     default: '',            type: 'number' },
      { key: 'stage2',                 label: 'Stage 2 % of Exposure',       default: '',            type: 'number' },
      { key: 'stage3',                 label: 'Stage 3 % of Exposure',       default: '',            type: 'number' },
    ],
  },

  banking_capital: {
    label: 'Banking & Capital (Basel IV)',
    description: 'SA/IRB credit RWA, LCR, NSFR, capital ratios',
    apiEndpoint: '/api/v1/banking-capital/calculate',
    dbTables: ['fi_entities', 'fi_financials', 'fi_loan_books', 'fi_green_finance', 'fi_financed_emissions'],
    migration: '011',
    fields: [
      { key: 'totalExposure',          label: 'Total Exposure (EUR)',         default: '',            type: 'number' },
      { key: 'cet1',                   label: 'CET1 Capital (EUR)',           default: '',            type: 'number' },
      { key: 'at1',                    label: 'AT1 Capital (EUR)',            default: '',            type: 'number' },
      { key: 'tier2',                  label: 'Tier 2 Capital (EUR)',         default: '',            type: 'number' },
      { key: 'creditRWA',              label: 'Credit RWA (EUR)',             default: '',            type: 'number' },
      { key: 'marketRWA',              label: 'Market RWA (EUR)',             default: '',            type: 'number' },
      { key: 'opRWA',                  label: 'Operational RWA (EUR)',        default: '',            type: 'number' },
      { key: 'hqla',                   label: 'HQLA (EUR)',                   default: '',            type: 'number' },
      { key: 'outflows',               label: '30-day Net Outflows (EUR)',    default: '',            type: 'number' },
      { key: 'inflows',                label: '30-day Inflows (EUR)',         default: '',            type: 'number' },
      { key: 'asf',                    label: 'Available Stable Funding (EUR)',default: '',           type: 'number' },
      { key: 'rsf',                    label: 'Required Stable Funding (EUR)',default: '',            type: 'number' },
      { key: 'irbPd',                  label: 'IRB PD',                      default: '',            type: 'number' },
      { key: 'irbLgd',                 label: 'IRB LGD',                     default: '',            type: 'number' },
      { key: 'irbEad',                 label: 'IRB EAD (EUR)',                default: '',            type: 'number' },
      { key: 'irbMat',                 label: 'IRB Maturity (years)',         default: '',            type: 'number' },
      { key: 'stage2Pct',              label: 'Stage 2 % of Book',           default: '',            type: 'number' },
      { key: 'stage3Pct',              label: 'Stage 3 % of Book',           default: '',            type: 'number' },
    ],
  },

  regulatory: {
    label: 'Regulatory (CSRD / SFDR / TCFD / ISSB)',
    description: 'Multi-framework regulatory compliance and readiness assessment',
    apiEndpoint: '/api/v1/regulatory/csrd-readiness',
    dbTables: ['regulatory_entities', 'csrd_entity_registry', 'csrd_gap_tracker', 'csrd_kpi_values', 'sfdr_pai_disclosures', 'eu_taxonomy_assessments', 'tcfd_assessments'],
    migration: '009 / 013 / 014 / 015',
    fields: [
      { key: 'entity',                 label: 'Entity Name',                 default: '',            type: 'string' },
      { key: 'entitySize',             label: 'Entity Size',                 default: 'large_piu',   type: 'enum', options: ['large_piu','listed_sme','unlisted_sme'] },
      { key: 'reportingYear',          label: 'Reporting Year',              default: '2024',        type: 'number' },
      { key: 'firstReportingYear',     label: 'First CSRD Reporting Year',   default: '2025',        type: 'number' },
      { key: 'sfdrArticle',            label: 'SFDR Classification',         default: 'Article 8',   type: 'enum', options: ['Article 6','Article 8','Article 8+','Article 9'] },
      { key: 'esrs_e1_status',         label: 'ESRS E1 Status',              default: 'partial',     type: 'enum', options: ['complete','partial','planned','na'] },
      { key: 'esrs_e1_score',          label: 'ESRS E1 Score (0–100)',        default: '',            type: 'number' },
      { key: 'esrs_s1_status',         label: 'ESRS S1 Status',              default: 'partial',     type: 'enum', options: ['complete','partial','planned','na'] },
      { key: 'esrs_s1_score',          label: 'ESRS S1 Score (0–100)',        default: '',            type: 'number' },
      { key: 'esrs_g1_status',         label: 'ESRS G1 Status',              default: 'partial',     type: 'enum', options: ['complete','partial','planned','na'] },
      { key: 'esrs_g1_score',          label: 'ESRS G1 Score (0–100)',        default: '',            type: 'number' },
    ],
  },

  supply_chain: {
    label: 'Supply Chain (Scope 3 / SBTi)',
    description: 'Scope 3 value chain emissions and SBTi target setting',
    apiEndpoint: '/api/v1/supply-chain/scope3',
    dbTables: ['sc_entities', 'scope3_assessments', 'scope3_activities', 'sbti_targets', 'sbti_trajectories', 'emission_factor_library'],
    migration: '007',
    fields: [
      { key: 'entityName',             label: 'Entity Name',                 default: '',            type: 'string' },
      { key: 'sector',                 label: 'Sector',                      default: '',            type: 'string' },
      { key: 'reportingYear',          label: 'Reporting Year',              default: '2024',        type: 'number' },
      { key: 'scope1_tco2e',           label: 'Scope 1 (tCO2e)',             default: '',            type: 'number' },
      { key: 'scope2_tco2e',           label: 'Scope 2 (tCO2e)',             default: '',            type: 'number' },
      { key: 'scope3_cat1_tco2e',      label: 'Scope 3 Cat 1 Purchased Goods (tCO2e)', default: '', type: 'number' },
      { key: 'scope3_cat11_tco2e',     label: 'Scope 3 Cat 11 Products Sold (tCO2e)', default: '',  type: 'number' },
      { key: 'sbti_target_year',       label: 'SBTi Target Year',            default: '2030',        type: 'number' },
      { key: 'sbti_pathway',           label: 'SBTi Pathway',                default: '1.5c',        type: 'enum', options: ['1.5c','well_below_2c','2c'] },
      { key: 'sbti_base_year',         label: 'SBTi Base Year',              default: '2019',        type: 'number' },
      { key: 'sbti_reduction_pct',     label: 'SBTi Reduction Target (%)',   default: '',            type: 'number' },
    ],
  },

  stranded_assets: {
    label: 'Stranded Assets',
    description: 'Fossil fuel reserves, power plants and real estate stranding risk',
    apiEndpoint: '/api/v1/stranded-assets/analyze',
    dbTables: ['energy_stranded_assets_register', 'ecl_assessments'],
    migration: '012 / 046',
    fields: [
      { key: 'assetName',              label: 'Asset Name',                  default: '',            type: 'string' },
      { key: 'assetType',              label: 'Asset Type',                  default: 'power_plant', type: 'enum', options: ['power_plant','oil_gas_reserves','real_estate','infrastructure'] },
      { key: 'bookValue',              label: 'Book Value (EUR)',             default: '',            type: 'number' },
      { key: 'capacityMW',             label: 'Capacity (MW) — for power',   default: '',            type: 'number' },
      { key: 'fuelType',               label: 'Fuel Type',                   default: 'coal',        type: 'enum', options: ['coal','gas','oil','nuclear','lignite'] },
      { key: 'remainingLifeYears',     label: 'Remaining Useful Life (yrs)', default: '',            type: 'number' },
      { key: 'co2Intensity',           label: 'CO2 Intensity (tCO2/MWh)',    default: '',            type: 'number' },
      { key: 'scenario',               label: 'NGFS Scenario',               default: 'net_zero_2050', type: 'string' },
    ],
  },

  sovereign_climate: {
    label: 'Sovereign Climate Risk',
    description: 'Climate-adjusted sovereign creditworthiness and portfolio VaR',
    apiEndpoint: '/api/v1/sovereign-climate-risk/portfolio',
    dbTables: ['sovereign_climate_assessments', 'sovereign_portfolio_assessments'],
    migration: '046',
    fields: [
      { key: 'country',                label: 'Country ISO2',                default: '',            type: 'string' },
      { key: 'exposure_eur',           label: 'Exposure (EUR)',              default: '',            type: 'number' },
      { key: 'scenario',               label: 'NGFS Scenario',               default: 'delayed_transition', type: 'enum', options: ['net_zero_2050','below_2c','delayed_transition','current_policies','nationally_determined'] },
      { key: 'rating_sp',              label: 'Current S&P Rating',          default: '',            type: 'string' },
    ],
  },
};

// ─────────────────────────────────────────────────────────────────────────────
// Flatten nested persona module fields to CSV-compatible flat keys
// ─────────────────────────────────────────────────────────────────────────────
function flattenModuleData(moduleKey, moduleData) {
  const schema = MODULE_SCHEMAS[moduleKey];
  if (!schema) return {};
  const row = {};
  schema.fields.forEach(f => {
    const raw = moduleData?.[f.key];
    if (raw === undefined || raw === null) {
      row[f.key] = f.default;
    } else if (Array.isArray(raw)) {
      row[f.key] = raw.join(';');
    } else if (typeof raw === 'object') {
      row[f.key] = JSON.stringify(raw);
    } else {
      row[f.key] = String(raw);
    }
  });
  return row;
}

// ─────────────────────────────────────────────────────────────────────────────
// Build CSV string for a module, one row per persona that has data for it
// ─────────────────────────────────────────────────────────────────────────────
export function buildModuleCsv(moduleKey) {
  const schema = MODULE_SCHEMAS[moduleKey];
  if (!schema) return '';

  const headers = [
    'persona_id',
    'persona_name',
    'institution',
    'sector',
    'role',
    ...schema.fields.map(f => f.key),
  ];

  const rows = [headers];

  // Add a comment-row as second row (for documentation)
  const commentRow = [
    '# persona_id',
    '# Display name of persona user',
    '# Institution name',
    '# Sector',
    '# Role',
    ...schema.fields.map(f => `# ${f.label}${f.options ? ` [${f.options.join('|')}]` : ''}`),
  ];
  rows.push(commentRow);

  ALL_PERSONAS.forEach(persona => {
    const moduleData = persona.modules?.[moduleKey];
    if (!moduleData) return; // skip personas that don't use this module
    const flat = flattenModuleData(moduleKey, moduleData);
    rows.push([
      persona.id,
      persona.name,
      persona.institution,
      persona.sector,
      persona.role,
      ...schema.fields.map(f => flat[f.key] ?? ''),
    ]);
  });

  // Add empty template row for user to fill in
  rows.push([
    'YOUR_PERSONA_ID',
    'Your Name, Your Role',
    'Your Institution',
    'Your Sector',
    'Your Role',
    ...schema.fields.map(f => f.default || ''),
  ]);

  return rows.map(row =>
    row.map(v => {
      const s = String(v ?? '');
      return s.includes(',') || s.includes('"') || s.includes('\n')
        ? `"${s.replace(/"/g, '""')}"`
        : s;
    }).join(',')
  ).join('\n');
}

// ─────────────────────────────────────────────────────────────────────────────
// Build JSON template for a module
// ─────────────────────────────────────────────────────────────────────────────
export function buildModuleJson(moduleKey) {
  const schema = MODULE_SCHEMAS[moduleKey];
  if (!schema) return '{}';

  const personas = ALL_PERSONAS
    .filter(p => p.modules?.[moduleKey])
    .map(p => ({
      persona_id: p.id,
      persona_name: p.name,
      institution: p.institution,
      sector: p.sector,
      role: p.role,
      module_data: p.modules[moduleKey],
    }));

  // Append blank template
  const blankTemplate = {};
  MODULE_SCHEMAS[moduleKey].fields.forEach(f => {
    blankTemplate[f.key] = f.default || null;
  });
  personas.push({
    persona_id: 'YOUR_PERSONA_ID',
    persona_name: 'Your Name, Your Role',
    institution: 'Your Institution',
    sector: 'Your Sector',
    role: 'Your Role',
    module_data: blankTemplate,
  });

  return JSON.stringify({
    _meta: {
      module: moduleKey,
      label: schema.label,
      description: schema.description,
      apiEndpoint: schema.apiEndpoint,
      dbTables: schema.dbTables,
      migration: schema.migration,
      generated: new Date().toISOString(),
    },
    personas,
  }, null, 2);
}

// ─────────────────────────────────────────────────────────────────────────────
// Trigger browser download
// ─────────────────────────────────────────────────────────────────────────────
export function downloadCsvTemplate(moduleKey) {
  const schema = MODULE_SCHEMAS[moduleKey];
  if (!schema) return;
  const content = buildModuleCsv(moduleKey);
  const blob = new Blob([content], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `template_${moduleKey}_${new Date().toISOString().split('T')[0]}.csv`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function downloadJsonTemplate(moduleKey) {
  const schema = MODULE_SCHEMAS[moduleKey];
  if (!schema) return;
  const content = buildModuleJson(moduleKey);
  const blob = new Blob([content], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `template_${moduleKey}_${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// ─────────────────────────────────────────────────────────────────────────────
// Parse uploaded CSV back to an array of row objects
// ─────────────────────────────────────────────────────────────────────────────
export function parseCsvUpload(csvText) {
  const lines = csvText.split('\n').filter(l => l.trim() && !l.trim().startsWith('#'));
  if (lines.length < 2) return { headers: [], rows: [], errors: ['File is empty or has no data rows'] };

  const parseRow = (line) => {
    const result = [];
    let inQuote = false;
    let cell = '';
    for (let i = 0; i < line.length; i++) {
      if (line[i] === '"') {
        if (inQuote && line[i + 1] === '"') { cell += '"'; i++; }
        else inQuote = !inQuote;
      } else if (line[i] === ',' && !inQuote) {
        result.push(cell.trim()); cell = '';
      } else {
        cell += line[i];
      }
    }
    result.push(cell.trim());
    return result;
  };

  const headers = parseRow(lines[0]);
  const rows = lines.slice(1).map((line, idx) => {
    const values = parseRow(line);
    const row = {};
    headers.forEach((h, i) => { row[h] = values[i] ?? ''; });
    row._rowIndex = idx + 2;
    return row;
  }).filter(r => r.persona_id && r.persona_id !== 'YOUR_PERSONA_ID');

  return { headers, rows, errors: [] };
}
