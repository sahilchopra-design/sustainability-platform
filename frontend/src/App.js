import React, { useState, useEffect, useRef, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route, NavLink, useLocation, useNavigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Provider } from 'react-redux';
import { store } from './store';
import './App.css';
import { ErrorBoundary, RouteErrorBoundary } from './components/shared/ErrorBoundary';

import Dashboard from './pages/Dashboard';
import Portfolios from './pages/Portfolios';
import PortfolioDetail from './pages/PortfolioDetail';
import Analysis from './pages/Analysis';
import Results from './pages/Results';
import ScenarioData from './pages/ScenarioData';
import ScenarioBuilder from './pages/ScenarioBuilder';
import DataHub from './pages/DataHub';
import ComparisonPage from './pages/ComparisonPage';
import ScenarioBrowserPage from './pages/ScenarioBrowserPage';
import ImpactCalculatorPage from './pages/ImpactCalculatorPage';
import PortfolioManagerPage from './pages/PortfolioManagerPage';
import LoginPage from './pages/LoginPage';
import AlertsPage from './pages/AlertsPage';
import NGFSScenariosPage from './pages/NGFSScenariosPage';
import CustomBuilderPage from './pages/CustomBuilderPage';
import SubAnalysisPage from './pages/SubAnalysisPage';
import CBAMPage from './pages/CBAMPage';
import CarbonDashboard from './features/carbon/pages/CarbonDashboard';
import DCMCalculatorPage from './features/carbon/pages/DCMCalculatorPage';
import NatureRiskPage from './features/nature-risk/pages/NatureRiskPage';
import StrandedAssetsPage from './features/stranded-assets/pages/StrandedAssetsPage';
import UnifiedValuationPage from './features/valuation/pages/UnifiedValuationPage';
import SustainabilityPage from './features/sustainability/pages/SustainabilityPage';
import ScenarioAnalysisPage from './features/scenarios/pages/ScenarioAnalysisPage';
import PortfolioAnalyticsPage from './features/portfolio-analytics/pages/PortfolioAnalyticsPage';
import FinancialRiskPage from './features/financial-risk/pages/FinancialRiskPage';
import RealEstateAssessmentPage from './features/real-estate/pages/RealEstateAssessmentPage';
import SupplyChainPage from './features/supply-chain/pages/SupplyChainPage';
import SectorAssessmentsPage from './features/supply-chain/pages/SectorAssessmentsPage';
import RegulatoryPage from './features/regulatory/pages/RegulatoryPage';
import InteractiveDashboard from './pages/InteractiveDashboard';
import PortfolioHealthPage from './features/portfolio-health/pages/PortfolioHealthPage';
import GlidepathTrackerPage from './features/glidepath/GlidepathTrackerPage';
import PeerBenchmarkPage from './features/regulatory/pages/PeerBenchmarkPage';
import AnalystPortfoliosPage from './features/portfolio-analytics/AnalystPortfoliosPage';
import CompanyProfilesPage from './features/company-profiles/CompanyProfilesPage';
import DataIntakeDashboard from './features/data-intake/pages/DataIntakeDashboard';
import LoanPortfolioUpload from './features/data-intake/pages/LoanPortfolioUpload';
import CounterpartyEmissionsWizard from './features/data-intake/pages/CounterpartyEmissionsWizard';
import RealEstateEUIUpload from './features/data-intake/pages/RealEstateEUIUpload';
import ShippingFleetUpload from './features/data-intake/pages/ShippingFleetUpload';
import SteelBorrowersEntry from './features/data-intake/pages/SteelBorrowersEntry';
import ProjectFinanceIntake from './features/data-intake/pages/ProjectFinanceIntake';
import InternalConfigPage from './features/data-intake/pages/InternalConfigPage';
import PersonaTemplatesPage from './features/data-intake/pages/PersonaTemplatesPage';
import EngagementTrackerPage from './features/financial-risk/pages/EngagementTrackerPage';
import MonteCarloPage from './features/risk/MonteCarloPage';
import ScenarioBuilderPage from './features/scenario-builder/pages/ScenarioBuilderPage';
import ScenarioGalleryPage from './features/scenario-builder/pages/ScenarioGalleryPage';
import AsiaRegulatoryPage from './pages/AsiaRegulatoryPage';
import ChinaTradePage from './pages/ChinaTradePage';
import DataMappingPage from './pages/DataMappingPage';
import CA100Page from './features/esg-disclosure/pages/CA100Page';
import CountryRiskPage from './features/country-risk/pages/CountryRiskPage';
import DataPreviewPage from './pages/DataPreviewPage';
import ClimateRiskPage from './features/climate-risk/pages/ClimateRiskPage';
import DisclosureFrameworksPage from './features/disclosure-frameworks/pages/DisclosureFrameworksPage';
import EURegulatoryHubPage from './features/eu-regulatory/pages/EURegulatoryHubPage';
import BankingCapitalPage from './features/banking-capital/pages/BankingCapitalPage';
import AssetManagementPage from './features/asset-management/pages/AssetManagementPage';
import SovereignEmissionsPage from './features/sovereign-emissions/pages/SovereignEmissionsPage';
import PlatformIntelligencePage from './features/platform-intelligence/pages/PlatformIntelligencePage';
import DoubleMaterialityPage from './features/double-materiality/pages/DoubleMaterialityPage';
import SFDRPAIPage from './features/sfdr-pai/pages/SFDRPAIPage';
import XBRLPage from './features/xbrl/pages/XBRLPage';
import PEDealsPage from './features/pe-deals/pages/PEDealsPage';
import ResidentialREPage from './features/residential-re/pages/ResidentialREPage';
import TechnologyRiskPage from './features/technology-risk/pages/TechnologyRiskPage';
import FundManagementPage from './features/fund-management/pages/FundManagementPage';
import DMEDashboardPage from './features/dme/pages/DMEDashboardPage';
import SentimentAnalysisPage from './features/sentiment-analysis/pages/SentimentAnalysisPage';
import SovereignClimateRiskPage from './features/sovereign-climate-risk/pages/SovereignClimateRiskPage';
import SECClimatePage from './features/sec-climate/pages/SECClimatePage';
import GreenHydrogenPage from './features/green-hydrogen/pages/GreenHydrogenPage';
import StressTestingPage from './features/stress-testing/pages/StressTestingPage';
import GeothermalPage from './features/geothermal/pages/GeothermalPage';
import NotFoundPage from './components/shared/NotFoundPage';
import GarEtsPage from './features/gar-ets/pages/GarEtsPage';
import ProjectFinancePage from './features/project-finance/pages/ProjectFinancePage';
import DataHubIngestionPage from './features/data-hub/pages/DataHubIngestionPage';
import EnergyFinancePage from './features/energy-finance/pages/EnergyFinancePage';
import EnergyTransitionPage from './features/energy-transition/pages/EnergyTransitionPage';
import EiopaStressPage from './features/eiopa-stress/pages/EiopaStressPage';
import IORPPensionPage from './features/iorp-pension/pages/IORPPensionPage';
import AssurancePage from './features/assurance/pages/AssurancePage';
import SFDRAnnexPage from './features/sfdr-annex/pages/SFDRAnnexPage';
import StewardshipPage from './features/stewardship/pages/StewardshipPage';
import EUDRPage from './features/eudr/pages/EUDRPage';
import CSDDDPage from './features/csddd/pages/CSDDDPage';
import BaselCapitalPage from './features/basel-capital/pages/BaselCapitalPage';
import TNFDPage from './features/tnfd/pages/TNFDPage';
import PCAFQualityPage from './features/pcaf-quality/pages/PCAFQualityPage';
import CDPPage from './features/cdp/pages/CDPPage';
import GRIPage from './features/gri/pages/GRIPage';
import SASBPage from './features/sasb/pages/SASBPage';
import ModelValidationPage from './features/model-validation/pages/ModelValidationPage';
import UKSDRPage from './features/uk-sdr/pages/UKSDRPage';
import MiFIDSPTPage from './features/mifid-spt/pages/MiFIDSPTPage';
import TCFDMetricsPage from './features/tcfd-metrics/pages/TCFDMetricsPage';
import EUGBSPage from './features/eu-gbs/pages/EUGBSPage';
import PRIIPSKIDPage from './features/priips-kid/pages/PRIIPSKIDPage';
import ESMAFundNamesPage from './features/esma-fund-names/pages/ESMAFundNamesPage';
import SLFinancePage from './features/sl-finance/pages/SLFinancePage';
import IFRSS1Page from './features/ifrs-s1/pages/IFRSS1Page';
import EUTaxonomyGARPage from './features/eu-taxonomy-gar/pages/EUTaxonomyGARPage';
import EBAPillar3Page from './features/eba-pillar3/pages/EBAPillar3Page';
import Scope3CategoriesPage from './features/scope3-categories/pages/Scope3CategoriesPage';
import SFDRProductReportingPage from './features/sfdr-product-reporting/pages/SFDRProductReportingPage';
import BiodiversityFinancePage from './features/biodiversity-finance/pages/BiodiversityFinancePage';
import IFRSS2Page from './features/ifrs-s2/pages/IFRSS2Page';
import GRIStandardsPage from './features/gri-standards/pages/GRIStandardsPage';
import TPTTransitionPlanPage from './features/tpt-transition-plan/pages/TPTTransitionPlanPage';
import PCAFSovereignPage from './features/pcaf-sovereign/pages/PCAFSovereignPage';
import ESRSE2E5Page from './features/esrs-e2-e5/pages/ESRSE2E5Page';
import GreenwashingPage from './features/greenwashing/pages/GreenwashingPage';
import CarbonCreditQualityPage from './features/carbon-credit-quality/pages/CarbonCreditQualityPage';
import ClimateStressTestPage from './features/climate-stress-test/pages/ClimateStressTestPage';
import TNFDLEAPPage from './features/tnfd-leap/pages/TNFDLEAPPage';
import NetZeroTargetsPage from './features/net-zero-targets/pages/NetZeroTargetsPage';
import ESGDataQualityPage from './features/esg-data-quality/pages/ESGDataQualityPage';
import RegulatoryPenaltiesPage from './features/regulatory-penalties/pages/RegulatoryPenaltiesPage';
import BaselLiquidityPage from './features/basel-liquidity/pages/BaselLiquidityPage';
import SocialTaxonomyPage from './features/social-taxonomy/pages/SocialTaxonomyPage';
import ForcedLabourPage from './features/forced-labour/pages/ForcedLabourPage';
import TransitionFinancePage from './features/transition-finance/pages/TransitionFinancePage';
import CSRDDMAPage from './features/csrd-dma/pages/CSRDDMAPage';
import PhysicalHazardPage from './features/physical-hazard/pages/PhysicalHazardPage';
import AvoidedEmissionsPage from './features/avoided-emissions/pages/AvoidedEmissionsPage';
import BiodiversityFinanceV2Page from './features/biodiversity-finance-v2/pages/BiodiversityFinanceV2Page';
import PrudentialClimateRiskPage from './features/prudential-climate-risk/pages/PrudentialClimateRiskPage';
import CarbonMarketsIntelPage from './features/carbon-markets-intel/pages/CarbonMarketsIntelPage';
import JustTransitionPage from './features/just-transition/pages/JustTransitionPage';
import ShippingMaritimePage from './features/shipping-maritime/pages/ShippingMaritimePage';
import AviationClimatePage from './features/aviation-climate/pages/AviationClimatePage';
import CommercialREPage from './features/commercial-re/pages/CommercialREPage';
import InfrastructureFinancePage from './features/infrastructure-finance/pages/InfrastructureFinancePage';
import NatureBasedSolutionsPage from './features/nature-based-solutions/pages/NatureBasedSolutionsPage';
import WaterRiskPage from './features/water-risk/pages/WaterRiskPage';
import FoodSystemPage from './features/food-system/pages/FoodSystemPage';
import CircularEconomyPage from './features/circular-economy/pages/CircularEconomyPage';
import ClimateLitigationPage from './features/climate-litigation/pages/ClimateLitigationPage';    // E56 Climate Litigation & Legal Risk
import ESGRatingsPage from './features/esg-ratings/pages/ESGRatingsPage';                        // E57 ESG Ratings Reform
import MethaneFugitivePage from './features/methane-fugitive/pages/MethaneFugitivePage';          // E58 Methane & Fugitive Emissions
import HealthClimatePage from './features/health-climate/pages/HealthClimatePage';                // E59 Health-Climate Nexus
import MaritimePage from './features/maritime/pages/MaritimePage';                                // E60 Maritime & Shipping Decarbonisation
import HydrogenPage from './features/hydrogen/pages/HydrogenPage';                               // E61 Hydrogen Economy Finance
import CDRPage from './features/cdr/pages/CDRPage';                                              // E63 Carbon Removal & CDR Finance
import BiodiversityCreditsPage from './features/biodiversity-credits/pages/BiodiversityCreditsPage'; // E65 Biodiversity Credits & Nature Markets
import Scope3AnalyticsPage from './features/scope3-analytics/pages/Scope3AnalyticsPage';          // E67 Scope 3 Deep-Dive Analytics
import BlueEconomyPage from './features/blue-economy/pages/BlueEconomyPage';                      // E68 Blue Economy & Ocean Finance
import SovereignDebtClimatePage from './features/sovereign-debt-climate/pages/SovereignDebtClimatePage'; // E69 Climate-Linked Sovereign Debt
import LossDamageFinancePage from './features/loss-damage-finance/pages/LossDamageFinancePage';   // E70 Loss & Damage Finance
import CarbonPriceETSPage from './features/carbon-price-ets/pages/CarbonPriceETSPage';            // E71 Carbon Price Forecasting & ETS Analytics
import BlendedFinancePage from './features/blended-finance/pages/BlendedFinancePage';           // E72 Blended Finance & DFI
import MRVPage from './features/mrv/pages/MRVPage';                                              // E73 Climate Data & MRV Infrastructure
import RealAssetDecarbPage from './features/real-asset-decarb/pages/RealAssetDecarbPage';        // E74 Real Asset Decarbonisation
import TradeFinanceESGPage from './features/trade-finance-esg/pages/TradeFinanceESGPage';         // E75 Sustainable Trade Finance
import AIRiskPage from './features/ai-risk/pages/AIRiskPage';                             // E76 AI & ML Risk Finance
import NatureCapitalPage from './features/nature-capital/pages/NatureCapitalPage';         // E77 Nature Capital Accounting
import ClimateFinancePage from './features/climate-finance/pages/ClimateFinancePage';       // E78 Climate Finance Flows
import ESGMAPage from './features/esg-ma/pages/ESGMAPage';                                 // E79 ESG M&A Due Diligence
import { PersonaProvider } from './context/PersonaContext';
import PersonaSwitcher from './components/shared/PersonaSwitcher';
import GlobalDemoBanner from './components/shared/GlobalDemoBanner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchOnWindowFocus: false, retry: 1 } },
});

