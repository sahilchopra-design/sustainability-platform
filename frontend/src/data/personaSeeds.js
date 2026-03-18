/**
 * personaSeeds.js  —  v2.0  (comprehensive module coverage)
 *
 * 12 institution × role personas across Finance, Energy, Supply Chain, and
 * Manufacturing.  Every persona carries realistic default inputs for every
 * module it would plausibly use, drawn from publicly available benchmarks
 * (IRENA 2024, ENTSO-E, ECB, EBA, GRI, CSRD IG3, ETS Phase IV, PCAF v2).
 *
 * Module keys  →  Page
 * ─────────────────────────────────────────────────────────────────────
 *  banking_capital      BankingCapitalPage   (Basel IV IRB/SA/LCR/NSFR)
 *  carbon               CarbonDashboard      (Scope 1/2/3)
 *  supply_chain         SupplyChainPage      (Scope 3 / SBTi)
 *  cbam                 CBAMPage             (CBAM calculator)
 *  energy_finance       EnergyFinancePage    (LCOE / PPA / Project Finance)
 *  dcm                  DCMCalculatorPage    (CDM/VCS/GS methodology)
 *  portfolio            PortfolioAnalyticsPage
 *  financial_risk       FinancialRiskPage    (ECL / PCAF)
 *  scenario             ScenarioAnalysisPage (NGFS)
 *  real_estate          RealEstateAssessmentPage (RICS/CRREM)
 *  gar_ets              GarEtsPage           (GAR + EU ETS Phase IV)
 *  regulatory           RegulatoryPage       (SFDR / CSRD / TCFD / ISSB / BRSR)
 *  nature_risk          NatureRiskPage       (TNFD LEAP / Water / Biodiversity)
 *  stranded_assets      StrandedAssetsPage   (Reserves / Power plants / RE)
 *  sustainability       SustainabilityPage   (GRESB / LEED / BREEAM / NABERS)
 *  eu_regulatory        EURegulatoryHubPage  (EUDR / CSDDD / Taxonomy)
 *  project_finance      ProjectFinancePage   (DSCR / LLCR / Green Bond)
 *  energy_transition    EnergyTransitionPage (Fleet / Grid EF / Avoided / OGMP)
 *  climate_risk         ClimateRiskPage      (Physical / Transition / Integrated)
 *  stress_testing       StressTestingPage    (EBA GL/2017/16 ECL stress)
 *  residential_re       ResidentialREPage    (CRREM / RICS / Spatial Hazard)
 *  valuation            UnifiedValuationPage (Income / Cost / Comparable)
 *  asset_management     AssetManagementPage  (PACTA / GBS / Factor overlays)
 *  double_materiality   DoubleMaterialityPage (EFRAG DMA)
 *  sfdr_pai             SFDRPAIPage          (Art 4 RTS PAI indicators)
 *  sovereign_climate    SovereignClimateRiskPage (NGFS sovereign notch adj.)
 *  green_hydrogen       GreenHydrogenPage    (LCOH / RFNBO / Electrolyser)
 *  technology_risk      TechnologyRiskPage   (Automation / AI / Fintech)
 *  sector_assessments   SectorAssessmentsPage (Data centre / CAT / Power plant)
 *  country_risk         CountryRiskPage      (Sovereign risk composite)
 *  monte_carlo          MonteCarloPage       (P5/P95 VaR / sensitivity)
 */

// ─── FINANCE ─────────────────────────────────────────────────────────────────

const EU_BANK_INVESTMENT_LEAD = {
  id: 'EU_BANK_INVESTMENT_LEAD',
  name: 'Thomas Krieger, Head of Credit Portfolio',
  institution: 'FirstEuro Bank AG',
  institutionType: 'European Bank (G-SIB)',
  sector: 'Finance',
  role: 'Investment Lead',
  colour: 'bg-blue-600',
  tagline: 'IRB models · IFRS 9 ECL · Basel IV capital · Climate credit risk',
  logo: '🏦',

  modules: {
    banking_capital: {
      saClass: 'corporate', cqs: '3', saAmount: '8500000',
      irbPd: '0.018', irbLgd: '0.42', irbEad: '12000000', irbMat: '3.2', irbClass: 'corporate',
      hqla: '22000000000', outflows: '18500000000', inflows: '7200000000',
      asf: '242000000000', rsf: '198000000000',
      totalExposure: '195000000000', portfolioSize: '14200', avgRating: 'BBB-',
      collateralType: 'unsecured_senior', avgMaturity: '4', stage2Pct: '8.5', stage3Pct: '2.1',
      warmingC: '2.0', cet1: '18500000000', at1: '4200000000', tier2: '6800000000',
      creditRWA: '148000000000', marketRWA: '22400000000', opRWA: '14200000000',
      leverage: '580000000000', ccyBuffer: '0.5',
    },
    portfolio: {
      waci: 185, finEmissions: 2800000, pcafScore: 2.8, greenShare: 12.3,
      label: 'FirstEuro Bank AG — Credit Portfolio (€195 B)',
    },
    financial_risk: {
      exposure: '195000000000', pd: '0.018', lgd: '0.42',
      stage2: '8.5', stage3: '2.1', entityName: 'FirstEuro Bank AG',
    },
    dcm: { methodologyCode: 'ACM0004', sector: 'Waste' },
    scenario: { entity: 'FirstEuro Bank AG', scenario: 'delayed_transition' },
    gar_ets: {
      // Green Asset Ratio — lending book breakdown
      totalAssets: '195000000000',
      taxonomyEligiblePct: '44.1',   // 44.1% eligible exposures (EBA KPIs 2024)
      taxonomyAlignedPct: '12.3',    // 12.3% GAR (Green Asset Ratio)
      residentialMortgages: '52000000000',
      commercialRE: '28000000000',
      corporateLoans: '89000000000',
      smeLoans: '18000000000',
      energyEfficiencyLoansPct: '18.4',
      renewableFinancePct: '6.2',
      greenBondHoldings: '4800000000',
    },
    stress_testing: {
      // EBA GL/2017/16 ICAAP stress scenarios
      baseEclM: '1850',              // €1.85 B base ECL
      adverseEclM: '3420',           // €3.42 B adverse
      severelyAdverseEclM: '5680',   // €5.68 B severely adverse
      pdShockAdverse: '0.035',
      pdShockSevere: '0.062',
      lgdShockAdverse: '0.51',
      lgdShockSevere: '0.62',
      climatePhysicalRisk: '320',    // €320 M climate-physical ECL add-on
      climateTransitionRisk: '890',  // €890 M climate-transition ECL add-on
    },
    residential_re: {
      // Sample residential RE loan book
      avgEpcRating: 'C',
      avgEui: '195',                 // kWh/m²/yr (German residential stock)
      crremTarget2030: '130',
      crremTarget2050: '70',
      portfolioSqm: '4200000',       // 4.2M m² financed
      greenMortgagePct: '8.4',
      avgLtv: '68.5',
      avgYearBuilt: '1978',
    },
    asset_management: {
      // PACTA temperature score + green bond data
      portTemperatureScore: '2.6',   // °C portfolio temperature score
      greenBondAllocationPct: '14.8',
      esgTiltFactor: '0.12',
      exclusionThresholds: { coal: 5, weapons: 0, tobacco: 10 },
      parisAlignedPct: '28.4',
      fossilFuelExposurePct: '6.2',
    },
    sovereign_climate: {
      countries: ['DE', 'FR', 'IT', 'ES', 'NL', 'AT', 'BE', 'PL'],
      exposureWeights: [0.28, 0.22, 0.18, 0.12, 0.08, 0.05, 0.04, 0.03],
      scenario: 'delayed_transition',
    },
    country_risk: {
      primaryCountry: 'DE',
      exposureCountries: ['DE','FR','IT','ES','PL','NL'],
    },
    monte_carlo: {
      portfolioValue: '195000000000',
      varConfidence: '99',
      timeHorizonDays: '250',
      volatility: '0.14',
      correlationMatrix: 'basel_iii',
    },
    climate_risk: {
      entity: 'FirstEuro Bank AG',
      entity_id: 'FEB-DE-001',
      entity_name: 'FirstEuro Bank AG',
      entity_type: 'counterparty',
      sector_nace: 'K64',
      latitude: 50.11,
      longitude: 8.68,
      asset_value_eur: 195000000000,
      flood_zone: false,
      annual_revenue_eur: 8500000000,
      carbon_intensity_tco2_eur: 0.014,
      capex_green_pct: 28,
      scenario: 'net_zero_2050',
      time_horizon: 10,
      physicalRiskScore: 3.2,
      transitionRiskScore: 5.8,
      sector: 'Financial Services',
      country: 'DE',
    },
    sfdr_pai: {
      reportingYear: 2024,
      aum: '195000000000',
      investeeCount: 14200,
      art8: true, art9: false,
      ghgScope1M: '2800000',
      fossilFuelPct: '6.2',
      renewableEnergyPct: '12.3',
    },
    double_materiality: {
      entity: 'FirstEuro Bank AG',
      sector: 'Financial Services',
      reportingYear: 2024,
      materialTopics: ['GHG emissions', 'Climate physical risk', 'Biodiversity loss', 'Social inequality'],
    },
  },
};

