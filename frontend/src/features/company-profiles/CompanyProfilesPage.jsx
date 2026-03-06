/**
 * CompanyProfilesPage — Comprehensive entity intelligence hub
 *
 * Covers:
 *  - Company identity & sector classification (GICS, NACE, NAICS)
 *  - Corporate financials (assets, revenue, employees, credit ratings)
 *  - Regulatory perimeter (systemic importance, supervisor)
 *  - Basel III prudential metrics (CET1, leverage, LCR, NSFR, RWA, NPL)
 *  - Pillar 3 ESG disclosures (GAR, BTAR, financed emissions, physical/transition risk)
 *  - Solvency II (SCR, MCR, own funds, combined ratio)
 *  - Asset manager (AUM, RI AUM, SFDR classification, stewardship)
 *  - GHG own-operations (Scope 1/2/3, intensity, energy, water, waste)
 *  - ESG memberships (NZBA, PCAF, SBTi, TCFD, TNFD, CDP, UN PRB, GFANZ)
 *  - Regulatory frameworks applicable (CSRD, ISSB, BRSR)
 */
import React, { useState, useEffect, useCallback } from 'react';

const API = 'http://localhost:8001';

// ─── Formatting helpers ────────────────────────────────────────────────────────
const fmt = {
  pct:      (v) => v == null ? '—' : `${parseFloat(v).toFixed(1)}%`,
  num:      (v, dp = 2) => v == null ? '—' : parseFloat(v).toLocaleString('en-US', { maximumFractionDigits: dp }),
  eur_bn:   (v) => v == null ? '—' : `€${parseFloat(v).toFixed(1)} bn`,
  eur_mn:   (v) => v == null ? '—' : `€${parseFloat(v).toFixed(0)} mn`,
  tco2:     (v) => v == null ? '—' : `${(parseFloat(v) / 1000).toFixed(1)} kt`,
  ratio:    (v) => v == null ? '—' : `${parseFloat(v).toFixed(2)}x`,
  int:      (v) => v == null ? '—' : parseInt(v).toLocaleString('en-US'),
  bool:     (v) => v == null ? '—' : (v ? 'Yes' : 'No'),
  year:     (v) => v == null ? '—' : String(v),
  text:     (v) => v == null || v === '' ? '—' : v,
};

// ─── Sub-components ────────────────────────────────────────────────────────────

function KpiCard({ label, value, unit = '', color = 'cyan', sub }) {
  const colors = {
    cyan:   'text-cyan-400',
    green:  'text-emerald-400',
    amber:  'text-amber-400',
    red:    'text-red-400',
    blue:   'text-blue-400',
    purple: 'text-purple-400',
  };
  return (
    <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
      <p className="text-xs text-slate-400 uppercase tracking-wider mb-1">{label}</p>
      <p className={`text-2xl font-mono font-bold ${colors[color] || colors.cyan}`}>
        {value}<span className="text-sm text-slate-400 ml-1">{unit}</span>
      </p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  );
}

function DataRow({ label, value, highlight }) {
  return (
    <div className={`flex justify-between items-start py-2 border-b border-slate-700/50 ${highlight ? 'bg-slate-800/30 px-2 rounded' : ''}`}>
      <span className="text-xs text-slate-400 w-1/2">{label}</span>
      <span className="text-xs text-slate-200 text-right w-1/2 font-mono">{value}</span>
    </div>
  );
}

function SectionHeading({ children }) {
  return (
    <h3 className="text-xs font-semibold text-cyan-400 uppercase tracking-widest mt-6 mb-3 border-b border-slate-700 pb-1">
      {children}
    </h3>
  );
}