// ─── Nav structure ────────────────────────────────────────────────────────────

const NAV_GROUPS = [
  {
    label: 'Pulse',
    items: [
      { to: '/portfolio-health',   icon: 'activity',      label: 'Portfolio Health',      badge: 'NEW' },
    ],
  },
  {
    label: 'DME',
    items: [
      { to: '/dme-dashboard',       icon: 'activity',    label: 'DME Dashboard',          badge: 'VELOCITY' },
      { to: '/sentiment',            icon: 'message-circle', label: 'Sentiment Analysis',   badge: 'NLP' },
    ],
  },
  {
    label: 'Analytics',
    items: [
      { to: '/interactive',        icon: 'bar-chart',     label: 'Interactive Analytics', badge: 'LIVE' },
      { to: '/',                   icon: 'layout',        label: 'Overview Dashboard',   end: true },
      { to: '/impact',             icon: 'target',        label: 'Impact Calculator' },
      { to: '/portfolio-analytics',icon: 'pie-chart',     label: 'Portfolio Analytics' },
      { to: '/analyst-portfolios', icon: 'briefcase',     label: 'Analyst Workbench',    badge: 'NEW' },
      { to: '/glidepath-tracker',  icon: 'trending-up',   label: 'Glidepath Tracker',    badge: 'NEW' },
      { to: '/asset-management', icon: 'briefcase',     label: 'Asset Management',     badge: 'PACTA·GBS' },
      { to: '/fund-management',    icon: 'briefcase',     label: 'Fund Management',      badge: 'ILPA·SFDR' },
      { to: '/pe-deals',           icon: 'bar-chart',     label: 'PE Deal Pipeline',     badge: 'NEW' },
      { to: '/scenario-analysis',  icon: 'calculator',    label: 'Scenario Analysis' },
      { to: '/sub-analysis',       icon: 'microscope',    label: 'Sub-Parameter' },
    ],
  },
  {
    label: 'ESG Modules',
    items: [
      { to: '/carbon',             icon: 'leaf',          label: 'Carbon Credits' },
      { to: '/dcm-calculator',     icon: 'flask',         label: 'DCM Methodology Engine', badge: 'NEW' },
      { to: '/nature-risk',        icon: 'tree',          label: 'Nature Risk (TNFD)' },
      { to: '/stranded-assets',    icon: 'trending-down', label: 'Stranded Assets' },
      { to: '/valuation',          icon: 'building',      label: 'Asset Valuation' },
      { to: '/sustainability',     icon: 'award',         label: 'Sustainability (GRESB)' },
      { to: '/cbam',               icon: 'globe',         label: 'CBAM Calculator' },
    ],
  },
  {
    label: 'Risk & Sector',
    items: [
      { to: '/climate-risk',            icon: 'thermometer', label: 'Climate Risk Engine',      badge: 'NEW' },
      { to: '/monte-carlo',             icon: 'cpu',         label: 'Monte Carlo Simulation',   badge: 'NEW' },
      { to: '/financial-risk',          icon: 'shield',      label: 'Financial Risk (ECL/PCAF)' },
      { to: '/real-estate-assessment',  icon: 'home',      label: 'Real Estate (RICS/CRREM)' },
      { to: '/supply-chain',            icon: 'truck',     label: 'Supply Chain Scope 3' },
      { to: '/sector-assessments',      icon: 'server',    label: 'Sector Assessments' },
      { to: '/engagement-tracker',      icon: 'users',     label: 'Engagement Tracker',       badge: 'NEW' },
      { to: '/country-risk',            icon: 'globe',     label: 'Country Risk',             badge: 'NEW' },
      { to: '/residential-re',          icon: 'home',      label: 'Residential RE',           badge: 'CRREM·RICS' },
      { to: '/technology-risk',         icon: 'cpu',       label: 'Technology Risk',          badge: 'AI·Fintech' },
      { to: '/banking-capital',         icon: 'shield',    label: 'Banking & Capital',        badge: 'Basel·PCAF' },
      { to: '/sovereign-emissions',     icon: 'globe',     label: 'Sovereign & Emissions',    badge: 'NEW' },
      { to: '/sovereign-climate-risk',  icon: 'globe',     label: 'Sovereign Climate Risk',   badge: 'NGFS' },
      { to: '/stress-testing',          icon: 'shield',    label: 'Stress Testing',           badge: 'EBA·ECL' },
      { to: '/geothermal',             icon: 'thermometer', label: 'Geothermal Energy',       badge: 'LCOE' },
      { to: '/green-hydrogen',         icon: 'zap',       label: 'Green Hydrogen',            badge: 'RFNBO' },
      { to: '/energy-finance',         icon: 'sun',       label: 'Energy Finance',            badge: 'Wind·Solar·PPA' },
      { to: '/energy-transition',      icon: 'trending-up', label: 'Energy Transition',       badge: 'Fleet·Grid·Avoided' },
      { to: '/gar-ets',                icon: 'leaf',      label: 'GAR & EU ETS',              badge: 'Art 449a·ETS2' },
      { to: '/project-finance',        icon: 'bar-chart', label: 'Project Finance',           badge: 'DSCR·Blended' },
      { to: '/eiopa-stress',           icon: 'shield',    label: 'EIOPA ORSA Stress Test',    badge: 'SolvII·Art45a' },
      { to: '/iorp-pension',           icon: 'briefcase', label: 'IORP II Pension Risk',        badge: 'IORP II·E8' },
      { to: '/basel-capital',          icon: 'landmark',  label: 'Basel IV Capital',            badge: 'Basel IV·CRR3' },
    ],
  },
  {
    label: 'Regulatory',
    items: [
      { to: '/regulatory',        icon: 'file-text',  label: 'Regulatory Reporting',  badge: 'SFDR·CSRD·ISSB' },
      { to: '/asia-regulatory',   icon: 'globe',      label: 'Asia Regulatory',        badge: 'BRSR·HKMA·CBI' },
      { to: '/peer-benchmark',    icon: 'users',       label: 'Peer Benchmark',         badge: 'NEW' },
      { to: '/company-profiles',  icon: 'building',    label: 'Company Profiles',        badge: 'NEW' },
      { to: '/ca100',             icon: 'target',      label: 'CA100+ Benchmark',        badge: 'NEW' },
      { to: '/disclosure-frameworks', icon: 'file-text', label: 'Disclosure Frameworks',   badge: 'TNFD·CDP·GRI' },
      { to: '/eu-regulatory',   icon: 'globe',       label: 'EU Regulatory Hub',        badge: 'EUDR·CSDDD' },
      { to: '/sec-climate',     icon: 'file-text',   label: 'SEC Climate Disclosure',   badge: 'Reg S-K·S-X' },
      { to: '/xbrl',            icon: 'file-text',   label: 'XBRL Filing & Ingestion',  badge: 'ESRS·IFRS' },
      { to: '/double-materiality', icon: 'grid',     label: 'Double Materiality',       badge: 'EFRAG·DMA' },
      { to: '/sfdr-pai',             icon: 'bar-chart-2', label: 'SFDR PAI',                  badge: 'Art 4·RTS' },
      { to: '/assurance-readiness',  icon: 'award',        label: 'Assurance Readiness',       badge: 'ISSA5000·E10' },
      { to: '/sfdr-annex',           icon: 'file-text',   label: 'SFDR Annex I-V',             badge: 'Art8·9·E9' },
      { to: '/stewardship',          icon: 'users',       label: 'Stewardship & Engagement',   badge: 'GFANZ·E6' },
      { to: '/eudr',                 icon: 'leaf',        label: 'EUDR Compliance',             badge: 'EUDR·Art4' },
      { to: '/csddd',                icon: 'shield',      label: 'CSDDD Due Diligence',         badge: 'CSDDD·Art6' },
      { to: '/tnfd-assessment',      icon: 'map-pin',     label: 'TNFD Nature Assessment',      badge: 'TNFD·v1.0' },
      { to: '/pcaf-quality',         icon: 'sliders',     label: 'PCAF Data Quality',           badge: 'PCAF·DQS' },
      { to: '/cdp-scoring',          icon: 'leaf',        label: 'CDP Climate & Water',          badge: 'CDP·A-List' },
      { to: '/gri-standards',        icon: 'book-open',   label: 'GRI Standards 2021',           badge: 'GRI·2021' },
      { to: '/sasb-industry',        icon: 'bar-chart',   label: 'SASB Industry Standards',      badge: 'SASB·SICS' },
      { to: '/model-validation',     icon: 'check-square',label: 'Model Validation',             badge: 'BCBS239·MVF' },
      { to: '/uk-sdr',               icon: 'flag',         label: 'UK SDR Labels',                badge: 'FCA·SDR·E11' },
      { to: '/mifid-spt',            icon: 'users',        label: 'MiFID II Sustainability Prefs', badge: 'MiFID·SPT·E12' },
      { to: '/tcfd-metrics',         icon: 'thermometer',  label: 'TCFD Metrics & Targets',        badge: 'TCFD·E13' },
      { to: '/eu-gbs',               icon: 'leaf',         label: 'EU Green Bond Standard',        badge: 'EU·GBS·E14' },
      { to: '/priips-kid',           icon: 'file-text',    label: 'PRIIPs KID ESG',                badge: 'PRIIPs·KID·E15' },
      { to: '/esma-fund-names',      icon: 'tag',          label: 'ESMA Fund Names Guidelines',    badge: 'ESMA·FN·E16' },
      { to: '/sl-finance',           icon: 'link',         label: 'Sustainability-Linked Finance', badge: 'SLB·SLL·E17' },
      { to: '/ifrs-s1',              icon: 'book-open',    label: 'IFRS S1 Sustainability',        badge: 'IFRS·S1·E18' },
      { to: '/eu-taxonomy-gar',      icon: 'percent',      label: 'EU Taxonomy GAR/BTAR',          badge: 'GAR·BTAR·E19' },
      { to: '/eba-pillar3',          icon: 'layers',       label: 'EBA Pillar 3 ESG',              badge: 'EBA·P3·E20' },
      { to: '/scope3-categories',    icon: 'git-branch',   label: 'Scope 3 Categories',            badge: 'GHG·S3·E21' },
      { to: '/sfdr-product-reporting', icon: 'file-plus',  label: 'SFDR Product Reporting',        badge: 'SFDR·PR·E22' },
      { to: '/biodiversity-finance', icon: 'feather',      label: 'Biodiversity Finance Metrics',  badge: 'TNFD·BIO·E23' },
      { to: '/ifrs-s2',              icon: 'thermometer',  label: 'ISSB S2 Climate Disclosures',   badge: 'IFRS·S2·E24' },
      { to: '/gri-standards',        icon: 'list',         label: 'GRI Standards Reporting',       badge: 'GRI·300·E25' },
      { to: '/tpt-transition-plan',  icon: 'trending-up',  label: 'TPT Transition Plan',           badge: 'TPT·TP·E26' },
      { to: '/pcaf-sovereign',       icon: 'globe',        label: 'PCAF Sovereign Bonds',          badge: 'PCAF·SOV·E27' },
      { to: '/esrs-e2-e5',           icon: 'wind',         label: 'ESRS E2-E5 Environment',        badge: 'ESRS·ENV·E28' },
      { to: '/greenwashing',         icon: 'alert-circle', label: 'Greenwashing Risk',             badge: 'GW·RISK·E29' },
      { to: '/carbon-credit-quality',icon: 'award',        label: 'Carbon Credit Quality',         badge: 'CCQ·CCP·E30' },
      { to: '/climate-stress-test',  icon: 'activity',     label: 'Climate Stress Testing',        badge: 'CST·ECB·E31' },
      { to: '/tnfd-leap',            icon: 'map',          label: 'TNFD LEAP Process',             badge: 'TNFD·LEAP·E32' },
      { to: '/net-zero-targets',     icon: 'target',       label: 'Net Zero Targets',              badge: 'NZ·SBTi·E33' },
      { to: '/esg-data-quality',     icon: 'database',     label: 'ESG Data Quality',              badge: 'DQ·ESG·E34' },
      { to: '/regulatory-penalties', icon: 'shield',       label: 'Regulatory Penalties',          badge: 'REG·ENF·E35' },
      { to: '/basel-liquidity',      icon: 'bank',         label: 'Basel III Liquidity',           badge: 'LCR·NSFR·E36' },
      { to: '/social-taxonomy',      icon: 'users',        label: 'Social Taxonomy & Impact',      badge: 'SOC·IMP·E37' },
      { to: '/forced-labour',        icon: 'alert-circle', label: 'Forced Labour Risk',            badge: 'FLR·ILO·E38' },
      { to: '/transition-finance',   icon: 'trending-up',  label: 'Transition Finance',            badge: 'TF·GFANZ·E39' },
      { to: '/csrd-dma',             icon: 'check-square', label: 'CSRD Double Materiality',       badge: 'DMA·ESRS·E40' },
      { to: '/physical-hazard',      icon: 'thermometer',  label: 'Physical Climate Hazard',       badge: 'PHY·AR6·E41' },
      { to: '/avoided-emissions',    icon: 'minus-circle', label: 'Scope 4 Avoided Emissions',     badge: 'S4·AE·E42' },
      { to: '/green-hydrogen',       icon: 'zap',          label: 'Green Hydrogen',                badge: 'H2·EU·E43' },
      { to: '/biodiversity-finance-v2', icon: 'feather',   label: 'Biodiversity Finance v2',       badge: 'TNFD·PBAF·E44' },
      { to: '/prudential-climate-risk', icon: 'shield',    label: 'Prudential Climate Risk',       badge: 'BES·ICAAP·E45' },
      { to: '/carbon-markets-intel',    icon: 'award',     label: 'Carbon Markets Intelligence',   badge: 'Art6·VCMI·E46' },
      { to: '/just-transition',         icon: 'users',     label: 'Just Transition & Social Risk', badge: 'ILO·JT·E47' },
      { to: '/shipping-maritime',       icon: 'anchor',    label: 'Shipping & Maritime',           badge: 'CII·FuelEU·E48' },
      { to: '/aviation-climate',        icon: 'wind',      label: 'Aviation Climate Risk',         badge: 'CORSIA·SAF·E49' },
      { to: '/commercial-re',           icon: 'building',  label: 'Commercial RE Net Zero',        badge: 'CRREM·GRESB·E50' },
      { to: '/infrastructure-finance',  icon: 'zap',       label: 'Infrastructure Climate Finance',badge: 'EP4·IFC·E51' },
      { to: '/nature-based-solutions',  icon: 'tree',      label: 'Nature-Based Solutions',        badge: 'NbS·REDD·E52' },
      { to: '/water-risk',              icon: 'droplet',   label: 'Water Risk & Security',         badge: 'WRI·CDP·E53' },
      { to: '/food-system',             icon: 'sun',       label: 'Food System & Land Use',        badge: 'FLAG·TNFD·E54' },
      { to: '/circular-economy',        icon: 'refresh-cw',label: 'Circular Economy Finance',      badge: 'ESRS·MCI·E55' },
      { to: '/climate-litigation',      icon: 'shield',    label: 'Climate Litigation & Legal',    badge: 'TCFD·D&O·E56' },
      { to: '/esg-ratings',             icon: 'star',      label: 'ESG Ratings Reform',            badge: 'ESRA·DIV·E57' },
      { to: '/methane-fugitive',        icon: 'cloud',     label: 'Methane & Fugitive Emissions',  badge: 'CH4·OGMP·E58' },
      { to: '/health-climate',          icon: 'activity',  label: 'Health-Climate Nexus',          badge: 'WHO·HEAT·E59' },
      { to: '/maritime',                icon: 'anchor',    label: 'Maritime Decarbonisation',      badge: 'CII·IMO·E60' },
      { to: '/hydrogen',                icon: 'zap',       label: 'Hydrogen Economy Finance',      badge: 'H2·RFNBO·E61' },
      { to: '/cdr',                     icon: 'cloud-off', label: 'Carbon Removal & CDR',          badge: 'CDR·VCMI·E63' },
      { to: '/biodiversity-credits',    icon: 'feather',   label: 'Biodiversity Credits',          badge: 'BNG·SBTN·E65' },
      { to: '/scope3-analytics',        icon: 'layers',    label: 'Scope 3 Deep-Dive Analytics',   badge: 'GHG·FLAG·E67' },
      { to: '/blue-economy',            icon: 'globe',     label: 'Blue Economy & Ocean Finance',   badge: 'ICMA·SOF·E68' },
      { to: '/sovereign-debt-climate',  icon: 'landmark',  label: 'Climate-Linked Sovereign Debt',  badge: 'CRDC·DfN·E69' },
      { to: '/loss-damage-finance',     icon: 'alert-triangle', label: 'Loss & Damage Finance',     badge: 'FRLD·WIM·E70' },
      { to: '/carbon-price-ets',        icon: 'trending-up', label: 'Carbon Price & ETS Analytics', badge: 'ETS·IEA·E71' },
      { to: '/blended-finance',      icon: 'layers',       label: 'Blended Finance & DFI',         badge: 'IFC·DFI·E72' },
      { to: '/mrv',                  icon: 'cpu',          label: 'Climate Data & MRV',             badge: 'ISO·SAT·E73' },
      { to: '/real-asset-decarb',    icon: 'building',     label: 'Real Asset Decarbonisation',     badge: 'CRREM·E74' },
      { to: '/trade-finance-esg',    icon: 'truck',        label: 'Sustainable Trade Finance',      badge: 'EP4·ECA·E75' },
      { to: '/ai-risk',           icon: 'cpu',          label: 'AI & ML Risk Finance',          badge: 'EU·AI·E76' },
      { to: '/nature-capital',    icon: 'leaf',         label: 'Nature Capital Accounting',     badge: 'SEEA·TNFD·E77' },
      { to: '/climate-finance',   icon: 'trending-up',  label: 'Climate Finance Flows',         badge: 'CPI·NCQG·E78' },
      { to: '/esg-ma',            icon: 'briefcase',    label: 'ESG M&A Due Diligence',         badge: 'UNGP·MA·E79' },
    ],
  },
  {
    label: 'Scenarios & Data',
    items: [
      { to: '/scenario-gallery',     icon: 'layers',       label: 'Scenario Gallery',    badge: 'NEW' },
      { to: '/scenario-builder-v2',  icon: 'wrench',       label: 'Scenario Builder v2', badge: 'NEW' },
      { to: '/browser',       icon: 'search',       label: 'Scenario Browser' },
      { to: '/data-hub',            icon: 'database',  label: 'Data Hub' },
      { to: '/data-hub-ingestion',  icon: 'activity',  label: 'Ingestion Monitor',   badge: 'NEW' },
      { to: '/data-mapping',        icon: 'link',      label: 'Data Mapping',        badge: 'NEW' },
      { to: '/data-preview',  icon: 'database',     label: 'Data Preview',        badge: 'NEW' },
      { to: '/ngfs',          icon: 'globe',        label: 'NGFS Catalog' },
      { to: '/comparison',    icon: 'git-compare',  label: 'Comparison' },
      { to: '/custom-builder',icon: 'wrench',       label: 'Custom Builder' },
    ],
  },
  {
    label: 'Portfolio',
    items: [
      { to: '/portfolios',        icon: 'briefcase', label: 'Portfolios' },
      { to: '/portfolio-manager', icon: 'upload',    label: 'Upload & Edit' },
      { to: '/analysis',          icon: 'bar-chart', label: 'Run Analysis' },
    ],
  },
  {
    label: 'Data Intake',
    items: [
      { to: '/data-intake',                icon: 'database',   label: 'Overview',              badge: 'NEW' },
      { to: '/data-intake/portfolio',      icon: 'upload',     label: 'Loan Portfolio' },
      { to: '/data-intake/counterparty',   icon: 'users',      label: 'Counterparty Emissions' },
      { to: '/data-intake/real-estate',    icon: 'home',       label: 'Real Estate EUI' },
      { to: '/data-intake/shipping-fleet', icon: 'anchor',     label: 'Shipping Fleet' },
      { to: '/data-intake/steel-borrowers',icon: 'tool',       label: 'Steel Borrowers' },
      { to: '/data-intake/project-finance',icon: 'zap',        label: 'Project Finance' },
      { to: '/data-intake/internal-config',    icon: 'settings',   label: 'Internal Config' },
      { to: '/data-intake/persona-templates',   icon: 'layers',     label: 'Persona Templates', badge: 'NEW' },
    ],
  },
  {
    label: 'China Trade',
    items: [
      { to: '/china-trade', icon: 'globe', label: 'China Trade Platform', badge: 'CBAM·CETS·ESG' },
    ],
  },
  {
    label: 'Platform',
    items: [
      { to: '/platform-intelligence', icon: 'cpu', label: 'Platform Intelligence', badge: 'Lineage·360' },
    ],
  },
];