const EU_BANK_ANALYTICS_LEAD = {
  id: 'EU_BANK_ANALYTICS_LEAD',
  name: 'Priya Sharma, Head of Climate Analytics',
  institution: 'FirstEuro Bank AG',
  institutionType: 'European Bank (G-SIB)',
  sector: 'Finance',
  role: 'Analytics Lead',
  colour: 'bg-indigo-600',
  tagline: 'PCAF financed emissions · WACI · Paris alignment · Portfolio heatmaps',
  logo: '📊',

  modules: {
    portfolio: {
      waci: 185, finEmissions: 2800000, pcafScore: 2.8, greenShare: 12.3,
      label: 'FirstEuro Bank AG — Full Portfolio (€195 B)',
    },
    banking_capital: {
      saClass: 'corporate', cqs: '3', saAmount: '8500000',
      irbPd: '0.018', irbLgd: '0.42', irbEad: '12000000', irbMat: '3.2', irbClass: 'corporate',
      hqla: '22000000000', outflows: '18500000000', inflows: '7200000000',
      asf: '242000000000', rsf: '198000000000',
      totalExposure: '195000000000', portfolioSize: '14200', avgRating: 'BBB-',
      collateralType: 'unsecured_senior', avgMaturity: '4', stage2Pct: '8.5', stage3Pct: '2.1',
      warmingC: '2.0', cet1: '18500000000', at1: '4200000000', tier2: '6800000000',
      creditRWA: '148000000000', marketRWA: '22400000000', opRWA: '14200000000',
      leverage: '580000000000', ccyBuffer: '0.5',
    },
    financial_risk: {
      exposure: '195000000000', pd: '0.018', lgd: '0.42',
      stage2: '8.5', stage3: '2.1', entityName: 'FirstEuro Bank AG',
    },
    scenario: { entity: 'FirstEuro Bank AG', scenario: 'net_zero_2050' },
    dcm: { methodologyCode: 'VM0045', sector: 'Forestry' },
    climate_risk: {
      entity: 'FirstEuro Bank AG',
      entity_id: 'FEB-DE-001',
      entity_name: 'FirstEuro Bank AG',
      entity_type: 'counterparty',
      sector_nace: 'K64',
      latitude: 50.11,
      longitude: 8.68,
      asset_value_eur: 195000000000,
      flood_zone: false,
      annual_revenue_eur: 8500000000,
      carbon_intensity_tco2_eur: 0.014,
      capex_green_pct: 28,
      scenario: 'net_zero_2050',
      time_horizon: 10,
      physicalRiskScore: 3.2,
      transitionRiskScore: 5.8,
      sector: 'Financial Services',
      country: 'DE',
    },
    monte_carlo: {
      portfolioValue: '195000000000',
      varConfidence: '99',
      timeHorizonDays: '250',
      volatility: '0.14',
      correlationMatrix: 'basel_iii',
    },
    gar_ets: {
      totalAssets: '195000000000',
      taxonomyEligiblePct: '44.1',
      taxonomyAlignedPct: '12.3',
      residentialMortgages: '52000000000',
      commercialRE: '28000000000',
      corporateLoans: '89000000000',
      smeLoans: '18000000000',
      energyEfficiencyLoansPct: '18.4',
      renewableFinancePct: '6.2',
      greenBondHoldings: '4800000000',
    },
    asset_management: {
      portTemperatureScore: '2.6',
      greenBondAllocationPct: '14.8',
      esgTiltFactor: '0.12',
      exclusionThresholds: { coal: 5, weapons: 0, tobacco: 10 },
      parisAlignedPct: '28.4',
      fossilFuelExposurePct: '6.2',
    },
    sovereign_climate: {
      countries: ['DE', 'FR', 'IT', 'ES', 'NL', 'AT', 'BE', 'PL'],
      exposureWeights: [0.28, 0.22, 0.18, 0.12, 0.08, 0.05, 0.04, 0.03],
      scenario: 'net_zero_2050',
    },
  },
};

const EU_BANK_SUSTAINABILITY_LEAD = {
  id: 'EU_BANK_SUSTAINABILITY_LEAD',
  name: 'Ingrid Larsen, Head of ESG Regulatory Affairs',
  institution: 'FirstEuro Bank AG',
  institutionType: 'European Bank (G-SIB)',
  sector: 'Finance',
  role: 'Sustainability & Regulatory Lead',
  colour: 'bg-emerald-600',
  tagline: 'CSRD · SFDR PAI · Pillar 3 ESG · EU Taxonomy · TCFD',
  logo: '🌿',

  modules: {
    portfolio: {
      waci: 185, finEmissions: 2800000, pcafScore: 2.8, greenShare: 12.3,
      label: 'FirstEuro Bank AG — CSRD Reporting Entity',
    },
    scenario: { entity: 'FirstEuro Bank AG', scenario: 'below_2c' },
    dcm: { methodologyCode: 'GS_WASH_CleanWater', sector: 'Household' },
    banking_capital: {
      saClass: 'corporate', cqs: '3', saAmount: '8500000',
      irbPd: '0.018', irbLgd: '0.42', irbEad: '12000000', irbMat: '3.2', irbClass: 'corporate',
      hqla: '22000000000', outflows: '18500000000', inflows: '7200000000',
      asf: '242000000000', rsf: '198000000000',
      totalExposure: '195000000000', portfolioSize: '14200', avgRating: 'BBB-',
      collateralType: 'unsecured_senior', avgMaturity: '4', stage2Pct: '8.5', stage3Pct: '2.1',
      warmingC: '2.0', cet1: '18500000000', at1: '4200000000', tier2: '6800000000',
      creditRWA: '148000000000', marketRWA: '22400000000', opRWA: '14200000000',
      leverage: '580000000000', ccyBuffer: '0.5',
    },
    regulatory: {
      // CSRD first reporting year 2025 (financial year 2024)
      entity: 'FirstEuro Bank AG',
      entitySize: 'large_piu',
      firstReportingYear: 2025,
      reportingYear: 2024,
      esrsReadiness: {
        'ESRS 2': { status: 'complete', score: 92 },
        'ESRS E1': { status: 'complete', score: 85 },
        'ESRS E2': { status: 'partial', score: 58 },
        'ESRS E3': { status: 'partial', score: 52 },
        'ESRS E4': { status: 'planned', score: 35 },
        'ESRS E5': { status: 'planned', score: 30 },
        'ESRS S1': { status: 'complete', score: 88 },
        'ESRS S2': { status: 'partial', score: 65 },
        'ESRS G1': { status: 'complete', score: 94 },
      },
      sfdrArticle: 'Article 8',
      tcfdMaturity: { governance: 4, strategy: 3, risk_mgmt: 3, metrics: 3 },
      pillar3Esg: true,
    },
    sfdr_pai: {
      reportingYear: 2024,
      aum: '195000000000',
      investeeCount: 14200,
      art8: true, art9: false,
      ghgScope1M: '2800000',
      fossilFuelPct: '6.2',
      renewableEnergyPct: '12.3',
    },
    double_materiality: {
      entity: 'FirstEuro Bank AG',
      sector: 'Financial Services',
      reportingYear: 2024,
      materialTopics: ['GHG emissions', 'Climate physical risk', 'Biodiversity loss', 'Social inequality'],
    },
    gar_ets: {
      totalAssets: '195000000000',
      taxonomyEligiblePct: '44.1',
      taxonomyAlignedPct: '12.3',
      residentialMortgages: '52000000000',
      commercialRE: '28000000000',
      corporateLoans: '89000000000',
      smeLoans: '18000000000',
      energyEfficiencyLoansPct: '18.4',
      renewableFinancePct: '6.2',
      greenBondHoldings: '4800000000',
    },
    climate_risk: {
      entity: 'FirstEuro Bank AG',
      entity_id: 'FEB-DE-001',
      entity_name: 'FirstEuro Bank AG',
      entity_type: 'counterparty',
      sector_nace: 'K64',
      latitude: 50.11,
      longitude: 8.68,
      asset_value_eur: 195000000000,
      flood_zone: false,
      annual_revenue_eur: 8500000000,
      carbon_intensity_tco2_eur: 0.014,
      capex_green_pct: 28,
      scenario: 'net_zero_2050',
      time_horizon: 10,
      physicalRiskScore: 3.2,
      transitionRiskScore: 5.8,
      sector: 'Financial Services',
      country: 'DE',
    },
    nature_risk: {
      entity: 'FirstEuro Bank AG',
      exposedSectors: ['Real Estate', 'Agriculture', 'Food & Beverage'],
      waterRiskScore: 2.8,
      biodiversityFootprintM: 420,
      tnfdLeapPhase: 'Assess',
    },
  },
};

