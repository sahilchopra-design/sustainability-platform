"""
036 – Add CDM methodological tools tables.

Creates:
  - cdm_tool: Master catalog of 43 CDM methodological tools.
  - cdm_tool_execution: Audit log for tool calculation runs.
  - methodology_tool_dependency: Maps methodology→tool requirements.

Seeds 43 rows into cdm_tool and ~200 rows into methodology_tool_dependency.
"""

from alembic import op
import sqlalchemy as sa

revision = '036_add_cdm_tools_tables'
down_revision = '035_add_gri_standards_and_mapping'
branch_labels = None
depends_on = None


def upgrade():
    # ------------------------------------------------------------------
    # 1) CDM Tool catalog
    # ------------------------------------------------------------------
    op.create_table(
        'cdm_tool',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('code', sa.String(20), nullable=False, unique=True,
                  comment='Tool code (e.g. TOOL01, AR-TOOL14)'),
        sa.Column('name', sa.String(255), nullable=False,
                  comment='Full tool name'),
        sa.Column('short_name', sa.String(100), nullable=True),
        sa.Column('category', sa.String(50), nullable=False,
                  comment='Tool category'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.String(20), nullable=True),
        sa.Column('unfccc_reference', sa.String(200), nullable=True),
        sa.Column('applicable_scopes', sa.JSON(), server_default='[]'),
        sa.Column('input_schema', sa.JSON(), server_default='{}'),
        sa.Column('output_schema', sa.JSON(), server_default='{}'),
        sa.Column('default_parameters', sa.JSON(), server_default='{}'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_cdm_tool_code', 'cdm_tool', ['code'])
    op.create_index('ix_cdm_tool_category', 'cdm_tool', ['category'])

    # ------------------------------------------------------------------
    # 2) CDM Tool execution audit log
    # ------------------------------------------------------------------
    op.create_table(
        'cdm_tool_execution',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('tool_code', sa.String(20),
                  sa.ForeignKey('cdm_tool.code', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('methodology_code', sa.String(50), nullable=True),
        sa.Column('portfolio_id', sa.Text(), nullable=True),
        sa.Column('project_id', sa.Text(), nullable=True),
        sa.Column('inputs', sa.JSON(), server_default='{}'),
        sa.Column('outputs', sa.JSON(), server_default='{}'),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(20), server_default='completed'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
    )
    op.create_index('ix_cte_tool_code', 'cdm_tool_execution', ['tool_code'])
    op.create_index('ix_cte_methodology', 'cdm_tool_execution', ['methodology_code'])
    op.create_index('ix_cte_portfolio', 'cdm_tool_execution', ['portfolio_id'])

    # ------------------------------------------------------------------
    # 3) Methodology → Tool dependency mapping
    # ------------------------------------------------------------------
    op.create_table(
        'methodology_tool_dependency',
        sa.Column('id', sa.Text(), primary_key=True),
        sa.Column('methodology_code', sa.String(50), nullable=False),
        sa.Column('tool_code', sa.String(20),
                  sa.ForeignKey('cdm_tool.code', ondelete='CASCADE'),
                  nullable=False),
        sa.Column('usage_context', sa.String(100), nullable=True,
                  comment='baseline | project_emissions | additionality | leakage'),
        sa.Column('is_mandatory', sa.Boolean(), server_default='true'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('now()')),
        sa.UniqueConstraint('methodology_code', 'tool_code',
                            name='uq_methodology_tool'),
    )
    op.create_index('ix_mtd_methodology', 'methodology_tool_dependency',
                    ['methodology_code'])
    op.create_index('ix_mtd_tool', 'methodology_tool_dependency',
                    ['tool_code'])
    op.create_index('ix_mtd_meth_tool', 'methodology_tool_dependency',
                    ['methodology_code', 'tool_code'])

    # ------------------------------------------------------------------
    # 4) Seed 43 CDM tools
    # ------------------------------------------------------------------
    import uuid

    def _tid(code):
        """Deterministic UUID from tool code."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"cdm-tool-{code}"))

    tools = [
        ("TOOL01", "Tool for the demonstration and assessment of additionality",
         "Additionality Assessment", "ADDITIONALITY", "09.0"),
        ("TOOL02", "Combined tool to identify the baseline scenario and demonstrate additionality",
         "Baseline + Additionality", "ADDITIONALITY", "07.0"),
        ("TOOL03", "Tool to calculate project or leakage CO2 emissions from fossil fuel combustion",
         "Fossil Fuel CO2", "EMISSION_CALCULATION", "03.0"),
        ("TOOL04", "Emissions from solid waste disposal sites",
         "Waste FOD Model", "WASTE", "08.0"),
        ("TOOL05", "Baseline, project and/or leakage emissions from electricity consumption",
         "Electricity Emissions", "EMISSION_CALCULATION", "03.0"),
        ("TOOL06", "Project emissions from flaring",
         "Flaring Emissions", "EMISSION_CALCULATION", "02.0"),
        ("TOOL07", "Tool to calculate the emission factor for an electricity system",
         "Grid Emission Factor", "GRID", "07.0"),
        ("TOOL08", "Tool to determine the mass flow of a greenhouse gas in a gaseous stream",
         "GHG Mass Flow", "EMISSION_CALCULATION", "03.0"),
        ("TOOL09", "Determining the baseline efficiency of thermal or electric energy generation systems",
         "Baseline Efficiency", "BASELINE", "03.0"),
        ("TOOL10", "Tool to determine the remaining lifetime of equipment",
         "Equipment Lifetime", "EQUIPMENT", "01.0"),
        ("TOOL11", "Assessment of the validity of the original/current baseline and update of the baseline at the renewal of the crediting period",
         "Baseline Validity", "BASELINE", "03.0"),
        ("TOOL12", "Project and leakage emissions from transportation of freight",
         "Freight Transport", "TRANSPORT", "02.0"),
        ("TOOL13", "Project and leakage emissions from composting",
         "Composting Emissions", "WASTE", "01.0"),
        ("TOOL14", "Project and leakage emissions from anaerobic digesters",
         "Anaerobic Digester", "WASTE", "01.0"),
        ("TOOL15", "Upstream leakage emissions associated with fossil fuel use",
         "Upstream Leakage", "LEAKAGE", "02.0"),
        ("TOOL16", "Project and leakage emissions from biomass",
         "Biomass Emissions", "BIOMASS", "04.0"),
        ("TOOL17", "Baseline setting and monitoring methodology for the establishment of the inter-urban cargo modal shift baseline",
         "Cargo Modal Shift", "TRANSPORT", "01.0"),
        ("TOOL18", "Baseline methodology for the establishment of the urban passenger transport modal shift baseline",
         "Passenger Transport", "TRANSPORT", "01.0"),
        ("TOOL19", "Demonstration of additionality of microscale project activities",
         "Microscale Additionality", "SMALL_SCALE", "10.0"),
        ("TOOL20", "Tool for the assessment of debundling for small-scale CDM project activities",
         "SSC Debundling", "SMALL_SCALE", "05.0"),
        ("TOOL21", "Demonstration of additionality of small-scale project activities",
         "SSC Additionality", "SMALL_SCALE", "13.0"),
        ("TOOL22", "Leakage in biomass small-scale project activities",
         "Biomass Leakage SSC", "SMALL_SCALE", "05.0"),
        ("TOOL23", "Additionality of first-of-its-kind project activities",
         "First-of-its-Kind", "ADDITIONALITY", "01.0"),
        ("TOOL24", "Common practice analysis",
         "Common Practice", "COMMON_PRACTICE", "03.0"),
        ("TOOL25", "Apportioning of emissions from a joint production process to the main product and co-products",
         "Emissions Apportioning", "INDUSTRIAL", "01.0"),
        ("TOOL26", "Methodology for accounting of HFC-23 emission reductions",
         "HFC-23 Accounting", "INDUSTRIAL", "04.0"),
        ("TOOL27", "Investment analysis",
         "Investment Analysis", "INVESTMENT", "03.0"),
        ("TOOL28", "Tool for determining project emissions from refrigerant systems",
         "Refrigerant Emissions", "REFRIGERANT", "01.0"),
        ("TOOL29", "Standardized baselines for efficient refrigerators and air conditioners",
         "SB Appliances", "DEFAULT_VALUES", "01.0"),
        ("TOOL30", "Calculation of the fraction of non-renewable biomass",
         "fNRB Calculation", "BIOMASS", "04.0"),
        ("TOOL31", "Standardized baselines for building sector energy efficiency",
         "SB Buildings", "BUILDING", "01.0"),
        ("TOOL32", "Positive lists of technologies",
         "Positive Lists", "DEFAULT_VALUES", "09.0"),
        ("TOOL33", "Default values for common parameters",
         "Default Values", "DEFAULT_VALUES", "03.0"),
        ("AR-TOOL02", "Combined tool to identify the baseline scenario and demonstrate additionality in A/R CDM project activities",
         "A/R Additionality", "AFFORESTATION", "01.0"),
        ("AR-TOOL03", "Calculation of the number of sample plots for measurements within A/R CDM project activities",
         "A/R Sample Plots", "AFFORESTATION", "02.0"),
        ("AR-TOOL08", "Estimation of non-CO2 GHG emissions resulting from burning of biomass attributable to an A/R CDM project activity",
         "A/R Biomass Burning", "AFFORESTATION", "04.0"),
        ("AR-TOOL12", "Estimation of carbon stocks and change in carbon stocks in dead wood and litter in A/R CDM project activities",
         "Dead Wood/Litter C", "AFFORESTATION", "03.0"),
        ("AR-TOOL14", "Estimation of carbon stocks and change in carbon stocks of trees and shrubs in an A/R CDM project activity",
         "Tree/Shrub Carbon", "AFFORESTATION", "04.1"),
        ("AR-TOOL15", "Estimation of the increase in GHG emissions attributable to displacement of pre-project agricultural activities in an A/R CDM project activity",
         "Displaced Agriculture", "AFFORESTATION", "02.0"),
        ("AR-TOOL16", "Tool for estimation of change in soil organic carbon stocks due to the implementation of A/R CDM project activities",
         "Soil Carbon Change", "AFFORESTATION", "01.1"),
        ("AR-TOOL17", "Estimation of aboveground tree biomass using allometric equations in A/R CDM project activities",
         "Allometric Biomass", "AFFORESTATION", "01.0"),
        ("AR-TOOL18", "Estimation of aboveground tree biomass using wood volume equations in A/R CDM project activities",
         "Volume-Based Biomass", "AFFORESTATION", "01.0"),
        ("AR-TOOL19", "Demonstration of eligibility of lands for A/R CDM project activities",
         "Land Eligibility", "AFFORESTATION", "03.0"),
    ]

    op.bulk_insert(
        sa.table('cdm_tool',
                 sa.column('id', sa.Text),
                 sa.column('code', sa.String),
                 sa.column('name', sa.String),
                 sa.column('short_name', sa.String),
                 sa.column('category', sa.String),
                 sa.column('version', sa.String),
                 sa.column('status', sa.String)),
        [
            {
                "id": _tid(code),
                "code": code,
                "name": name,
                "short_name": short_name,
                "category": cat,
                "version": ver,
                "status": "active",
            }
            for code, name, short_name, cat, ver in tools
        ]
    )

    # ------------------------------------------------------------------
    # 5) Seed methodology → tool dependencies
    # ------------------------------------------------------------------
    deps = {
        "ACM0001": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL04", "baseline"), ("TOOL06", "project_emissions")],
        "ACM0002": [("TOOL01", "additionality"), ("TOOL02", "additionality"), ("TOOL05", "project_emissions"), ("TOOL07", "baseline"), ("TOOL27", "additionality"), ("TOOL32", "additionality"), ("TOOL33", "baseline"), ("TOOL03", "leakage"), ("TOOL15", "leakage")],
        "ACM0003": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL05", "project_emissions"), ("TOOL07", "baseline"), ("TOOL16", "project_emissions")],
        "ACM0005": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL05", "project_emissions"), ("TOOL07", "baseline"), ("TOOL09", "baseline")],
        "ACM0006": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL07", "baseline"), ("TOOL16", "project_emissions")],
        "ACM0007": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL07", "baseline"), ("TOOL09", "baseline"), ("TOOL27", "additionality")],
        "ACM0008": [("TOOL01", "additionality"), ("TOOL03", "project_emissions"), ("TOOL06", "project_emissions"), ("TOOL08", "monitoring")],
        "ACM0009": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL07", "baseline"), ("TOOL15", "leakage")],
        "ACM0010": [("TOOL01", "additionality"), ("TOOL03", "project_emissions"), ("TOOL04", "baseline"), ("TOOL14", "project_emissions")],
        "ACM0012": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL05", "project_emissions"), ("TOOL07", "baseline"), ("TOOL09", "baseline")],
        "ACM0014": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL25", "project_emissions")],
        "ACM0022": [("TOOL01", "additionality"), ("TOOL03", "leakage"), ("TOOL04", "baseline"), ("TOOL13", "project_emissions")],
        "ACM0023": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL05", "project_emissions"), ("TOOL07", "baseline"), ("TOOL12", "baseline")],
        "AMS-I.A": [("TOOL07", "baseline"), ("TOOL19", "additionality"), ("TOOL21", "additionality")],
        "AMS-I.B": [("TOOL07", "baseline"), ("TOOL19", "additionality"), ("TOOL20", "additionality"), ("TOOL21", "additionality")],
        "AMS-I.C": [("TOOL07", "baseline"), ("TOOL16", "project_emissions"), ("TOOL19", "additionality"), ("TOOL21", "additionality")],
        "AMS-I.D": [("TOOL07", "baseline"), ("TOOL19", "additionality"), ("TOOL20", "additionality"), ("TOOL21", "additionality")],
        "AMS-I.E": [("TOOL07", "baseline"), ("TOOL19", "additionality"), ("TOOL21", "additionality")],
        "AMS-II.D": [("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL19", "additionality"), ("TOOL21", "additionality")],
        "AMS-II.E": [("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL18", "baseline"), ("TOOL21", "additionality")],
        "AMS-II.G": [("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL09", "baseline"), ("TOOL21", "additionality")],
        "AMS-III.AU": [("TOOL04", "baseline"), ("TOOL14", "project_emissions"), ("TOOL19", "additionality"), ("TOOL21", "additionality")],
        "AMS-III.B": [("TOOL04", "baseline"), ("TOOL14", "project_emissions"), ("TOOL21", "additionality")],
        "AMS-III.C": [("TOOL12", "baseline"), ("TOOL17", "baseline"), ("TOOL21", "additionality")],
        "AMS-III.D": [("TOOL04", "baseline"), ("TOOL21", "additionality")],
        "AM0012": [("TOOL01", "additionality"), ("TOOL03", "project_emissions"), ("TOOL08", "monitoring")],
        "AM0036": [("TOOL01", "additionality"), ("TOOL28", "baseline")],
        "AR-ACM0003": [("AR-TOOL02", "additionality"), ("AR-TOOL03", "monitoring"), ("AR-TOOL14", "project_emissions"), ("AR-TOOL17", "project_emissions"), ("AR-TOOL19", "additionality")],
        "VM0001": [("TOOL01", "additionality"), ("AR-TOOL14", "baseline"), ("AR-TOOL16", "baseline")],
        "VM0006": [("TOOL01", "additionality"), ("TOOL03", "baseline"), ("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL09", "baseline")],
        "VM0007": [("TOOL01", "additionality"), ("AR-TOOL14", "baseline"), ("AR-TOOL16", "baseline")],
        "VM0012": [("TOOL01", "additionality"), ("AR-TOOL14", "baseline"), ("AR-TOOL12", "baseline")],
        "VM0022": [("TOOL01", "additionality"), ("TOOL03", "leakage")],
        "VM0033": [("TOOL01", "additionality"), ("AR-TOOL14", "baseline"), ("AR-TOOL16", "baseline")],
        "VM0042": [("TOOL01", "additionality"), ("AR-TOOL16", "project_emissions")],
        "VM0044": [("TOOL01", "additionality"), ("TOOL03", "leakage"), ("TOOL16", "project_emissions")],
        "VM0047": [("TOOL01", "additionality"), ("AR-TOOL14", "project_emissions"), ("AR-TOOL16", "project_emissions"), ("AR-TOOL19", "additionality")],
        "VM0048": [("TOOL02", "additionality"), ("AR-TOOL14", "baseline"), ("AR-TOOL15", "leakage"), ("AR-TOOL16", "baseline")],
        "TPDDTEC": [("TOOL03", "baseline"), ("TOOL19", "additionality"), ("TOOL30", "baseline")],
        "TPDDTEC-SWH": [("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL19", "additionality")],
        "GS4GG_RE": [("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL32", "additionality")],
        "GS4GG_EE": [("TOOL05", "baseline"), ("TOOL07", "baseline"), ("TOOL09", "baseline")],
        "CAR-FOR": [("TOOL01", "additionality"), ("AR-TOOL14", "project_emissions")],
        "CAR-URB": [("TOOL01", "additionality"), ("AR-TOOL14", "project_emissions")],
        "ACR-ERW": [("TOOL01", "additionality"), ("TOOL03", "leakage")],
        "ACR-SOC": [("TOOL01", "additionality"), ("AR-TOOL16", "project_emissions")],
    }

    def _did(meth, tool):
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"mtd-{meth}-{tool}"))

    dep_rows = []
    for meth_code, tool_list in deps.items():
        for tool_code, ctx in tool_list:
            dep_rows.append({
                "id": _did(meth_code, tool_code),
                "methodology_code": meth_code,
                "tool_code": tool_code,
                "usage_context": ctx,
                "is_mandatory": True,
            })

    op.bulk_insert(
        sa.table('methodology_tool_dependency',
                 sa.column('id', sa.Text),
                 sa.column('methodology_code', sa.String),
                 sa.column('tool_code', sa.String),
                 sa.column('usage_context', sa.String),
                 sa.column('is_mandatory', sa.Boolean)),
        dep_rows
    )


def downgrade():
    op.drop_table('methodology_tool_dependency')
    op.drop_table('cdm_tool_execution')
    op.drop_table('cdm_tool')