// ─── Auth callback ────────────────────────────────────────────────────────────

function AuthCallback({ onAuth }) {
  const hasProcessed = useRef(false);
  const navigate = useNavigate();

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = window.location.hash;
    const match = hash.match(/session_id=([^&]+)/);
    if (!match) { navigate('/login'); return; }

    const sessionId = match[1];
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    fetch(`${API_URL}/api/auth/google/session`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ session_id: sessionId }),
    })
      .then(r => { if (!r.ok) throw new Error('Auth failed'); return r.json(); })
      .then(data => {
        localStorage.setItem('session_token', data.session_token);
        onAuth(data);
        navigate('/', { state: { user: data } });
      })
      .catch(() => navigate('/login'));
  }, [navigate, onAuth]);

  return (
    <div className="flex items-center justify-center h-screen bg-white text-slate-700 font-mono text-sm">
      <div className="flex items-center gap-3">
        <div className="w-4 h-4 border-2 border-black border-t-transparent rounded-full animate-spin" />
        Authenticating…
      </div>
    </div>
  );
}

// ─── Route title map ──────────────────────────────────────────────────────────

const ROUTE_TITLES = {
  '/':                      'Overview Dashboard',
  '/interactive':           'Interactive Analytics',
  '/portfolios':            'Portfolios',
  '/analysis':              'Run Analysis',
  '/scenario-data':         'Scenario Data',
  '/scenario-builder':      'Scenario Builder',
  '/data-hub':              'Data Hub',
  '/browser':               'Scenario Browser',
  '/comparison':            'Comparison',
  '/impact':                'Impact Calculator',
  '/portfolio-manager':     'Portfolio Manager',
  '/alerts':                'Alerts',
  '/ngfs':                  'NGFS Catalog',
  '/custom-builder':        'Custom Builder',
  '/sub-analysis':          'Sub-Parameter Analysis',
  '/cbam':                  'CBAM Calculator',
  '/carbon':                'Carbon Credits',
  '/dcm-calculator':        'DCM Methodology Engine',
  '/nature-risk':           'Nature Risk (TNFD)',
  '/stranded-assets':       'Stranded Assets',
  '/valuation':             'Asset Valuation',
  '/sustainability':        'Sustainability',
  '/scenario-analysis':     'Scenario Analysis',
  '/portfolio-analytics':   'Portfolio Analytics',
  '/financial-risk':        'Financial Risk — ECL / PCAF',
  '/real-estate-assessment':'Real Estate Assessment (RICS / CRREM)',
  '/supply-chain':          'Supply Chain — Scope 3',
  '/sector-assessments':    'Sector Assessments',
  '/regulatory':            'Regulatory Reporting',
  '/peer-benchmark':        'Peer Benchmark Gap Assessment',
  '/analyst-portfolios':    'Analyst Portfolio Workbench',
  '/company-profiles':      'Company Profiles',
  '/glidepath-tracker':     'Glidepath Tracker',
  '/engagement-tracker':    'Engagement Tracker',
  '/monte-carlo':           'Monte Carlo Simulation — P5/P25/P50/P75/P95',
  '/scenario-builder-v2':  'Scenario Builder v2 — NGFS Phase IV',
  '/scenario-gallery':     'Scenario Gallery',
  '/asia-regulatory':      'Asia-Pacific Regulatory Frameworks',
  '/china-trade':          'China Trade & Sustainability Platform',
  '/climate-risk':         'Climate Risk Engine — Physical / Transition / Integrated',
  '/data-mapping':         'Data Mapping — Source to KPI to Module',
  '/data-preview':          'Data Preview — Tables, Relationships & Mappings',
  '/disclosure-frameworks': 'Disclosure Frameworks — TNFD · CDP · GRI · SASB · SEC',
  '/eu-regulatory':         'EU Regulatory Hub — Taxonomy · EUDR · CSDDD · Transition Plan',
  '/banking-capital':       'Banking & Capital — Basel III/IV · PCAF Quality · Model Validation',
  '/asset-management':      'Asset Management — PACTA · GBS · Factor Overlays',
  '/sovereign-emissions':   'Sovereign & Emissions — Sovereign Risk · Insurance · Agriculture',
  '/platform-intelligence': 'Platform Intelligence — Lineage · Entity 360 · Report Compiler',
  '/double-materiality':    'Double Materiality Assessment — EFRAG IG 1 · ESRS',
  '/sfdr-pai':              'SFDR PAI — Principal Adverse Impact Indicators · Article 4 RTS',
  '/xbrl':                  'XBRL Export & Ingestion — ESRS · IFRS Taxonomies',
  '/pe-deals':              'PE Deal Pipeline — ESG Screening · IRR Sensitivity · ILPA Impact',
  '/residential-re':        'Residential Real Estate — CRREM · RICS ESG · Spatial Hazard · Retrofit',
  '/technology-risk':       'Technology Risk — Automation Disruption · AI Adoption · Digital Readiness · Fintech',
  '/fund-management':       'Fund Management — LP Analytics · SFDR Exclusion · ILPA Reporting',
  '/dme-dashboard':          'DME Dashboard — Velocity · Alerts · Contagion · DMI · Greenwashing · Policy',
  '/sentiment':              'Sentiment Analysis — Multi-Stakeholder · News · Social · Regulatory · NLP',
  '/sovereign-climate-risk': 'Sovereign Climate Risk — NGFS Scenarios · Rating Adjustment · Climate VaR',
  '/sec-climate':            'SEC Climate Disclosure — Reg S-K 1500-1505 · Reg S-X 14-02 · Attestation',
  '/green-hydrogen':         'Green Hydrogen — LCOH · Carbon Intensity · RFNBO · Electrolyser Economics',
  '/stress-testing':         'Stress Testing — Multi-Scenario ECL · PD Backtesting · EBA GL/2017/16',
  '/geothermal':             'Geothermal Energy — LCOE · Viability · Seismicity · NPV/IRR',
  '/energy-finance':         'Energy Finance — Wind · Solar · LCOE · PPA Risk · Project Finance',
  '/energy-transition':      'Energy Transition — Fleet Transition · Grid EF · Avoided Emissions · OGMP Methane',
  '/gar-ets':                'GAR & EU ETS — Green Asset Ratio · Free Allocation · ETS2 Readiness',
  '/project-finance':        'Project Finance — DSCR · LLCR · IRR · Blended Finance · Green Bonds',
  '/data-hub-ingestion':            'Data Hub — Ingestion Monitor · Source Catalog · KPI Mappings',
  '/data-intake/persona-templates': 'Persona & Module Templates — Bulk Upload · Lineage Map',
  '/eiopa-stress':                  'EIOPA ORSA Climate Stress Test — Solvency II Art. 45a · 4 Scenarios · Capital Adequacy',
  '/iorp-pension':                  'IORP II Pension Climate Risk — EIOPA Stress Test · Art 28 ORA · ALM · SFDR FMP Classification',
  '/assurance-readiness':           'Assurance Readiness — ISSA 5000 · ISAE 3000 · CSRD Art. 26a · 26 Criteria',
  '/sfdr-annex':                    'SFDR Annex I-V — PAI Statement · Art. 8/9 Pre-contractual & Periodic Templates',
  '/stewardship':                   'Stewardship & Engagement — Portfolio Engagement · Proxy Votes · Escalation · GFANZ E6',
  '/eudr':                          'EUDR Compliance — Commodity Screening · Country Risk · Due Diligence · DDS Generator',
  '/csddd':                         'CSDDD Due Diligence — Scope Assessment · Adverse Impacts · DD Compliance · Penalties',
  '/basel-capital':                 'Basel IV Capital — CET1/CAR · Credit Risk SA/IRB · FRTB · LCR/NSFR · Climate RWA',
  '/tnfd-assessment':               'TNFD Nature Assessment — LEAP Framework · 14 Disclosures · ENCORE Dependencies · Double Materiality',
  '/pcaf-quality':                  'PCAF Data Quality Score — DQS 1–5 · Portfolio DQS · SFDR PAI Coverage · Confidence Bands',
  '/cdp-scoring':                   'CDP Climate & Water Scoring — A-List · 15 Climate Modules · 9 Water Modules · TCFD Aligned',
  '/gri-standards':                 'GRI Standards 2021 — Universal Standards · Topic Standards · ESRS Linkage · SDG Mapping',
  '/sasb-industry':                 'SASB Industry Standards — SICS · 77 Industries · IFRS S2 Aligned · Peer Comparison',
  '/model-validation':              'Model Validation Framework — BCBS 239 · 17 Models · 12 Statistical Tests · Champion-Challenger',
  '/uk-sdr':                        'UK SDR — FCA PS 23/16 · 4 Investment Labels · Anti-Greenwashing Rule · Naming & Marketing Requirements · ICIS Score',
  '/mifid-spt':                     'MiFID II Sustainability Preferences — Art 2(7) Categories A/B/C · EC Del. Reg. 2021/1253 · Product Suitability Matrix · E12',
  '/tcfd-metrics':                  'TCFD Metrics & Targets — 11 Recommendations · 4 Pillars · Sector Supplements · Maturity 1-5 · Cross-Framework · E13',
  '/eu-gbs':                        'EU Green Bond Standard — Regulation 2023/2631 · GBFS · Allocation Report · Impact Report · ESMA ER · Standards Comparison · E14',
  '/priips-kid':                    'PRIIPs KID ESG — Regulation 1286/2014 · SRI 1-7 · Performance Scenarios · RIY · ESG Inserts by SFDR Classification · E15',
  '/esma-fund-names':              'ESMA Fund Names Guidelines — ESMA/2024/249 · 80% ESG/Sustainability Threshold · PAB Exclusions · Nov 2024 / May 2025 Deadlines · E16',
  '/sl-finance':                   'Sustainability-Linked Finance — ICMA SLB Principles 2023 · LMA SLL Principles · KPI SMART Scoring · SPT Calibration · Coupon Step-Up · E17',
  '/ifrs-s1':                      'IFRS S1 Sustainability Disclosures — ISSB June 2023 · 4 Pillars · SASB Industry Mapping · Governance/Strategy/Risk/Metrics · E18',
  '/eu-taxonomy-gar':              'EU Taxonomy GAR/BTAR — Article 8 Delegated Act 2021/4987 · Green Asset Ratio · Banking Book TAR · 6 Environmental Objectives · E19',
  '/eba-pillar3':                  'EBA Pillar 3 ESG Disclosures — GL/2022/03 · CRR Art 449a · 10 Templates · Physical Risk Heatmap · Financed Emissions · Carbon-Related Assets · E20',
  '/scope3-categories':            'Scope 3 Categories Engine — GHG Protocol Value Chain Standard 2011 · 15 Categories · SBTi FLAG/Non-FLAG · Coverage Rule · C15 Investments · E21',
  '/sfdr-product-reporting':       'SFDR Product Periodic Reporting — RTS 2022/1288 Annex III/V · Art 8/9 Periodic Reports · Product PAI · Sustainable Investment Verification · E22',
  '/biodiversity-finance':         'Biodiversity Finance Metrics — TNFD v1.0 Core Metrics · SBTN Step 5 · CBD GBF Target 15 · MSA Footprint · Nature-Related Risk Quantification · E23',
  '/ifrs-s2':                      'ISSB S2 Climate-Related Disclosures — IFRS S2 June 2023 · 4 Pillars · Scenario Analysis · Physical & Transition Risk · SASB Industry Metrics · E24',
  '/gri-standards':                'GRI Standards Reporting Engine — GRI 1/2/3 Universal Standards 2021 · GRI 300 Environment · Material Topics · Content Index · Assurance · E25',
  '/tpt-transition-plan':          'TPT Transition Plan Framework — TPT Disclosure Framework 2023 · 6 Elements · Quality Tier · Net Zero Targets · Financed Emissions · FCA Alignment · E26',
  '/pcaf-sovereign':               'PCAF Sovereign Bonds & Loans — PCAF Part D 2023 · GDP Attribution · Sovereign GHG Inventory · NDC Alignment · National Circumstances · E27',
  '/esrs-e2-e5':                   'CSRD ESRS E2-E5 Environment — Pollution · Water & Marine Resources · Biodiversity & Ecosystems · Circular Economy · ESRS IG3 Metrics · E28',
  '/greenwashing':                 'Greenwashing Risk & Substantiation — EU Reg 2023/2441 · FCA Consumer Duty · Claim Screening · Label Verification · Misleading Terms · E29',
  '/carbon-credit-quality':        'Carbon Credit Quality & Integrity — ICVCM Core Carbon Principles · VCS · Gold Standard · Additionality · Permanence · CORSIA · Article 6 · E30',
  '/climate-stress-test':          'Climate Stress Testing — ECB CST 2022 · EBA 2023 · 3 NGFS Scenarios · PD Migration · LGD Uplift · CET1 Depletion · Sectoral Exposure · E31',
  '/tnfd-leap':                    'TNFD LEAP Process Assessment — Locate · Evaluate · Assess · Prepare · ENCORE Dependencies · Nature-Related Risk & Opportunity · TNFD 2023 · E32',
  '/net-zero-targets':             'Net Zero Target Setting — SBTi Corporate · NZBA · NZAMI · NZAOA · Temperature Score · Pathway Gap · Interim Milestones · BVCM · E33',
  '/esg-data-quality':             'ESG Data Quality & Coverage — E/S/G Pillar Scoring · DQS Framework · Provider Divergence · Material Gaps · BCBS 239 Data Governance · E34',
  '/regulatory-penalties':         'Regulatory Penalty & Enforcement — CSRD · SFDR · EU Taxonomy · EUDR · CSDDD · Max Penalty Calculation · Supervisory Authority Mapping · E35',
  '/basel-liquidity':              'Basel III Liquidity Risk — LCR · NSFR · IRRBB · ALM Gap · HQLA Level 1/2A/2B · CRR2 · BCBS 238/295 · Climate HQLA Haircut · E36',
  '/social-taxonomy':              'Social Taxonomy & Impact Measurement — EU Social Taxonomy 3 Objectives · IMP 5 Dimensions · IRIS+ · SFDR Art 2(17) · SDG Alignment · E37',
  '/forced-labour':                'Forced Labour Risk Assessment — EU FLR 2024/3015 · ILO 11 Indicators · UK MSA Section 54 · German LkSG · Compliance Programme Maturity · E38',
  '/transition-finance':           'Transition Finance Classification — GFANZ 4-Category · UK TPT Sector Pathways · Singapore GTT · Japan GX · ICMA CTF Handbook · TFR vs GAR · E39',
  '/csrd-dma':                     'CSRD Double Materiality Assessment — ESRS 1 §§42-49 · Impact Materiality · Financial Materiality · Stakeholder Engagement · Topic Prioritisation · E40',
  '/physical-hazard':              'Physical Climate Hazard Scoring — IPCC AR6 · Flood · Wildfire · Heat Stress · Sea Level Rise · Cyclone · Drought · CRREM Pathway · E41',
  '/avoided-emissions':            'Scope 4 Avoided Emissions — GHG Protocol 2022 · Enablement · Substitution · Facilitated · Article 6 ITMOs · SBTi BVCM · E42',
  '/green-hydrogen':               'Green Hydrogen & Energy Transition — EU Delegated Act 2023/1184 · LCOH · Electrolyser CAPEX · Green/Blue/Pink H2 · H2 Bank · IRA 45V · E43',
  '/biodiversity-finance-v2':      'Biodiversity Finance v2 — TNFD v1.0 LEAP · PBAF Attribution · ENCORE 23 Ecosystem Services · GBF COP15 30×30 · MSA Footprint · BFFI · BNG Metric 4.0 · E44',
  '/prudential-climate-risk':      'Prudential Climate Risk — BOE/PRA BES 2025 · ECB DFAST 2024 · NGFS v4 Scenarios · ICAAP Pillar 2a/2b · Basel SRP 43.1 · EBA SREP Climate Overlay · E45',
  '/carbon-markets-intel':         'Carbon Markets Intelligence — Paris Art 6.2/6.4 · VCMI Claims Code Gold/Silver/Bronze · ICVCM 10 CCPs · CORSIA Phase 2 · VCM Registries · Credit Pricing · E46',
  '/just-transition':              'Just Transition & Social Risk — ILO JT Guidelines 5 Dimensions · CSRD ESRS S1-S4 · SEC Human Capital Item 101c · Anker Living Wage · Worker Displacement · CBI · E47',
  '/shipping-maritime':            'Shipping & Maritime Decarbonisation — IMO GHG Strategy 2023 · CII A–E Rating · EEXI · Poseidon Principles · FuelEU Maritime · Sea Cargo Charter · EU ETS Shipping · E48',
  '/aviation-climate':             'Aviation Climate Risk — CORSIA Phase 2 · SAF Blending Mandates ReFuelEU/IRA 45Z · EU ETS Aviation · IATA Net Zero 2050 · Aircraft Asset Stranding · E49',
  '/commercial-re':                'Commercial Real Estate Net Zero — CRREM 2.0 Stranding · EPC/EPBD 2024 · GRESB Real Estate · REFI Protocol · NABERS Energy · Green Lease · Retrofit NPV/IRR · E50',
  '/infrastructure-finance':       'Infrastructure Climate Finance — Equator Principles IV · IFC Performance Standards 1–8 · OECD Common Approaches · Paris Alignment DFIs · Blended Finance · DSCR Stress · E51',
  '/nature-based-solutions':       'Nature-Based Solutions & Carbon Sequestration — IUCN Global Standard v2.0 · REDD+ VM0007 · Blue Carbon VM0033/VM0024 · Soil Carbon IPCC Tier 1–3 · ARR · AFOLU Net Balance · E52',
  '/water-risk':                   'Water Risk & Security — WRI Aqueduct 4.0 · CDP Water Security A-List · CSRD ESRS E3 · TNFD Water Dependency · CEO Water Mandate · UN SDG 6 · E53',
  '/food-system':                  'Food System & Land Use Finance — SBTi FLAG · FAO Crop Yield RCP Scenarios · TNFD Food LEAP · EUDR Deforestation-Free · ICTI · FOLU · Agricultural Financed Emissions · E54',
  '/circular-economy':             'Circular Economy Finance — CSRD ESRS E5 · Ellen MacArthur Foundation MCI · WBCSD Circular Transition Indicators · EPR Schemes · EU CRM Act 2023 · ISO 14044 LCA · E55',
  '/climate-litigation':           'Climate Litigation & Legal Risk — TCFD Disclosure Liability · EU Green Claims Directive 2023/2441 · FCA Consumer Duty · D&O Climate Exposure · SEC Reg S-K · Attribution Science · E56',
  '/esg-ratings':                  'ESG Ratings Reform — EU ESRA 2024/3005 · Berg et al. Divergence (Scope/Weight/Measurement) · Bias Detection · Composite AAA–CCC · E-Pillar Divergence · MSCI/Sustainalytics/Bloomberg · E57',
  '/methane-fugitive':             'Methane & Fugitive Emissions — EU Methane Regulation 2024/1787 · OGMP 2.0 Levels 1–5 · IPCC AR6 GWP-100/GWP-20 · Super-Emitter Detection · IEA Abatement Curve · EPA OOOOa/b LDAR · E58',
  '/health-climate':               'Health-Climate Nexus — WBGT Heat Stress · WHO AQG 2021 · EU Air Quality Directive 2024 · Vector Disease RCP Projections · Lancet Countdown · WHO Country Climate & Health Profiles · E59',
  '/maritime':                     'Maritime & Shipping Decarbonisation — IMO GHG Strategy 2023 · CII MARPOL Annex VI · EEXI Energy Efficiency · EU ETS Shipping · FuelEU Maritime 2023/1805 · Alternative Fuels · Ship Stranding · E60',
  '/hydrogen':                     'Hydrogen Economy Finance — EU Hydrogen Strategy 2020 · RFNBO Delegated Act 2023/1184 · EU H2 Bank · LCOH by Pathway · Green/Blue/Grey/Pink Taxonomy · IEA H2 Review · Demand Sectors · E61',
  '/just-transition-finance':      'Just Transition Finance — ILO Just Transition Guidelines · World Bank JT Framework 2022 · EU JTM 2021/1056 · ICMA Social Bond Principles 2023 · COP26 JETP Pledges · SDG 8/10 · E62',
  '/cdr':                          'Carbon Removal & CDR Finance — IPCC AR6 CDR Taxonomy · BeZero Carbon AAA–CCC · Oxford Principles 2024 · VCMI Claims Code · Article 6.4 Paris Agreement · Puro.earth · Isometric · E63',
  // E64 transition-finance route already declared above (E39 entry)
  '/biodiversity-credits':         'Biodiversity Credits & Nature Markets — UK BNG DEFRA Metric 4.0 · EU Nature Restoration Law 2024/1991 · SBTN v1.1 · TNFD LEAP Advanced Metrics · Biodiversity Credit Alliance · IUCN · E65',
  // E66 climate-stress-test route already declared above (E31 entry)
  '/scope3-analytics':             'Scope 3 Deep-Dive Analytics — GHG Protocol Categories 1–15 · FLAG Forest/Land/Agriculture · Avoided Emissions Framework · PCAF DQS · SBTi Scope 3 Guidance 2022 · E67',
  '/blue-economy':                 'Blue Economy & Ocean Finance — ICMA Blue Bond Principles 2023 · Sustainable Ocean Finance (SOF) · Blue Carbon (Mangroves/Seagrass/Saltmarsh) · High Seas Treaty BBNJ 2023 · Ocean Acidification · OECD Ocean Finance · E68',
  '/sovereign-debt-climate':       'Climate-Linked Sovereign Debt — Climate Resilience Debt Clauses (CRDC) · Debt-for-Nature Swaps · IMF Resilience & Sustainability Trust · Paris Club MOU · SIDS Vulnerability Index · Catastrophe-Deferred Payment · E69',
  '/loss-damage-finance':          'Loss & Damage Finance — COP28 Fund for Response to Loss & Damage · WIM Santiago Network · Global Shield v2 · V20 Vulnerable Group · Parametric Trigger Design · Warsaw International Mechanism · E70',
  '/carbon-price-ets':             'Carbon Price Forecasting & ETS Analytics — EU ETS Phase 4 (LRF 4.3%) · UK ETS · California Cap-and-Trade · China ETS (8 Sectors) · RGGI · Korea ETS · IEA SDS/APS Pathways · Cross-Border Leakage · CBAM · E71',
  '/blended-finance':      'Blended Finance & DFI Instruments — IFC Performance Standards · MIGA · EBRD · ADB · Convergence 2023 · Concessional Layers · First-Loss · Mobilisation Ratios · OECD DAC · E72',
  '/mrv':                  'Climate Data & MRV Infrastructure — ISO 14064-3:2019 · CDP CDSB · TROPOMI Satellite · GHGSat · IPCC AR6 Uncertainty · AI-Assisted Quality · Digital MRV Tiers 1–5 · ISAE 3410 · E73',
  '/real-asset-decarb':    'Real Asset Decarbonisation — CRREM 2.0 Pathways · Lock-In Risk · Capex Transition Planning · Retrofit NPV · Brown-to-Green Portfolio · SBTi Buildings/Industry · Stranded Cost Curves · E74',
  '/trade-finance-esg':    'Sustainable Trade Finance — Equator Principles v4 (2020) · OECD Arrangement on Export Credits · ICC Sustainable Trade Finance Principles 2022 · Supply-Chain ESG Dynamic Discounting · Trade Flow GHG · E75',
  '/ai-risk':         'AI & ML Risk Finance — EU AI Act 2024/1689 · NIST AI RMF 1.0 · Algorithmic Bias Detection · GDPR Art 22 · EU AI Liability Directive · Explainability Scoring · AI Governance · E76',
  '/nature-capital':  'Nature Capital Accounting — SEEA EA 2021 · TNFD v1.0 Natural Capital · ENCORE 62 Services · TEEB Biome Values · Natural Capital Balance Sheet · WAVES · CBD GBF Target 15 · E77',
  '/climate-finance': 'Climate Finance Flows Tracking — OECD CRS Rio Markers · UNFCCC Art 2.1(c) Paris Alignment · CPI Global Landscape 2023 · NCQG $300bn/yr COP29 · MDB Joint Tracking · Private Mobilisation · E78',
  '/esg-ma':          'ESG M&A Due Diligence — UNGP 31 Guiding Principles · EU CSDDD Art 3 · ESG Valuation Adjustment · Post-Merger ESG Integration · OECD RBC Due Diligence · W&I ESG Reps · E79',
};