// ─── ENERGY ──────────────────────────────────────────────────────────────────

const UTILITY_INVESTMENT_LEAD = {
  id: 'UTILITY_INVESTMENT_LEAD',
  name: 'Lars Andersen, Head of Green Investments',
  institution: 'NordWind AG',
  institutionType: 'European Utility / IPP',
  sector: 'Energy',
  role: 'Investment Lead',
  colour: 'bg-sky-600',
  tagline: 'Wind · Solar · PPAs · LCOE modelling · Stranded asset register',
  logo: '⚡',

  modules: {
    energy_finance: {
      technology: 'wind_onshore', capacityMW: '250', capexPerKw: '1180',
      capacityFactor: '0.33', wacc: '6.2', lifetimeYears: '25',
      opexPerMwh: '12.5', gridEf: '0.385', ppaPrice: '54', ppaTerm: '15',
    },
    scenario: { entity: 'NordWind AG', scenario: 'net_zero_2050' },
    carbon: {
      scope1: '145000', scope2Market: '18500', scope2Location: '68400',
      scope3Total: '890000', entity: 'NordWind AG', sector: 'Energy',
      revenueM: '2840', gridEfCountry: 'DE',
    },
    dcm: { methodologyCode: 'AMS_I_B_SolarPVMiniGrid', sector: 'Energy' },
    portfolio: {
      waci: 68, finEmissions: 0, pcafScore: 0, greenShare: 78,
      label: 'NordWind AG — Renewable Asset Portfolio (4.2 GW)',
    },
    project_finance: {
      // Offshore wind — Bornholm II (500 MW)
      projectName: 'Bornholm II Offshore Wind',
      technology: 'wind_offshore',
      capacityMW: '500',
      capexM: '1425',              // €1.425 B capex (€2,850/kW)
      debtPct: '70',               // 70% gearing
      interestRate: '4.8',
      loanTermYears: '18',
      dscrTarget: '1.35',
      annualRevenueM: '148',       // €148 M/yr at €82/MWh PPA
      opexM: '24.2',               // €22/MWh × 8760h × 0.41 CF × 0.5GW
      ppaPrice: '82', ppaTerm: '20',
      greenBondFramework: 'EUGBS',
      isCLPFO: true,               // Clean energy transition CBAM-link
    },
    stranded_assets: {
      // Gas peaker plants at risk
      assetType: 'power_plant',
      technology: 'CCGT',
      capacityMW: '420',
      commissionYear: '2008',
      remainingLifeYears: '13',
      currentCapacityFactor: '0.22',
      marginalCostEurMwh: '88',
      carbonCostEurTco2: '63',
      stranding_probability_2030: '0.45',
      stranding_probability_2040: '0.82',
    },
    green_hydrogen: {
      // Green H2 for NordWind's industrial offtakers
      electrolyserMW: '100',
      capacityFactor: '0.45',      // Coupled to offshore wind CF
      capexPerKw: '820',           // €820/kW (2025 alkaline stack)
      stackLifetimeH: '80000',
      electricityPriceEurMwh: '28', // Curtailed power / PPA
      waterCostEurM3: '2.5',
      deliveryMode: 'pipeline',
      targetSector: 'steel_dri',
      rfnboCompliant: true,
    },
    energy_transition: {
      // Fleet + grid alignment
      country: 'DE',
      scenario: 'net_zero_2050',
      targetYear: 2035,
      fleetSize: '480',            // NordWind corporate vehicles
      currentEvPct: '18',
      targetEvPct2030: '100',
      gridEfToday: '0.385',       // Germany ENTSO-E 2024
      gridEfTarget2030: '0.220',
      windCapacityGw: '4.2',
      solarCapacityGw: '0.8',
      totalGenerationTwhyr: '14.8',
      plants: [
        { id: 1, name: 'Bornholm II Offshore Wind', technology: 'wind', capacity_mw: 500, age_years: 2, annual_emissions_tco2: 0, replacement_tech: 'offshore_wind' },
        { id: 2, name: 'NordWind Solar Park', technology: 'solar_pv', capacity_mw: 180, age_years: 4, annual_emissions_tco2: 0, replacement_tech: 'solar_pv' },
        { id: 3, name: 'Backup CCGT Peaker', technology: 'gas_ccgt', capacity_mw: 120, age_years: 18, annual_emissions_tco2: 95000, replacement_tech: 'battery_storage' },
      ],
    },
    climate_risk: {
      entity: 'NordWind AG',
      entity_id: 'NW-DE-001',
      entity_name: 'NordWind AG',
      entity_type: 'asset',
      sector_nace: 'D35',
      latitude: 54.9,
      longitude: 14.6,
      asset_value_eur: 2800000000,
      flood_zone: false,
      annual_revenue_eur: 680000000,
      carbon_intensity_tco2_eur: 0.14,
      capex_green_pct: 92,
      scenario: 'net_zero_2050',
      time_horizon: 10,
      physicalRiskScore: 4.1,      // Offshore assets exposed to storms
      transitionRiskScore: 1.8,    // Low — renewables are the transition
      sector: 'Utilities',
      country: 'DE',
    },
    sector_assessments: {
      // Power plant analysis
      plantType: 'onshore_wind',
      installYear: '2024',
      location: 'North Sea / Baltic',
      capacityMW: '4200',
      annualGenerationGwh: '12200',
      co2PerMwh: '8',              // g/kWh lifecycle
      remainingLife: '24',
    },
  },
};