function Badge({ label, variant = 'default' }) {
  const v = {
    default: 'bg-slate-700 text-slate-300',
    green:   'bg-emerald-900/60 text-emerald-300 border border-emerald-700',
    amber:   'bg-amber-900/60 text-amber-300 border border-amber-700',
    red:     'bg-red-900/60 text-red-300 border border-red-700',
    blue:    'bg-blue-900/60 text-blue-300 border border-blue-700',
    cyan:    'bg-cyan-900/60 text-cyan-300 border border-cyan-700',
    purple:  'bg-purple-900/60 text-purple-300 border border-purple-700',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-semibold mr-1 mb-1 ${v[variant] || v.default}`}>
      {label}
    </span>
  );
}

function MembershipBadges({ p }) {
  const items = [
    { key: 'nzba_member',      label: 'NZBA',      variant: 'green' },
    { key: 'pcaf_member',      label: 'PCAF',      variant: 'green' },
    { key: 'tcfd_supporter',   label: 'TCFD',      variant: 'blue' },
    { key: 'tnfd_supporter',   label: 'TNFD',      variant: 'blue' },
    { key: 'un_prb_signatory', label: 'UN PRB',    variant: 'purple' },
    { key: 'gfanz_member',     label: 'GFANZ',     variant: 'purple' },
    { key: 'nzaoa_member',     label: 'NZAOA',     variant: 'cyan' },
    { key: 'un_pri_signatory', label: 'UN PRI',    variant: 'cyan' },
    { key: 'pact_signatory',   label: 'PACT',      variant: 'cyan' },
    { key: 'equator_principles',label: 'Equator',  variant: 'blue' },
  ];
  const active = items.filter(i => p[i.key]);
  if (!active.length) return <span className="text-xs text-slate-500">None recorded</span>;
  return <div>{active.map(i => <Badge key={i.key} label={i.label} variant={i.variant} />)}</div>;
}

// ─── Detail panel tabs ─────────────────────────────────────────────────────────

function IdentityTab({ p }) {
  return (
    <div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <KpiCard label="Total Assets" value={fmt.eur_bn(p.total_assets_eur_bn)} color="cyan" />
        <KpiCard label="Annual Revenue" value={fmt.eur_mn(p.annual_revenue_eur_mn)} color="blue" />
        <KpiCard label="Employees (FTE)" value={fmt.int(p.employees_fte)} color="purple" />
        <KpiCard label="Market Cap" value={fmt.eur_bn(p.market_cap_eur_bn)} color="amber" />
      </div>

      <SectionHeading>Legal & Identity</SectionHeading>
      <DataRow label="Legal Name"          value={fmt.text(p.legal_name)} />
      <DataRow label="Trading Name"        value={fmt.text(p.trading_name)} />
      <DataRow label="LEI"                 value={fmt.text(p.entity_lei)} />
      <DataRow label="ISIN (Primary)"      value={fmt.text(p.isin_primary)} />
      <DataRow label="Ticker"              value={fmt.text(p.ticker_symbol)} />
      <DataRow label="Bloomberg"           value={fmt.text(p.bloomberg_ticker)} />
      <DataRow label="Stock Exchange"      value={fmt.text(p.stock_exchange)} />
      <DataRow label="Listing Status"      value={fmt.text(p.listing_status)} />
      <DataRow label="Incorporation"       value={fmt.text(p.incorporation_country)} />
      <DataRow label="HQ City"             value={fmt.text(p.headquarters_city)} />
      <DataRow label="HQ Country"          value={fmt.text(p.headquarters_country)} />
      <DataRow label="Founded"             value={fmt.year(p.founded_year)} />
      <DataRow label="Fiscal Year End"     value={fmt.text(p.fiscal_year_end)} />
      <DataRow label="Parent Entity LEI"   value={fmt.text(p.parent_entity_lei)} />

      <SectionHeading>Sector Classification</SectionHeading>
      <DataRow label="Primary Sector"      value={fmt.text(p.primary_sector)} />
      <DataRow label="Institution Type"    value={fmt.text(p.institution_type)} />
      <DataRow label="GICS Sector"         value={fmt.text(p.gics_sector)} />
      <DataRow label="GICS Industry Group" value={fmt.text(p.gics_industry_group)} />
      <DataRow label="GICS Industry"       value={fmt.text(p.gics_industry)} />
      <DataRow label="GICS Sub-Industry"   value={fmt.text(p.gics_sub_industry)} />
      <DataRow label="NACE Code"           value={fmt.text(p.nace_code)} />
      <DataRow label="NAICS Code"          value={fmt.text(p.naics_code)} />
      <DataRow label="SIC Code"            value={fmt.text(p.sic_code)} />

      <SectionHeading>Credit & Ratings</SectionHeading>
      <DataRow label="S&P Rating"          value={fmt.text(p.credit_rating_sp)} />
      <DataRow label="Moody's Rating"      value={fmt.text(p.credit_rating_moodys)} />
      <DataRow label="Fitch Rating"        value={fmt.text(p.credit_rating_fitch)} />

      <SectionHeading>Regulatory Perimeter</SectionHeading>
      <DataRow label="Financial Institution" value={fmt.bool(p.is_financial_institution)} />
      <DataRow label="Supervisor"          value={fmt.text(p.regulatory_supervisor)} />
      <DataRow label="Framework"           value={fmt.text(p.regulatory_framework)} />
      <DataRow label="Systemic Importance" value={fmt.text(p.systemic_importance)} />
      <DataRow label="FSB Bucket"          value={fmt.text(p.systemic_importance_bucket)} />
      <DataRow label="Deposit Guarantee"   value={fmt.text(p.deposit_guarantee_scheme)} />
    </div>
  );
}

function PrudentialTab({ p }) {
  const cet1Color = p.cet1_ratio_pct >= 13 ? 'green' : p.cet1_ratio_pct >= 10.5 ? 'amber' : 'red';
  const lcrColor  = p.lcr_pct  >= 130 ? 'green' : p.lcr_pct  >= 100 ? 'amber' : 'red';
  const nsfrColor = p.nsfr_pct >= 110 ? 'green' : p.nsfr_pct >= 100 ? 'amber' : 'red';
  const lvrColor  = p.leverage_ratio_pct >= 4 ? 'green' : p.leverage_ratio_pct >= 3 ? 'amber' : 'red';

  return (
    <div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <KpiCard label="CET1 Ratio" value={fmt.pct(p.cet1_ratio_pct)} color={cet1Color} sub="Min 4.5% + buffers" />
        <KpiCard label="LCR" value={fmt.pct(p.lcr_pct)} color={lcrColor} sub="Min 100%" />
        <KpiCard label="NSFR" value={fmt.pct(p.nsfr_pct)} color={nsfrColor} sub="Min 100%" />
        <KpiCard label="Leverage Ratio" value={fmt.pct(p.leverage_ratio_pct)} color={lvrColor} sub="Min 3%" />
      </div>

      <SectionHeading>Basel III Capital Ratios</SectionHeading>
      <DataRow label="CET1 Ratio"              value={fmt.pct(p.cet1_ratio_pct)} highlight />
      <DataRow label="Tier 1 Capital Ratio"    value={fmt.pct(p.tier1_capital_ratio_pct)} />
      <DataRow label="Total Capital Ratio"     value={fmt.pct(p.total_capital_ratio_pct)} />
      <DataRow label="Leverage Ratio"          value={fmt.pct(p.leverage_ratio_pct)} highlight />
      <DataRow label="Pillar 2 Requirement"    value={fmt.pct(p.pillar2_requirement_pct)} />
      <DataRow label="Combined Buffer"         value={fmt.pct(p.combined_buffer_requirement_pct)} />
      <DataRow label="SREP Composite Score"    value={fmt.text(p.srep_composite_score)} />

      <SectionHeading>Liquidity</SectionHeading>
      <DataRow label="LCR"                     value={fmt.pct(p.lcr_pct)} highlight />
      <DataRow label="NSFR"                    value={fmt.pct(p.nsfr_pct)} highlight />
      <DataRow label="ICAAP Passed"            value={fmt.bool(p.icaap_passed)} />
      <DataRow label="ILAAP Passed"            value={fmt.bool(p.ilaap_passed)} />

      <SectionHeading>Risk-Weighted Assets</SectionHeading>
      <DataRow label="Total RWA"               value={fmt.eur_bn(p.rwa_eur_bn)} highlight />
      <DataRow label="RWA — Credit Risk"       value={fmt.eur_bn(p.rwa_credit_eur_bn)} />
      <DataRow label="RWA — Market Risk"       value={fmt.eur_bn(p.rwa_market_eur_bn)} />
      <DataRow label="RWA — Operational Risk"  value={fmt.eur_bn(p.rwa_operational_eur_bn)} />
      <DataRow label="Total Exposure"          value={fmt.eur_bn(p.total_exposure_eur_bn)} />
      <DataRow label="MREL Requirement"        value={fmt.eur_bn(p.mreel_eur_bn)} />
      <DataRow label="MREL Met"                value={fmt.bool(p.mrel_met)} />

      <SectionHeading>Asset Quality & Profitability</SectionHeading>
      <DataRow label="NPL Ratio"               value={fmt.pct(p.npl_ratio_pct)} highlight />
      <DataRow label="NPL Coverage Ratio"      value={fmt.pct(p.npl_coverage_ratio_pct)} />
      <DataRow label="Cost of Risk"            value={p.cost_of_risk_bps != null ? `${p.cost_of_risk_bps} bps` : '—'} />
      <DataRow label="ROE"                     value={fmt.pct(p.roe_pct)} />
      <DataRow label="ROA"                     value={fmt.pct(p.roa_pct)} />
      <DataRow label="NIM"                     value={fmt.pct(p.nim_pct)} />
      <DataRow label="Cost-to-Income Ratio"    value={fmt.pct(p.cost_income_ratio_pct)} />
      <DataRow label="Loan Book"               value={fmt.eur_bn(p.loan_book_eur_bn)} />
      <DataRow label="Deposit Base"            value={fmt.eur_bn(p.deposit_base_eur_bn)} />

      <SectionHeading>Solvency II (Insurance)</SectionHeading>
      <DataRow label="SCR Coverage Ratio"      value={fmt.pct(p.solvency2_scr_ratio_pct)} highlight />
      <DataRow label="MCR Coverage Ratio"      value={fmt.pct(p.solvency2_mcr_ratio_pct)} />
      <DataRow label="Own Funds"               value={fmt.eur_bn(p.solvency2_own_funds_eur_bn)} />
      <DataRow label="SCR (EUR)"               value={fmt.eur_bn(p.solvency2_scr_eur_bn)} />
      <DataRow label="Best Estimate Liabilities" value={fmt.eur_bn(p.solvency2_best_estimate_liabilities_eur_bn)} />
      <DataRow label="Combined Ratio"          value={fmt.pct(p.combined_ratio_pct)} />
      <DataRow label="Loss Ratio"              value={fmt.pct(p.loss_ratio_pct)} />
      <DataRow label="Expense Ratio"           value={fmt.pct(p.expense_ratio_pct)} />
      <DataRow label="Investment Return"       value={fmt.pct(p.investment_return_pct)} />
      <DataRow label="Nat-Cat Climate Exposure" value={fmt.eur_bn(p.climate_nat_cat_exposure_eur_bn)} />
      {p.sfcr_report_url && (
        <a href={p.sfcr_report_url} target="_blank" rel="noopener noreferrer"
           className="inline-block mt-2 text-xs text-cyan-400 hover:text-cyan-300 underline">
          SFCR Report
        </a>
      )}
    </div>
  );
}

function Pillar3Tab({ p }) {
  return (
    <div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <KpiCard label="Green Asset Ratio" value={fmt.pct(p.p3_gar_pct)} color="green" sub="EU Taxonomy aligned / covered assets" />
        <KpiCard label="BTAR" value={fmt.pct(p.p3_btar_pct)} color="green" sub="Banking Book TAR" />
        <KpiCard label="WACI" value={p.p3_waci_tco2e_meur != null ? `${parseFloat(p.p3_waci_tco2e_meur).toFixed(2)}` : '—'}
                 unit="tCO₂/MEUR" color="amber" />
        <KpiCard label="Temp. Alignment" value={p.p3_temperature_alignment_c != null ? `${p.p3_temperature_alignment_c}°C` : '—'} color="red" />
      </div>

      <SectionHeading>Pillar 3 — EU Taxonomy & Green Finance</SectionHeading>
      <DataRow label="Green Asset Ratio (GAR)"       value={fmt.pct(p.p3_gar_pct)} highlight />
      <DataRow label="Off-Balance Sheet GAR"          value={fmt.pct(p.p3_off_balance_sheet_gar_pct)} />
      <DataRow label="BTAR"                           value={fmt.pct(p.p3_btar_pct)} highlight />
      {p.p3_report_url && (
        <div className="mt-1 mb-2">
          <a href={p.p3_report_url} target="_blank" rel="noopener noreferrer"
             className="text-xs text-cyan-400 hover:text-cyan-300 underline">
            Pillar 3 Report {p.p3_report_date ? `(${p.p3_report_date})` : ''}
          </a>
        </div>
      )}

      <SectionHeading>Climate Risk Exposure</SectionHeading>
      <DataRow label="Transition Risk Exposure"       value={fmt.eur_bn(p.p3_transition_risk_exposure_eur_bn)} highlight />
      <DataRow label="Physical Risk Exposure"         value={fmt.eur_bn(p.p3_physical_risk_exposure_eur_bn)} highlight />
      <DataRow label="RE Collateral Physical Risk"    value={fmt.pct(p.p3_real_estate_collateral_phys_risk_pct)} />
      <DataRow label="Corporate Collateral Phys. Risk" value={fmt.pct(p.p3_corporate_collateral_phys_risk_pct)} />
      <DataRow label="Fossil Fuel Exposure"           value={fmt.eur_bn(p.p3_fossil_fuel_exposure_eur_bn)} />
      <DataRow label="Renewable Energy Exposure"      value={fmt.eur_bn(p.p3_renewable_energy_exposure_eur_bn)} />

      <SectionHeading>Financed Emissions (PCAF)</SectionHeading>
      <DataRow label="Scope 1 (own ops)"              value={fmt.tco2(p.p3_scope1_tco2e)} />
      <DataRow label="Scope 2 (own ops)"              value={fmt.tco2(p.p3_scope2_tco2e)} />
      <DataRow label="Scope 3 (own ops)"              value={fmt.tco2(p.p3_scope3_tco2e)} />
      <DataRow label="Financed Emissions (absolute)"  value={fmt.tco2(p.p3_financed_emissions_tco2e)} highlight />
      <DataRow label="WACI (tCO₂/MEUR)"              value={p.p3_waci_tco2e_meur != null ? parseFloat(p.p3_waci_tco2e_meur).toFixed(4) : '—'} highlight />
      <DataRow label="Implied Temperature Rise"       value={p.p3_temperature_alignment_c != null ? `${p.p3_temperature_alignment_c}°C` : '—'} />

      <SectionHeading>Sustainable Finance</SectionHeading>
      <DataRow label="Green Bonds Issued"             value={fmt.eur_bn(p.green_bond_issuance_eur_bn)} />
      <DataRow label="SLL / ESG-linked Loans"         value={fmt.eur_bn(p.sustainability_linked_loans_eur_bn)} />
      <DataRow label="Social Bonds Issued"            value={fmt.eur_bn(p.social_bond_issuance_eur_bn)} />
      <DataRow label="Sust. Finance Target"           value={fmt.eur_bn(p.sustainable_finance_target_eur_bn)} />
      <DataRow label="Target Year"                    value={fmt.year(p.sustainable_finance_target_year)} />
      <DataRow label="Achieved to Date"               value={fmt.eur_bn(p.sustainable_finance_achieved_eur_bn)} />
    </div>
  );
}

function ClimateTab({ p }) {
  const sbtiColor = p.sbti_status === 'Approved' ? 'green' : p.sbti_status === 'Committed' ? 'amber' : 'red';
  return (
    <div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <KpiCard label="Net Zero Target" value={fmt.year(p.net_zero_target_year)} color="green" />
        <KpiCard label="SBTi Status" value={fmt.text(p.sbti_status) || '—'} color={sbtiColor} />
        <KpiCard label="CDP Score" value={fmt.text(p.cdp_score)} color="blue" sub={p.cdp_year ? `${p.cdp_year}` : ''} />
        <KpiCard label="Scope 1 GHG" value={fmt.tco2(p.scope1_tco2e)} color="amber" />
      </div>

      <SectionHeading>Own Operations GHG (ESRS E1)</SectionHeading>
      <DataRow label="Scope 1"                        value={fmt.tco2(p.scope1_tco2e)} highlight />
      <DataRow label="Scope 2 (market-based)"         value={fmt.tco2(p.scope2_tco2e_market)} />
      <DataRow label="Scope 2 (location-based)"       value={fmt.tco2(p.scope2_tco2e_location)} />
      <DataRow label="Scope 3 (total)"                value={fmt.tco2(p.scope3_tco2e_total)} />
      <DataRow label="GHG Intensity (tCO₂/MEUR)"     value={p.ghg_intensity_tco2e_meur_revenue != null ? parseFloat(p.ghg_intensity_tco2e_meur_revenue).toFixed(4) : '—'} />

      <SectionHeading>Energy & Resources (ESRS E1/E3/E5)</SectionHeading>
      <DataRow label="Energy Consumption (MWh)"       value={fmt.num(p.energy_consumption_mwh, 0)} />
      <DataRow label="Renewable Energy %"             value={fmt.pct(p.renewable_energy_pct)} highlight />
      <DataRow label="Water Consumption (m³)"         value={fmt.num(p.water_consumption_m3, 0)} />
      <DataRow label="Waste Recycled %"               value={fmt.pct(p.waste_recycled_pct)} />

      <SectionHeading>EU Taxonomy Alignment</SectionHeading>
      <DataRow label="Taxonomy-Aligned Revenue %"     value={fmt.pct(p.eu_taxonomy_aligned_revenue_pct)} highlight />
      <DataRow label="Taxonomy-Aligned CapEx %"       value={fmt.pct(p.eu_taxonomy_aligned_capex_pct)} />
      <DataRow label="Taxonomy-Aligned OpEx %"        value={fmt.pct(p.eu_taxonomy_aligned_opex_pct)} />

      <SectionHeading>Net-Zero Commitments</SectionHeading>
      <DataRow label="Net Zero Target Year"           value={fmt.year(p.net_zero_target_year)} highlight />
      <DataRow label="Interim Target Year"            value={fmt.year(p.interim_target_year)} />
      <DataRow label="Interim Reduction %"            value={fmt.pct(p.interim_emission_reduction_pct)} />
      <DataRow label="Base Year"                      value={fmt.year(p.base_year)} />
      <DataRow label="Transition Plan Published"      value={fmt.bool(p.transition_plan_published)} />
      <DataRow label="Assurance Provider"             value={fmt.text(p.assurance_provider)} />
      <DataRow label="Assurance Level"                value={fmt.text(p.assurance_level)} />
      {p.transition_plan_url && (
        <a href={p.transition_plan_url} target="_blank" rel="noopener noreferrer"
           className="inline-block mt-2 text-xs text-cyan-400 hover:text-cyan-300 underline">
          Transition Plan
        </a>
      )}

      <SectionHeading>Health & Safety (ESRS S1)</SectionHeading>
      <DataRow label="TRIR"                           value={p.trir != null ? parseFloat(p.trir).toFixed(4) : '—'} />
      <DataRow label="LTIR"                           value={p.ltir != null ? parseFloat(p.ltir).toFixed(4) : '—'} />
      <DataRow label="Fatalities"                     value={fmt.text(p.fatalities)} />
      <DataRow label="Gender Pay Gap %"               value={fmt.pct(p.gender_pay_gap_pct)} />

      <SectionHeading>Governance (ESRS G1)</SectionHeading>
      <DataRow label="Corruption Incidents"           value={fmt.text(p.corruption_incidents)} />
      <DataRow label="Board Size"                     value={fmt.text(p.board_size)} />
      <DataRow label="Board Independence %"           value={fmt.pct(p.board_independence_pct)} />
      <DataRow label="Board Gender Diversity %"       value={fmt.pct(p.board_gender_diversity_pct)} />
      <DataRow label="CEO Pay Ratio"                  value={fmt.ratio(p.ceo_pay_ratio)} />
      <DataRow label="ESG-linked Exec Pay"            value={fmt.bool(p.executive_esg_pay_linkage)} />
    </div>
  );
}

function MembershipsTab({ p }) {
  const frameworks = p.mandatory_frameworks || [];
  const voluntary  = p.voluntary_frameworks  || [];

  return (
    <div>
      <SectionHeading>ESG Memberships & Initiatives</SectionHeading>
      <MembershipBadges p={p} />

      <div className="mt-4 space-y-1">
        <DataRow label="SBTi Status"           value={fmt.text(p.sbti_status)} />
        <DataRow label="SBTi Approval Date"    value={fmt.text(p.sbti_approval_date)} />
        <DataRow label="SBTi Target Year"      value={fmt.year(p.sbti_target_year)} />
        <DataRow label="NZBA Sectors Covered"  value={fmt.text(p.nzba_financed_sectors)} />
        <DataRow label="NZBA Commitment Date"  value={fmt.text(p.nzba_commitment_date)} />
        <DataRow label="CDP Score"             value={fmt.text(p.cdp_score)} />
        <DataRow label="CDP Year"              value={fmt.year(p.cdp_year)} />
        <DataRow label="Stewardship Code"      value={fmt.text(p.stewardship_code_name)} />
      </div>

      <SectionHeading>Regulatory Frameworks Applicable</SectionHeading>
      <DataRow label="CSRD Applicable"         value={fmt.bool(p.csrd_applicable)} />
      <DataRow label="CSRD First Year"         value={fmt.year(p.csrd_first_reporting_year)} />
      <DataRow label="ISSB Adopted"            value={fmt.bool(p.issb_adopted)} />
      <DataRow label="TCFD Mandatory"          value={fmt.bool(p.tcfd_mandatory)} />
      <DataRow label="BRSR Applicable"         value={fmt.bool(p.brsr_applicable)} />

      {frameworks.length > 0 && (
        <>
          <SectionHeading>Mandatory Frameworks</SectionHeading>
          <div className="flex flex-wrap gap-1 mt-1">
            {frameworks.map(f => <Badge key={f} label={f} variant="amber" />)}
          </div>
        </>
      )}
      {voluntary.length > 0 && (
        <>
          <SectionHeading>Voluntary Frameworks</SectionHeading>
          <div className="flex flex-wrap gap-1 mt-1">
            {voluntary.map(f => <Badge key={f} label={f} variant="blue" />)}
          </div>
        </>
      )}

      <SectionHeading>Asset Manager</SectionHeading>
      <DataRow label="AUM"                         value={fmt.eur_bn(p.aum_eur_bn)} />
      <DataRow label="Responsible Investment AUM"  value={fmt.eur_bn(p.responsible_investment_aum_eur_bn)} />
      <DataRow label="RI AUM %"                    value={fmt.pct(p.responsible_investment_aum_pct)} />
      <DataRow label="SFDR Art 8 AUM"              value={fmt.eur_bn(p.article8_aum_eur_bn)} />
      <DataRow label="SFDR Art 9 AUM"              value={fmt.eur_bn(p.article9_aum_eur_bn)} />
      <DataRow label="SFDR Classification"         value={fmt.text(p.sfdr_fund_classification)} />
      <DataRow label="Engagement Votes (Total)"    value={fmt.int(p.engagement_votes_total)} />
      <DataRow label="ESG Votes %"                 value={fmt.pct(p.engagement_votes_esg_pct)} />
      <DataRow label="Shareholder Resolutions Sup %" value={fmt.pct(p.shareholder_resolutions_supported_pct)} />

      <SectionHeading>Data & Source</SectionHeading>
      <DataRow label="Data Source"     value={fmt.text(p.data_source)} />
      <DataRow label="Reporting Year"  value={fmt.year(p.reporting_year)} />
      <DataRow label="Last Updated"    value={p.updated_at ? new Date(p.updated_at).toLocaleDateString() : '—'} />
      {p.sustainability_report_url && (
        <a href={p.sustainability_report_url} target="_blank" rel="noopener noreferrer"
           className="inline-block mt-2 text-xs text-cyan-400 hover:text-cyan-300 underline">
          Sustainability Report
        </a>
      )}
    </div>
  );
}

// ─── Detail panel ──────────────────────────────────────────────────────────────

const DETAIL_TABS = [
  { id: 'identity',    label: 'Identity & Sector' },
  { id: 'prudential',  label: 'Prudential' },
  { id: 'pillar3',     label: 'Pillar 3 / ESG' },
  { id: 'climate',     label: 'Climate & GHG' },
  { id: 'memberships', label: 'Memberships' },
];

function ProfileDetailPanel({ profile, onClose }) {
  const [activeTab, setActiveTab] = useState('identity');
  const p = profile;

  return (
    <div className="fixed inset-0 z-50 flex">
      {/* Backdrop */}
      <div className="flex-1 bg-black/60" onClick={onClose} />

      {/* Panel */}
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-700 flex flex-col overflow-hidden shadow-2xl">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-700 bg-slate-800/60">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-base font-bold text-slate-100">{p.legal_name}</h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {[p.institution_type, p.headquarters_country, p.entity_lei].filter(Boolean).join(' · ')}
              </p>
              <div className="mt-2 flex flex-wrap gap-1">
                {p.systemic_importance && p.systemic_importance !== 'None' && (
                  <Badge label={p.systemic_importance} variant="red" />
                )}
                {p.nzba_member && <Badge label="NZBA" variant="green" />}
                {p.pcaf_member && <Badge label="PCAF" variant="green" />}
                {p.sbti_status === 'Approved' && <Badge label="SBTi ✓" variant="green" />}
                {p.tcfd_supporter && <Badge label="TCFD" variant="blue" />}
                <Badge label={p.data_source === 'csrd_report' ? 'Real Data' : 'Analyst Estimate'} variant={p.data_source === 'csrd_report' ? 'cyan' : 'default'} />
              </div>
            </div>
            <button onClick={onClose} className="text-slate-500 hover:text-slate-300 ml-4 text-xl leading-none">&times;</button>
          </div>

          {/* Tabs */}
          <div className="flex gap-1 mt-4 overflow-x-auto pb-1">
            {DETAIL_TABS.map(t => (
              <button
                key={t.id}
                onClick={() => setActiveTab(t.id)}
                className={`px-3 py-1.5 text-xs font-medium rounded whitespace-nowrap transition-colors ${
                  activeTab === t.id
                    ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/40'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>

        {/* Tab content */}
        <div className="flex-1 overflow-y-auto px-6 py-4">
          {activeTab === 'identity'    && <IdentityTab    p={p} />}
          {activeTab === 'prudential'  && <PrudentialTab  p={p} />}
          {activeTab === 'pillar3'     && <Pillar3Tab     p={p} />}
          {activeTab === 'climate'     && <ClimateTab     p={p} />}
          {activeTab === 'memberships' && <MembershipsTab p={p} />}
        </div>
      </div>
    </div>
  );
}

// ─── List card ────────────────────────────────────────────────────────────────

function ProfileCard({ profile, onClick }) {
  const p = profile;
  const typeColor = {
    'Bank':           'bg-blue-900/40 text-blue-300',
    'Insurance':      'bg-purple-900/40 text-purple-300',
    'Asset Manager':  'bg-cyan-900/40 text-cyan-300',
    'Energy':         'bg-amber-900/40 text-amber-300',
    'Technology':     'bg-green-900/40 text-green-300',
    'Corporate':      'bg-slate-700/60 text-slate-300',
  }[p.institution_type] || 'bg-slate-700/60 text-slate-300';

  return (
    <div
      onClick={onClick}
      className="bg-slate-800/50 border border-slate-700 rounded-lg p-4 cursor-pointer hover:border-cyan-500/50 hover:bg-slate-800 transition-all"
    >
      <div className="flex items-start justify-between mb-2">
        <div>
          <p className="text-sm font-semibold text-slate-100 leading-tight">{p.legal_name}</p>
          <p className="text-xs text-slate-400 mt-0.5">
            {[p.headquarters_city, p.headquarters_country].filter(Boolean).join(', ')}
          </p>
        </div>
        <span className={`text-[10px] font-semibold px-2 py-0.5 rounded ${typeColor}`}>
          {p.institution_type || 'Corporate'}
        </span>
      </div>

      {/* Key metrics row */}
      <div className="grid grid-cols-3 gap-2 mt-3 pt-3 border-t border-slate-700/50">
        <div>
          <p className="text-[9px] text-slate-500 uppercase">Assets</p>
          <p className="text-xs font-mono text-slate-300">{fmt.eur_bn(p.total_assets_eur_bn)}</p>
        </div>
        <div>
          <p className="text-[9px] text-slate-500 uppercase">CET1</p>
          <p className="text-xs font-mono text-slate-300">{fmt.pct(p.cet1_ratio_pct)}</p>
        </div>
        <div>
          <p className="text-[9px] text-slate-500 uppercase">GAR</p>
          <p className="text-xs font-mono text-slate-300">{fmt.pct(p.p3_gar_pct)}</p>
        </div>
      </div>

      {/* Memberships */}
      <div className="mt-2 flex flex-wrap gap-1">
        {p.nzba_member    && <Badge label="NZBA"  variant="green" />}
        {p.pcaf_member    && <Badge label="PCAF"  variant="green" />}
        {p.sbti_status === 'Approved' && <Badge label="SBTi"  variant="green" />}
        {p.tcfd_supporter && <Badge label="TCFD"  variant="blue"  />}
        {p.data_source === 'csrd_report' && <Badge label="Real Data" variant="cyan" />}
      </div>

      {p.systemic_importance && p.systemic_importance !== 'None' && (
        <div className="mt-2">
          <Badge label={p.systemic_importance} variant="red" />
        </div>
      )}
    </div>
  );
}

// ─── Main page ─────────────────────────────────────────────────────────────────

const SECTOR_OPTIONS = [
  'All', 'financial_institution', 'energy_developer', 'real_estate',
  'technology', 'insurance', 'corporate',
];
const TYPE_OPTIONS = [
  'All', 'Bank', 'Insurance', 'Asset Manager', 'Energy',
  'Technology', 'Corporate', 'Private Equity', 'Venture Capital',
];

export default function CompanyProfilesPage() {
  const [profiles, setProfiles]       = useState([]);
  const [total, setTotal]             = useState(0);
  const [loading, setLoading]         = useState(true);
  const [search, setSearch]           = useState('');
  const [sector, setSector]           = useState('All');
  const [instType, setInstType]       = useState('All');
  const [isFI, setIsFI]               = useState(null);
  const [selected, setSelected]       = useState(null);
  const [extracting, setExtracting]   = useState(false);
  const [seeding, setSeeding]         = useState(false);
  const [extractResult, setExtractResult] = useState(null);
  const [error, setError]             = useState(null);

  const fetchProfiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: '200', offset: '0' });
      if (search) params.set('search', search);
      if (sector !== 'All') params.set('sector', sector);
      if (instType !== 'All') params.set('institution_type', instType);
      if (isFI !== null) params.set('is_fi', isFI);

      const res = await fetch(`${API}/api/v1/company-profiles/?${params}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setProfiles(data.profiles || []);
      setTotal(data.total || 0);
    } catch (err) {
      setError(err.message);
      setProfiles([]);
    } finally {
      setLoading(false);
    }
  }, [search, sector, instType, isFI]);

  useEffect(() => {
    fetchProfiles();
  }, [fetchProfiles]);

  const handleExtract = async () => {
    setExtracting(true);
    setExtractResult(null);
    try {
      const res = await fetch(`${API}/api/v1/company-profiles/extract-from-reports`, { method: 'POST' });
      const data = await res.json();
      setExtractResult(data);
      fetchProfiles();
    } catch (err) {
      setExtractResult({ error: err.message });
    } finally {
      setExtracting(false);
    }
  };

  const handleSeed = async () => {
    setSeeding(true);
    try {
      const res = await fetch(`${API}/api/v1/company-profiles/seed-from-engine`, { method: 'POST' });
      const data = await res.json();
      setExtractResult(data);
      fetchProfiles();
    } catch (err) {
      setExtractResult({ error: err.message });
    } finally {
      setSeeding(false);
    }
  };

  // Summary stats
  const fiCount    = profiles.filter(p => p.is_financial_institution).length;
  const realCount  = profiles.filter(p => p.data_source === 'csrd_report').length;
  const nzbaCount  = profiles.filter(p => p.nzba_member).length;
  const sbtiCount  = profiles.filter(p => p.sbti_status === 'Approved').length;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 p-6">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100">Company Profiles</h1>
        <p className="text-sm text-slate-400 mt-1">
          Entity identity, sector classification, Basel III prudential metrics, Pillar 3 ESG disclosures,
          Solvency II, and climate commitments — {total} entities
        </p>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <KpiCard label="Total Entities"         value={total}      color="cyan"   />
        <KpiCard label="Financial Institutions" value={fiCount}    color="blue"   />
        <KpiCard label="Real CSRD Data"         value={realCount}  color="green"  sub="Extracted from annual reports" />
        <KpiCard label="SBTi Approved"          value={sbtiCount}  color="amber"  />
      </div>

      {/* Action buttons (data population) */}
      <div className="flex gap-3 mb-6">
        <button
          onClick={handleExtract}
          disabled={extracting}
          className="px-4 py-2 text-sm bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 rounded-lg font-medium transition-colors"
          data-testid="extract-from-reports-btn"
        >
          {extracting ? 'Extracting...' : 'Extract from CSRD Reports'}
        </button>
        <button
          onClick={handleSeed}
          disabled={seeding}
          className="px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 disabled:opacity-50 rounded-lg font-medium transition-colors"
          data-testid="seed-from-engine-btn"
        >
          {seeding ? 'Seeding...' : 'Seed from Peer Engine'}
        </button>
        {extractResult && (
          <div className={`flex items-center px-3 py-2 rounded-lg text-xs ${extractResult.error ? 'bg-red-900/40 text-red-300' : 'bg-emerald-900/40 text-emerald-300'}`}>
            {extractResult.error
              ? `Error: ${extractResult.error}`
              : extractResult.profiles_created !== undefined
                ? `Created ${extractResult.profiles_created}, updated ${extractResult.profiles_updated}`
                : `Created ${extractResult.created}, skipped ${extractResult.skipped}`
            }
          </div>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-3 mb-6">
        <input
          type="text"
          placeholder="Search by name, LEI, ISIN, ticker..."
          value={search}
          onChange={e => setSearch(e.target.value)}
          className="flex-1 min-w-48 bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-cyan-500"
          data-testid="company-search"
        />
        <select
          value={sector}
          onChange={e => setSector(e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
        >
          {SECTOR_OPTIONS.map(s => <option key={s} value={s}>{s === 'All' ? 'All Sectors' : s}</option>)}
        </select>
        <select
          value={instType}
          onChange={e => setInstType(e.target.value)}
          className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
        >
          {TYPE_OPTIONS.map(t => <option key={t} value={t}>{t === 'All' ? 'All Types' : t}</option>)}
        </select>
        <select
          value={isFI === null ? 'all' : isFI ? 'fi' : 'non-fi'}
          onChange={e => setIsFI(e.target.value === 'all' ? null : e.target.value === 'fi')}
          className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-cyan-500"
        >
          <option value="all">All Entities</option>
          <option value="fi">Financial Institutions</option>
          <option value="non-fi">Non-Financial</option>
        </select>
      </div>

      {/* Content */}
      {loading ? (
        <div className="grid grid-cols-3 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-40 bg-slate-800/50 border border-slate-700 rounded-lg animate-pulse" />
          ))}
        </div>
      ) : error ? (
        <div className="text-center py-16">
          <p className="text-slate-400 mb-2">Could not load company profiles</p>
          <p className="text-xs text-slate-500 mb-4">{error}</p>
          <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-6 max-w-md mx-auto text-left">
            <p className="text-sm font-semibold text-slate-300 mb-2">Populate company profiles:</p>
            <ol className="text-xs text-slate-400 space-y-1 list-decimal list-inside">
              <li>Click <strong className="text-cyan-400">Extract from CSRD Reports</strong> to load real data from the 8 processed annual reports</li>
              <li>Click <strong className="text-cyan-400">Seed from Peer Engine</strong> to add analyst estimates for all 61 benchmark institutions</li>
            </ol>
          </div>
        </div>
      ) : profiles.length === 0 ? (
        <div className="text-center py-16">
          <p className="text-slate-400 mb-2">No company profiles found</p>
          <p className="text-xs text-slate-500 mb-4">
            {search || sector !== 'All' || instType !== 'All'
              ? 'Try clearing the filters'
              : 'Use the buttons above to populate profiles'}
          </p>
          {!search && sector === 'All' && instType === 'All' && (
            <div className="flex gap-3 justify-center">
              <button onClick={handleExtract} disabled={extracting}
                className="px-4 py-2 text-sm bg-cyan-600 hover:bg-cyan-500 rounded-lg">
                Extract from CSRD Reports
              </button>
              <button onClick={handleSeed} disabled={seeding}
                className="px-4 py-2 text-sm bg-slate-700 hover:bg-slate-600 rounded-lg">
                Seed from Peer Engine
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {profiles.map(p => (
            <ProfileCard key={p.id} profile={p} onClick={() => setSelected(p)} />
          ))}
        </div>
      )}

      {/* Detail panel */}
      {selected && (
        <ProfileDetailPanel profile={selected} onClose={() => setSelected(null)} />
      )}
    </div>
  );
}