// ─── Backend health hook ──────────────────────────────────────────────────────

function useBackendHealth() {
  const [status, setStatus] = useState('checking'); // 'online' | 'offline' | 'checking'
  useEffect(() => {
    let cancelled = false;
    const check = () => {
      fetch(`${API_URL}/api/health`, { signal: AbortSignal.timeout(3000) })
        .then(r => { if (!cancelled) setStatus(r.ok ? 'online' : 'offline'); })
        .catch(() => { if (!cancelled) setStatus('offline'); });
    };
    check();
    const id = setInterval(check, 30000);
    return () => { cancelled = true; clearInterval(id); };
  }, []);
  return status;
}

// ─── Top header ───────────────────────────────────────────────────────────────

function TopHeader({ user, onLogout, sidebarOpen, onToggleSidebar }) {
  const location = useLocation();
  const navigate = useNavigate();
  const backendStatus = useBackendHealth();
  const title = ROUTE_TITLES[location.pathname] || 'Analytics Platform';

  return (
    <header className="h-12 bg-white border-b border-gray-200 flex items-center px-4 gap-3 shrink-0 z-10 shadow-[0_1px_2px_rgba(0,0,0,0.04)]">
      {/* Sidebar toggle */}
      <button
        onClick={onToggleSidebar}
        className="text-gray-400 hover:text-gray-700 transition-colors p-1.5 rounded-md hover:bg-gray-100"
        title={sidebarOpen ? 'Collapse sidebar' : 'Expand sidebar'}
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
          <path strokeLinecap="round" strokeLinejoin="round"
            d={sidebarOpen
              ? 'M4 6h16M4 12h16M4 18h16'
              : 'M4 6h16M4 12h16M4 18h16'} />
        </svg>
      </button>

      {/* Page title */}
      <div className="flex items-center gap-2 min-w-0">
        <span className="text-xs text-gray-400 font-medium">A2 Intelligence</span>
        <span className="text-gray-300 text-xs">/</span>
        <span className="text-sm font-medium text-gray-800 truncate">{title}</span>
      </div>

      <div className="flex-1" />

      {/* Persona switcher */}
      <PersonaSwitcher />

      <div className="w-px h-5 bg-gray-200" />

      {/* Backend status */}
      <div className="flex items-center gap-1.5 bg-gray-50 px-2.5 py-1 rounded-full border border-gray-200">
        <div className={`w-1.5 h-1.5 rounded-full ${
          backendStatus === 'online'   ? 'bg-emerald-500' :
          backendStatus === 'offline'  ? 'bg-red-400' :
          'bg-amber-400 animate-pulse'
        }`} />
        <span className="text-[11px] text-gray-600 font-medium">
          {backendStatus === 'online' ? 'Connected' : backendStatus === 'offline' ? 'Offline' : 'Connecting'}
        </span>
      </div>

      <div className="w-px h-5 bg-gray-200" />

      {/* Current date */}
      <span className="text-xs text-gray-500 font-mono tabular-nums hidden sm:block">
        {new Date().toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })}
      </span>

      <div className="w-px h-5 bg-gray-200" />

      {/* User avatar + logout */}
      <div className="flex items-center gap-2.5">
        {user?.picture ? (
          <img src={user.picture} alt="" className="w-7 h-7 rounded-full ring-2 ring-gray-200" />
        ) : (
          <div className="w-7 h-7 rounded-full bg-[#164E8A] flex items-center justify-center text-[11px] font-semibold text-white">
            {user?.name?.[0]?.toUpperCase() || 'D'}
          </div>
        )}
        <span className="text-xs text-gray-700 hidden md:block truncate max-w-[120px] font-medium">{user?.name}</span>
        <button
          onClick={onLogout}
          title="Sign out"
          className="text-gray-400 hover:text-gray-600 transition-colors p-1.5 rounded-md hover:bg-gray-100"
          data-testid="logout-btn"
        >
          <svg className="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
          </svg>
        </button>
      </div>
    </header>
  );
}