const UTILITY_ANALYTICS_LEAD = {
  id: 'UTILITY_ANALYTICS_LEAD',
  name: 'Sofie Hansen, Climate Analytics Lead',
  institution: 'NordWind AG',
  institutionType: 'European Utility / IPP',
  sector: 'Energy',
  role: 'Analytics Lead',
  colour: 'bg-cyan-600',
  tagline: 'GHG inventory · CRREM · Renewable mix · Stranded-asset risk curves',
  logo: '🔬',

  modules: {
    carbon: {
      scope1: '145000', scope2Market: '18500', scope2Location: '68400',
      scope3Total: '890000', entity: 'NordWind AG', sector: 'Energy',
      revenueM: '2840', gridEfCountry: 'DE',
    },
    energy_finance: {
      technology: 'wind_offshore', capacityMW: '500', capexPerKw: '2850',
      capacityFactor: '0.41', wacc: '7.1', lifetimeYears: '30',
      opexPerMwh: '22', gridEf: '0.385', ppaPrice: '82', ppaTerm: '20',
    },
    dcm: { methodologyCode: 'VM0017', sector: 'Blue Carbon' },
    scenario: { entity: 'NordWind AG', scenario: 'below_2c' },
    portfolio: {
      waci: 68, finEmissions: 0, pcafScore: 0, greenShare: 78,
      label: 'NordWind AG — GHG Analytics View',
    },
    climate_risk: {
      entity: 'NordWind AG',
      entity_id: 'NW-DE-002',
      entity_name: 'NordWind AG',
      entity_type: 'asset',
      sector_nace: 'D35',
      latitude: 54.9,
      longitude: 14.6,
      asset_value_eur: 2800000000,
      annual_revenue_eur: 680000000,
      carbon_intensity_tco2_eur: 0.14,
      capex_green_pct: 92,
      scenario: 'net_zero_2050',
      time_horizon: 15,
      physicalRiskScore: 4.1,
      transitionRiskScore: 1.8,
      sector: 'Utilities',
      country: 'DE',
    },
    energy_transition: {
      country: 'DE',
      scenario: 'net_zero_2050',
      targetYear: 2035,
      fleetSize: '480',
      currentEvPct: '18',
      targetEvPct2030: '100',
      gridEfToday: '0.385',
      gridEfTarget2030: '0.220',
      windCapacityGw: '4.2',
      solarCapacityGw: '0.8',
      totalGenerationTwhyr: '14.8',
      plants: [
        { id: 1, name: 'Bornholm II Offshore Wind', technology: 'wind', capacity_mw: 500, age_years: 2, annual_emissions_tco2: 0, replacement_tech: 'offshore_wind' },
        { id: 2, name: 'NordWind Solar Park', technology: 'solar_pv', capacity_mw: 180, age_years: 4, annual_emissions_tco2: 0, replacement_tech: 'solar_pv' },
        { id: 3, name: 'Backup CCGT Peaker', technology: 'gas_ccgt', capacity_mw: 120, age_years: 18, annual_emissions_tco2: 95000, replacement_tech: 'battery_storage' },
      ],
    },
    stranded_assets: {
      assetType: 'power_plant',
      technology: 'CCGT',
      capacityMW: '420',
      commissionYear: '2008',
      remainingLifeYears: '13',
      currentCapacityFactor: '0.22',
      marginalCostEurMwh: '88',
      carbonCostEurTco2: '63',
      stranding_probability_2030: '0.45',
      stranding_probability_2040: '0.82',
    },
    nature_risk: {
      entity: 'NordWind AG',
      exposedSectors: ['Utilities', 'Construction'],
      waterRiskScore: 2.1,
      biodiversityFootprintM: 85,
      tnfdLeapPhase: 'Locate',
    },
    sector_assessments: {
      plantType: 'onshore_wind',
      installYear: '2024',
      location: 'North Sea / Baltic',
      capacityMW: '4200',
      annualGenerationGwh: '12200',
      co2PerMwh: '8',
      remainingLife: '24',
    },
  },
};

const OIL_GAS_SUSTAINABILITY_LEAD = {
  id: 'OIL_GAS_SUSTAINABILITY_LEAD',
  name: 'Carla Mendes, Head of Sustainability & Climate Risk',
  institution: 'AtlanticPetroleum plc',
  institutionType: 'Integrated Oil & Gas Major',
  sector: 'Energy',
  role: 'Sustainability & Regulatory Lead',
  colour: 'bg-orange-600',
  tagline: 'TCFD mandatory · Scope 3 Cat 11 · Transition plan · Carbon credits',
  logo: '🛢️',

  modules: {
    carbon: {
      scope1: '8200000', scope2Market: '980000', scope2Location: '1250000',
      scope3Total: '48500000', entity: 'AtlanticPetroleum plc',
      sector: 'Oil & Gas', revenueM: '48200', gridEfCountry: 'global_avg',
    },
    dcm: { methodologyCode: 'AM0057_GreenHydrogen', sector: 'Industry' },
    scenario: { entity: 'AtlanticPetroleum plc', scenario: 'current_policies' },
    supply_chain: {
      entityName: 'AtlanticPetroleum plc', revenueM: '48200',
      cat1: '2100000', cat4: '890000', cat11: '48500000',
      sbtiStatus: 'committed',
      sbtiTarget: '-25% Scope 1+2 by 2030; -30% Scope 3 by 2035 (vs 2019)',
    },
    portfolio: {
      waci: 1840, finEmissions: 0, pcafScore: 0, greenShare: 2.1,
      label: 'AtlanticPetroleum plc — TCFD Transition Risk View',
    },
    stranded_assets: {
      // Upstream reserves at risk — IEA NZE scenario
      assetType: 'oil_gas_reserves',
      reservoirType: 'offshore_conventional',
      provedReservesMMBOE: '2850',   // Proved reserves
      breakEvenUsdBbl: '42',         // Breakeven oil price
      capexCommittedBnUsd: '18.4',
      scenarioOilPrice2030: '55',    // IEA NZE 2030 oil price
      stranded2030Pct: '28',         // % reserves stranded under NZE
      stranded2040Pct: '64',
      carbonCostPerBbl: '8.5',
    },
    regulatory: {
      entity: 'AtlanticPetroleum plc',
      entitySize: 'large_piu',
      firstReportingYear: 2025,
      reportingYear: 2024,
      esrsReadiness: {
        'ESRS 2': { status: 'complete', score: 88 },
        'ESRS E1': { status: 'complete', score: 82 },
        'ESRS E2': { status: 'partial', score: 45 },
        'ESRS E3': { status: 'partial', score: 40 },
        'ESRS E4': { status: 'planned', score: 20 },
        'ESRS E5': { status: 'planned', score: 18 },
        'ESRS S1': { status: 'partial', score: 72 },
        'ESRS G1': { status: 'complete', score: 90 },
      },
      sfdrArticle: 'n/a',
      tcfdMaturity: { governance: 4, strategy: 4, risk_mgmt: 3, metrics: 4 },
    },
    eu_regulatory: {
      // CSDDD compliance (large non-EU filer, thresholds met)
      entityRevenue: '48200',
      entityEmployees: '58000',
      csddGroup: 'non_eu_group_1',
      adverseImpacts: ['ENV-01', 'ENV-02', 'ENV-05', 'HR-01', 'HR-02'],
      ddComplianceScore: 62,
      valueChainTier: 3,
    },
    climate_risk: {
      entity: 'AtlanticPetroleum plc',
      entity_id: 'ATP-GB-001',
      entity_name: 'AtlanticPetroleum plc',
      entity_type: 'asset',
      sector_nace: 'B06',
      latitude: 57.15,
      longitude: -2.09,
      asset_value_eur: 42000000000,
      flood_zone: false,
      annual_revenue_eur: 28000000000,
      carbon_intensity_tco2_eur: 0.87,
      capex_green_pct: 12,
      scenario: 'delayed_transition',
      time_horizon: 10,
      physicalRiskScore: 5.8,      // High — offshore assets, tropical assets
      transitionRiskScore: 8.9,    // Very high — core fossil fuel company
      sector: 'Oil & Gas',
      country: 'UK',
    },
    energy_transition: {
      country: 'GB',
      scenario: 'delayed_transition',
      targetYear: 2045,
      fleetSize: '2400',
      currentEvPct: '4',
      targetEvPct2030: '40',
      gridEfToday: '0.485',       // UK grid EF 2024
      gridEfTarget2030: '0.210',
      totalEmissionsScope1: '8200000',
      methaneIntensityPct: '0.18', // % methane as share of gas production
      plants: [
        { id: 1, name: 'Shetland Gas Platform', technology: 'gas_ocgt', capacity_mw: 80, age_years: 22, annual_emissions_tco2: 420000, replacement_tech: 'offshore_wind' },
        { id: 2, name: 'North Sea FPSO', technology: 'oil', capacity_mw: 50, age_years: 31, annual_emissions_tco2: 310000, replacement_tech: 'green_hydrogen' },
        { id: 3, name: 'Grangemouth Refinery CHP', technology: 'gas_ccgt', capacity_mw: 240, age_years: 19, annual_emissions_tco2: 780000, replacement_tech: 'biomass' },
      ],
    },
    nature_risk: {
      entity: 'AtlanticPetroleum plc',
      exposedSectors: ['Oil & Gas', 'Chemicals'],
      waterRiskScore: 6.2,
      biodiversityFootprintM: 2800,
      tnfdLeapPhase: 'Assess',
    },
    green_hydrogen: {
      // Blue H2 + CCS transition strategy
      electrolyserMW: '0',         // No green H2 yet — evaluating
      capexPerKw: '1200',          // Blue H2 SMR+CCS capex
      electricityPriceEurMwh: '65',
      rfnboCompliant: false,
      targetSector: 'refining',
      blueH2CcsCapturePct: '90',
    },
    sector_assessments: {
      plantType: 'natural_gas',
      installYear: '2005',
      location: 'North Sea',
      capacityMW: '1200',
      annualGenerationGwh: '4800',
      co2PerMwh: '420',
      remainingLife: '10',
    },
  },
};

