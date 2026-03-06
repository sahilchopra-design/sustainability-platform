"""
Seed assets_pg with the 8 real CSRD entities as portfolio holdings.

- FI entities (ABN AMRO, BNP, ING, Rabobank) → demo-eu-banking-sfdr
- Energy entities (EDP, ENGIE, Orsted, RWE) → demo-energy-transition

Asset values derived from csrd_entity_registry + fi_financials / energy_financials (2024).
Existing CSRD entity assets are deleted and re-seeded so this is idempotent.
"""

import sys
import os
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2

DB = "postgresql://postgres.kytzcbipsghprsqoalvi:KimiaAImpact2026@aws-1-us-east-2.pooler.supabase.com:5432/postgres"


def seed():
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    # ── Pull entity registry data ────────────────────────────────────────────────
    cur.execute("""
        SELECT
            cer.id,
            cer.legal_name,
            cer.primary_sector,
            cer.net_turnover_meur,
            cer.balance_sheet_total_meur,
            cer.fi_entity_id,
            cer.energy_entity_id
        FROM csrd_entity_registry cer
        ORDER BY cer.primary_sector, cer.legal_name
    """)
    entities = cur.fetchall()
    print(f"Found {len(entities)} CSRD entities")

    # ── Pull FI financials for exposure estimates ────────────────────────────────
    cur.execute("""
        SELECT fie.id, ff.total_assets, ff.npl_ratio_pct, ff.cet1_ratio_pct
        FROM fi_financials ff
        JOIN fi_entities fie ON fie.id = ff.entity_id
        WHERE ff.reporting_year = 2024
    """)
    fi_fin = {str(r[0]): r for r in cur.fetchall()}

    # ── Pull energy financials for exposure estimates ────────────────────────────
    cur.execute("""
        SELECT ee.id, ef.total_revenues, ef.total_assets
        FROM energy_financials ef
        JOIN energy_entities ee ON ee.id = ef.entity_id
        WHERE ef.reporting_year = 2024
    """)
    en_fin = {str(r[0]): r for r in cur.fetchall()}

    # ── Pull GHG scope 1+2 for base_pd proxy ────────────────────────────────────
    cur.execute("""
        SELECT entity_registry_id,
               scope1_gross_tco2e,
               scope2_market_based_tco2e
        FROM esrs_e1_ghg_emissions
        WHERE reporting_year = 2024
    """)
    ghg = {str(r[0]): r for r in cur.fetchall()}

    # ── Delete existing CSRD entity assets to keep idempotent ───────────────────
    csrd_names = [e[1] for e in entities]
    cur.execute(
        "DELETE FROM assets_pg WHERE company_name = ANY(%s)",
        (csrd_names,)
    )
    deleted = cur.rowcount
    print(f"Deleted {deleted} existing CSRD asset rows")

    # ── Asset definitions ────────────────────────────────────────────────────────
    # FI sector mapping
    fi_asset_type_map = {
        "ABN AMRO": "Corporate Bond",
        "BNP Paribas": "Corporate Bond",
        "ING Group": "Corporate Bond",
        "Rabobank": "Corporate Bond",
    }
    # Energy sector mapping
    en_asset_type_map = {
        "EDP": "Infrastructure Equity",
        "ENGIE": "Infrastructure Equity",
        "Orsted": "Infrastructure Equity",
        "RWE Group": "Infrastructure Equity",
    }

    assets = []

    for eid, name, sector, turnover, bs_total, fi_id, en_id in entities:
        eid_str = str(eid)
        fi_id_str = str(fi_id) if fi_id else None
        en_id_str = str(en_id) if en_id else None

        # Determine portfolio
        if fi_id_str:
            portfolio_id = "demo-eu-banking-sfdr"
            asset_type = fi_asset_type_map.get(name, "Corporate Bond")
            company_sector = "Financial Services"
            company_subsector = "Banking"
            fi = fi_fin.get(fi_id_str)
            # Exposure = 2% of total assets (typical bond position in a diversified portfolio)
            exposure = round(float(fi[1]) * 0.02, 1) if fi and fi[1] else round(float(bs_total or 0) * 0.02, 1)
            market_value = round(exposure * 0.97, 1)
            # base_pd from npl_ratio as proxy; npl_ratio is % — scale to decimal
            npl = float(fi[2]) if fi and fi[2] else 1.5
            base_pd = round(min(npl / 100.0 * 1.5, 0.08), 4)   # factor 1.5 × npl → PD
            base_lgd = 0.45   # LGD standard for senior unsecured
            rating_map = {
                "ABN AMRO": "A",
                "BNP Paribas": "A",
                "ING Group": "A-",
                "Rabobank": "AA-",
            }
            rating = rating_map.get(name, "BBB+")
            maturity = 5

        elif en_id_str:
            portfolio_id = "demo-energy-transition"
            asset_type = en_asset_type_map.get(name, "Infrastructure Equity")
            company_sector = "Energy"
            company_subsector = "Utilities"
            en = en_fin.get(en_id_str)
            # Exposure = 5% of total assets (equity position)
            en_bs = float(en[2]) if en and en[2] else float(bs_total or 0)
            exposure = round(en_bs * 0.05, 1) if en_bs else round(float(bs_total or 0) * 0.05, 1)
            market_value = round(exposure * 1.05, 1)  # slight premium for renewables
            base_pd = 0.015   # investment-grade energy utility
            base_lgd = 0.40
            rating_map = {
                "EDP": "BBB+",
                "ENGIE": "BBB+",
                "Orsted": "BBB",
                "RWE Group": "BBB+",
            }
            rating = rating_map.get(name, "BBB")
            maturity = 7

        else:
            # Fallback — should not occur
            portfolio_id = "demo-eu-banking-sfdr"
            asset_type = "Corporate Bond"
            company_sector = sector or "Other"
            company_subsector = ""
            exposure = round(float(bs_total or 0) * 0.02, 1)
            market_value = round(exposure * 0.97, 1)
            base_pd = 0.02
            base_lgd = 0.45
            rating = "BBB"
            maturity = 5

        asset_id = str(uuid.uuid4())
        assets.append((
            asset_id, portfolio_id, asset_type,
            name, company_sector, company_subsector,
            exposure, market_value, base_pd, base_lgd,
            rating, maturity
        ))

    # ── Insert ───────────────────────────────────────────────────────────────────
    cur.executemany("""
        INSERT INTO assets_pg
            (id, portfolio_id, asset_type, company_name, company_sector,
             company_subsector, exposure, market_value, base_pd, base_lgd,
             rating, maturity_years)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT DO NOTHING
    """, assets)

    conn.commit()
    print(f"\nInserted {len(assets)} CSRD entity assets into assets_pg:")
    for a in assets:
        print(f"  [{a[2]:26s}] {a[3]:30s}  portfolio={a[1]}  exposure={a[6]:,.0f} mEUR  pd={a[8]:.4f}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    seed()
