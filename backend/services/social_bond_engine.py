"""
Social Bond & Impact Finance Engine — E85
Standards: ICMA Social Bond Principles (SBP) June 2023;
ICMA Sustainability Bond Guidelines 2021; ICMA Impact Reporting Handbook 2023;
UN Sustainable Development Goals (SDGs) Agenda 2030;
IRIS+ v5.3 (GIIN 2023); IMP Five Dimensions of Impact (2018);
EVPA Impact Measurement & Management Guide (2022);
Social Value Act 2012 (UK); SROI Guide NPC (2012 rev);
UN Social Protection Floor Initiative; IFC Social & Environmental Standards.
"""

import logging
import math
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Reference Data
# ---------------------------------------------------------------------------

ICMA_SBP_PROJECT_CATEGORIES: Dict[str, Dict] = {
    "affordable_housing": {
        "icma_code": "AH",
        "description": "Financing of affordable and social housing for low-income populations",
        "eligible_activities": [
            "Construction of social housing units",
            "Renovation of existing affordable housing stock",
            "Mortgage-backed lending to below-median income households",
            "Transitional housing for homeless populations",
            "Supportive housing for people with disabilities",
        ],
        "typical_kpis": [
            "Number of social housing units financed",
            "Number of households housed",
            "Average rent-to-income ratio (%)",
            "Number of people with secure housing",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category AH",
        "sdg_primary": [11],
        "sdg_secondary": [1, 10],
    },
    "access_to_essential_services": {
        "icma_code": "AES",
        "description": "Financing of essential services including education, healthcare, finance and utilities",
        "eligible_activities": [
            "Construction/renovation of healthcare facilities",
            "Expansion of public education infrastructure",
            "Digital literacy and skills training programs",
            "Access to clean water and sanitation services",
            "Maternal and child health services in underserved areas",
        ],
        "typical_kpis": [
            "Number of patients/students served",
            "Healthcare facility capacity added (beds)",
            "Literacy rate improvement (%)",
            "Access rate to clean water (% population)",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category AES",
        "sdg_primary": [3, 4, 6],
        "sdg_secondary": [1, 10],
    },
    "affordable_basic_infrastructure": {
        "icma_code": "ABI",
        "description": "Infrastructure providing affordable access to basic services and utilities",
        "eligible_activities": [
            "Rural electrification projects",
            "Public transport infrastructure in underserved areas",
            "Digital connectivity/broadband for rural/deprived areas",
            "Water supply and wastewater treatment systems",
            "Community health centres and diagnostic labs",
        ],
        "typical_kpis": [
            "Population connected to grid (persons)",
            "km of new public transport routes",
            "Number of communities connected to broadband",
            "Volume of safe water produced (m³/day)",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category ABI",
        "sdg_primary": [9, 11],
        "sdg_secondary": [1, 6, 7],
    },
    "employment_generation": {
        "icma_code": "EG",
        "description": "Programs targeting job creation especially for vulnerable or disadvantaged populations",
        "eligible_activities": [
            "SME lending to job-creating businesses in deprived areas",
            "Vocational training and apprenticeship programs",
            "Social enterprise support and incubation",
            "Youth employment initiatives (NEET populations)",
            "Microfinance for self-employment in developing markets",
        ],
        "typical_kpis": [
            "Number of full-time equivalent (FTE) jobs created",
            "Number of training beneficiaries",
            "Share of beneficiaries from disadvantaged groups (%)",
            "Job retention rate at 12 months (%)",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category EG",
        "sdg_primary": [8],
        "sdg_secondary": [1, 10],
    },
    "food_security": {
        "icma_code": "FS",
        "description": "Financing of sustainable food production and food security programs",
        "eligible_activities": [
            "Small-holder farmer credit and support programs",
            "Agricultural development in food-insecure regions",
            "Food banks and surplus redistribution networks",
            "Nutrition supplementation programs for vulnerable children",
            "Climate-resilient agricultural infrastructure",
        ],
        "typical_kpis": [
            "Number of smallholder farmers supported",
            "Tonnes of food produced/redistributed",
            "Prevalence of undernourishment reduction (%)",
            "Number of households with improved food security",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category FS",
        "sdg_primary": [2],
        "sdg_secondary": [1, 10],
    },
    "socioeconomic_advancement": {
        "icma_code": "SEA",
        "description": "Programs promoting socioeconomic development and empowerment",
        "eligible_activities": [
            "Financial inclusion and digital payment infrastructure",
            "Community development finance for deprived areas",
            "Women's economic empowerment programs",
            "Indigenous community economic development",
            "Migrant integration and language training programs",
        ],
        "typical_kpis": [
            "Number of beneficiaries gaining access to financial services",
            "Income increase for beneficiary households (%)",
            "Number of women-owned businesses supported",
            "Poverty headcount reduction (persons)",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category SEA",
        "sdg_primary": [10, 1],
        "sdg_secondary": [5, 8],
    },
    "affordable_credit": {
        "icma_code": "AC",
        "description": "Provision of affordable credit to underserved individuals and micro-enterprises",
        "eligible_activities": [
            "Microfinance and microloan programs (<€25k)",
            "Student loan schemes for low-income learners",
            "Below-market rate SME lending in deprived areas",
            "Consumer credit counselling and debt management",
            "Affordable mortgage guarantee schemes",
        ],
        "typical_kpis": [
            "Number of microloans disbursed",
            "Total value of affordable credit provided (€M)",
            "Effective interest rate compared to market benchmark (%)",
            "Loan repayment rate (%)",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category AC",
        "sdg_primary": [1, 10],
        "sdg_secondary": [8],
    },
    "disease_mitigation": {
        "icma_code": "DM",
        "description": "Prevention, alleviation and mitigation of disease and pandemics",
        "eligible_activities": [
            "Vaccine development and distribution programs",
            "Communicable disease surveillance and response",
            "HIV/AIDS, malaria, TB prevention and treatment",
            "Non-communicable disease screening programs",
            "Pandemic preparedness infrastructure",
        ],
        "typical_kpis": [
            "Number of individuals vaccinated",
            "Incidence rate reduction for target disease (%)",
            "Number of healthcare workers trained",
            "Years of life lost (YLL) reduction",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category DM",
        "sdg_primary": [3],
        "sdg_secondary": [1, 10],
    },
    "healthcare": {
        "icma_code": "HC",
        "description": "Financing of healthcare infrastructure, services and research for underserved populations",
        "eligible_activities": [
            "Construction of hospitals and clinics in deprived areas",
            "Mental health services and facilities",
            "Telemedicine and digital health infrastructure",
            "Medical research for neglected tropical diseases",
            "Palliative and end-of-life care for low-income populations",
        ],
        "typical_kpis": [
            "Number of patient visits enabled",
            "Reduction in infant/maternal mortality rate",
            "Number of healthcare facilities constructed/upgraded",
            "Average waiting time reduction (days)",
        ],
        "sbp_ref": "ICMA SBP 2023 Appendix 1, Category HC",
        "sdg_primary": [3],
        "sdg_secondary": [1, 10, 16],
    },
}

TARGET_POPULATION_GROUPS: Dict[str, Dict] = {
    "people_below_poverty_line": {
        "icma_definition": "Individuals living on <$2.15/day (World Bank 2022 international poverty line)",
        "measurement_approach": "Income-based survey data; proxy means testing; geographic poverty maps",
        "proxy_indicators": ["household income quintile", "deprivation index score", "benefit recipient status"],
        "un_sdg_ref": "SDG 1.1.1 — proportion below international poverty line",
    },
    "excluded_communities": {
        "icma_definition": "Communities excluded from mainstream social and economic systems by geography, race, ethnicity or caste",
        "measurement_approach": "Geographic deprivation indices; social exclusion composite score",
        "proxy_indicators": ["Index of Multiple Deprivation decile", "remote/rural classification", "racial equity score"],
        "un_sdg_ref": "SDG 10.2 — social, economic and political inclusion",
    },
    "migrants": {
        "icma_definition": "International migrants including refugees, asylum-seekers, and economic migrants",
        "measurement_approach": "UNHCR registration data; national migration statistics; self-declaration",
        "proxy_indicators": ["UNHCR registration status", "length of residence", "country of origin HDI"],
        "un_sdg_ref": "SDG 10.7 — safe, orderly migration and mobility",
    },
    "people_with_disabilities": {
        "icma_definition": "Persons with long-term physical, mental, intellectual or sensory impairments (UN CRPD 2006)",
        "measurement_approach": "Washington Group Short Set (WG-SS); self-reported functional difficulty",
        "proxy_indicators": ["WG-SS disability score", "disability benefit receipt", "accessibility audit results"],
        "un_sdg_ref": "SDG 10.2; UN CRPD Art 28 — adequate standard of living",
    },
    "unemployed": {
        "icma_definition": "Persons without employment, available and seeking work (ILO definition)",
        "measurement_approach": "ILO labour force survey; claimant count; youth NEET rate",
        "proxy_indicators": ["unemployment duration (months)", "NEET status", "local unemployment rate vs national"],
        "un_sdg_ref": "SDG 8.5 — full and productive employment",
    },
    "women_girls": {
        "icma_definition": "Women and girls experiencing gender-based discrimination and economic exclusion",
        "measurement_approach": "Gender disaggregated data; Gender Development Index; self-identification",
        "proxy_indicators": ["gender pay gap (%)", "female labour force participation rate", "GDI score"],
        "un_sdg_ref": "SDG 5 — gender equality and women's empowerment",
    },
    "lgbtq_plus": {
        "icma_definition": "LGBTQ+ individuals facing discrimination, violence and social exclusion",
        "measurement_approach": "Self-identification in anonymised surveys; LGBTQ+ rights index by country",
        "proxy_indicators": ["ILGA LGBTQ+ rights index", "hate crime reporting rate", "legal protection status"],
        "un_sdg_ref": "SDG 10.3 — eliminate discriminatory laws and policies",
    },
    "aging_populations": {
        "icma_definition": "Individuals aged 65+ (OECD), especially those at risk of poverty or social isolation",
        "measurement_approach": "Age-disaggregated data; old-age poverty rate; social isolation index",
        "proxy_indicators": ["at-risk-of-poverty rate 65+", "pension adequacy ratio", "social participation index"],
        "un_sdg_ref": "SDG 1.3 — social protection systems including floors",
    },
    "vulnerable_youth": {
        "icma_definition": "Young people aged 15-24 at risk of poverty, NEET, or social exclusion",
        "measurement_approach": "NEET rate; youth poverty rate; child poverty index",
        "proxy_indicators": ["NEET rate (%)", "youth unemployment rate", "free school meal eligibility"],
        "un_sdg_ref": "SDG 4.4 — youth with relevant skills for employment; SDG 8.6",
    },
    "indigenous_peoples": {
        "icma_definition": "Indigenous peoples and local communities as defined by ILO Convention 169",
        "measurement_approach": "Self-identification; official government recognition; land rights documentation",
        "proxy_indicators": ["ILO 169 recognition status", "Indigenous economic inclusion index", "land tenure security"],
        "un_sdg_ref": "SDG 2.3 — equal access to land; SDG 10.3 — equal opportunity",
    },
}

# 40 Social KPIs mapped to category, population, SDG target and measurement guidance
SOCIAL_KPI_LIBRARY: List[Dict] = [
    # Affordable Housing
    {"id": "SK001", "name": "Social housing units financed", "category": "affordable_housing", "population": "people_below_poverty_line", "sdg_target": "11.1", "unit": "units", "measurement": "Count of units with legally binding affordability covenant", "quantifiable": True},
    {"id": "SK002", "name": "Households housed", "category": "affordable_housing", "population": "excluded_communities", "sdg_target": "11.1", "unit": "households", "measurement": "Number of household tenancy agreements signed", "quantifiable": True},
    {"id": "SK003", "name": "Average rent-to-income ratio", "category": "affordable_housing", "population": "people_below_poverty_line", "sdg_target": "11.1", "unit": "%", "measurement": "Mean rent / gross household income × 100", "quantifiable": True},
    {"id": "SK004", "name": "Energy-efficient homes retrofitted", "category": "affordable_housing", "population": "people_below_poverty_line", "sdg_target": "7.1", "unit": "units", "measurement": "EPC rating improvement from E/F/G to C or above", "quantifiable": True},
    # Access to Essential Services
    {"id": "SK005", "name": "Patients receiving healthcare", "category": "access_to_essential_services", "population": "people_below_poverty_line", "sdg_target": "3.8", "unit": "patients/year", "measurement": "Annual outpatient visits funded by bond proceeds", "quantifiable": True},
    {"id": "SK006", "name": "Students enrolled in supported programs", "category": "access_to_essential_services", "population": "vulnerable_youth", "sdg_target": "4.1", "unit": "students", "measurement": "Total enrolment count at funded institutions", "quantifiable": True},
    {"id": "SK007", "name": "Access to clean water (households)", "category": "access_to_essential_services", "population": "excluded_communities", "sdg_target": "6.1", "unit": "households", "measurement": "Households connected to safe water supply within project area", "quantifiable": True},
    {"id": "SK008", "name": "Digital literacy training beneficiaries", "category": "access_to_essential_services", "population": "aging_populations", "sdg_target": "4.4", "unit": "persons", "measurement": "Persons completing ≥8 hours of accredited digital skills training", "quantifiable": True},
    # Affordable Basic Infrastructure
    {"id": "SK009", "name": "Population newly connected to electricity", "category": "affordable_basic_infrastructure", "population": "excluded_communities", "sdg_target": "7.1", "unit": "persons", "measurement": "Registered electricity connections in project area", "quantifiable": True},
    {"id": "SK010", "name": "Public transport route km added", "category": "affordable_basic_infrastructure", "population": "people_below_poverty_line", "sdg_target": "11.2", "unit": "km", "measurement": "Verified km of new or upgraded public transport routes", "quantifiable": True},
    {"id": "SK011", "name": "Communities connected to broadband", "category": "affordable_basic_infrastructure", "population": "excluded_communities", "sdg_target": "9.c", "unit": "communities", "measurement": "Communities with ≥30Mbps broadband newly served", "quantifiable": True},
    {"id": "SK012", "name": "Safe water volume produced", "category": "affordable_basic_infrastructure", "population": "people_below_poverty_line", "sdg_target": "6.1", "unit": "m³/day", "measurement": "Verified daily output of water treatment facility", "quantifiable": True},
    # Employment Generation
    {"id": "SK013", "name": "Full-time equivalent jobs created", "category": "employment_generation", "population": "unemployed", "sdg_target": "8.5", "unit": "FTE", "measurement": "FTE employment sustained ≥12 months post-investment", "quantifiable": True},
    {"id": "SK014", "name": "Vocational training completions", "category": "employment_generation", "population": "vulnerable_youth", "sdg_target": "4.4", "unit": "persons", "measurement": "Accredited vocational qualifications awarded", "quantifiable": True},
    {"id": "SK015", "name": "Women-owned businesses supported", "category": "employment_generation", "population": "women_girls", "sdg_target": "5.b", "unit": "businesses", "measurement": "SMEs with ≥51% female ownership receiving financing", "quantifiable": True},
    {"id": "SK016", "name": "Youth NEET placed into employment", "category": "employment_generation", "population": "vulnerable_youth", "sdg_target": "8.6", "unit": "persons", "measurement": "NEET individuals in sustained employment ≥6 months", "quantifiable": True},
    # Food Security
    {"id": "SK017", "name": "Smallholder farmers supported", "category": "food_security", "population": "people_below_poverty_line", "sdg_target": "2.3", "unit": "farmers", "measurement": "Farmers receiving credit/technical support through bond proceeds", "quantifiable": True},
    {"id": "SK018", "name": "Food redistributed from surplus", "category": "food_security", "population": "people_below_poverty_line", "sdg_target": "12.3", "unit": "tonnes", "measurement": "Verified tonnes redistributed through funded food banks", "quantifiable": True},
    {"id": "SK019", "name": "Children receiving nutrition support", "category": "food_security", "population": "vulnerable_youth", "sdg_target": "2.2", "unit": "children", "measurement": "Children enrolled in supplementary feeding programs", "quantifiable": True},
    {"id": "SK020", "name": "Agricultural yield increase", "category": "food_security", "population": "people_below_poverty_line", "sdg_target": "2.3", "unit": "%", "measurement": "Average crop yield change vs. baseline for funded farmers", "quantifiable": True},
    # Socioeconomic Advancement
    {"id": "SK021", "name": "Persons gaining financial services access", "category": "socioeconomic_advancement", "population": "excluded_communities", "sdg_target": "8.10", "unit": "persons", "measurement": "First-time bank/payment account holders funded", "quantifiable": True},
    {"id": "SK022", "name": "Income increase for beneficiary households", "category": "socioeconomic_advancement", "population": "people_below_poverty_line", "sdg_target": "1.4", "unit": "% increase", "measurement": "Average household income change vs. control group", "quantifiable": True},
    {"id": "SK023", "name": "Indigenous community enterprises funded", "category": "socioeconomic_advancement", "population": "indigenous_peoples", "sdg_target": "8.3", "unit": "enterprises", "measurement": "Enterprises with majority indigenous ownership receiving financing", "quantifiable": True},
    {"id": "SK024", "name": "Poverty headcount reduction", "category": "socioeconomic_advancement", "population": "people_below_poverty_line", "sdg_target": "1.2", "unit": "persons", "measurement": "Persons crossing national poverty line post-program", "quantifiable": True},
    # Affordable Credit
    {"id": "SK025", "name": "Microloans disbursed", "category": "affordable_credit", "population": "people_below_poverty_line", "sdg_target": "8.10", "unit": "loans", "measurement": "Count of microloans <€25k disbursed", "quantifiable": True},
    {"id": "SK026", "name": "Total affordable credit provided", "category": "affordable_credit", "population": "excluded_communities", "sdg_target": "8.10", "unit": "€M", "measurement": "Total principal of below-market-rate credit facilities", "quantifiable": True},
    {"id": "SK027", "name": "Interest rate discount vs. market rate", "category": "affordable_credit", "population": "people_below_poverty_line", "sdg_target": "8.10", "unit": "bps", "measurement": "Basis point spread between market rate and charged rate", "quantifiable": True},
    {"id": "SK028", "name": "Student loans to low-income learners", "category": "affordable_credit", "population": "vulnerable_youth", "sdg_target": "4.3", "unit": "loans", "measurement": "Student loans to households in lowest income quartile", "quantifiable": True},
    # Disease Mitigation
    {"id": "SK029", "name": "Individuals vaccinated", "category": "disease_mitigation", "population": "people_below_poverty_line", "sdg_target": "3.8", "unit": "persons", "measurement": "Verified vaccine doses administered (not double-counted)", "quantifiable": True},
    {"id": "SK030", "name": "Disease incidence rate reduction", "category": "disease_mitigation", "population": "excluded_communities", "sdg_target": "3.3", "unit": "%", "measurement": "Incidence rate change for target disease in program area", "quantifiable": True},
    {"id": "SK031", "name": "Healthcare workers trained", "category": "disease_mitigation", "population": "excluded_communities", "sdg_target": "3.c", "unit": "workers", "measurement": "Health workers receiving accredited clinical training", "quantifiable": True},
    {"id": "SK032", "name": "Years of life lost (YLL) reduction", "category": "disease_mitigation", "population": "people_below_poverty_line", "sdg_target": "3.4", "unit": "YLL averted", "measurement": "YLL averted calculated using WHO standard life tables", "quantifiable": True},
    # Healthcare
    {"id": "SK033", "name": "Patient visits enabled", "category": "healthcare", "population": "people_below_poverty_line", "sdg_target": "3.8", "unit": "visits/year", "measurement": "Annual outpatient/inpatient visits at funded facilities", "quantifiable": True},
    {"id": "SK034", "name": "Infant mortality rate reduction", "category": "healthcare", "population": "women_girls", "sdg_target": "3.2", "unit": "per 1,000 live births", "measurement": "IMR change in program area vs. national trend", "quantifiable": True},
    {"id": "SK035", "name": "Healthcare facilities constructed/upgraded", "category": "healthcare", "population": "excluded_communities", "sdg_target": "3.8", "unit": "facilities", "measurement": "Facilities commissioned and operational", "quantifiable": True},
    {"id": "SK036", "name": "Mental health service users", "category": "healthcare", "population": "people_with_disabilities", "sdg_target": "3.4", "unit": "persons/year", "measurement": "Unique individuals accessing funded mental health services", "quantifiable": True},
    # Cross-cutting
    {"id": "SK037", "name": "LGBTQ+ inclusive services delivered", "category": "access_to_essential_services", "population": "lgbtq_plus", "sdg_target": "10.2", "unit": "persons", "measurement": "Self-identified LGBTQ+ beneficiaries of funded services", "quantifiable": False},
    {"id": "SK038", "name": "Disability-accessible units created", "category": "affordable_housing", "population": "people_with_disabilities", "sdg_target": "11.1", "unit": "units", "measurement": "Housing units meeting BS 8300 / EN 301 549 accessibility standards", "quantifiable": True},
    {"id": "SK039", "name": "Refugee resettlement support", "category": "socioeconomic_advancement", "population": "migrants", "sdg_target": "10.7", "unit": "persons", "measurement": "Refugees receiving housing, language and employment support", "quantifiable": True},
    {"id": "SK040", "name": "Elder care places funded", "category": "healthcare", "population": "aging_populations", "sdg_target": "3.4", "unit": "places", "measurement": "Residential or day-care places at funded facilities", "quantifiable": True},
]

# SDG social bond mapping — Goals 1, 2, 3, 4, 5, 6, 8, 10, 11, 16
SDG_SOCIAL_MAPPING: Dict[int, Dict] = {
    1: {"title": "No Poverty", "categories": ["affordable_housing", "affordable_credit", "socioeconomic_advancement", "food_security"], "target_ids": ["1.1", "1.2", "1.3", "1.4"]},
    2: {"title": "Zero Hunger", "categories": ["food_security"], "target_ids": ["2.1", "2.2", "2.3", "2.4"]},
    3: {"title": "Good Health and Well-Being", "categories": ["disease_mitigation", "healthcare", "access_to_essential_services"], "target_ids": ["3.1", "3.2", "3.3", "3.4", "3.8", "3.c"]},
    4: {"title": "Quality Education", "categories": ["access_to_essential_services", "affordable_credit", "employment_generation"], "target_ids": ["4.1", "4.3", "4.4", "4.5"]},
    5: {"title": "Gender Equality", "categories": ["employment_generation", "socioeconomic_advancement", "healthcare"], "target_ids": ["5.1", "5.4", "5.5", "5.b"]},
    6: {"title": "Clean Water and Sanitation", "categories": ["access_to_essential_services", "affordable_basic_infrastructure"], "target_ids": ["6.1", "6.2", "6.3"]},
    8: {"title": "Decent Work and Economic Growth", "categories": ["employment_generation", "affordable_credit", "socioeconomic_advancement"], "target_ids": ["8.3", "8.5", "8.6", "8.10"]},
    10: {"title": "Reduced Inequalities", "categories": ["affordable_housing", "socioeconomic_advancement", "access_to_essential_services", "affordable_credit"], "target_ids": ["10.1", "10.2", "10.3", "10.7"]},
    11: {"title": "Sustainable Cities and Communities", "categories": ["affordable_housing", "affordable_basic_infrastructure"], "target_ids": ["11.1", "11.2", "11.3"]},
    16: {"title": "Peace, Justice and Strong Institutions", "categories": ["healthcare", "access_to_essential_services"], "target_ids": ["16.1", "16.2", "16.6"]},
}

IMPACT_MEASUREMENT_STANDARDS: Dict[str, Dict] = {
    "iris_plus": {
        "framework": "IRIS+ v5.3 (GIIN 2023)",
        "applicability": ["employment_generation", "affordable_credit", "food_security", "healthcare"],
        "key_metrics": ["PI4814 (Jobs created)", "PI6647 (Clients below poverty line)", "OI9999 (Social value)"],
        "quantitative_bias": "high",
        "reporting_frequency": "annual",
        "certification": False,
        "url": "https://iris.thegiin.org/",
    },
    "imp_five_dimensions": {
        "framework": "IMP Five Dimensions of Impact (2018)",
        "applicability": ["all"],
        "key_metrics": ["What (outcome)", "Who (beneficiary)", "How much (depth × breadth)", "Contribution (additionality)", "Risk (impact risk)"],
        "quantitative_bias": "medium",
        "reporting_frequency": "deal-level",
        "certification": False,
        "url": "https://impactmanagementproject.com/",
    },
    "evpa": {
        "framework": "EVPA Impact Measurement & Management Guide 2022",
        "applicability": ["affordable_credit", "socioeconomic_advancement", "employment_generation"],
        "key_metrics": ["Theory of change", "SROI ratio", "Evidence grade (A-E)"],
        "quantitative_bias": "medium",
        "reporting_frequency": "bi-annual",
        "certification": False,
        "url": "https://evpa.eu.com/",
    },
    "sroi": {
        "framework": "Social Return on Investment (SROI) — NPC Guide 2012 rev",
        "applicability": ["all"],
        "key_metrics": ["Financial proxy value", "SROI ratio (£ social value per £ invested)", "Deadweight", "Attribution"],
        "quantitative_bias": "high",
        "reporting_frequency": "deal-level",
        "certification": False,
        "url": "https://www.thinknpc.org/resource-hub/sroi/",
    },
    "social_value_act": {
        "framework": "Social Value Act 2012 (UK) / HM Treasury Green Book Social Value",
        "applicability": ["affordable_housing", "employment_generation", "access_to_essential_services"],
        "key_metrics": ["Wellbeing-adjusted life year (WALY)", "Value per wellbeing point (£30,687 p.a.)", "Social Value Unit"],
        "quantitative_bias": "high",
        "reporting_frequency": "annual",
        "certification": False,
        "url": "https://www.gov.uk/government/publications/social-value-act-information-and-resources",
    },
}

SPO_PROVIDERS: Dict[str, Dict] = {
    "sustainalytics": {
        "full_name": "Sustainalytics (Morningstar)",
        "focus": ["social", "sustainability", "green"],
        "turnaround_weeks": 6,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "LMA SLP"],
        "spf_accredited": False,
    },
    "iss_esg": {
        "full_name": "ISS ESG",
        "focus": ["social", "green", "sustainability"],
        "turnaround_weeks": 5,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "ICMA SBG"],
        "spf_accredited": False,
    },
    "vigeo_eiris": {
        "full_name": "Vigeo Eiris (Moody's)",
        "focus": ["social", "green", "ESG"],
        "turnaround_weeks": 6,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "UN SDGs"],
        "spf_accredited": False,
    },
    "cicero": {
        "full_name": "CICERO Shades of Green",
        "focus": ["green", "climate", "sustainability"],
        "turnaround_weeks": 8,
        "framework_coverage": ["ICMA GBP", "Climate alignment"],
        "spf_accredited": False,
    },
    "dnv": {
        "full_name": "DNV (Det Norske Veritas)",
        "focus": ["social", "green", "sustainability", "assurance"],
        "turnaround_weeks": 6,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "ISAE 3000"],
        "spf_accredited": True,
    },
    "bureau_veritas": {
        "full_name": "Bureau Veritas",
        "focus": ["social", "green", "assurance"],
        "turnaround_weeks": 5,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "ISO 14064"],
        "spf_accredited": True,
    },
    "moodys_ve": {
        "full_name": "Moody's Investors Service (V.E)",
        "focus": ["social", "green", "ESG scoring"],
        "turnaround_weeks": 4,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "EU GBS"],
        "spf_accredited": False,
    },
    "msci": {
        "full_name": "MSCI ESG Research",
        "focus": ["ESG rating", "social", "sustainability"],
        "turnaround_weeks": 7,
        "framework_coverage": ["ICMA SBP", "ICMA SBG", "SDG screening"],
        "spf_accredited": False,
    },
    "sp_global": {
        "full_name": "S&P Global Ratings (Green Evaluation)",
        "focus": ["green", "social", "sustainability"],
        "turnaround_weeks": 5,
        "framework_coverage": ["ICMA GBP", "ICMA SBP", "ICMA SBG"],
        "spf_accredited": False,
    },
    "fitch": {
        "full_name": "Fitch Ratings (ESG Relevance Scores)",
        "focus": ["ESG", "social", "green"],
        "turnaround_weeks": 5,
        "framework_coverage": ["ICMA SBP", "ICMA GBP", "TCFD-aligned"],
        "spf_accredited": False,
    },
}

# ICMA SBP 4 core component weights
ICMA_SBP_COMPONENT_WEIGHTS = {
    "use_of_proceeds": 0.30,
    "process_for_project_evaluation": 0.25,
    "management_of_proceeds": 0.25,
    "reporting": 0.20,
}

# Excluded activities under ICMA SBP (illustrative — issuer must screen)
ICMA_SBP_EXCLUDED_ACTIVITIES = [
    "Gambling and gaming facilities",
    "Tobacco production and distribution",
    "Alcohol production (above threshold)",
    "Weapons and defence manufacturing",
    "Fossil fuel extraction",
    "Forced or child labour supply chains",
    "Deforestation or habitat destruction",
    "Projects with unmitigated adverse social impacts",
]


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SocialBondEngine:
    """E85 — Social Bond & Impact Finance Engine."""

    # -----------------------------------------------------------------------
    # 1. ICMA SBP Compliance Assessment
    # -----------------------------------------------------------------------

    def assess_icma_sbp_compliance(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Score the four ICMA Social Bond Principles components.

        Component weights:
          Use of Proceeds 30% | Project Evaluation 25% | Management 25% | Reporting 20%
        Source: ICMA Social Bond Principles June 2023.
        """
        logger.info("assess_icma_sbp_compliance: bond=%s", bond_data.get("bond_name"))

        scores: Dict[str, Dict] = {}
        gaps: List[str] = []

        # 1. Use of Proceeds (30%)
        uop_score = 0
        has_categories = len(bond_data.get("project_categories", [])) > 0
        all_eligible = all(c in ICMA_SBP_PROJECT_CATEGORIES for c in bond_data.get("project_categories", []))
        if has_categories:
            uop_score += 50
        if all_eligible:
            uop_score += 30
        if bond_data.get("excluded_activities_screened", False):
            uop_score += 20
        else:
            gaps.append("Excluded activities screening not documented (ICMA SBP §1)")
        scores["use_of_proceeds"] = {"raw": uop_score, "weighted": uop_score * ICMA_SBP_COMPONENT_WEIGHTS["use_of_proceeds"]}

        # 2. Process for Project Evaluation & Selection (25%)
        eval_score = 0
        if bond_data.get("has_framework", False):
            eval_score += 40
        else:
            gaps.append("Social Bond Framework not in place (ICMA SBP §2)")
        if len(bond_data.get("target_populations", [])) > 0:
            eval_score += 30
        else:
            gaps.append("Target population groups not specified (ICMA SBP §2)")
        if bond_data.get("has_spo", False):
            eval_score += 30
        else:
            gaps.append("Second Party Opinion (SPO) not obtained (ICMA SBP §2 best practice)")
        scores["process_for_project_evaluation"] = {"raw": eval_score, "weighted": eval_score * ICMA_SBP_COMPONENT_WEIGHTS["process_for_project_evaluation"]}

        # 3. Management of Proceeds (25%)
        mgmt_score = 0
        if bond_data.get("has_dedicated_account", True):
            mgmt_score += 50
        else:
            gaps.append("Dedicated proceeds account not established (ICMA SBP §3)")
        if bond_data.get("unallocated_proceeds_policy", True):
            mgmt_score += 30
        if bond_data.get("has_internal_audit", False):
            mgmt_score += 20
        else:
            gaps.append("Internal/external audit of proceeds management recommended (ICMA SBP §3)")
        scores["management_of_proceeds"] = {"raw": mgmt_score, "weighted": mgmt_score * ICMA_SBP_COMPONENT_WEIGHTS["management_of_proceeds"]}

        # 4. Reporting (20%)
        report_score = 0
        if bond_data.get("has_allocation_reporting", False):
            report_score += 50
        else:
            gaps.append("Allocation reporting not committed (ICMA SBP §4 — annual minimum)")
        if bond_data.get("has_impact_reporting", False):
            report_score += 50
        else:
            gaps.append("Impact reporting not committed (ICMA SBP §4 — best practice)")
        scores["reporting"] = {"raw": report_score, "weighted": report_score * ICMA_SBP_COMPONENT_WEIGHTS["reporting"]}

        # Weighted total
        overall_score = sum(v["weighted"] for v in scores.values())
        sbp_aligned = overall_score >= 65

        return {
            "bond_name": bond_data.get("bond_name"),
            "entity_id": bond_data.get("entity_id"),
            "component_scores": scores,
            "overall_sbp_score": round(overall_score, 1),
            "sbp_aligned": sbp_aligned,
            "alignment_label": "SBP Aligned" if sbp_aligned else "Partial Alignment",
            "gaps": gaps,
            "gap_count": len(gaps),
            "recommended_spo_providers": [
                p for p, d in SPO_PROVIDERS.items() if "social" in d["focus"]
            ][:4],
            "icma_ref": "ICMA Social Bond Principles (SBP) June 2023",
        }

    # -----------------------------------------------------------------------
    # 2. Use of Proceeds Assessment
    # -----------------------------------------------------------------------

    def assess_use_of_proceeds(
        self,
        entity_id: str,
        bond_name: str,
        categories: List[Dict[str, Any]],
        total_issuance_m: float,
    ) -> Dict[str, Any]:
        """
        Assess category eligibility, allocation, and excluded activities screen.
        Source: ICMA SBP 2023 Appendix 1 — eligible project categories.
        """
        logger.info("assess_use_of_proceeds: entity=%s bond=%s", entity_id, bond_name)

        allocated_m = sum(c.get("amount_m", 0) for c in categories)
        allocation_gap_m = total_issuance_m - allocated_m
        allocation_pct = (allocated_m / total_issuance_m * 100) if total_issuance_m > 0 else 0

        category_table: List[Dict] = []
        primary_category = None
        primary_amount = 0.0
        ineligible = []
        eligible_count = 0

        for cat in categories:
            cat_key = cat.get("category", "")
            amount = cat.get("amount_m", 0)
            eligible = cat_key in ICMA_SBP_PROJECT_CATEGORIES
            if eligible:
                eligible_count += 1
                cat_data = ICMA_SBP_PROJECT_CATEGORIES[cat_key]
                if amount > primary_amount:
                    primary_amount = amount
                    primary_category = cat_key
            else:
                ineligible.append(cat_key)

            category_table.append({
                "category": cat_key,
                "description": cat.get("description", ""),
                "amount_m_eur": amount,
                "share_pct": round(amount / total_issuance_m * 100, 1) if total_issuance_m > 0 else 0,
                "icma_eligible": eligible,
                "icma_code": ICMA_SBP_PROJECT_CATEGORIES.get(cat_key, {}).get("icma_code", "N/A"),
                "sbp_ref": ICMA_SBP_PROJECT_CATEGORIES.get(cat_key, {}).get("sbp_ref", ""),
            })

        eligibility_pct = (eligible_count / max(1, len(categories))) * 100

        # Excluded activities screen
        excluded_screen = [
            {"activity": exc, "applies": False, "status": "Clear"}
            for exc in ICMA_SBP_EXCLUDED_ACTIVITIES
        ]

        return {
            "entity_id": entity_id,
            "bond_name": bond_name,
            "total_issuance_m_eur": total_issuance_m,
            "total_allocated_m_eur": round(allocated_m, 2),
            "unallocated_m_eur": round(allocation_gap_m, 2),
            "allocation_pct": round(allocation_pct, 1),
            "categories_assessed": len(categories),
            "eligible_categories_count": eligible_count,
            "ineligible_categories": ineligible,
            "eligibility_pct": round(eligibility_pct, 1),
            "primary_category": primary_category,
            "secondary_categories": [c["category"] for c in category_table if c["category"] != primary_category and c["icma_eligible"]],
            "category_allocation_table": category_table,
            "excluded_activities_screen": excluded_screen,
            "use_of_proceeds_complete": allocation_pct >= 100 and len(ineligible) == 0,
            "icma_ref": "ICMA SBP 2023 §1 — Use of Proceeds; Appendix 1",
        }

    # -----------------------------------------------------------------------
    # 3. Target Population Assessment
    # -----------------------------------------------------------------------

    def assess_target_population(
        self,
        entity_id: str,
        bond_name: str,
        populations_data: List[Dict[str, Any]],
        additionality_evidence: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Validate target population groups, beneficiary count methodology,
        additionality, and geographic coverage.
        Source: ICMA SBP 2023 §2 — Project Evaluation; UN SDG definitions.
        """
        logger.info("assess_target_population: entity=%s bond=%s", entity_id, bond_name)

        validated_populations = []
        total_beneficiaries = 0
        geographies = set()
        unrecognised = []

        for pop in populations_data:
            group = pop.get("group", "")
            count = pop.get("count", 0)
            geography = pop.get("geography", "")
            method = pop.get("measurement_method", "")

            if group in TARGET_POPULATION_GROUPS:
                pop_data = TARGET_POPULATION_GROUPS[group]
                method_quality = "quantified" if count > 0 else "qualitative"
                total_beneficiaries += count
                if geography:
                    geographies.add(geography)
                validated_populations.append({
                    "group": group,
                    "icma_definition": pop_data["icma_definition"],
                    "beneficiary_count": count,
                    "geography": geography,
                    "measurement_method": method,
                    "method_quality": method_quality,
                    "proxy_indicators": pop_data["proxy_indicators"],
                    "un_sdg_ref": pop_data["un_sdg_ref"],
                    "validated": True,
                })
            else:
                unrecognised.append(group)
                validated_populations.append({
                    "group": group,
                    "beneficiary_count": pop.get("count", 0),
                    "validated": False,
                    "issue": "Group not in ICMA SBP recognised target populations",
                })

        quantified_count = sum(1 for p in validated_populations if p.get("method_quality") == "quantified")
        quantification_rate = (quantified_count / max(1, len(validated_populations))) * 100

        # Additionality assessment
        additionality_score = 0
        if additionality_evidence:
            additionality_score += 50
            if "counterfactual" in additionality_evidence.lower():
                additionality_score += 25
            if "baseline" in additionality_evidence.lower():
                additionality_score += 25

        additionality_level = (
            "strong" if additionality_score >= 80
            else "moderate" if additionality_score >= 50
            else "weak" if additionality_score >= 25
            else "not_assessed"
        )

        return {
            "entity_id": entity_id,
            "bond_name": bond_name,
            "populations_count": len(populations_data),
            "validated_populations_count": len(validated_populations) - len(unrecognised),
            "unrecognised_groups": unrecognised,
            "total_beneficiaries": total_beneficiaries,
            "geographic_coverage": sorted(geographies),
            "geographic_spread": len(geographies),
            "quantification_rate_pct": round(quantification_rate, 1),
            "additionality_evidence_provided": bool(additionality_evidence),
            "additionality_score": additionality_score,
            "additionality_level": additionality_level,
            "population_details": validated_populations,
            "icma_ref": "ICMA SBP 2023 §2 — Process for Project Evaluation and Selection",
        }

    # -----------------------------------------------------------------------
    # 4. Social KPI Scoring
    # -----------------------------------------------------------------------

    def score_social_kpis(
        self,
        entity_id: str,
        bond_name: str,
        project_category: str,
        kpis_list: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Score KPI quality: quantified vs qualitative ratio, ICMA alignment,
        and suggest additional KPIs from the library.
        Source: ICMA Impact Reporting Handbook 2023; IRIS+ v5.3.
        """
        logger.info("score_social_kpis: entity=%s category=%s kpis=%d", entity_id, project_category, len(kpis_list))

        # Filter library for category
        library_kpis = [k for k in SOCIAL_KPI_LIBRARY if k["category"] == project_category]
        library_names = {k["name"].lower() for k in library_kpis}

        scored_kpis: List[Dict] = []
        quantified_count = 0
        aligned_count = 0
        total_score = 0

        for kpi in kpis_list:
            name = kpi.get("name", "")
            value = kpi.get("value")
            baseline = kpi.get("baseline")
            target = kpi.get("target")
            sdg_target = kpi.get("sdg_target")

            has_value = value is not None
            has_baseline = baseline is not None
            has_target = target is not None
            has_sdg = bool(sdg_target)
            is_aligned = name.lower() in library_names

            kpi_score = 0
            if has_value:
                kpi_score += 30
                quantified_count += 1
            if has_baseline:
                kpi_score += 20
            if has_target:
                kpi_score += 20
            if has_sdg:
                kpi_score += 15
            if is_aligned:
                kpi_score += 15
                aligned_count += 1

            total_score += kpi_score
            scored_kpis.append({
                "name": name,
                "value": value,
                "baseline": baseline,
                "target": target,
                "sdg_target": sdg_target,
                "kpi_score": kpi_score,
                "has_quantified_value": has_value,
                "has_baseline": has_baseline,
                "has_target": has_target,
                "aligned_to_icma_library": is_aligned,
                "quality_tier": "gold" if kpi_score >= 80 else "silver" if kpi_score >= 50 else "bronze",
            })

        n = max(1, len(kpis_list))
        overall_kpi_quality = total_score / n
        quantification_ratio = (quantified_count / n) * 100
        alignment_ratio = (aligned_count / n) * 100

        # Suggest additional KPIs not yet reported
        reported_names = {k.get("name", "").lower() for k in kpis_list}
        suggested = [
            {"id": k["id"], "name": k["name"], "unit": k["unit"], "sdg_target": k["sdg_target"]}
            for k in library_kpis
            if k["name"].lower() not in reported_names
        ][:5]

        return {
            "entity_id": entity_id,
            "bond_name": bond_name,
            "project_category": project_category,
            "kpis_submitted": len(kpis_list),
            "quantified_kpis": quantified_count,
            "quantification_ratio_pct": round(quantification_ratio, 1),
            "icma_aligned_kpis": aligned_count,
            "alignment_ratio_pct": round(alignment_ratio, 1),
            "overall_kpi_quality_score": round(overall_kpi_quality, 1),
            "kpi_quality_tier": (
                "gold" if overall_kpi_quality >= 80
                else "silver" if overall_kpi_quality >= 55
                else "bronze"
            ),
            "scored_kpis": scored_kpis,
            "suggested_additional_kpis": suggested,
            "impact_standards_ref": "ICMA Impact Reporting Handbook 2023; IRIS+ v5.3 (GIIN)",
        }

    # -----------------------------------------------------------------------
    # 5. SDG Alignment
    # -----------------------------------------------------------------------

    def map_sdg_alignment(
        self,
        entity_id: str,
        bond_name: str,
        project_categories: List[str],
        kpis: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Map project categories and KPIs to SDG goals and targets.
        Returns SDG matrix, primary/secondary SDG, and contribution score.
        Source: UN SDG Agenda 2030; ICMA SDG Mapping to SBP 2023.
        """
        logger.info("map_sdg_alignment: entity=%s bond=%s", entity_id, bond_name)

        sdg_hits: Dict[int, int] = {}
        sdg_targets_hit: Dict[int, List[str]] = {}

        # From categories
        for cat in project_categories:
            cat_data = ICMA_SBP_PROJECT_CATEGORIES.get(cat, {})
            for sdg in cat_data.get("sdg_primary", []):
                sdg_hits[sdg] = sdg_hits.get(sdg, 0) + 3
            for sdg in cat_data.get("sdg_secondary", []):
                sdg_hits[sdg] = sdg_hits.get(sdg, 0) + 1

        # From KPI SDG targets
        for kpi in kpis:
            target = kpi.get("sdg_target", "")
            if target:
                try:
                    goal = int(str(target).split(".")[0])
                    sdg_hits[goal] = sdg_hits.get(goal, 0) + 2
                    sdg_targets_hit.setdefault(goal, [])
                    if target not in sdg_targets_hit[goal]:
                        sdg_targets_hit[goal].append(target)
                except (ValueError, IndexError):
                    pass

        if not sdg_hits:
            primary_sdg = None
            secondary_sdgs = []
            sdg_score = 0
        else:
            sorted_sdgs = sorted(sdg_hits.items(), key=lambda x: x[1], reverse=True)
            primary_sdg = sorted_sdgs[0][0]
            secondary_sdgs = [s[0] for s in sorted_sdgs[1:6]]
            max_possible = max(sdg_hits.values()) if sdg_hits else 1
            sdg_score = min(100, (sum(sdg_hits.values()) / max(1, len(project_categories) * 5)) * 100)

        sdg_matrix = []
        for sdg_num, count in sorted(sdg_hits.items()):
            sdg_data = SDG_SOCIAL_MAPPING.get(sdg_num, {})
            sdg_matrix.append({
                "sdg_goal": sdg_num,
                "sdg_title": sdg_data.get("title", f"SDG {sdg_num}"),
                "contribution_weight": count,
                "is_primary": sdg_num == primary_sdg,
                "is_secondary": sdg_num in secondary_sdgs,
                "targets_addressed": sdg_targets_hit.get(sdg_num, []),
                "relevant_categories": [c for c in sdg_data.get("categories", []) if c in project_categories],
            })

        return {
            "entity_id": entity_id,
            "bond_name": bond_name,
            "sdgs_addressed_count": len(sdg_hits),
            "primary_sdg": primary_sdg,
            "secondary_sdgs": secondary_sdgs,
            "sdg_contribution_score": round(sdg_score, 1),
            "sdg_breadth_tier": (
                "comprehensive" if len(sdg_hits) >= 5
                else "broad" if len(sdg_hits) >= 3
                else "focused" if len(sdg_hits) >= 1
                else "none"
            ),
            "sdg_matrix": sdg_matrix,
            "un_ref": "UN Sustainable Development Goals — Agenda 2030",
            "icma_ref": "ICMA SDG Mapping to SBP 2023",
        }

    # -----------------------------------------------------------------------
    # 6. Impact Score
    # -----------------------------------------------------------------------

    def calculate_impact_score(self, bond_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Composite impact score:
          ICMA SBP compliance 40% + SDG alignment 25% + KPI quality 25% + additionality 10%
        """
        logger.info("calculate_impact_score: bond=%s", bond_data.get("bond_name"))

        icma_score = bond_data.get("sbp_score", 0)
        sdg_score = bond_data.get("sdg_score", 0)
        kpi_score = bond_data.get("kpi_quality_score", 0)
        additionality_score = bond_data.get("additionality_score", 0)

        composite = (
            icma_score * 0.40
            + sdg_score * 0.25
            + kpi_score * 0.25
            + additionality_score * 0.10
        )

        tier = (
            "Gold" if composite >= 80
            else "Silver" if composite >= 65
            else "Bronze" if composite >= 50
            else "Standard"
        )

        return {
            "bond_name": bond_data.get("bond_name"),
            "composite_impact_score": round(composite, 1),
            "bond_tier": tier,
            "score_components": {
                "icma_sbp_compliance_40pct": round(icma_score * 0.40, 1),
                "sdg_alignment_25pct": round(sdg_score * 0.25, 1),
                "kpi_quality_25pct": round(kpi_score * 0.25, 1),
                "additionality_10pct": round(additionality_score * 0.10, 1),
            },
            "market_positioning": {
                "Gold": "Top-tier impact; eligible for dedicated social bond indices",
                "Silver": "Strong alignment; institutional investor grade",
                "Bronze": "Meets minimum SBP requirements; room for improvement",
                "Standard": "Partial compliance; significant gaps to address",
            }.get(tier, ""),
        }

    # -----------------------------------------------------------------------
    # 7. Full Assessment
    # -----------------------------------------------------------------------

    def run_full_assessment(
        self,
        entity_id: str,
        bond_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Orchestrate all social bond sub-assessments.
        Returns full_result with bond_tier (Gold/Silver/Bronze/Standard).
        """
        logger.info("run_full_assessment: entity=%s bond=%s", entity_id, bond_data.get("bond_name"))

        bond_data["entity_id"] = entity_id
        results: Dict[str, Any] = {"entity_id": entity_id, "bond_name": bond_data.get("bond_name")}

        # 1. ICMA SBP compliance
        sbp_result = self.assess_icma_sbp_compliance(bond_data)
        results["icma_sbp_compliance"] = sbp_result

        # 2. Use of proceeds
        if "categories" in bond_data:
            uop_result = self.assess_use_of_proceeds(
                entity_id=entity_id,
                bond_name=bond_data.get("bond_name", ""),
                categories=bond_data["categories"],
                total_issuance_m=bond_data.get("total_issuance_m", 0),
            )
            results["use_of_proceeds"] = uop_result

        # 3. Target population
        if "populations" in bond_data:
            pop_result = self.assess_target_population(
                entity_id=entity_id,
                bond_name=bond_data.get("bond_name", ""),
                populations_data=bond_data["populations"],
                additionality_evidence=bond_data.get("additionality_evidence"),
            )
            results["target_population"] = pop_result
            additionality_score = pop_result["additionality_score"]
        else:
            additionality_score = 0

        # 4. KPI scoring
        if "kpis" in bond_data and "primary_category" in bond_data:
            kpi_result = self.score_social_kpis(
                entity_id=entity_id,
                bond_name=bond_data.get("bond_name", ""),
                project_category=bond_data["primary_category"],
                kpis_list=bond_data["kpis"],
            )
            results["kpi_assessment"] = kpi_result
            kpi_quality = kpi_result["overall_kpi_quality_score"]
        else:
            kpi_quality = 0

        # 5. SDG alignment
        sdg_result = self.map_sdg_alignment(
            entity_id=entity_id,
            bond_name=bond_data.get("bond_name", ""),
            project_categories=bond_data.get("project_categories", []),
            kpis=bond_data.get("kpis", []),
        )
        results["sdg_alignment"] = sdg_result

        # 6. Composite impact score
        impact_input = {
            "bond_name": bond_data.get("bond_name"),
            "sbp_score": sbp_result["overall_sbp_score"],
            "sdg_score": sdg_result["sdg_contribution_score"],
            "kpi_quality_score": kpi_quality,
            "additionality_score": additionality_score,
        }
        impact_result = self.calculate_impact_score(impact_input)
        results["impact_score"] = impact_result

        results["bond_tier"] = impact_result["bond_tier"]
        results["composite_impact_score"] = impact_result["composite_impact_score"]
        results["assessment_standard"] = (
            "ICMA Social Bond Principles (SBP) June 2023; "
            "UN SDG Agenda 2030; IRIS+ v5.3 (GIIN 2023)"
        )

        return results


# ---------------------------------------------------------------------------
# E85 — Required Named Constants (route-layer aliases)
# ---------------------------------------------------------------------------

# ICMA SBP 4 core components with sub-criteria and weights.
# Source: ICMA Social Bond Principles June 2023
ICMA_SBP_COMPONENTS: Dict[str, Any] = {
    "use_of_proceeds": {
        "weight": 0.30,
        "description": "Clear identification of eligible social project categories and expected social outcomes",
        "sub_criteria": [
            "Eligible social project categories clearly defined",
            "Target populations explicitly identified",
            "Expected social outcomes stated with measurable indicators",
            "Environmental and social safeguards documented",
            "Projects listed or described in the bond framework",
        ],
        "icma_ref": "ICMA SBP 2023 § Use of Proceeds",
    },
    "process_evaluation": {
        "weight": 0.25,
        "description": "Issuer's documented criteria and process for project selection and portfolio management",
        "sub_criteria": [
            "Written eligibility criteria for project selection",
            "ESG risk screening methodology documented",
            "Decision-making body with E&S expertise identified",
            "Alignment with recognised social taxonomies / SDGs",
            "Exclusion criteria for harmful activities",
        ],
        "icma_ref": "ICMA SBP 2023 § Process for Project Evaluation and Selection",
    },
    "management_proceeds": {
        "weight": 0.25,
        "description": "Formal tracking and allocation of net proceeds to eligible projects",
        "sub_criteria": [
            "Proceeds tracked in dedicated sub-account or register",
            "Unallocated proceeds invested in liquid assets",
            "Annual reconciliation of allocated vs. raised proceeds",
            "Internal audit or auditor attestation on allocation",
            "Re-allocation policy for project cancellations",
        ],
        "icma_ref": "ICMA SBP 2023 § Management of Proceeds",
    },
    "reporting": {
        "weight": 0.20,
        "description": "Annual reporting on allocation and social impact outcomes",
        "sub_criteria": [
            "Allocation report published at least annually",
            "Impact report with quantitative output indicators",
            "Use of standardised KPIs (IRIS+, ICMA Impact Handbook)",
            "Third-party verification of impact data",
            "SDG mapping included in impact report",
        ],
        "icma_ref": "ICMA SBP 2023 § Reporting",
    },
}

# 9 ICMA-aligned social project categories (list form for route serialisation)
SOCIAL_PROJECT_CATEGORIES: List[Dict[str, Any]] = [
    {
        "name":                "affordable_housing",
        "description":         "Financing affordable and social housing for low-income or vulnerable populations",
        "eligible_activities": [
            "Construction of social housing units",
            "Renovation of existing affordable housing stock",
            "Mortgage-backed lending to below-median income households",
            "Transitional housing for homeless populations",
            "Supportive housing for people with disabilities",
        ],
        "sdg_alignment":       [1, 11],
        "icma_code":           "AH",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "access_to_education",
        "description":         "Improving access to quality education for underserved learners",
        "eligible_activities": [
            "Scholarships and bursaries for low-income students",
            "Construction and renovation of school infrastructure",
            "Digital learning platforms in underserved communities",
            "Early childhood development programs",
            "Vocational and technical education facilities",
        ],
        "sdg_alignment":       [4, 10],
        "icma_code":           "AE",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "affordable_basic_infrastructure",
        "description":         "Providing affordable access to energy, water, sanitation and transport",
        "eligible_activities": [
            "Rural electrification projects",
            "Safe drinking water and sanitation infrastructure",
            "Affordable public transport networks",
            "Digital connectivity in remote areas",
            "Low-cost housing infrastructure",
        ],
        "sdg_alignment":       [6, 7, 9, 11],
        "icma_code":           "ABI",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "employment_generation",
        "description":         "Creating jobs and enhancing skills for disadvantaged groups",
        "eligible_activities": [
            "SME financing for job creation in deprived areas",
            "Vocational training and reskilling programs",
            "Social enterprise financing",
            "Women entrepreneur support funds",
            "Youth employment and apprenticeship schemes",
        ],
        "sdg_alignment":       [8, 10],
        "icma_code":           "EG",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "food_security",
        "description":         "Improving food access and smallholder agricultural productivity",
        "eligible_activities": [
            "Smallholder farmer financing in low-income countries",
            "Food bank and redistribution infrastructure",
            "Nutrition supplementation programs",
            "Sustainable agriculture for subsistence farmers",
            "Cold chain infrastructure in food-insecure regions",
        ],
        "sdg_alignment":       [2, 1],
        "icma_code":           "FS",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "socioeconomic_empowerment",
        "description":         "Expanding economic participation and financial inclusion",
        "eligible_activities": [
            "Microfinance for unbanked populations",
            "Financial literacy and inclusion programs",
            "Community development finance institutions",
            "Indigenous enterprise support",
            "Refugee economic integration programs",
        ],
        "sdg_alignment":       [1, 8, 10],
        "icma_code":           "SE",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "affordable_healthcare",
        "description":         "Expanding access to healthcare for underserved populations",
        "eligible_activities": [
            "Community health clinic construction and equipment",
            "Mobile health units for rural communities",
            "Disease prevention and vaccination programs",
            "Mental health services in deprived areas",
            "Maternal and child health care facilities",
        ],
        "sdg_alignment":       [3, 1],
        "icma_code":           "AHC",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "gender_equality",
        "description":         "Financing projects that advance gender equality and women's empowerment",
        "eligible_activities": [
            "Women-led business financing facilities",
            "Girls' education and retention programs",
            "Domestic violence shelter and support services",
            "Equal pay and workforce diversity initiatives",
            "Women's land and property rights programs",
        ],
        "sdg_alignment":       [5, 8, 10],
        "icma_code":           "GE",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
    {
        "name":                "digital_inclusion",
        "description":         "Reducing the digital divide for marginalised and rural communities",
        "eligible_activities": [
            "Broadband connectivity in underserved areas",
            "Digital literacy training programs",
            "Subsidised device access for low-income households",
            "E-government services in remote areas",
            "Assistive technology for people with disabilities",
        ],
        "sdg_alignment":       [9, 4, 10],
        "icma_code":           "DI",
        "sbp_ref":             "ICMA SBP 2023 Appendix 1",
    },
]

# 10 target population groups (list form for route serialisation)
TARGET_POPULATION_GROUPS: List[str] = [
    "living_below_poverty_line",
    "excluded_or_marginalized_communities",
    "people_with_disabilities",
    "migrants_and_displaced_persons",
    "women_and_girls",
    "elderly_populations",
    "youth_and_children",
    "indigenous_peoples",
    "workers_at_risk_of_displacement",
    "underserved_rural_communities",
]

# SDG social bond relevance mapping (SDGs 1-11, 16, 17)
# Relevance score: 3=primary, 2=significant, 1=indirect
SDG_SOCIAL_MAPPING: Dict[int, Dict[str, Any]] = {
    1:  {"name": "No Poverty",                        "social_bond_relevance": 3},
    2:  {"name": "Zero Hunger",                       "social_bond_relevance": 3},
    3:  {"name": "Good Health and Well-Being",        "social_bond_relevance": 3},
    4:  {"name": "Quality Education",                 "social_bond_relevance": 3},
    5:  {"name": "Gender Equality",                   "social_bond_relevance": 3},
    6:  {"name": "Clean Water and Sanitation",        "social_bond_relevance": 2},
    7:  {"name": "Affordable and Clean Energy",       "social_bond_relevance": 2},
    8:  {"name": "Decent Work and Economic Growth",   "social_bond_relevance": 3},
    9:  {"name": "Industry, Innovation and Infrastructure", "social_bond_relevance": 2},
    10: {"name": "Reduced Inequalities",              "social_bond_relevance": 3},
    11: {"name": "Sustainable Cities and Communities","social_bond_relevance": 2},
    16: {"name": "Peace, Justice and Strong Institutions", "social_bond_relevance": 1},
    17: {"name": "Partnerships for the Goals",        "social_bond_relevance": 1},
}


# ---------------------------------------------------------------------------
# E85 — Module-level wrapper functions (thin delegates to SocialBondEngine)
# ---------------------------------------------------------------------------

_SBE = SocialBondEngine()


def assess_icma_sbp_compliance(bond_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Score all 4 SBP components, compute composite, identify gaps,
    assign SBP tier (premium/standard/partial/non-compliant).
    """
    return _SBE.assess_icma_sbp_compliance(bond_data)


def map_use_of_proceeds(bond_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Categorise project activities to ICMA categories, compute eligible %,
    primary category, check excluded activities.
    """
    return _SBE.assess_use_of_proceeds(bond_data)


def assess_target_population(bond_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate target population definition, estimate beneficiary reach,
    compute geographic coverage score.
    """
    return _SBE.assess_target_population(bond_data)


def score_social_kpis(bond_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check KPI completeness vs library (mandatory categories), quantification rate,
    SDG alignment, impact measurement method.
    """
    return _SBE.score_social_kpis(bond_data)


def compute_sdg_alignment(bond_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map all project activities to SDGs, identify primary SDG, secondary SDGs,
    compute composite SDG alignment score.
    """
    return _SBE.map_sdg_alignment(bond_data)


def run_full_assessment(bond_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Orchestrate all E85 sub-methods and produce consolidated assessment.
    Produces: sbp_composite_score, sbp_aligned, impact_score, bond_tier,
    kpis_defined, kpis_quantified, sdg_alignment, primary_sdg, beneficiaries_count.
    """
    return _SBE.run_full_assessment(bond_data)