// ─── SUPPLY CHAIN ─────────────────────────────────────────────────────────────

const MANUFACTURER_ANALYTICS_LEAD = {
  id: 'MANUFACTURER_ANALYTICS_LEAD',
  name: 'Kai Fischer, Head of Supply Chain Analytics',
  institution: 'EuroAuto GmbH',
  institutionType: 'Automotive OEM (Tier-1 Exporter)',
  sector: 'Supply Chain',
  role: 'Analytics Lead',
  colour: 'bg-violet-600',
  tagline: 'Scope 3 Cat 1 & 11 · SBTi 1.5°C · Supplier engagement · CSRD E1/E2',
  logo: '🚗',

  modules: {
    supply_chain: {
      entityName: 'EuroAuto GmbH', revenueM: '12800',
      cat1: '1850000', cat2: '42000', cat3: '68000', cat4: '245000',
      cat5: '31000', cat6: '18400', cat7: '12200',
      cat11: '4200000', cat12: '185000', totalScope3: '6851600',
      sbtiStatus: 'approved',
      sbtiTarget: '-42% Scope 1+2 by 2030; -25% Scope 3 by 2030 (vs 2019)',
      sbtiPathway: '1.5°C',
      topSupplierCountries: ['DE','PL','CZ','CN','RO'],
    },
    carbon: {
      scope1: '285000', scope2Market: '95000', scope2Location: '148000',
      scope3Total: '6851600', entity: 'EuroAuto GmbH',
      sector: 'Automotive', revenueM: '12800', gridEfCountry: 'DE',
    },
    dcm: { methodologyCode: 'GS_AGRI_SoilCarbon', sector: 'Agriculture' },
    cbam: {
      product: 'steel', quantity: '185000', origin: 'TR',
      carbonIntensity: '2.10', euEtsPrice: '63',
    },
    scenario: { entity: 'EuroAuto GmbH', scenario: 'below_2c' },
    climate_risk: {
      entity: 'EuroAuto GmbH',
      entity_id: 'EAG-DE-001',
      entity_name: 'EuroAuto GmbH',
      entity_type: 'asset',
      sector_nace: 'C29',
      latitude: 48.14,
      longitude: 11.58,
      asset_value_eur: 185000000000,
      flood_zone: false,
      annual_revenue_eur: 185000000000,
      carbon_intensity_tco2_eur: 0.65,
      capex_green_pct: 38,
      scenario: 'below_2c',
      time_horizon: 10,
      physicalRiskScore: 3.6,
      transitionRiskScore: 7.2,    // High — ICE exposure
      sector: 'Automotive',
      country: 'DE',
    },
    nature_risk: {
      entity: 'EuroAuto GmbH',
      exposedSectors: ['Automotive', 'Mining & Metals'],
      waterRiskScore: 3.1,
      biodiversityFootprintM: 580,
      tnfdLeapPhase: 'Locate',
    },
    technology_risk: {
      sector: 'automotive',
      automationRisk: '6.8',       // High — assembly lines
      aiAdoptionIndex: '4.2',
      evDisruptionScore: '8.5',    // Very high
      digitalReadinessScore: '62', // DESI-equivalent
    },
    regulatory: {
      entity: 'EuroAuto GmbH',
      entitySize: 'large_piu',
      firstReportingYear: 2025,
      reportingYear: 2024,
      esrsReadiness: {
        'ESRS 2': { status: 'complete', score: 82 },
        'ESRS E1': { status: 'complete', score: 88 },
        'ESRS E2': { status: 'partial', score: 55 },
        'ESRS S1': { status: 'partial', score: 70 },
        'ESRS S2': { status: 'planned', score: 40 },
        'ESRS G1': { status: 'partial', score: 75 },
      },
      sfdrArticle: 'n/a',
      tcfdMaturity: { governance: 3, strategy: 3, risk_mgmt: 2, metrics: 3 },
    },
    eu_regulatory: {
      // EUDR: rubber and leather supply chain
      eudrCommodities: ['rubber', 'cattle'],
      suppliersScreened: 480,
      suppliersHighRisk: 42,
      dueDiligenceScore: 74,
      traceabilityPct: '68',
      csddGroup: 'eu_group_1',
      adverseImpacts: ['ENV-02', 'HR-04', 'HR-06'],
    },
    energy_transition: {
      country: 'DE',
      scenario: 'below_2c',
      targetYear: 2040,
      fleetSize: '8200',           // Company + dealer fleet
      currentEvPct: '12',
      targetEvPct2030: '85',
      gridEfToday: '0.385',
      gridEfTarget2030: '0.220',
      evProduction2024: '280000',  // Units EV produced
      targetEvShare2030: '80',     // % of production
    },
  },
};

const RETAILER_SUSTAINABILITY_LEAD = {
  id: 'RETAILER_SUSTAINABILITY_LEAD',
  name: 'Sophie Laurent, Head of ESG Compliance',
  institution: 'PanEuro Retail SA',
  institutionType: 'Pan-European Retailer',
  sector: 'Supply Chain',
  role: 'Sustainability & Regulatory Lead',
  colour: 'bg-pink-600',
  tagline: 'EUDR · CSRD year-1 · CSDDD value chain · Commodity due diligence',
  logo: '🛒',

  modules: {
    supply_chain: {
      entityName: 'PanEuro Retail SA', revenueM: '8400',
      cat1: '620000', cat4: '185000', cat11: '92000', cat12: '68000',
      totalScope3: '965000', sbtiStatus: 'committed',
      sbtiTarget: '-46% Scope 3 by 2030 (vs 2020)',
      sbtiPathway: 'Well below 2°C',
      topSupplierCountries: ['FR','DE','BR','ID','MY'],
    },
    carbon: {
      scope1: '48000', scope2Market: '62000', scope2Location: '89000',
      scope3Total: '965000', entity: 'PanEuro Retail SA',
      sector: 'Retail', revenueM: '8400', gridEfCountry: 'FR',
    },
    dcm: { methodologyCode: 'VM0009', sector: 'Forestry' },
    scenario: { entity: 'PanEuro Retail SA', scenario: 'net_zero_2050' },
    portfolio: {
      waci: 115, finEmissions: 0, pcafScore: 0, greenShare: 8.4,
      label: 'PanEuro Retail SA — CSRD Reporting Entity',
    },
    eu_regulatory: {
      // EUDR: coffee, cocoa, soy, palm oil, wood
      eudrCommodities: ['coffee', 'cocoa', 'soy', 'oil_palm', 'wood'],
      suppliersScreened: 1240,
      suppliersHighRisk: 185,
      dueDiligenceScore: 58,       // Medium compliance
      traceabilityPct: '52',
      csddGroup: 'eu_group_1',
      adverseImpacts: ['ENV-02', 'HR-04', 'HR-07', 'HR-09'],
      eudrCountriesHighRisk: ['BR','ID','MY','NG','CM'],
    },
    regulatory: {
      entity: 'PanEuro Retail SA',
      entitySize: 'large_piu',
      firstReportingYear: 2026,
      reportingYear: 2025,
      esrsReadiness: {
        'ESRS 2': { status: 'partial', score: 68 },
        'ESRS E1': { status: 'partial', score: 72 },
        'ESRS E2': { status: 'planned', score: 28 },
        'ESRS S1': { status: 'complete', score: 82 },
        'ESRS S2': { status: 'partial', score: 55 },
        'ESRS G1': { status: 'partial', score: 70 },
      },
      sfdrArticle: 'n/a',
      tcfdMaturity: { governance: 2, strategy: 2, risk_mgmt: 2, metrics: 2 },
    },
    nature_risk: {
      entity: 'PanEuro Retail SA',
      exposedSectors: ['Agriculture', 'Food & Beverage', 'Forestry'],
      waterRiskScore: 4.8,
      biodiversityFootprintM: 920,
      tnfdLeapPhase: 'Evaluate',
      deforestationRiskScore: 7.2,
    },
    double_materiality: {
      entity: 'PanEuro Retail SA',
      sector: 'Retail',
      reportingYear: 2025,
      materialTopics: ['Deforestation', 'Supply chain labour', 'Packaging waste', 'GHG Scope 3'],
    },
    climate_risk: {
      entity: 'PanEuro Retail SA',
      entity_id: 'PRS-FR-001',
      entity_name: 'PanEuro Retail SA',
      entity_type: 'asset',
      sector_nace: 'G47',
      latitude: 48.86,
      longitude: 2.35,
      asset_value_eur: 12000000000,
      flood_zone: false,
      annual_revenue_eur: 84000000000,
      carbon_intensity_tco2_eur: 0.011,
      capex_green_pct: 22,
      scenario: 'net_zero_2050',
      time_horizon: 10,
      physicalRiskScore: 4.2,
      transitionRiskScore: 4.8,
      sector: 'Retail',
      country: 'FR',
    },
    cbam: {
      product: 'aluminium',
      quantity: '42000',
      origin: 'CN',
      carbonIntensity: '16.8',    // tCO2/t (China aluminium — coal-heavy grid)
      euEtsPrice: '63',
    },
  },
};