// ─── Sidebar ──────────────────────────────────────────────────────────────────

function Sidebar({ open, user }) {
  return (
    <aside className={`bg-[#1A2035] flex flex-col shrink-0 transition-all duration-200 ${
      open ? 'w-60' : 'w-14'
    }`}>
      {/* Brand */}
      <div className={`h-12 border-b border-white/10 flex items-center shrink-0 ${open ? 'px-4 gap-3' : 'justify-center'}`}>
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-[#3B82F6] to-[#164E8A] flex items-center justify-center shrink-0 shadow-lg shadow-blue-900/30">
          <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
          </svg>
        </div>
        {open && (
          <div className="min-w-0">
            <p className="text-[13px] font-semibold text-white tracking-tight leading-none">A2 Intelligence</p>
            <p className="text-[10px] text-gray-400 mt-1">Climate Risk Analytics</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto overflow-x-hidden py-3 space-y-4 px-2 scrollbar-none">
        {NAV_GROUPS.map(group => (
          <NavGroup key={group.label} label={group.label} open={open}>
            {group.items.map(item => (
              <SideLink key={item.to} {...item} sidebarOpen={open} />
            ))}
          </NavGroup>
        ))}
      </nav>

      {/* Footer */}
      {open && (
        <div className="p-3 border-t border-white/10 shrink-0">
          <div className="flex items-center gap-2">
            <img src="/aa-impact-logo.jpg" alt="AA Impact" className="h-4 w-4 rounded object-cover opacity-60" />
            <span className="text-[10px] text-gray-500">AA Impact Inc. © 2025</span>
          </div>
        </div>
      )}
    </aside>
  );
}

function NavGroup({ label, open, children }) {
  if (!open) {
    return <div className="space-y-0.5">{children}</div>;
  }
  return (
    <div>
      <p className="text-[10px] font-semibold text-gray-500 uppercase tracking-[0.1em] mb-1.5 px-2 truncate">{label}</p>
      <div className="space-y-0.5">{children}</div>
    </div>
  );
}

function SideLink({ to, icon, label, end, badge, sidebarOpen }) {
  const d = ICON_MAP[icon] || ICON_MAP.layout;
  return (
    <NavLink
      to={to}
      end={end}
      title={!sidebarOpen ? label : undefined}
      className={({ isActive }) =>
        `flex items-center rounded-md transition-all group relative ${
          sidebarOpen ? 'gap-2.5 px-2.5 py-[7px]' : 'justify-center px-0 py-2'
        } ${
          isActive
            ? 'bg-[#243352] text-white shadow-sm'
            : 'text-gray-400 hover:text-white hover:bg-white/[0.07]'
        }`
      }
      data-testid={`nav-${to.replace('/', '') || 'dashboard'}`}
    >
      <svg className="h-[15px] w-[15px] shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.8}>
        <path strokeLinecap="round" strokeLinejoin="round" d={d} />
      </svg>
      {sidebarOpen && (
        <>
          <span className="text-[12.5px] truncate flex-1">{label}</span>
          {badge && (
            <span className="text-[8px] font-mono font-bold text-blue-300 bg-blue-400/15 px-1.5 py-0.5 rounded shrink-0 leading-none">
              {badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

// ─── Main app router ──────────────────────────────────────────────────────────

function AppRouter() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);
  const [isCallback, setIsCallback] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    if (location.hash?.includes('session_id=')) {
      setIsCallback(true);
      setChecking(false);
      return;
    }
    const token = localStorage.getItem('session_token');
    if (!token) { setChecking(false); return; }

    // Dev bypass token — skip backend validation in development builds
    if (token === 'dev-bypass-local' && process.env.NODE_ENV === 'development') {
      setUser({ name: 'Developer', email: 'dev@local', role: 'admin', picture: null });
      setChecking(false);
      return;
    }

    fetch(`${API_URL}/api/auth/me`, {
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(data => { setUser(data); setChecking(false); })
      .catch(() => { localStorage.removeItem('session_token'); setChecking(false); });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = useCallback(async () => {
    const token = localStorage.getItem('session_token');
    await fetch(`${API_URL}/api/auth/logout`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      credentials: 'include',
    }).catch(() => {});
    localStorage.removeItem('session_token');
    setUser(null);
  }, []);

  if (isCallback) return <AuthCallback onAuth={setUser} />;

  if (checking) {
    return (
      <div className="flex items-center justify-center h-screen bg-white text-slate-400 font-mono text-xs">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 border-2 border-black/20 border-t-black/60 rounded-full animate-spin" />
          Loading platform…
        </div>
      </div>
    );
  }

  if (!user) {
    return <LoginPage onAuth={(data) => setUser(data)} />;
  }

  return (
    <PersonaProvider>
    <div className="flex h-screen bg-white overflow-hidden">
      <Sidebar open={sidebarOpen} user={user} />

      <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
        <TopHeader
          user={user}
          onLogout={handleLogout}
          sidebarOpen={sidebarOpen}
          onToggleSidebar={() => setSidebarOpen(v => !v)}
        />

        {/* GAP-003: Global DEMO MODE banner — always visible above page content */}
        <GlobalDemoBanner />

        {/* Page content */}
        <main className="flex-1 overflow-auto bg-[#F3F4F6]">
          <Routes>
            <Route path="/"                        element={<Dashboard />} />
            <Route path="/portfolios"              element={<Portfolios />} />
            <Route path="/portfolios/:id"          element={<PortfolioDetail />} />
            <Route path="/analysis"                element={<Analysis />} />
            <Route path="/results/:runId"          element={<Results />} />
            <Route path="/scenario-data"           element={<ScenarioData />} />
            <Route path="/scenario-builder"        element={<ScenarioBuilder />} />
            <Route path="/data-hub"                element={<DataHub />} />
            <Route path="/browser"                 element={<ScenarioBrowserPage />} />
            <Route path="/comparison"              element={<ComparisonPage />} />
            <Route path="/impact"                  element={<ImpactCalculatorPage />} />
            <Route path="/portfolio-manager"       element={<PortfolioManagerPage />} />
            <Route path="/alerts"                  element={<AlertsPage />} />
            <Route path="/ngfs"                    element={<NGFSScenariosPage />} />
            <Route path="/custom-builder"          element={<CustomBuilderPage />} />
            <Route path="/sub-analysis"            element={<SubAnalysisPage />} />
            <Route path="/cbam"                    element={<CBAMPage />} />
            <Route path="/carbon"                  element={<CarbonDashboard />} />
            <Route path="/dcm-calculator"          element={<DCMCalculatorPage />} />
            <Route path="/nature-risk"             element={<NatureRiskPage />} />
            <Route path="/stranded-assets"         element={<StrandedAssetsPage />} />
            <Route path="/valuation"               element={<UnifiedValuationPage />} />
            <Route path="/sustainability"          element={<SustainabilityPage />} />
            <Route path="/scenario-analysis"       element={<ScenarioAnalysisPage />} />
            <Route path="/portfolio-analytics"     element={<PortfolioAnalyticsPage />} />
            <Route path="/financial-risk"          element={<FinancialRiskPage />} />
            <Route path="/real-estate-assessment"  element={<RealEstateAssessmentPage />} />
            <Route path="/supply-chain"            element={<SupplyChainPage />} />
            <Route path="/sector-assessments"      element={<SectorAssessmentsPage />} />
            <Route path="/regulatory"              element={<RegulatoryPage />} />
            <Route path="/interactive"             element={<InteractiveDashboard />} />
            <Route path="/portfolio-health"        element={<PortfolioHealthPage />} />
            <Route path="/glidepath-tracker"       element={<GlidepathTrackerPage />} />
            <Route path="/peer-benchmark"          element={<PeerBenchmarkPage />} />
            <Route path="/analyst-portfolios"      element={<AnalystPortfoliosPage />} />
            <Route path="/company-profiles"        element={<CompanyProfilesPage />} />
            {/* Category C — Data Intake */}
            <Route path="/data-intake"                element={<DataIntakeDashboard />} />
            <Route path="/data-intake/portfolio"      element={<LoanPortfolioUpload />} />
            <Route path="/data-intake/counterparty"   element={<CounterpartyEmissionsWizard />} />
            <Route path="/data-intake/real-estate"    element={<RealEstateEUIUpload />} />
            <Route path="/data-intake/shipping-fleet" element={<ShippingFleetUpload />} />
            <Route path="/data-intake/steel-borrowers" element={<SteelBorrowersEntry />} />
            <Route path="/data-intake/project-finance" element={<ProjectFinanceIntake />} />
            <Route path="/data-intake/internal-config"    element={<InternalConfigPage />} />
            <Route path="/data-intake/persona-templates" element={<PersonaTemplatesPage />} />
            {/* Category D — Engagement Tracker */}
            <Route path="/engagement-tracker"          element={<EngagementTrackerPage />} />
            {/* P2 — Monte Carlo Simulation */}
            <Route path="/monte-carlo"                 element={<MonteCarloPage />} />
            {/* Scenario Builder v2 — NGFS Phase IV */}
            <Route path="/scenario-builder-v2"        element={<ScenarioBuilderPage />} />
            <Route path="/scenario-gallery"           element={<ScenarioGalleryPage />} />
            {/* Asia Regulatory — BRSR / HKMA / BoJ / ASEAN / PBoC / CBI */}
            <Route path="/asia-regulatory"            element={<AsiaRegulatoryPage />} />
            {/* Data Mapping — source to KPI to module */}
            <Route path="/data-mapping"               element={<DataMappingPage />} />
            {/* CA100+ Net Zero Company Benchmark */}
            <Route path="/ca100"                      element={<CA100Page />} />
            {/* Country Risk & Governance */}
            <Route path="/country-risk"               element={<CountryRiskPage />} />
            {/* Data Preview — table browser, FK relationships, datapoint mappings */}
            <Route path="/data-preview"               element={<DataPreviewPage />} />
            {/* China Trade Platform — standalone module */}
            <Route path="/china-trade"                element={<ChinaTradePage />} />
            {/* Climate Risk Engine — Physical / Transition / Integrated */}
            <Route path="/climate-risk"               element={<ClimateRiskPage />} />
            {/* Strategic Hub Pages — 6 new modules */}
            <Route path="/disclosure-frameworks"      element={<DisclosureFrameworksPage />} />
            <Route path="/eu-regulatory"              element={<EURegulatoryHubPage />} />
            <Route path="/banking-capital"            element={<BankingCapitalPage />} />
            <Route path="/asset-management"           element={<AssetManagementPage />} />
            <Route path="/sovereign-emissions"        element={<SovereignEmissionsPage />} />
            <Route path="/platform-intelligence"      element={<PlatformIntelligencePage />} />
            {/* Phase 11 — Double Materiality + SFDR PAI */}
            <Route path="/double-materiality"         element={<DoubleMaterialityPage />} />
            <Route path="/sfdr-pai"                    element={<SFDRPAIPage />} />
            {/* Phase 12 — Remaining engine frontends */}
            <Route path="/xbrl"                       element={<XBRLPage />} />
            <Route path="/pe-deals"                   element={<PEDealsPage />} />
            <Route path="/residential-re"             element={<ResidentialREPage />} />
            <Route path="/technology-risk"            element={<TechnologyRiskPage />} />
            <Route path="/fund-management"            element={<FundManagementPage />} />
            {/* DME (Dynamic Materiality Engine) — integrated from sahilchopra-design/DME */}
            <Route path="/dme-dashboard"              element={<DMEDashboardPage />} />
            <Route path="/sentiment"                  element={<SentimentAnalysisPage />} />
            <Route path="/sovereign-climate-risk"     element={<SovereignClimateRiskPage />} />
            <Route path="/sec-climate"                element={<SECClimatePage />} />
            <Route path="/green-hydrogen"             element={<GreenHydrogenPage />} />
            <Route path="/stress-testing"             element={<StressTestingPage />} />
            <Route path="/geothermal"                 element={<GeothermalPage />} />
            <Route path="/energy-finance"             element={<EnergyFinancePage />} />
            <Route path="/energy-transition"          element={<EnergyTransitionPage />} />
            <Route path="/gar-ets"                    element={<GarEtsPage />} />
            <Route path="/project-finance"            element={<ProjectFinancePage />} />
            <Route path="/data-hub-ingestion"         element={<DataHubIngestionPage />} />
            <Route path="/eiopa-stress"               element={<EiopaStressPage />} />
            <Route path="/iorp-pension"               element={<IORPPensionPage />} />
            <Route path="/assurance-readiness"        element={<AssurancePage />} />
            <Route path="/sfdr-annex"                 element={<SFDRAnnexPage />} />
            <Route path="/stewardship"                element={<StewardshipPage />} />
            <Route path="/eudr"                       element={<EUDRPage />} />
            <Route path="/csddd"                      element={<CSDDDPage />} />
            <Route path="/basel-capital"              element={<BaselCapitalPage />} />
            <Route path="/tnfd-assessment"            element={<TNFDPage />} />
            <Route path="/pcaf-quality"               element={<PCAFQualityPage />} />
            <Route path="/cdp-scoring"                element={<CDPPage />} />
            <Route path="/gri-standards"              element={<GRIPage />} />
            <Route path="/sasb-industry"              element={<SASBPage />} />
            <Route path="/model-validation"           element={<ModelValidationPage />} />
            <Route path="/uk-sdr"                     element={<UKSDRPage />} />
            <Route path="/mifid-spt"                  element={<MiFIDSPTPage />} />
            <Route path="/tcfd-metrics"               element={<TCFDMetricsPage />} />
            <Route path="/eu-gbs"                     element={<EUGBSPage />} />
            <Route path="/priips-kid"                 element={<PRIIPSKIDPage />} />
            <Route path="/esma-fund-names"            element={<ESMAFundNamesPage />} />
            <Route path="/sl-finance"                 element={<SLFinancePage />} />
            <Route path="/ifrs-s1"                    element={<IFRSS1Page />} />
            <Route path="/eu-taxonomy-gar"            element={<EUTaxonomyGARPage />} />
            <Route path="/eba-pillar3"               element={<EBAPillar3Page />} />
            <Route path="/scope3-categories"         element={<Scope3CategoriesPage />} />
            <Route path="/sfdr-product-reporting"    element={<SFDRProductReportingPage />} />
            <Route path="/biodiversity-finance"      element={<BiodiversityFinancePage />} />
            <Route path="/ifrs-s2"                   element={<IFRSS2Page />} />
            <Route path="/gri-standards"             element={<GRIStandardsPage />} />
            <Route path="/tpt-transition-plan"       element={<TPTTransitionPlanPage />} />
            <Route path="/pcaf-sovereign"            element={<PCAFSovereignPage />} />
            <Route path="/esrs-e2-e5"                element={<ESRSE2E5Page />} />
            <Route path="/greenwashing"              element={<GreenwashingPage />} />
            <Route path="/carbon-credit-quality"     element={<CarbonCreditQualityPage />} />
            <Route path="/climate-stress-test"       element={<ClimateStressTestPage />} />
            <Route path="/tnfd-leap"                 element={<TNFDLEAPPage />} />
            <Route path="/net-zero-targets"          element={<NetZeroTargetsPage />} />
            <Route path="/esg-data-quality"          element={<ESGDataQualityPage />} />
            <Route path="/regulatory-penalties"      element={<RegulatoryPenaltiesPage />} />
            <Route path="/basel-liquidity"           element={<BaselLiquidityPage />} />
            <Route path="/social-taxonomy"           element={<SocialTaxonomyPage />} />
            <Route path="/forced-labour"             element={<ForcedLabourPage />} />
            <Route path="/transition-finance"        element={<TransitionFinancePage />} />
            <Route path="/csrd-dma"                  element={<CSRDDMAPage />} />
            <Route path="/physical-hazard"           element={<PhysicalHazardPage />} />
            <Route path="/avoided-emissions"         element={<AvoidedEmissionsPage />} />
            <Route path="/green-hydrogen"            element={<GreenHydrogenPage />} />
            <Route path="/biodiversity-finance-v2"   element={<BiodiversityFinanceV2Page />} />
            <Route path="/prudential-climate-risk"   element={<PrudentialClimateRiskPage />} />
            <Route path="/carbon-markets-intel"      element={<CarbonMarketsIntelPage />} />
            <Route path="/just-transition"           element={<JustTransitionPage />} />
            <Route path="/shipping-maritime"         element={<ShippingMaritimePage />} />
            <Route path="/aviation-climate"          element={<AviationClimatePage />} />
            <Route path="/commercial-re"             element={<CommercialREPage />} />
            <Route path="/infrastructure-finance"    element={<InfrastructureFinancePage />} />
            <Route path="/nature-based-solutions"    element={<NatureBasedSolutionsPage />} />
            <Route path="/water-risk"                element={<WaterRiskPage />} />
            <Route path="/food-system"               element={<FoodSystemPage />} />
            <Route path="/circular-economy"          element={<CircularEconomyPage />} />
            <Route path="/climate-litigation"        element={<ClimateLitigationPage />} />
            <Route path="/esg-ratings"               element={<ESGRatingsPage />} />
            <Route path="/methane-fugitive"          element={<MethaneFugitivePage />} />
            <Route path="/health-climate"            element={<HealthClimatePage />} />
            <Route path="/maritime"                  element={<MaritimePage />} />
            <Route path="/hydrogen"                  element={<HydrogenPage />} />
            <Route path="/cdr"                       element={<CDRPage />} />
            <Route path="/biodiversity-credits"      element={<BiodiversityCreditsPage />} />
            <Route path="/scope3-analytics"          element={<Scope3AnalyticsPage />} />
            <Route path="/blue-economy"              element={<BlueEconomyPage />} />
            <Route path="/sovereign-debt-climate"    element={<SovereignDebtClimatePage />} />
            <Route path="/loss-damage-finance"       element={<LossDamageFinancePage />} />
            <Route path="/carbon-price-ets"          element={<CarbonPriceETSPage />} />
            <Route path="/blended-finance"      element={<BlendedFinancePage />} />
            <Route path="/mrv"                  element={<MRVPage />} />
            <Route path="/real-asset-decarb"    element={<RealAssetDecarbPage />} />
            <Route path="/trade-finance-esg"    element={<TradeFinanceESGPage />} />
            <Route path="/ai-risk"          element={<AIRiskPage />} />
            <Route path="/nature-capital"   element={<NatureCapitalPage />} />
            <Route path="/climate-finance"  element={<ClimateFinancePage />} />
            <Route path="/esg-ma"           element={<ESGMAPage />} />
            <Route path="*"                          element={<NotFoundPage />} />
          </Routes>
        </main>
      </div>
    </div>
    </PersonaProvider>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <Router>
            <AppRouter />
          </Router>
        </QueryClientProvider>
      </Provider>
    </ErrorBoundary>
  );
}

// ─── Icon map ─────────────────────────────────────────────────────────────────

const ICON_MAP = {
  activity:      'M22 12h-4l-3 9L9 3l-3 9H2',
  layout:        'M4 5a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1V5zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1V5zM4 15a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1H5a1 1 0 01-1-1v-4zm10 0a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z',
  target:        'M12 2a10 10 0 100 20 10 10 0 000-20zm0 4a6 6 0 100 12 6 6 0 000-12zm0 4a2 2 0 100 4 2 2 0 000-4z',
  microscope:    'M9 2v6h2V2H9zm-1 8a4 4 0 108 0H8zm-4 8h16v2H4v-2z',
  search:        'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z',
  database:      'M4 7v10c0 2 3.6 4 8 4s8-2 8-4V7M4 7c0 2 3.6 4 8 4s8-2 8-4M4 7c0-2 3.6-4 8-4s8 2 8 4',
  globe:         'M12 2a10 10 0 100 20 10 10 0 000-20zM2 12h20M12 2a15 15 0 014 10 15 15 0 01-4 10 15 15 0 01-4-10A15 15 0 0112 2z',
  'git-compare': 'M18 21a3 3 0 100-6 3 3 0 000 6zM6 9a3 3 0 100-6 3 3 0 000 6zm12 3V9a3 3 0 00-3-3h-4M6 15v-3',
  wrench:        'M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3.77-3.77a6 6 0 01-7.94 7.94l-6.91 6.91a2.12 2.12 0 01-3-3l6.91-6.91a6 6 0 017.94-7.94l-3.76 3.76z',
  briefcase:     'M20 7H4a2 2 0 00-2 2v10a2 2 0 002 2h16a2 2 0 002-2V9a2 2 0 00-2-2zM16 7V5a2 2 0 00-2-2h-4a2 2 0 00-2 2v2',
  upload:        'M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M17 8l-5-5-5 5M12 3v12',
  'bar-chart':   'M18 20V10M12 20V4M6 20v-6',
  bell:          'M18 8A6 6 0 006 8c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 01-3.46 0',
  layers:        'M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5',
  archive:       'M21 8v13H3V8M1 3h22v5H1zM10 12h4',
  leaf:          'M11 20A7 7 0 019.8 6.1C15.5 5 17 4.48 19 2c1 2 2 4.18 2 8 0 5.5-4.78 10-10 10zM2 21c0-3 1.85-5.36 5.08-6C9.5 14.52 12 13 13 12',
  tree:          'M12 22v-7m0 0c-3.5 0-6-2.5-6-6 0-2 1-4 3-5.5C10 2.5 11 2 12 2s2 .5 3 1.5c2 1.5 3 3.5 3 5.5 0 3.5-2.5 6-6 6z',
  'trending-down':'M23 18l-9.5-9.5-5 5L1 6M17 18h6v-6',
  'trending-up':  'M23 6l-9.5 9.5-5-5L1 18M17 6h6v6',
  building:      'M3 21h18M5 21V7l8-4v18M19 21V11l-6-4M9 9v.01M9 12v.01M9 15v.01M9 18v.01',
  award:         'M12 15l-2 5-1.5-4-4.5 1.5L6 13 2 11l4-2L4 4.5 8.5 6 10 2l2 5 2-5 1.5 4 4.5-1.5L18 9l4 2-4 2 2 4.5-4.5-1.5L14 20l-2-5z',
  calculator:    'M4 2h16a2 2 0 012 2v16a2 2 0 01-2 2H4a2 2 0 01-2-2V4a2 2 0 012-2zm3 4h10M7 10h2M7 14h2M7 18h2M15 10h2M15 14h2M15 18h2M11 10h2M11 14h2M11 18h2',
  cpu:           'M9 3H5a2 2 0 00-2 2v4m6-6h10a2 2 0 012 2v4M9 3v18m0 0h10a2 2 0 002-2V9M9 21H5a2 2 0 01-2-2V9m0 0h18',
  'pie-chart':   'M21.21 15.89A10 10 0 118 2.83M22 12A10 10 0 0012 2v10z',
  shield:        'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z',
  home:          'M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2V9zM9 22V12h6v10',
  truck:         'M1 3h15v13H1V3zM16 8h4l3 3v5h-7V8zM5.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3zM18.5 21a1.5 1.5 0 100-3 1.5 1.5 0 000 3z',
  server:        'M2 2h20v8H2V2zm0 12h20v8H2v-8zm5 4h.01M5 6h.01',
  'file-text':   'M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6zM14 2v6h6M16 13H8M16 17H8M10 9H8',
  users:         'M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zm8 4a3 3 0 100-6 3 3 0 000 6zm3 2v-1a3 3 0 00-3-3h-1',
  link:          'M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71',
  thermometer:   'M14 14.76V3.5a2.5 2.5 0 00-5 0v11.26a4.5 4.5 0 105 0z',
  landmark:      'M3 22h18M4 10h16M2 10l10-8 10 8M6 10v12M18 10v12M10 10v12M14 10v12',
  'map-pin':     'M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0118 0zM12 13a3 3 0 100-6 3 3 0 000 6z',
  sliders:       'M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6',
  'book-open':   'M2 3h6a4 4 0 014 4v14a3 3 0 00-3-3H2zM22 3h-6a4 4 0 00-4 4v14a3 3 0 013-3h7z',
  'check-square':'M9 11l3 3L22 4M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11',
};

export default App;