const MANUFACTURER_INVESTMENT_LEAD = {
  id: 'MANUFACTURER_INVESTMENT_LEAD',
  name: 'Marco Bianchi, Head of Decarbonisation Finance',
  institution: 'EuroAuto GmbH',
  institutionType: 'Automotive OEM (Tier-1 Exporter)',
  sector: 'Supply Chain',
  role: 'Investment Lead',
  colour: 'bg-purple-600',
  tagline: 'CBAM exposure · Green capex · EV transition ROI · Green bond issuance',
  logo: '💼',

  modules: {
    cbam: {
      product: 'steel', quantity: '185000', origin: 'TR',
      carbonIntensity: '2.10', euEtsPrice: '63',
    },
    supply_chain: {
      entityName: 'EuroAuto GmbH', revenueM: '12800',
      cat1: '1850000', cat4: '245000', cat11: '4200000',
      totalScope3: '6851600', sbtiStatus: 'approved',
      sbtiTarget: '-42% Scope 1+2 by 2030; -25% Scope 3 by 2030',
      sbtiPathway: '1.5°C',
      topSupplierCountries: ['DE','PL','CZ','CN','RO'],
    },
    dcm: { methodologyCode: 'ACM0024_ElectricVehicles', sector: 'Transport' },
    scenario: { entity: 'EuroAuto GmbH', scenario: 'delayed_transition' },
    carbon: {
      scope1: '285000', scope2Market: '95000', scope2Location: '148000',
      scope3Total: '6851600', entity: 'EuroAuto GmbH',
      sector: 'Automotive', revenueM: '12800', gridEfCountry: 'DE',
    },
    project_finance: {
      // EV gigafactory green bond
      projectName: 'Zwickau EV Battery Gigafactory',
      technology: 'battery_manufacturing',
      capacityMW: '0',             // Not a power asset
      capexM: '2200',              // €2.2 B gigafactory investment
      debtPct: '55',
      interestRate: '3.8',
      loanTermYears: '12',
      dscrTarget: '1.45',
      annualRevenueM: '1840',      // Battery supply revenue
      opexM: '285',
      greenBondFramework: 'ICMA_GBS',
      isCLPFO: false,
    },
    stranded_assets: {
      // ICE powertrain manufacturing lines
      assetType: 'manufacturing',
      technology: 'ICE_powertrain',
      investedCapitalM: '4800',    // Book value of ICE assets
      remainingUsefulLife: '12',   // years
      evTransitionYear: '2030',    // Target ICE phase-out
      strandingRisk: '0.62',
      strandedValueM: '2100',      // Expected stranded book value
    },
    energy_transition: {
      country: 'DE',
      scenario: 'below_2c',
      targetYear: 2040,
      fleetSize: '8200',
      currentEvPct: '12',
      targetEvPct2030: '85',
      gridEfToday: '0.385',
      gridEfTarget2030: '0.220',
      evProduction2024: '280000',
      targetEvShare2030: '80',
    },
    climate_risk: {
      entity: 'EuroAuto GmbH',
      entity_id: 'EAG-DE-002',
      entity_name: 'EuroAuto GmbH',
      entity_type: 'asset',
      sector_nace: 'C29',
      latitude: 48.14,
      longitude: 11.58,
      asset_value_eur: 185000000000,
      flood_zone: false,
      annual_revenue_eur: 185000000000,
      carbon_intensity_tco2_eur: 0.65,
      capex_green_pct: 38,
      scenario: 'below_2c',
      time_horizon: 10,
      physicalRiskScore: 3.6,
      transitionRiskScore: 7.2,
      sector: 'Automotive',
      country: 'DE',
    },
    green_hydrogen: {
      // H2-DRI steel sourcing for supply chain decarbonisation
      electrolyserMW: '0',
      electricityPriceEurMwh: '42',
      targetSector: 'steel_dri',
      rfnboCompliant: true,
      supplierH2PriceEurKg: '4.8', // Target green H2 price for DRI steel
    },
  },
};

// ─── MANUFACTURING ────────────────────────────────────────────────────────────

const STEEL_ANALYTICS_LEAD = {
  id: 'STEEL_ANALYTICS_LEAD',
  name: 'Henrik Müller, Head of Climate & ETS Analytics',
  institution: 'EuroSteel AG',
  institutionType: 'Integrated Steel Producer (EU ETS Phase IV)',
  sector: 'Manufacturing',
  role: 'Analytics Lead',
  colour: 'bg-gray-700',
  tagline: 'EU ETS Phase IV · CBAM · BF-BOF decarbonisation · Green hydrogen DRI',
  logo: '🏭',

  modules: {
    cbam: {
      product: 'steel', quantity: '0', origin: 'DE',
      carbonIntensity: '1.85', euEtsPrice: '63',
      exportQuantity: '580000', embeddedCarbon: '1072300',
    },
    carbon: {
      scope1: '5900000', scope2Market: '380000', scope2Location: '520000',
      scope3Total: '1480000', entity: 'EuroSteel AG',
      sector: 'Steel', revenueM: '4200', gridEfCountry: 'DE',
    },
    supply_chain: {
      entityName: 'EuroSteel AG', revenueM: '4200',
      cat1: '820000', cat4: '148000', totalScope3: '1480000',
      sbtiStatus: 'committed',
      sbtiTarget: '-20% Scope 1 by 2030; net zero by 2050 (green H2 DRI pathway)',
      sbtiPathway: 'Well below 2°C',
      topSupplierCountries: ['AU','BR','UA','ZA','SE'],
    },
    dcm: { methodologyCode: 'AM0075_CarbonCapture', sector: 'Industry' },
    scenario: { entity: 'EuroSteel AG', scenario: 'delayed_transition' },
    portfolio: {
      waci: 1405, finEmissions: 0, pcafScore: 0, greenShare: 1.8,
      label: 'EuroSteel AG — CSRD E1 / ETS Analytics',
    },
    gar_ets: {
      // ETS compliance (producer lens)
      installationId: 'DE_ETS_EUST_001',
      sector: 'Iron & Steel',
      benchmark: 'hot_metal',
      hal: '3150000',              // tonnes HAL (Historical Activity Level)
      year: '2025',
      verifiedEmissions: '5900000',
      freeAllocation: '4250000',   // Free allocation based on BM × HAL × CLEF
      purchased: '1650000',        // Purchased EUAs to cover deficit
      banked: '180000',
      carbonPrice: '63',
      carbonLeakage: true,         // Steel is carbon leakage listed
      etsDeficitTco2: '1650000',
      etsComplianceCostM: '103.95', // 1.65M × €63
    },
    green_hydrogen: {
      // H2-DRI transition roadmap
      electrolyserMW: '500',       // Phase 1 electrolyser
      capacityFactor: '0.50',
      capexPerKw: '780',           // 2026 alkaline, volume discount
      stackLifetimeH: '90000',
      electricityPriceEurMwh: '35',
      waterCostEurM3: '2.2',
      deliveryMode: 'on_site',
      targetSector: 'steel_dri',
      rfnboCompliant: true,
      h2PerTonneSteel: '54',       // kg H2 per tonne DRI steel
      costBreakdownEurKg: { capex: 0.85, opex: 0.42, electricity: 1.98, water: 0.05, other: 0.15 },
    },
    stranded_assets: {
      assetType: 'manufacturing',
      technology: 'BF_BOF',
      investedCapitalM: '8400',
      remainingUsefulLife: '18',
      evTransitionYear: '2040',    // DRI transition
      strandingRisk: '0.48',
      strandedValueM: '3200',
    },
    climate_risk: {
      entity: 'EuroSteel AG',
      entity_id: 'ESG-DE-001',
      entity_name: 'EuroSteel AG',
      entity_type: 'asset',
      sector_nace: 'C24',
      latitude: 51.46,
      longitude: 7.01,
      asset_value_eur: 6800000000,
      flood_zone: true,
      annual_revenue_eur: 4200000000,
      carbon_intensity_tco2_eur: 1.41,
      capex_green_pct: 18,
      scenario: 'delayed_transition',
      time_horizon: 10,
      physicalRiskScore: 3.8,      // Ruhr valley flood/heat risk
      transitionRiskScore: 9.2,    // Very high — hard-to-abate sector
      sector: 'Steel',
      country: 'DE',
    },
    sector_assessments: {
      plantType: 'blast_furnace',
      installYear: '1992',
      location: 'Duisburg, Germany',
      capacityMW: '0',
      annualOutputKt: '3150',
      co2PerTonneProduct: '1.85',
      euBenchmark: '0.709',        // BF-BOF benchmark
      benchmarkGap: '1.141',
    },
    regulatory: {
      entity: 'EuroSteel AG',
      entitySize: 'large_piu',
      firstReportingYear: 2025,
      reportingYear: 2024,
      esrsReadiness: {
        'ESRS 2': { status: 'complete', score: 85 },
        'ESRS E1': { status: 'complete', score: 90 },
        'ESRS E2': { status: 'partial', score: 42 },
        'ESRS S1': { status: 'partial', score: 68 },
        'ESRS G1': { status: 'complete', score: 88 },
      },
      sfdrArticle: 'n/a',
      tcfdMaturity: { governance: 3, strategy: 3, risk_mgmt: 3, metrics: 4 },
    },
    energy_transition: {
      country: 'DE',
      scenario: 'delayed_transition',
      targetYear: 2045,
      // Energy mix transition for the steel plant
      currentCoalPct: '72',
      currentGasPct: '18',
      currentElecPct: '10',
      targetGreenH2Pct2030: '15',
      targetGreenH2Pct2050: '75',
      totalEnergyConsumptionGwh: '18400',
      energyIntensityGjPerTonne: '18.2',
      plants: [
        { id: 1, name: 'BF-BOF Blast Furnace #1', technology: 'coal', capacity_mw: 650, age_years: 28, annual_emissions_tco2: 3100000, replacement_tech: 'green_hydrogen' },
        { id: 2, name: 'BF-BOF Blast Furnace #2', technology: 'coal', capacity_mw: 620, age_years: 21, annual_emissions_tco2: 2800000, replacement_tech: 'green_hydrogen' },
        { id: 3, name: 'EAF Electric Arc Furnace', technology: 'wind', capacity_mw: 180, age_years: 8, annual_emissions_tco2: 0, replacement_tech: 'wind' },
      ],
    },
    nature_risk: {
      entity: 'EuroSteel AG',
      exposedSectors: ['Mining & Metals', 'Steel'],
      waterRiskScore: 5.1,         // High water use: ~5 m³/t steel
      biodiversityFootprintM: 240,
      tnfdLeapPhase: 'Locate',
    },
  },
};

const PHARMA_SUSTAINABILITY_LEAD = {
  id: 'PHARMA_SUSTAINABILITY_LEAD',
  name: 'Amira Hassan, Head of Sustainability',
  institution: 'PharmaCo BV',
  institutionType: 'Global Pharmaceutical Manufacturer',
  sector: 'Manufacturing',
  role: 'Sustainability & Regulatory Lead',
  colour: 'bg-teal-600',
  tagline: 'CSRD ESRS E1-E5 · Nature risk (TNFD LEAP) · Scope 3 Cat 1 APIs',
  logo: '💊',

  modules: {
    carbon: {
      scope1: '185000', scope2Market: '48000', scope2Location: '112000',
      scope3Total: '2850000', entity: 'PharmaCo BV',
      sector: 'Pharmaceuticals', revenueM: '9600', gridEfCountry: 'NL',
    },
    supply_chain: {
      entityName: 'PharmaCo BV', revenueM: '9600',
      cat1: '1200000', cat4: '195000', cat6: '38000', cat11: '980000',
      totalScope3: '2850000', sbtiStatus: 'approved',
      sbtiTarget: '-50% Scope 1+2 by 2030; -42% Scope 3 by 2030 (vs 2019)',
      sbtiPathway: '1.5°C',
      topSupplierCountries: ['CN','IN','DE','US','IE'],
    },
    dcm: { methodologyCode: 'AMS_III_A_WastewaterSmallScale', sector: 'Waste' },
    scenario: { entity: 'PharmaCo BV', scenario: 'net_zero_2050' },
    portfolio: {
      waci: 297, finEmissions: 0, pcafScore: 0, greenShare: 14.2,
      label: 'PharmaCo BV — CSRD Reporting Entity',
    },
    nature_risk: {
      entity: 'PharmaCo BV',
      // TNFD LEAP — high dependency on water & biodiversity for API synthesis
      exposedSectors: ['Pharmaceuticals', 'Chemicals', 'Agriculture'],
      waterRiskScore: 7.4,         // Very high — API water intensity ~1,800 L/unit
      biodiversityFootprintM: 1450,
      tnfdLeapPhase: 'Evaluate',
      deforestationRiskScore: 2.4,
      waterWithdrawalM3Yr: '18400000',
      criticalHabitatProximity: ['Hyderabad API cluster', 'Hangzhou industrial zone'],
    },
    regulatory: {
      entity: 'PharmaCo BV',
      entitySize: 'large_piu',
      firstReportingYear: 2025,
      reportingYear: 2024,
      esrsReadiness: {
        'ESRS 2': { status: 'complete', score: 90 },
        'ESRS E1': { status: 'complete', score: 88 },
        'ESRS E2': { status: 'partial', score: 62 },
        'ESRS E3': { status: 'complete', score: 82 },  // Water — high priority
        'ESRS E4': { status: 'partial', score: 55 },
        'ESRS E5': { status: 'partial', score: 48 },
        'ESRS S1': { status: 'complete', score: 92 },
        'ESRS S2': { status: 'partial', score: 70 },
        'ESRS G1': { status: 'complete', score: 95 },
      },
      sfdrArticle: 'n/a',
      tcfdMaturity: { governance: 4, strategy: 4, risk_mgmt: 3, metrics: 4 },
    },
    double_materiality: {
      entity: 'PharmaCo BV',
      sector: 'Pharmaceuticals',
      reportingYear: 2024,
      materialTopics: ['Water use & quality', 'Biodiversity', 'API supply chain', 'Patient access'],
    },
    eu_regulatory: {
      // CSDDD — global pharmaceutical supply chain
      eudrCommodities: [],         // No forest-risk commodities
      csddGroup: 'eu_group_1',
      adverseImpacts: ['ENV-03', 'ENV-06', 'HR-01', 'HR-05', 'HR-09'],
      ddComplianceScore: 72,
      valueChainTier: 3,
      entityRevenue: '9600',
      entityEmployees: '52000',
    },
    climate_risk: {
      entity: 'PharmaCo BV',
      entity_id: 'PCB-NL-001',
      entity_name: 'PharmaCo BV',
      entity_type: 'asset',
      sector_nace: 'C21',
      latitude: 52.37,
      longitude: 4.90,
      asset_value_eur: 14000000000,
      flood_zone: false,
      annual_revenue_eur: 9600000000,
      carbon_intensity_tco2_eur: 0.28,
      capex_green_pct: 35,
      scenario: 'net_zero_2050',
      time_horizon: 10,
      physicalRiskScore: 4.5,      // Supply chain in India/China flood-prone areas
      transitionRiskScore: 3.8,
      sector: 'Pharmaceuticals',
      country: 'NL',
    },
    sustainability: {
      // BREEAM + LEED for NL/US facilities
      certificationTarget: 'BREEAM_Excellent',
      currentScore: 72,            // % BREEAM score
      energyUse: '185',            // kWh/m²/yr
      waterUse: '4.2',             // m³/m²/yr
      wasteRecyclingPct: '68',
      renewablePct: '42',
      buildingArea: '285000',      // m² total floor area
    },
    cbam: {
      product: 'chemicals',
      quantity: '28000',           // tonnes pharma intermediates imported
      origin: 'CN',
      carbonIntensity: '4.2',
      euEtsPrice: '63',
    },
  },
};

const REAL_ESTATE_INVESTMENT_LEAD = {
  id: 'REAL_ESTATE_INVESTMENT_LEAD',
  name: 'Julia Weber, Head of Sustainable Investments',
  institution: 'PropFund AG',
  institutionType: 'Open-Ended Real Estate Fund (Germany)',
  sector: 'Manufacturing',
  role: 'Investment Lead',
  colour: 'bg-amber-600',
  tagline: 'CRREM pathways · RICS ESG · Green premium · Stranded RE identification',
  logo: '🏢',

  modules: {
    real_estate: {
      buildingType: 'office',
      area: '12500',               // m² NLA
      location: 'Frankfurt, Germany',
      currentEui: '168',           // kWh/m²/yr actual
      crremTarget2030: '108',      // kWh/m²/yr CRREM office Germany
      crremTarget2050: '55',
      greenCert: 'BREEAM Very Good',
      purchasePrice: '52000000',
      renovationCapex: '4200000',
      rentPerSqm: '385',           // €/m²/yr Frankfurt prime office
      greenPremium: '8.5',         // % green rent premium Frankfurt (CBRE 2024)
      vacancyRate: '4.2',
    },
    carbon: {
      scope1: '0', scope2Market: '0', scope2Location: '185000',
      scope3Total: '420000', entity: 'PropFund AG',
      sector: 'Real Estate', revenueM: '185', gridEfCountry: 'DE',
    },
    dcm: { methodologyCode: 'VM0026', sector: 'Buildings' },
    scenario: { entity: 'PropFund AG', scenario: 'below_2c' },
    portfolio: {
      waci: 42, finEmissions: 0, pcafScore: 0, greenShare: 38.2,
      label: 'PropFund AG — RE Portfolio (€2.8 B AUM, 82 assets)',
    },
    sustainability: {
      // GRESB 2024 results
      gresbScore: 82,              // Out of 100
      gresbRating: '4 Stars',
      gresbPercentile: '78',
      energyIntensity: '168',      // kWh/m²/yr portfolio average
      ghgIntensity: '28.4',        // kgCO2/m²/yr
      waterIntensity: '0.85',      // m³/m²/yr
      wasteRecyclingPct: '74',
      greenCertPct: '38.2',
      currentScore: 82,
      certificationTarget: 'BREEAM_Excellent',
      // GRESBCalculator form fields
      portfolio_name: 'PropFund AG — European RE Portfolio',
      entity_type: 'standing_investments',
      region: 'europe',
      total_aum: '2800000000',
      num_assets: '82',
      component_scores: {
        management: 22,            // /25 — strong governance
        policy: 7,                 // /8 — BREEAM-aligned policies
        risk_management: 9,        // /10 — flood+heat risk mapped
        stakeholder_engagement: 8, // /9 — tenant engagement programs
        performance_indicators: 36, // /48 — good data coverage
      },
    },
    valuation: {
      // Income approach — Frankfurt office
      nla: '12500',
      marketRent: '385',
      vacancyRate: '4.2',
      capRate: '3.85',             // % Frankfurt prime office cap rate (JLL Q1 2025)
      opexPct: '18',
      greenPremium: '8.5',
      buildingAge: '2012',
      epcRating: 'B',
    },
    residential_re: {
      // Residential portfolio sub-fund
      avgEpcRating: 'C',
      avgEui: '185',               // kWh/m²/yr (German Altbau stock)
      crremTarget2030: '130',
      crremTarget2050: '70',
      portfolioSqm: '820000',      // 820k m² residential
      avgLtv: '52.4',
      avgYearBuilt: '1985',
      retrofitCapexM: '48',        // €48 M retrofit capex planned
      greenMortgagePct: '22.8',
    },
    nature_risk: {
      entity: 'PropFund AG',
      exposedSectors: ['Real Estate', 'Construction'],
      waterRiskScore: 3.2,
      biodiversityFootprintM: 95,
      tnfdLeapPhase: 'Locate',
      floodRiskPct: '12.4',        // % of portfolio with high flood risk
      heatStressRiskPct: '18.8',
    },
    stranded_assets: {
      assetType: 'real_estate',
      technology: 'office_building',
      investedCapitalM: '2800',
      remainingUsefulLife: '30',
      strandingRisk: '0.22',
      strandedValueM: '420',       // EUI non-compliance stranding
      crremPathwayGap: '60',       // kWh/m²/yr gap vs 2030 pathway
    },
    climate_risk: {
      entity: 'PropFund AG',
      entity_id: 'PFA-DE-001',
      entity_name: 'PropFund AG',
      entity_type: 'portfolio',
      sector_nace: 'L68',
      latitude: 50.11,
      longitude: 8.68,
      asset_value_eur: 2800000000,
      flood_zone: true,
      annual_revenue_eur: 180000000,
      carbon_intensity_tco2_eur: 0.023,
      capex_green_pct: 55,
      scenario: 'below_2c',
      time_horizon: 10,
      physicalRiskScore: 5.2,      // Flood + heat risk to RE portfolio
      transitionRiskScore: 4.8,    // EPC regulatory tightening
      sector: 'Real Estate',
      country: 'DE',
    },
    gar_ets: {
      // As a real estate entity: ETS2 building exposure
      entityType: 'BUILDING_OWNER',
      sector: 'Real Estate',
      annualFuelConsumptionGj: '285000',  // Portfolio total
      scope1EmissionsTco2: '0',
      annualRevenueEur: '185000000',
      hasEmissionMonitoring: true,
      hasEnergyAudit: true,
      plannedRetrofitYear: '2026',
    },
    eu_regulatory: {
      // CSDDD — construction supply chain
      csddGroup: 'eu_group_2',
      adverseImpacts: ['ENV-01', 'HR-04'],
      ddComplianceScore: 78,
      entityRevenue: '185',
      entityEmployees: '420',
    },
  },
};

// ─── Master registry ──────────────────────────────────────────────────────────

export const ALL_PERSONAS = [
  EU_BANK_INVESTMENT_LEAD,
  EU_BANK_ANALYTICS_LEAD,
  EU_BANK_SUSTAINABILITY_LEAD,
  UTILITY_INVESTMENT_LEAD,
  UTILITY_ANALYTICS_LEAD,
  OIL_GAS_SUSTAINABILITY_LEAD,
  MANUFACTURER_ANALYTICS_LEAD,
  RETAILER_SUSTAINABILITY_LEAD,
  MANUFACTURER_INVESTMENT_LEAD,
  STEEL_ANALYTICS_LEAD,
  PHARMA_SUSTAINABILITY_LEAD,
  REAL_ESTATE_INVESTMENT_LEAD,
];

export const SECTORS = ['Finance', 'Energy', 'Supply Chain', 'Manufacturing'];

export const ROLES = [
  'Investment Lead',
  'Analytics Lead',
  'Sustainability & Regulatory Lead',
];

/** Quick lookup by id */
export const PERSONA_BY_ID = Object.fromEntries(
  ALL_PERSONAS.map(p => [p.id, p])
);

/** Default persona if nothing stored */
export const DEFAULT_PERSONA_ID = 'EU_BANK_INVESTMENT_LEAD';
