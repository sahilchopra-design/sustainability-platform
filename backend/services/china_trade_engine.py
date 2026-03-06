"""
China Trade Platform Engine — china_trade_engine.py

Six stakeholder-oriented engines:
  ChinaExporterEngine     — exporter lookup, CBAM readiness, carbon intensity scorecard
  CBAMAutoFillEngine      — cross-module CBAM Calculator integration (HS-code → EU benchmark)
  SupplierFrameworkEngine — importer requirement matching + supplier ranking
  ChinaESGETSEngine       — SSE/SZSE 2024 guidelines, CETS positions, NDC pathways
  TradeCorridorEngine     — bilateral trade corridors, P&L CBAM impact
  MarketplaceEngine       — carbon credit/allowance/certificate listings + price discovery

DB pattern: SessionLocal() directly (not get_db() generator — matches asia_regulatory_engine.py)
All engines fall back to curated reference data when ctp_* tables are empty.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ─── DB helpers ──────────────────────────────────────────────────────────────

def _exec_read(sql: str, params: Dict = None) -> List[Dict]:
    try:
        from db.postgres import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            result = db.execute(text(sql), params or {})
            cols = list(result.keys())
            return [dict(zip(cols, row)) for row in result.fetchall()]
        finally:
            db.close()
    except Exception as exc:
        logger.debug("china_trade_engine read error: %s", exc)
        return []


def _exec_write(sql: str, params: Dict = None) -> bool:
    try:
        from db.postgres import SessionLocal
        from sqlalchemy import text
        db = SessionLocal()
        try:
            db.execute(text(sql), params or {})
            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
    except Exception as exc:
        logger.debug("china_trade_engine write error: %s", exc)
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EXPORTER ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ChinaExporterEngine:
    """Exporter search, CBAM readiness scoring, carbon intensity benchmarking."""

    # Reference snapshot — 12 major Chinese exporters covering CBAM sectors
    _EXPORTERS = [
        {
            "entity_name": "China Baowu Steel Group",
            "entity_name_zh": "中国宝武钢铁集团",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Shanghai",
            "sector": "Steel",
            "sub_sector": "Crude Steel",
            "annual_revenue_usd_mn": 156000,
            "annual_export_volume_usd_mn": 8200,
            "is_ets_covered": True,
            "sse_stock_code": "600019",
            "primary_export_destinations": ["DE", "IT", "KR", "JP", "US"],
            "cbam_readiness_score": 62,
            "cbam_readiness_band": "Developing",
            "avg_embedded_carbon_tco2_per_tonne": 1.82,
            "vs_eu_benchmark_pct": 36.8,
            "green_certified": False,
            "cets_covered": True,
            "ets_registration_id": "CETS-SH-001",
        },
        {
            "entity_name": "HBIS Group",
            "entity_name_zh": "河钢集团",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Hebei",
            "sector": "Steel",
            "sub_sector": "Flat Products",
            "annual_revenue_usd_mn": 42000,
            "annual_export_volume_usd_mn": 3100,
            "is_ets_covered": True,
            "sse_stock_code": "000709",
            "primary_export_destinations": ["DE", "NL", "TR", "KR"],
            "cbam_readiness_score": 44,
            "cbam_readiness_band": "Emerging",
            "avg_embedded_carbon_tco2_per_tonne": 2.11,
            "vs_eu_benchmark_pct": 58.6,
            "green_certified": False,
            "cets_covered": True,
            "ets_registration_id": "CETS-HE-002",
        },
        {
            "entity_name": "Chalco (Aluminum Corp of China)",
            "entity_name_zh": "中国铝业",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Beijing",
            "sector": "Aluminium",
            "sub_sector": "Primary Aluminium",
            "annual_revenue_usd_mn": 35000,
            "annual_export_volume_usd_mn": 4500,
            "is_ets_covered": True,
            "sse_stock_code": "601600",
            "primary_export_destinations": ["DE", "JP", "KR", "US", "NL"],
            "cbam_readiness_score": 55,
            "cbam_readiness_band": "Developing",
            "avg_embedded_carbon_tco2_per_tonne": 12.4,
            "vs_eu_benchmark_pct": 119.6,
            "green_certified": False,
            "cets_covered": False,
            "ets_registration_id": None,
        },
        {
            "entity_name": "China Resources Cement",
            "entity_name_zh": "华润水泥",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Guangdong",
            "sector": "Cement",
            "sub_sector": "Portland Cement",
            "annual_revenue_usd_mn": 8200,
            "annual_export_volume_usd_mn": 620,
            "is_ets_covered": False,
            "sse_stock_code": None,
            "primary_export_destinations": ["HK", "VN", "ID", "PH"],
            "cbam_readiness_score": 38,
            "cbam_readiness_band": "Emerging",
            "avg_embedded_carbon_tco2_per_tonne": 0.612,
            "vs_eu_benchmark_pct": 7.6,
            "green_certified": False,
            "cets_covered": False,
            "ets_registration_id": None,
        },
        {
            "entity_name": "Sinopec Group",
            "entity_name_zh": "中国石化",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Beijing",
            "sector": "Chemicals",
            "sub_sector": "Nitrogen Fertilisers",
            "annual_revenue_usd_mn": 471000,
            "annual_export_volume_usd_mn": 6800,
            "is_ets_covered": True,
            "sse_stock_code": "600028",
            "primary_export_destinations": ["IN", "BR", "US", "DE", "AU"],
            "cbam_readiness_score": 58,
            "cbam_readiness_band": "Developing",
            "avg_embedded_carbon_tco2_per_tonne": 0.94,
            "vs_eu_benchmark_pct": 45.4,
            "green_certified": True,
            "green_certification_type": "PBoC",
            "cets_covered": True,
            "ets_registration_id": "CETS-BJ-003",
        },
        {
            "entity_name": "LONGi Green Energy",
            "entity_name_zh": "隆基绿能科技",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Shaanxi",
            "sector": "Renewables",
            "sub_sector": "Solar PV Modules",
            "annual_revenue_usd_mn": 9800,
            "annual_export_volume_usd_mn": 4200,
            "is_ets_covered": False,
            "sse_stock_code": "601012",
            "primary_export_destinations": ["DE", "NL", "US", "AU", "IN"],
            "cbam_readiness_score": 88,
            "cbam_readiness_band": "Leader",
            "avg_embedded_carbon_tco2_per_tonne": 0.38,
            "vs_eu_benchmark_pct": -28.3,
            "green_certified": True,
            "green_certification_type": "CBI",
            "cets_covered": False,
            "ets_registration_id": None,
        },
        {
            "entity_name": "BYD Company",
            "entity_name_zh": "比亚迪股份",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Guangdong",
            "sector": "Automotive",
            "sub_sector": "Battery Electric Vehicles",
            "annual_revenue_usd_mn": 85000,
            "annual_export_volume_usd_mn": 11200,
            "is_ets_covered": False,
            "szse_stock_code": "002594",
            "primary_export_destinations": ["AU", "NO", "DE", "NL", "IL"],
            "cbam_readiness_score": 82,
            "cbam_readiness_band": "Advanced",
            "avg_embedded_carbon_tco2_per_tonne": 0.0,
            "vs_eu_benchmark_pct": -100.0,
            "green_certified": True,
            "green_certification_type": "ISO14064",
            "cets_covered": False,
            "ets_registration_id": None,
        },
        {
            "entity_name": "CNOOC Limited",
            "entity_name_zh": "中国海洋石油",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Beijing",
            "sector": "Oil & Gas",
            "sub_sector": "LNG / Crude",
            "annual_revenue_usd_mn": 52000,
            "annual_export_volume_usd_mn": 9800,
            "is_ets_covered": True,
            "hkex_stock_code": "0883",
            "primary_export_destinations": ["JP", "KR", "DE", "GB", "FR"],
            "cbam_readiness_score": 61,
            "cbam_readiness_band": "Developing",
            "avg_embedded_carbon_tco2_per_tonne": 0.21,
            "vs_eu_benchmark_pct": 12.3,
            "green_certified": False,
            "cets_covered": True,
            "ets_registration_id": "CETS-BJ-004",
        },
        {
            "entity_name": "Zijin Mining Group",
            "entity_name_zh": "紫金矿业集团",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Fujian",
            "sector": "Metals",
            "sub_sector": "Copper / Gold",
            "annual_revenue_usd_mn": 28000,
            "annual_export_volume_usd_mn": 5100,
            "is_ets_covered": False,
            "sse_stock_code": "601899",
            "primary_export_destinations": ["JP", "KR", "DE", "US"],
            "cbam_readiness_score": 35,
            "cbam_readiness_band": "Emerging",
            "avg_embedded_carbon_tco2_per_tonne": 3.8,
            "vs_eu_benchmark_pct": 82.4,
            "green_certified": False,
            "cets_covered": False,
            "ets_registration_id": None,
        },
        {
            "entity_name": "CATL (Contemporary Amperex Technology)",
            "entity_name_zh": "宁德时代",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Fujian",
            "sector": "Battery Technology",
            "sub_sector": "Li-Ion Battery Cells",
            "annual_revenue_usd_mn": 45000,
            "annual_export_volume_usd_mn": 14800,
            "is_ets_covered": False,
            "szse_stock_code": "300750",
            "primary_export_destinations": ["DE", "HU", "US", "JP", "FR"],
            "cbam_readiness_score": 79,
            "cbam_readiness_band": "Advanced",
            "avg_embedded_carbon_tco2_per_tonne": 0.12,
            "vs_eu_benchmark_pct": -44.2,
            "green_certified": True,
            "green_certification_type": "ISO14064",
            "cets_covered": False,
            "ets_registration_id": None,
        },
        {
            "entity_name": "China Shenhua Energy",
            "entity_name_zh": "中国神华能源",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Beijing",
            "sector": "Power",
            "sub_sector": "Thermal Coal / Power",
            "annual_revenue_usd_mn": 38000,
            "annual_export_volume_usd_mn": 3200,
            "is_ets_covered": True,
            "sse_stock_code": "601088",
            "primary_export_destinations": ["JP", "KR", "IN", "TW"],
            "cbam_readiness_score": 29,
            "cbam_readiness_band": "Emerging",
            "avg_embedded_carbon_tco2_per_tonne": 0.83,
            "vs_eu_benchmark_pct": 128.6,
            "green_certified": False,
            "cets_covered": True,
            "ets_registration_id": "CETS-BJ-005",
        },
        {
            "entity_name": "Ganfeng Lithium Group",
            "entity_name_zh": "赣锋锂业集团",
            "entity_type": "exporter",
            "country_code": "CN",
            "province": "Jiangxi",
            "sector": "Critical Minerals",
            "sub_sector": "Lithium Compounds",
            "annual_revenue_usd_mn": 5400,
            "annual_export_volume_usd_mn": 2800,
            "is_ets_covered": False,
            "sse_stock_code": "002460",
            "primary_export_destinations": ["DE", "JP", "KR", "US", "AU"],
            "cbam_readiness_score": 71,
            "cbam_readiness_band": "Advanced",
            "avg_embedded_carbon_tco2_per_tonne": 1.4,
            "vs_eu_benchmark_pct": -15.2,
            "green_certified": True,
            "green_certification_type": "ResponsibleMinerals",
            "cets_covered": False,
            "ets_registration_id": None,
        },
    ]

    def search_exporters(
        self,
        query: Optional[str] = None,
        sector: Optional[str] = None,
        cbam_applicable: Optional[bool] = None,
        min_cbam_readiness: Optional[int] = None,
        limit: int = 20,
    ) -> Dict:
        # Try DB first
        rows = _exec_read(
            "SELECT * FROM ctp_entities WHERE country_code = 'CN' AND entity_type IN ('exporter','both') "
            "ORDER BY entity_name LIMIT :limit",
            {"limit": limit}
        )

        if rows:
            return {"source": "db", "count": len(rows), "exporters": rows}

        # Reference fallback
        results = list(self._EXPORTERS)
        if query:
            q = query.lower()
            results = [e for e in results if q in e["entity_name"].lower() or q in e.get("entity_name_zh", "").lower() or q in e.get("sector", "").lower()]
        if sector:
            results = [e for e in results if sector.lower() in e.get("sector", "").lower()]
        if cbam_applicable is not None:
            cbam_sectors = {"Steel", "Aluminium", "Cement", "Chemicals", "Fertiliser", "Power"}
            results = [e for e in results if cbam_applicable == (e.get("sector") in cbam_sectors)]
        if min_cbam_readiness is not None:
            results = [e for e in results if e.get("cbam_readiness_score", 0) >= min_cbam_readiness]

        return {
            "source": "reference",
            "count": len(results[:limit]),
            "exporters": results[:limit],
        }

    def get_exporter_profile(self, entity_name: str) -> Dict:
        rows = _exec_read(
            "SELECT e.*, d.overall_esg_score, d.esg_tier, d.e_score, d.s_score, d.g_score "
            "FROM ctp_entities e LEFT JOIN ctp_china_esg_disclosures d ON d.entity_id = e.id "
            "WHERE e.entity_name ILIKE :n LIMIT 1",
            {"n": f"%{entity_name}%"}
        )
        if rows:
            return rows[0]
        match = next(
            (e for e in self._EXPORTERS if entity_name.lower() in e["entity_name"].lower()),
            self._EXPORTERS[0]
        )
        return match

    def get_cbam_readiness_summary(self) -> Dict:
        """Distribution of CBAM readiness bands across Chinese exporters."""
        rows = _exec_read(
            "SELECT e.entity_name, l.competitiveness_risk, l.net_cbam_liability_eur "
            "FROM ctp_entities e JOIN ctp_cbam_liabilities l ON l.entity_id = e.id "
            "WHERE e.country_code = 'CN' ORDER BY l.net_cbam_liability_eur DESC LIMIT 20"
        )
        if rows:
            return {"source": "db", "data": rows}

        band_counts = {"Leader": 0, "Advanced": 0, "Developing": 0, "Emerging": 0}
        for e in self._EXPORTERS:
            band = e.get("cbam_readiness_band", "Emerging")
            band_counts[band] = band_counts.get(band, 0) + 1

        return {
            "source": "reference",
            "total_exporters": len(self._EXPORTERS),
            "band_distribution": [
                {"band": k, "count": v, "pct": round(v / len(self._EXPORTERS) * 100, 1)}
                for k, v in band_counts.items()
            ],
            "avg_cbam_readiness": round(
                sum(e["cbam_readiness_score"] for e in self._EXPORTERS) / len(self._EXPORTERS), 1
            ),
            "cbam_exposed_sectors": ["Steel", "Aluminium", "Cement", "Chemicals", "Power"],
            "top_exporters": sorted(self._EXPORTERS, key=lambda x: x["cbam_readiness_score"], reverse=True)[:5],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 2. CBAM AUTO-FILL ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class CBAMAutoFillEngine:
    """
    Cross-module endpoint: Given entity_name + hs_code, returns embedded carbon
    intensity and CETS price so the CBAM Calculator can auto-populate counterparty fields.
    """

    # EU CBAM Annex III — default embedded carbon (tCO2/tonne) by HS-4
    _EU_BENCHMARKS = {
        # Steel
        "7206": {"desc": "Iron / non-alloy steel ingots", "eu_benchmark_tco2": 0.878, "sector": "Steel"},
        "7207": {"desc": "Semi-finished iron/steel",       "eu_benchmark_tco2": 0.878, "sector": "Steel"},
        "7208": {"desc": "Flat-rolled iron (hot-rolled)",  "eu_benchmark_tco2": 1.331, "sector": "Steel"},
        "7209": {"desc": "Flat-rolled iron (cold-rolled)",  "eu_benchmark_tco2": 1.331, "sector": "Steel"},
        "7210": {"desc": "Flat-rolled iron (coated)",       "eu_benchmark_tco2": 1.331, "sector": "Steel"},
        "7214": {"desc": "Bars / rods",                     "eu_benchmark_tco2": 0.878, "sector": "Steel"},
        "7216": {"desc": "Angles / shapes / sections",      "eu_benchmark_tco2": 0.878, "sector": "Steel"},
        # Aluminium
        "7601": {"desc": "Unwrought aluminium",             "eu_benchmark_tco2": 5.647, "sector": "Aluminium"},
        "7604": {"desc": "Aluminium bars / rods",           "eu_benchmark_tco2": 5.647, "sector": "Aluminium"},
        "7606": {"desc": "Aluminium plates / sheet",        "eu_benchmark_tco2": 5.647, "sector": "Aluminium"},
        # Cement
        "2523": {"desc": "Portland cement",                 "eu_benchmark_tco2": 0.569, "sector": "Cement"},
        # Fertilisers
        "3102": {"desc": "Mineral / chemical nitrogenous",  "eu_benchmark_tco2": 0.646, "sector": "Fertiliser"},
        "3105": {"desc": "Mixed fertilisers",               "eu_benchmark_tco2": 0.646, "sector": "Fertiliser"},
        # Power
        "2716": {"desc": "Electrical energy",               "eu_benchmark_tco2": 0.276, "sector": "Power"},
    }

    # CETS current price and CNY/EUR conversion
    CETS_PRICE_CNY = 95.0       # CNY per tCO2 (March 2026)
    CNY_EUR_RATE   = 0.128      # 1 CNY = 0.128 EUR
    CETS_PRICE_EUR = round(CETS_PRICE_CNY * CNY_EUR_RATE, 2)   # ≈ 12.16 EUR/tCO2

    def supplier_lookup(
        self,
        entity_name: Optional[str] = None,
        hs_code: Optional[str] = None,
    ) -> Dict:
        """
        Key cross-module endpoint.
        Returns embedded carbon intensity + CETS price for the CBAM Calculator to auto-fill.
        """
        hs4 = (hs_code or "")[:4]
        benchmark = self._EU_BENCHMARKS.get(hs4)

        # Try DB
        rows = []
        if entity_name:
            rows = _exec_read(
                "SELECT ep.embedded_carbon_tco2_per_tonne, ep.production_process, ep.hs_code, "
                "ep.cbam_sector, ep.green_certified, ep.green_certification_type, "
                "e.entity_name, e.province, e.sector "
                "FROM ctp_export_products ep "
                "JOIN ctp_entities e ON e.id = ep.entity_id "
                "WHERE e.entity_name ILIKE :n AND ep.hs_code LIKE :hs "
                "ORDER BY ep.created_at DESC LIMIT 1",
                {"n": f"%{entity_name}%", "hs": f"{hs4}%"}
            )

        if rows:
            row = rows[0]
            embedded = float(row["embedded_carbon_tco2_per_tonne"])
        else:
            # Reference fallback: find matching exporter
            exporter_match = None
            if entity_name:
                exporter_match = next(
                    (e for e in ChinaExporterEngine._EXPORTERS
                     if entity_name.lower() in e["entity_name"].lower()),
                    None
                )
            embedded = exporter_match["avg_embedded_carbon_tco2_per_tonne"] if exporter_match else (
                benchmark["eu_benchmark_tco2"] * 1.35 if benchmark else 1.5
            )
            row = {
                "entity_name": entity_name or "Chinese Supplier (Reference)",
                "sector": exporter_match["sector"] if exporter_match else (benchmark["sector"] if benchmark else "Unknown"),
                "production_process": "BF-BOF" if (benchmark and benchmark["sector"] == "Steel") else "Reference",
                "green_certified": False,
            }

        eu_benchmark = benchmark["eu_benchmark_tco2"] if benchmark else None
        vs_benchmark_pct = round((embedded - eu_benchmark) / eu_benchmark * 100, 1) if eu_benchmark else None

        return {
            "entity_name": row.get("entity_name", entity_name),
            "sector": row.get("sector", "Unknown"),
            "hs_code": hs_code,
            "hs_description": benchmark["desc"] if benchmark else None,
            "embedded_carbon_tco2_per_tonne": embedded,
            "production_process": row.get("production_process", "Unknown"),
            "eu_benchmark_tco2_per_tonne": eu_benchmark,
            "vs_eu_benchmark_pct": vs_benchmark_pct,
            "green_certified": row.get("green_certified", False),
            "green_certification_type": row.get("green_certification_type"),
            "cets_price_cny_per_tco2": self.CETS_PRICE_CNY,
            "cets_price_eur_per_tco2": self.CETS_PRICE_EUR,
            "cbam_auto_fill": {
                "embedded_carbon": embedded,
                "eu_benchmark": eu_benchmark,
                "cets_price_eur": self.CETS_PRICE_EUR,
                "source": "ctp_db" if rows else "ctp_reference",
            },
        }

    def calculate_cbam_liability(
        self,
        entity_name: str,
        hs_code: str,
        export_volume_tonnes: float,
        eu_ets_price_eur: float = 65.0,
        export_value_eur_mn: Optional[float] = None,
    ) -> Dict:
        """Full CBAM liability calculation with CETS deduction."""
        lookup = self.supplier_lookup(entity_name=entity_name, hs_code=hs_code)
        embedded = lookup["embedded_carbon_tco2_per_tonne"]
        eu_benchmark = lookup["eu_benchmark_tco2_per_tonne"] or (embedded * 0.75)

        total_embedded_tco2 = embedded * export_volume_tonnes
        eu_benchmark_total = eu_benchmark * export_volume_tonnes
        excess_tco2 = max(0.0, total_embedded_tco2 - eu_benchmark_total)

        gross_cbam_eur = excess_tco2 * eu_ets_price_eur
        cets_paid_eur = excess_tco2 * self.CETS_PRICE_EUR
        net_cbam_eur = max(0.0, gross_cbam_eur - cets_paid_eur)

        price_impact_pct = None
        if export_value_eur_mn:
            price_impact_pct = round(net_cbam_eur / (export_value_eur_mn * 1_000_000) * 100, 2)

        risk = "low"
        if net_cbam_eur > 5_000_000: risk = "critical"
        elif net_cbam_eur > 1_000_000: risk = "high"
        elif net_cbam_eur > 200_000: risk = "medium"

        return {
            "entity_name": entity_name,
            "hs_code": hs_code,
            "export_volume_tonnes": export_volume_tonnes,
            "embedded_carbon_tco2": round(total_embedded_tco2, 2),
            "eu_benchmark_tco2": round(eu_benchmark_total, 2),
            "excess_carbon_tco2": round(excess_tco2, 2),
            "eu_ets_price_eur": eu_ets_price_eur,
            "cets_price_eur": self.CETS_PRICE_EUR,
            "carbon_price_differential_eur": round(eu_ets_price_eur - self.CETS_PRICE_EUR, 2),
            "gross_cbam_liability_eur": round(gross_cbam_eur, 2),
            "cets_carbon_already_paid_eur": round(cets_paid_eur, 2),
            "net_cbam_liability_eur": round(net_cbam_eur, 2),
            "net_cbam_liability_usd": round(net_cbam_eur * 1.09, 2),
            "price_impact_pct": price_impact_pct,
            "competitiveness_risk": risk,
            "cbam_phase": "full",
            "cets_deductibility_note": "CETS carbon costs deductible under EU CBAM Reg. (EU) 2023/956 Art.9",
        }

    def get_hs_benchmark_table(self) -> Dict:
        """All HS-4 EU benchmark values."""
        return {
            "benchmarks": self._EU_BENCHMARKS,
            "cets_price_cny": self.CETS_PRICE_CNY,
            "cets_price_eur": self.CETS_PRICE_EUR,
            "eu_ets_reference_eur": 65.0,
            "arbitrage_eur_per_tco2": round(65.0 - self.CETS_PRICE_EUR, 2),
            "source": "EU CBAM Regulation Annex III / EEX spot (2026-03)",
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 3. SUPPLIER FRAMEWORK ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class SupplierFrameworkEngine:
    """Importer sustainability requirements + supplier ranking."""

    _REQUIREMENTS = [
        {
            "importer_name": "Volkswagen AG",
            "framework": "CSDDD",
            "requirement_type": "carbon_intensity",
            "product_category": "Steel",
            "hs_codes_in_scope": ["7208", "7209", "7210"],
            "max_carbon_intensity_tco2_per_tonne": 1.1,
            "required_certifications": ["ResponsibleSteel", "ISO14064"],
            "reporting_frequency": "annual",
            "verified_data_required": True,
            "third_party_audit_required": True,
            "compliance_deadline": "2026-01-01",
            "preferred_supplier_discount_pct": 3.5,
            "penalty_clause": "Non-compliant suppliers subject to 18-month phase-out",
        },
        {
            "importer_name": "ArcelorMittal",
            "framework": "CBAM",
            "requirement_type": "carbon_intensity",
            "product_category": "Steel",
            "hs_codes_in_scope": ["7206", "7207", "7208"],
            "max_carbon_intensity_tco2_per_tonne": 1.5,
            "required_certifications": ["ISO14064"],
            "reporting_frequency": "quarterly",
            "verified_data_required": True,
            "third_party_audit_required": False,
            "compliance_deadline": "2026-06-30",
            "preferred_supplier_discount_pct": 2.0,
            "penalty_clause": "Carbon surcharge applied above 1.5 tCO2/t",
        },
        {
            "importer_name": "Airbus SE",
            "framework": "CSDDD",
            "requirement_type": "certification",
            "product_category": "Aluminium",
            "hs_codes_in_scope": ["7601", "7604", "7606"],
            "max_carbon_intensity_tco2_per_tonne": 8.0,
            "required_certifications": ["ASI Performance Standard", "ISO14064"],
            "reporting_frequency": "annual",
            "verified_data_required": True,
            "third_party_audit_required": True,
            "compliance_deadline": "2027-01-01",
            "preferred_supplier_discount_pct": 4.0,
            "penalty_clause": "De-listing from approved supplier register",
        },
        {
            "importer_name": "BASF SE",
            "framework": "CBAM",
            "requirement_type": "disclosure",
            "product_category": "Chemicals",
            "hs_codes_in_scope": ["3102", "3105"],
            "max_carbon_intensity_tco2_per_tonne": 0.8,
            "required_certifications": ["PBoC Green Label", "ISO14001"],
            "reporting_frequency": "annual",
            "verified_data_required": False,
            "third_party_audit_required": False,
            "compliance_deadline": "2026-12-31",
            "preferred_supplier_discount_pct": 1.5,
            "penalty_clause": "Carbon adjustment factor applied to purchase price",
        },
    ]

    def get_requirements(
        self,
        framework: Optional[str] = None,
        product_category: Optional[str] = None,
    ) -> Dict:
        rows = _exec_read("SELECT * FROM ctp_supplier_requirements WHERE active = TRUE ORDER BY compliance_deadline")
        if rows:
            return {"source": "db", "count": len(rows), "requirements": rows}

        results = list(self._REQUIREMENTS)
        if framework:
            results = [r for r in results if framework.upper() in r["framework"].upper()]
        if product_category:
            results = [r for r in results if product_category.lower() in r["product_category"].lower()]

        return {"source": "reference", "count": len(results), "requirements": results}

    def rank_suppliers(
        self,
        product_category: str,
        max_intensity: Optional[float] = None,
        require_certified: bool = False,
    ) -> Dict:
        """Rank Chinese exporters against importer requirements for a product category."""
        exporters = ChinaExporterEngine._EXPORTERS
        sector_map = {
            "steel": "Steel", "aluminium": "Aluminium", "aluminum": "Aluminium",
            "cement": "Cement", "chemicals": "Chemicals", "fertiliser": "Fertiliser",
        }
        target_sector = sector_map.get(product_category.lower(), product_category)
        candidates = [e for e in exporters if e.get("sector") == target_sector or product_category.lower() in e.get("sub_sector", "").lower()]

        if not candidates:
            candidates = exporters[:6]

        if max_intensity is not None:
            candidates = [e for e in candidates if e.get("avg_embedded_carbon_tco2_per_tonne", 999) <= max_intensity]
        if require_certified:
            candidates = [e for e in candidates if e.get("green_certified")]

        ranked = sorted(candidates, key=lambda x: x.get("cbam_readiness_score", 0), reverse=True)

        return {
            "product_category": product_category,
            "total_candidates": len(exporters),
            "qualifying_count": len(ranked),
            "ranked_suppliers": [
                {
                    "rank": i + 1,
                    "entity_name": s["entity_name"],
                    "sector": s.get("sector"),
                    "cbam_readiness_score": s.get("cbam_readiness_score"),
                    "cbam_readiness_band": s.get("cbam_readiness_band"),
                    "embedded_carbon_tco2_per_tonne": s.get("avg_embedded_carbon_tco2_per_tonne"),
                    "vs_eu_benchmark_pct": s.get("vs_eu_benchmark_pct"),
                    "green_certified": s.get("green_certified"),
                    "green_certification_type": s.get("green_certification_type"),
                }
                for i, s in enumerate(ranked)
            ],
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 4. CHINA ESG & ETS ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class ChinaESGETSEngine:
    """SSE/SZSE 2024 ESG disclosures, CETS positions, NDC sector pathways."""

    # CETS historical price (CNY/tCO2)
    CETS_PRICE_HISTORY = [
        {"year": 2021, "avg_price_cny": 48.0,  "phase": "Phase1"},
        {"year": 2022, "avg_price_cny": 56.3,  "phase": "Phase1"},
        {"year": 2023, "avg_price_cny": 68.1,  "phase": "Phase1"},
        {"year": 2024, "avg_price_cny": 83.5,  "phase": "Phase2"},
        {"year": 2025, "avg_price_cny": 91.2,  "phase": "Phase2"},
        {"year": 2026, "avg_price_cny": 95.0,  "phase": "Phase2"},
    ]

    # NDC sectoral pathways (MtCO2, selected milestones)
    NDC_PATHWAYS = [
        {"sector": "Power",       "year": 2030, "baseline_mtco2": 5200, "pathway_mtco2": 4800, "current_mtco2": 5100, "on_track": False, "milestone": "peak"},
        {"sector": "Power",       "year": 2060, "baseline_mtco2": 5200, "pathway_mtco2": 420,  "current_mtco2": None, "on_track": None,  "milestone": "neutrality"},
        {"sector": "Steel",       "year": 2030, "baseline_mtco2": 1750, "pathway_mtco2": 1580, "current_mtco2": 1720, "on_track": False, "milestone": "peak"},
        {"sector": "Steel",       "year": 2060, "baseline_mtco2": 1750, "pathway_mtco2": 80,   "current_mtco2": None, "on_track": None,  "milestone": "neutrality"},
        {"sector": "Cement",      "year": 2030, "baseline_mtco2": 1380, "pathway_mtco2": 1200, "current_mtco2": 1290, "on_track": True,  "milestone": "decline"},
        {"sector": "Transport",   "year": 2030, "baseline_mtco2": 1040, "pathway_mtco2": 980,  "current_mtco2": 1020, "on_track": False, "milestone": "peak"},
        {"sector": "Buildings",   "year": 2030, "baseline_mtco2": 620,  "pathway_mtco2": 540,  "current_mtco2": 580,  "on_track": True,  "milestone": "decline"},
        {"sector": "Agriculture", "year": 2030, "baseline_mtco2": 620,  "pathway_mtco2": 580,  "current_mtco2": 595,  "on_track": True,  "milestone": "interim"},
    ]

    def get_esg_dashboard(
        self,
        sector: Optional[str] = None,
        esg_tier: Optional[str] = None,
    ) -> Dict:
        rows = _exec_read(
            "SELECT entity_name, exchange, reporting_year, overall_esg_score, esg_tier, "
            "e_score, s_score, g_score, e_ghg_scope1_tco2e, e_renewable_pct, "
            "carbon_neutral_target_year "
            "FROM ctp_china_esg_disclosures "
            "ORDER BY overall_esg_score DESC LIMIT 50"
        )
        if rows:
            return {"source": "db", "disclosures": rows, "reporting_year": 2024}

        # Reference ESG scores from exporter reference list mapped to ESG format
        esg_data = [
            {"entity_name": "LONGi Green Energy",      "exchange": "SSE",  "overall_esg_score": 86, "esg_tier": "Leader",     "e_score": 91, "s_score": 78, "g_score": 82, "e_renewable_pct": 94.0, "carbon_neutral_target_year": 2028},
            {"entity_name": "BYD Company",              "exchange": "SZSE", "overall_esg_score": 82, "esg_tier": "Advanced",   "e_score": 88, "s_score": 79, "g_score": 74, "e_renewable_pct": 78.0, "carbon_neutral_target_year": 2035},
            {"entity_name": "CATL",                     "exchange": "SZSE", "overall_esg_score": 79, "esg_tier": "Advanced",   "e_score": 82, "s_score": 76, "g_score": 77, "e_renewable_pct": 65.0, "carbon_neutral_target_year": 2035},
            {"entity_name": "Ganfeng Lithium",          "exchange": "SSE",  "overall_esg_score": 71, "esg_tier": "Advanced",   "e_score": 68, "s_score": 72, "g_score": 75, "e_renewable_pct": 42.0, "carbon_neutral_target_year": 2040},
            {"entity_name": "Sinopec Group",            "exchange": "SSE",  "overall_esg_score": 65, "esg_tier": "Developing",  "e_score": 58, "s_score": 71, "g_score": 68, "e_renewable_pct": 18.0, "carbon_neutral_target_year": 2050},
            {"entity_name": "China Baowu Steel Group",  "exchange": "SSE",  "overall_esg_score": 62, "esg_tier": "Developing",  "e_score": 55, "s_score": 68, "g_score": 65, "e_renewable_pct": 12.0, "carbon_neutral_target_year": 2050},
            {"entity_name": "CNOOC Limited",            "exchange": "HKEX", "overall_esg_score": 61, "esg_tier": "Developing",  "e_score": 52, "s_score": 67, "g_score": 68, "e_renewable_pct": 8.0,  "carbon_neutral_target_year": 2050},
            {"entity_name": "Chalco",                   "exchange": "SSE",  "overall_esg_score": 55, "esg_tier": "Developing",  "e_score": 44, "s_score": 62, "g_score": 63, "e_renewable_pct": 22.0, "carbon_neutral_target_year": 2055},
            {"entity_name": "HBIS Group",               "exchange": "SZSE", "overall_esg_score": 44, "esg_tier": "Emerging",    "e_score": 36, "s_score": 52, "g_score": 48, "e_renewable_pct": 5.0,  "carbon_neutral_target_year": 2060},
            {"entity_name": "China Shenhua Energy",     "exchange": "SSE",  "overall_esg_score": 38, "esg_tier": "Emerging",    "e_score": 28, "s_score": 48, "g_score": 44, "e_renewable_pct": 3.0,  "carbon_neutral_target_year": 2060},
            {"entity_name": "Zijin Mining",             "exchange": "SSE",  "overall_esg_score": 35, "esg_tier": "Emerging",    "e_score": 29, "s_score": 40, "g_score": 40, "e_renewable_pct": 7.0,  "carbon_neutral_target_year": 2060},
            {"entity_name": "China Resources Cement",   "exchange": "HKEX", "overall_esg_score": 38, "esg_tier": "Emerging",    "e_score": 32, "s_score": 44, "g_score": 42, "e_renewable_pct": 4.0,  "carbon_neutral_target_year": 2060},
        ]

        if sector:
            # Can't filter easily by sector without sector mapping; return all
            pass
        if esg_tier:
            esg_data = [e for e in esg_data if e["esg_tier"] == esg_tier]

        tier_counts = {}
        for e in esg_data:
            t = e["esg_tier"]
            tier_counts[t] = tier_counts.get(t, 0) + 1

        return {
            "source": "reference",
            "reporting_year": 2024,
            "framework": "SSE/SZSE 2024 Mandatory ESG Guidelines",
            "total_companies": len(esg_data),
            "tier_distribution": tier_counts,
            "avg_overall_score": round(sum(e["overall_esg_score"] for e in esg_data) / len(esg_data), 1),
            "avg_e_score": round(sum(e["e_score"] for e in esg_data) / len(esg_data), 1),
            "disclosures": esg_data,
        }

    def get_ndc_alignment(self, sector: Optional[str] = None) -> Dict:
        rows = _exec_read(
            "SELECT * FROM ctp_ndc_pathways ORDER BY sector, year"
        )
        if rows:
            return {"source": "db", "pathways": rows}

        pathways = self.NDC_PATHWAYS
        if sector:
            pathways = [p for p in pathways if sector.lower() in p["sector"].lower()]

        on_track = sum(1 for p in pathways if p.get("on_track") is True)
        off_track = sum(1 for p in pathways if p.get("on_track") is False)

        return {
            "source": "reference",
            "china_ndc_targets": {
                "co2_peak_year": 2030,
                "carbon_neutrality_year": 2060,
                "non_fossil_energy_pct_2030": 25,
                "forest_stock_increase_m3": 6000,
                "wind_solar_capacity_gw_2030": 1200,
            },
            "sectors_on_track": on_track,
            "sectors_off_track": off_track,
            "pathways": pathways,
            "cets_price_cny": CBAMAutoFillEngine.CETS_PRICE_CNY,
            "cets_price_history": self.CETS_PRICE_HISTORY,
        }

    def get_ets_positions(self, sector: Optional[str] = None) -> Dict:
        rows = _exec_read(
            "SELECT * FROM ctp_ets_positions ORDER BY year DESC, sector LIMIT 100"
        )
        if rows:
            return {"source": "db", "positions": rows}

        positions = [
            {"entity_name": "China Shenhua Energy", "sector": "Power",    "year": 2024, "phase": "Phase2", "allocation_tco2": 88000000, "verified_emissions_tco2": 92000000, "surplus_deficit_tco2": -4000000, "compliance_status": "deficit",   "carbon_price_cny": 95.0, "compliance_cost_cny_mn": 380.0},
            {"entity_name": "China Baowu Steel",     "sector": "Steel",   "year": 2024, "phase": "Phase2", "allocation_tco2": 65000000, "verified_emissions_tco2": 61000000, "surplus_deficit_tco2":  4000000, "compliance_status": "surplus",   "carbon_price_cny": 95.0, "compliance_cost_cny_mn": -380.0},
            {"entity_name": "Chalco",                "sector": "Aluminium","year": 2024, "phase": "Phase2", "allocation_tco2": 22000000, "verified_emissions_tco2": 24500000, "surplus_deficit_tco2": -2500000, "compliance_status": "deficit",   "carbon_price_cny": 95.0, "compliance_cost_cny_mn": 237.5},
            {"entity_name": "China Resources Cement","sector": "Cement",   "year": 2024, "phase": "Phase2", "allocation_tco2": 18000000, "verified_emissions_tco2": 17200000, "surplus_deficit_tco2":   800000, "compliance_status": "surplus",   "carbon_price_cny": 95.0, "compliance_cost_cny_mn": -76.0},
            {"entity_name": "Sinopec",               "sector": "Chemicals","year": 2024, "phase": "Phase2", "allocation_tco2": 42000000, "verified_emissions_tco2": 43800000, "surplus_deficit_tco2": -1800000, "compliance_status": "deficit",   "carbon_price_cny": 95.0, "compliance_cost_cny_mn": 171.0},
        ]

        if sector:
            positions = [p for p in positions if sector.lower() in p["sector"].lower()]

        return {
            "source": "reference",
            "year": 2024,
            "cets_current_price_cny": 95.0,
            "cets_current_price_eur": round(95.0 * 0.128, 2),
            "phase": "Phase 2 (2024–2025)",
            "covered_sectors": ["Power", "Steel", "Aluminium", "Cement", "Chemicals", "Paper", "Aviation"],
            "covered_installations_est": 3500,
            "total_covered_emissions_gtco2": 8.5,
            "price_history": self.CETS_PRICE_HISTORY,
            "positions": positions,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 5. TRADE CORRIDOR ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class TradeCorridorEngine:
    """Bilateral trade corridors, CBAM P&L impact, carbon price arbitrage."""

    _CORRIDORS = [
        {
            "corridor_name": "China → EU",
            "origin_country": "CN",
            "destination_country": "EU",
            "trade_value_usd_bn": 618.0,
            "trade_volume_mn_tonnes": 285.0,
            "carbon_intensity_avg_tco2_per_tonne": 1.82,
            "total_embedded_carbon_mtco2": 518.7,
            "cbam_applicable": True,
            "carbon_border_regime": "EU_CBAM",
            "regime_full_implementation": "2026-01-01",
            "key_product_categories": ["Steel", "Aluminium", "Cement", "Chemicals", "Power"],
            "top_hs_codes": ["7208", "7601", "2523", "3102", "2716"],
            "annual_cbam_liability_est_eur_mn": 4280.0,
            "eu_ets_price_eur": 65.0,
            "cets_price_eur": 12.16,
            "arbitrage_eur_per_tco2": 52.84,
        },
        {
            "corridor_name": "China → UK",
            "origin_country": "CN",
            "destination_country": "GB",
            "trade_value_usd_bn": 98.0,
            "trade_volume_mn_tonnes": 52.0,
            "carbon_intensity_avg_tco2_per_tonne": 1.71,
            "total_embedded_carbon_mtco2": 88.9,
            "cbam_applicable": True,
            "carbon_border_regime": "UK_CBAM",
            "regime_full_implementation": "2027-01-01",
            "key_product_categories": ["Steel", "Aluminium", "Cement"],
            "top_hs_codes": ["7208", "7601", "2523"],
            "annual_cbam_liability_est_eur_mn": 620.0,
            "eu_ets_price_eur": 58.0,
            "cets_price_eur": 12.16,
            "arbitrage_eur_per_tco2": 45.84,
        },
        {
            "corridor_name": "China → USA",
            "origin_country": "CN",
            "destination_country": "US",
            "trade_value_usd_bn": 427.0,
            "trade_volume_mn_tonnes": 198.0,
            "carbon_intensity_avg_tco2_per_tonne": 1.68,
            "total_embedded_carbon_mtco2": 332.6,
            "cbam_applicable": False,
            "carbon_border_regime": "US_CCA",
            "regime_full_implementation": "2028-01-01",
            "key_product_categories": ["Steel", "Chemicals", "Electronics"],
            "top_hs_codes": ["7208", "3102", "8542"],
            "annual_cbam_liability_est_eur_mn": 1850.0,
            "eu_ets_price_eur": 40.0,
            "cets_price_eur": 12.16,
            "arbitrage_eur_per_tco2": 27.84,
        },
        {
            "corridor_name": "China → Japan",
            "origin_country": "CN",
            "destination_country": "JP",
            "trade_value_usd_bn": 177.0,
            "trade_volume_mn_tonnes": 88.0,
            "carbon_intensity_avg_tco2_per_tonne": 1.55,
            "total_embedded_carbon_mtco2": 136.4,
            "cbam_applicable": False,
            "carbon_border_regime": "None",
            "regime_full_implementation": None,
            "key_product_categories": ["Steel", "Chemicals", "Machinery"],
            "top_hs_codes": ["7208", "3102", "8479"],
            "annual_cbam_liability_est_eur_mn": 0.0,
            "eu_ets_price_eur": 0.0,
            "cets_price_eur": 12.16,
            "arbitrage_eur_per_tco2": 0.0,
        },
        {
            "corridor_name": "China → South Korea",
            "origin_country": "CN",
            "destination_country": "KR",
            "trade_value_usd_bn": 162.0,
            "trade_volume_mn_tonnes": 74.0,
            "carbon_intensity_avg_tco2_per_tonne": 1.60,
            "total_embedded_carbon_mtco2": 118.4,
            "cbam_applicable": False,
            "carbon_border_regime": "K-ETS",
            "regime_full_implementation": None,
            "key_product_categories": ["Steel", "Chemicals", "Battery"],
            "top_hs_codes": ["7208", "3102", "8507"],
            "annual_cbam_liability_est_eur_mn": 0.0,
            "eu_ets_price_eur": 22.0,
            "cets_price_eur": 12.16,
            "arbitrage_eur_per_tco2": 9.84,
        },
    ]

    def get_all_corridors(self) -> Dict:
        rows = _exec_read("SELECT * FROM ctp_trade_corridors ORDER BY trade_value_usd_bn DESC")
        if rows:
            return {"source": "db", "corridors": rows}
        return {"source": "reference", "corridors": self._CORRIDORS}

    def get_corridor(self, origin: str, destination: str) -> Dict:
        rows = _exec_read(
            "SELECT * FROM ctp_trade_corridors WHERE origin_country = :o AND destination_country = :d LIMIT 1",
            {"o": origin.upper(), "d": destination.upper()}
        )
        if rows:
            return rows[0]
        match = next(
            (c for c in self._CORRIDORS if c["origin_country"] == origin.upper() and c["destination_country"] == destination.upper()),
            self._CORRIDORS[0]
        )
        return match

    def get_pl_impact(
        self,
        sector: str,
        eu_ets_price_eur: float = 65.0,
    ) -> Dict:
        """P&L CBAM impact scenarios across 6 EU ETS price points."""
        price_scenarios = [40, 50, 60, 65, 75, 90]
        cets = CBAMAutoFillEngine.CETS_PRICE_EUR

        # Embedded carbon by sector (tCO2/tonne)
        sector_intensity = {
            "Steel": 1.82, "Aluminium": 12.4, "Cement": 0.612,
            "Chemicals": 0.94, "Power": 0.83, "Fertiliser": 0.94,
        }
        eu_benchmark = {
            "Steel": 1.331, "Aluminium": 5.647, "Cement": 0.569,
            "Chemicals": 0.7, "Power": 0.276, "Fertiliser": 0.646,
        }
        intensity = sector_intensity.get(sector, 1.5)
        benchmark = eu_benchmark.get(sector, 1.0)
        excess = max(0.0, intensity - benchmark)

        scenarios = []
        for p in price_scenarios:
            net_liability_per_tonne = max(0.0, excess * (p - cets))
            scenarios.append({
                "eu_ets_price_eur": p,
                "gross_cbam_eur_per_tonne": round(excess * p, 2),
                "cets_deduction_eur_per_tonne": round(excess * cets, 2),
                "net_cbam_eur_per_tonne": round(net_liability_per_tonne, 2),
                "price_impact_pct_at_500usd_sale": round(net_liability_per_tonne / 500 * 100, 2),
                "arbitrage_vs_eu_ets": round(p - cets, 2),
            })

        return {
            "sector": sector,
            "embedded_carbon_tco2_per_tonne": intensity,
            "eu_benchmark_tco2_per_tonne": benchmark,
            "excess_carbon_tco2_per_tonne": round(excess, 3),
            "cets_price_eur": cets,
            "current_eu_ets_price_eur": eu_ets_price_eur,
            "scenarios": scenarios,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# 6. MARKETPLACE ENGINE
# ═══════════════════════════════════════════════════════════════════════════════

class MarketplaceEngine:
    """Carbon credit / ETS allowance / certificate listings and price discovery."""

    PRICE_BENCHMARKS = {
        "CETS":          {"spot_usd": 13.1,  "forward_1y_usd": 16.8,  "unit": "tCO2", "exchange": "CBEEX"},
        "CCER":          {"spot_usd": 8.5,   "forward_1y_usd": 11.2,  "unit": "tCO2", "exchange": "CBEEX"},
        "VCS":           {"spot_usd": 5.8,   "forward_1y_usd": 7.4,   "unit": "tCO2", "exchange": "OTC/CBL"},
        "CDM":           {"spot_usd": 0.9,   "forward_1y_usd": 1.1,   "unit": "tCO2", "exchange": "OTC"},
        "EU_ETS":        {"spot_usd": 71.2,  "forward_1y_usd": 73.8,  "unit": "tCO2", "exchange": "EEX/ICE"},
        "CORSIA":        {"spot_usd": 4.2,   "forward_1y_usd": 5.6,   "unit": "tCO2", "exchange": "OTC"},
        "Gold_Standard": {"spot_usd": 12.4,  "forward_1y_usd": 14.9,  "unit": "tCO2", "exchange": "GSF"},
    }

    _LISTINGS = [
        {
            "listing_id": "L001",
            "seller_name": "China Baowu Steel Group",
            "listing_type": "ets_allowance",
            "product_description": "CETS Phase 2 allowances (CEAs) — Power sector, vintage 2024",
            "standard": "CETS",
            "volume_tco2": 4000000,
            "asking_price_usd_per_tco2": 13.5,
            "asking_price_cny_per_tco2": 97.0,
            "currency": "CNY",
            "geography_origin": "CN",
            "sector": "Steel",
            "vintage_year": 2024,
            "verification_status": "verified",
            "listing_status": "active",
            "co_benefits": {},
        },
        {
            "listing_id": "L002",
            "seller_name": "LONGi Green Energy",
            "listing_type": "carbon_credit",
            "product_description": "CCER credits — Solar power generation, Shaanxi Province",
            "standard": "CCER",
            "volume_tco2": 850000,
            "asking_price_usd_per_tco2": 9.2,
            "asking_price_cny_per_tco2": 71.9,
            "currency": "USD",
            "geography_origin": "CN",
            "sector": "Renewables",
            "vintage_year": 2024,
            "verification_status": "verified",
            "listing_status": "active",
            "co_benefits": {"biodiversity": False, "community": True, "water": False},
        },
        {
            "listing_id": "L003",
            "seller_name": "Ganfeng Lithium Group",
            "listing_type": "carbon_credit",
            "product_description": "VCS REDD+ avoided deforestation — Jiangxi Province forest",
            "standard": "VCS",
            "volume_tco2": 320000,
            "asking_price_usd_per_tco2": 6.4,
            "asking_price_cny_per_tco2": 50.0,
            "currency": "USD",
            "geography_origin": "CN",
            "sector": "Land Use",
            "vintage_year": 2023,
            "verification_status": "verified",
            "listing_status": "active",
            "co_benefits": {"biodiversity": True, "community": True, "water": True},
        },
        {
            "listing_id": "L004",
            "seller_name": "Chalco",
            "listing_type": "green_cert",
            "product_description": "ASI Performance Standard green aluminium certificates — 8,000t",
            "standard": "ASI",
            "volume_tco2": 0,
            "asking_price_usd_per_tco2": 18.0,
            "asking_price_cny_per_tco2": 140.6,
            "currency": "USD",
            "geography_origin": "CN",
            "sector": "Aluminium",
            "vintage_year": 2024,
            "verification_status": "verified",
            "listing_status": "active",
            "co_benefits": {"biodiversity": False, "community": False, "water": False},
        },
        {
            "listing_id": "L005",
            "seller_name": "Sinopec Group",
            "listing_type": "cbam_cert",
            "product_description": "Pre-validated CBAM certificates for EU-destined nitrogen fertilisers",
            "standard": "EU_CBAM",
            "volume_tco2": 180000,
            "asking_price_usd_per_tco2": 72.0,
            "asking_price_cny_per_tco2": 562.5,
            "currency": "EUR",
            "geography_origin": "CN",
            "sector": "Chemicals",
            "vintage_year": 2025,
            "verification_status": "verified",
            "listing_status": "active",
            "co_benefits": {},
        },
        {
            "listing_id": "L006",
            "seller_name": "CATL",
            "listing_type": "carbon_credit",
            "product_description": "Gold Standard credits — EV charging infrastructure, Guangdong",
            "standard": "Gold Standard",
            "volume_tco2": 145000,
            "asking_price_usd_per_tco2": 13.8,
            "asking_price_cny_per_tco2": 107.8,
            "currency": "USD",
            "geography_origin": "CN",
            "sector": "Transport",
            "vintage_year": 2024,
            "verification_status": "pending",
            "listing_status": "active",
            "co_benefits": {"biodiversity": False, "community": True, "water": False},
        },
    ]

    def get_listings(
        self,
        listing_type: Optional[str] = None,
        standard: Optional[str] = None,
        sector: Optional[str] = None,
        limit: int = 50,
    ) -> Dict:
        rows = _exec_read(
            "SELECT * FROM ctp_marketplace_listings WHERE listing_status = 'active' "
            "ORDER BY listed_at DESC LIMIT :limit",
            {"limit": limit}
        )
        if rows:
            return {"source": "db", "count": len(rows), "listings": rows}

        results = list(self._LISTINGS)
        if listing_type:
            results = [l for l in results if l["listing_type"] == listing_type]
        if standard:
            results = [l for l in results if standard.upper() in l["standard"].upper()]
        if sector:
            results = [l for l in results if sector.lower() in l["sector"].lower()]

        return {"source": "reference", "count": len(results[:limit]), "listings": results[:limit]}

    def get_price_discovery(self) -> Dict:
        return {
            "benchmarks": self.PRICE_BENCHMARKS,
            "spread_analysis": {
                "cets_vs_eu_ets_usd": round(
                    self.PRICE_BENCHMARKS["EU_ETS"]["spot_usd"] - self.PRICE_BENCHMARKS["CETS"]["spot_usd"], 2
                ),
                "ccer_vs_vcs_usd": round(
                    self.PRICE_BENCHMARKS["CCER"]["spot_usd"] - self.PRICE_BENCHMARKS["VCS"]["spot_usd"], 2
                ),
                "cbam_arbitrage_note": "EU CBAM allows CETS cost deduction under Art.9 — effective arbitrage = EU ETS price − CETS price",
            },
            "as_of": "2026-03-05",
            "sources": ["CBEEX", "EEX", "ICE", "CBL", "GSF", "OTC composite"],
        }

    def get_market_stats(self) -> Dict:
        return {
            "china_voluntary_market_usd_mn": 420,
            "cets_trading_volume_mtco2_2024": 212,
            "ccer_pipeline_mtco2": 800,
            "top_listing_types": ["ets_allowance", "carbon_credit", "green_cert", "cbam_cert"],
            "active_listings": len(self._LISTINGS),
            "total_volume_listed_tco2": sum(l["volume_tco2"] for l in self._LISTINGS if l["volume_tco2"] > 0),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# CROSS-MODULE ENGINE
# Bridges China Trade data into CBAM Calculator, Supply Chain, Financial Risk,
# Regulatory, Scenario Analysis, and Portfolio Analytics modules.
# ═══════════════════════════════════════════════════════════════════════════════

class CrossModuleEngine:
    """
    Aggregates China Trade data into formats consumed by other platform modules.

    Module bridges:
      scope3_cat1         -> Supply Chain (GHG Protocol Cat 1 purchased goods)
      ecl_cbam_overlay    -> Financial Risk (IFRS 9 ECL + CBAM credit risk)
      regulatory_csrd     -> Regulatory (CSRD E1/SFDR PAI China overlay)
      scenario_cets_ngfs  -> Scenario Analysis (CETS trajectory × NGFS scenarios)
      portfolio_cbam      -> Portfolio Analytics (portfolio-level CBAM exposure)
      entity_hub          -> All modules (per-entity cross-module data card)
    """

    CETS_PRICE_CNY = 95.0
    CETS_PRICE_EUR = 12.16
    EU_ETS_PRICE_EUR = 65.0

    # Scope 3 Cat 1 emission factors (tCO2/tonne) sourced from CETS verified data
    _SCOPE3_CAT1_FACTORS = [
        {"hs4": "7208", "product": "Hot-rolled steel coil",    "sector": "Steel",     "ef_tco2_t": 2.15, "source": "CETS verified 2024"},
        {"hs4": "7209", "product": "Cold-rolled steel sheet",  "sector": "Steel",     "ef_tco2_t": 2.38, "source": "CETS verified 2024"},
        {"hs4": "7601", "product": "Unwrought aluminium",      "sector": "Aluminium", "ef_tco2_t": 11.2, "source": "CETS verified 2024"},
        {"hs4": "7610", "product": "Aluminium structures",     "sector": "Aluminium", "ef_tco2_t": 9.8,  "source": "CETS verified 2024"},
        {"hs4": "2523", "product": "Portland cement",          "sector": "Cement",    "ef_tco2_t": 0.82, "source": "CETS verified 2024"},
        {"hs4": "2804", "product": "Industrial gases",         "sector": "Chemicals", "ef_tco2_t": 3.45, "source": "CETS verified 2024"},
        {"hs4": "3102", "product": "Nitrogenous fertilisers",  "sector": "Chemicals", "ef_tco2_t": 4.12, "source": "CETS verified 2024"},
        {"hs4": "8541", "product": "Solar PV modules",         "sector": "Renewables","ef_tco2_t": 0.38, "source": "IEA 2024 lifecycle"},
        {"hs4": "8504", "product": "Wind turbine components",  "sector": "Renewables","ef_tco2_t": 0.29, "source": "IEA 2024 lifecycle"},
        {"hs4": "8507", "product": "Li-ion batteries",         "sector": "Renewables","ef_tco2_t": 7.50, "source": "IEA 2024 lifecycle"},
    ]

    # CBAM credit risk bands for IFRS 9 ECL overlay
    _ECL_CBAM_BANDS = [
        {
            "risk_band": "Low",    "cbam_readiness_min": 75, "cbam_readiness_max": 100,
            "pd_uplift_bps": 0,    "lgd_uplift_bps": 0,
            "description": "CBAM-ready; ETS surplus; CETS-compliant",
            "ecl_stage": "Stage 1",
        },
        {
            "risk_band": "Medium", "cbam_readiness_min": 50, "cbam_readiness_max": 74,
            "pd_uplift_bps": 25,   "lgd_uplift_bps": 50,
            "description": "Developing CBAM compliance; moderate ETS deficit risk",
            "ecl_stage": "Stage 2",
        },
        {
            "risk_band": "High",   "cbam_readiness_min": 25, "cbam_readiness_max": 49,
            "pd_uplift_bps": 75,   "lgd_uplift_bps": 100,
            "description": "Low CBAM readiness; significant ETS deficit; PD uplift warranted",
            "ecl_stage": "Stage 2/3",
        },
        {
            "risk_band": "Critical", "cbam_readiness_min": 0, "cbam_readiness_max": 24,
            "pd_uplift_bps": 150,  "lgd_uplift_bps": 200,
            "description": "CBAM non-compliant; ETS excess deficit; credit impairment risk",
            "ecl_stage": "Stage 3",
        },
    ]

    # NGFS × CETS scenario overlay
    _NGFS_CETS_SCENARIOS = [
        {
            "ngfs_scenario": "Net Zero 2050",
            "cets_2025_cny": 95,  "cets_2030_cny": 145, "cets_2035_cny": 210, "cets_2040_cny": 290,
            "coverage_expansion": "Power + Industry + Transport by 2030",
            "cbam_arbitrage_2030_eur": 8.5,
            "transition_risk": "High near-term",
        },
        {
            "ngfs_scenario": "Delayed Transition",
            "cets_2025_cny": 85,  "cets_2030_cny": 105, "cets_2035_cny": 160, "cets_2040_cny": 250,
            "coverage_expansion": "Power by 2030; Industry by 2035",
            "cbam_arbitrage_2030_eur": 20.3,
            "transition_risk": "High post-2030",
        },
        {
            "ngfs_scenario": "Below 2 Degrees",
            "cets_2025_cny": 95,  "cets_2030_cny": 130, "cets_2035_cny": 185, "cets_2040_cny": 260,
            "coverage_expansion": "Power + Industry by 2028",
            "cbam_arbitrage_2030_eur": 12.4,
            "transition_risk": "Moderate",
        },
        {
            "ngfs_scenario": "Current Policies",
            "cets_2025_cny": 90,  "cets_2030_cny": 98,  "cets_2035_cny": 108, "cets_2040_cny": 120,
            "coverage_expansion": "Power sector only",
            "cbam_arbitrage_2030_eur": 45.1,
            "transition_risk": "Physical risk dominant",
        },
    ]

    # CSRD E1 / SFDR PAI mapping from SSE/SZSE 2024 ESG data
    _REGULATORY_CSRD_MAPPING = [
        {
            "china_disclosure": "SSE/SZSE Scope 1 GHG emissions (tCO2e)",
            "csrd_esrs": "ESRS E1-6 — GHG emissions (Scope 1)",
            "sfdr_pai": "PAI 1 — GHG emissions",
            "issb_s2": "IFRS S2 para 29(a) — Gross Scope 1",
            "coverage_pct": 88,
            "gap": "Biogenic CO2 not separately disclosed",
        },
        {
            "china_disclosure": "SSE/SZSE Scope 2 electricity emissions (tCO2e)",
            "csrd_esrs": "ESRS E1-6 — GHG emissions (Scope 2)",
            "sfdr_pai": "PAI 1 — GHG emissions",
            "issb_s2": "IFRS S2 para 29(b) — Gross Scope 2",
            "coverage_pct": 85,
            "gap": "Market-based Scope 2 not consistently disclosed",
        },
        {
            "china_disclosure": "CETS verified emissions (tCO2)",
            "csrd_esrs": "ESRS E1-4 — GHG reduction targets",
            "sfdr_pai": "PAI 4 — Fossil fuel sector exposure",
            "issb_s2": "IFRS S2 para 33 — Carbon offsets",
            "coverage_pct": 72,
            "gap": "CETS scope limited to power; Scope 3 absent",
        },
        {
            "china_disclosure": "SSE/SZSE water withdrawal (000 m3)",
            "csrd_esrs": "ESRS E3-4 — Water consumption",
            "sfdr_pai": "PAI 7 — Water usage",
            "issb_s2": "N/A (IFRS S1 general disclosure)",
            "coverage_pct": 65,
            "gap": "Recycled water not uniformly reported",
        },
        {
            "china_disclosure": "SSE/SZSE renewable energy ratio (%)",
            "csrd_esrs": "ESRS E1-5 — Energy consumption & mix",
            "sfdr_pai": "PAI 5 — Renewable energy ratio",
            "issb_s2": "IFRS S2 para 29(e) — Energy",
            "coverage_pct": 79,
            "gap": "Unbundled RECs not separately stated",
        },
    ]

    def get_scope3_cat1(self, sector: Optional[str] = None) -> Dict:
        """
        GHG Protocol Scope 3 Category 1 (Purchased Goods & Services) emission
        factors for Chinese exported goods.  Pulled from ctp_export_products first,
        then falls back to curated reference table.
        """
        rows = _exec_read("""
            SELECT ep.hs_code, ep.product_name, ep.sector,
                   ep.embedded_carbon_tco2_per_tonne AS ef_tco2_t,
                   ep.eu_benchmark_tco2_per_tonne,
                   ep.vs_eu_benchmark_pct,
                   e.entity_name, e.cbam_readiness_score
            FROM   ctp_export_products ep
            JOIN   ctp_entities e ON ep.entity_id = e.id
            WHERE  (:sector IS NULL OR ep.sector = :sector)
            ORDER  BY ef_tco2_t ASC
            LIMIT  100
        """, {"sector": sector})

        if not rows:
            factors = [f for f in self._SCOPE3_CAT1_FACTORS
                       if not sector or f["sector"] == sector]
        else:
            factors = rows

        return {
            "module": "Supply Chain — Scope 3 Cat 1",
            "description": "Chinese exported goods emission factors for GHG Protocol Cat 1 calculations",
            "ghg_protocol_category": "Category 1 — Purchased Goods and Services",
            "data_source": "CETS verified emissions 2024 / IEA lifecycle 2024",
            "factors": factors,
            "china_trade_link": "/china-trade?tab=exporters",
            "total_factors": len(factors),
        }

    def get_ecl_cbam_overlay(self) -> Dict:
        """
        IFRS 9 ECL overlay: maps Chinese exporter CBAM readiness to PD/LGD uplifts.
        Provides credit risk bands for financial institutions with China trade exposure.
        """
        rows = _exec_read("""
            SELECT e.entity_name, e.sector, e.cbam_readiness_score,
                   e.esg_tier, e.ets_registered,
                   ep.embedded_carbon_tco2_per_tonne,
                   cl.net_cbam_liability_eur,
                   cl.competitiveness_risk_band
            FROM   ctp_entities e
            LEFT JOIN ctp_export_products ep ON ep.entity_id = e.id
            LEFT JOIN ctp_cbam_liabilities cl ON cl.entity_id = e.id
            ORDER  BY e.cbam_readiness_score ASC
            LIMIT  50
        """)

        summary_by_band = {}
        for band in self._ECL_CBAM_BANDS:
            summary_by_band[band["risk_band"]] = {
                **band,
                "entity_count": 0,
                "example_entities": [],
            }

        for row in rows:
            score = row.get("cbam_readiness_score", 50)
            for band in self._ECL_CBAM_BANDS:
                if band["cbam_readiness_min"] <= score <= band["cbam_readiness_max"]:
                    summary_by_band[band["risk_band"]]["entity_count"] += 1
                    if len(summary_by_band[band["risk_band"]]["example_entities"]) < 3:
                        summary_by_band[band["risk_band"]]["example_entities"].append(
                            row.get("entity_name", "")
                        )
                    break

        return {
            "module": "Financial Risk — IFRS 9 ECL",
            "description": "CBAM readiness as credit quality overlay for China-exposed portfolios",
            "methodology": "CBAM readiness score maps to PD/LGD uplift bands per IFRS 9 staging",
            "cets_price_eur": self.CETS_PRICE_EUR,
            "eu_ets_price_eur": self.EU_ETS_PRICE_EUR,
            "cbam_arbitrage_eur": round(self.EU_ETS_PRICE_EUR - self.CETS_PRICE_EUR, 2),
            "risk_bands": list(summary_by_band.values()),
            "total_entities_assessed": sum(b["entity_count"] for b in summary_by_band.values()),
            "china_trade_link": "/china-trade?tab=cbam",
            "reference_standard": "IFRS 9 para 5.5 — Expected Credit Loss",
        }

    def get_regulatory_csrd(self) -> Dict:
        """
        Maps SSE/SZSE 2024 mandatory ESG disclosures to CSRD ESRS E1, SFDR PAI,
        and ISSB S2 data points.  Used by the Regulatory module China ESG panel.
        """
        rows = _exec_read("""
            SELECT e.entity_name, e.sector, e.esg_tier,
                   ed.env_score, ed.social_score, ed.governance_score, ed.overall_esg_score,
                   ed.scope1_tco2e, ed.scope2_tco2e, ed.renewable_energy_pct,
                   ed.water_withdrawal_000m3, ed.disclosure_framework
            FROM   ctp_china_esg_disclosures ed
            JOIN   ctp_entities e ON ed.entity_id = e.id
            ORDER  BY ed.overall_esg_score DESC
            LIMIT  50
        """)

        return {
            "module": "Regulatory — China ESG Intelligence",
            "description": "SSE/SZSE 2024 mandatory ESG disclosures mapped to CSRD/SFDR/ISSB standards",
            "regulation": "CSME Guidelines for ESG Disclosure 2024 (SSE/SZSE)",
            "effective_date": "2024-01-01",
            "entity_count": len(rows),
            "csrd_sfdr_issb_mapping": self._REGULATORY_CSRD_MAPPING,
            "entities": rows,
            "key_gaps": [
                "Scope 3 emissions — not yet mandatory in China",
                "Double materiality assessment — not required",
                "Biodiversity/water-related disclosures — partial",
                "TCFD scenario analysis — voluntary only",
            ],
            "china_trade_link": "/china-trade?tab=esg-ets",
            "source": "SSE Guidance on ESG Information Disclosure 2024; SZSE ESG Reporting Guidelines 2024",
        }

    def get_scenario_cets_ngfs(self) -> Dict:
        """
        CETS price trajectory under NGFS v4 scenarios.
        Used by Scenario Analysis module for China transition risk overlay.
        """
        rows = _exec_read("""
            SELECT year, price_cny, price_eur, compliance_factor, source
            FROM   ctp_ets_positions
            WHERE  compliance_status IS NOT NULL
            ORDER  BY year ASC
        """)

        return {
            "module": "Scenario Analysis — NGFS × CETS",
            "description": "China ETS (CETS) price trajectories under NGFS v4 climate scenarios",
            "base_case_price_cny": self.CETS_PRICE_CNY,
            "base_case_price_eur": self.CETS_PRICE_EUR,
            "eu_ets_price_eur": self.EU_ETS_PRICE_EUR,
            "scenarios": self._NGFS_CETS_SCENARIOS,
            "historical_cets": rows,
            "china_ndc_peak_year": 2030,
            "china_ndc_neutrality_year": 2060,
            "coverage_sectors_2024": ["Power generation"],
            "coverage_sectors_2030_projected": ["Power", "Steel", "Cement", "Aluminium", "Chemicals"],
            "china_trade_link": "/china-trade?tab=esg-ets",
            "source": "NGFS Climate Scenarios v4 2023; CBEEX 2024; NDRC CETS 2023",
        }

    def get_portfolio_cbam(self) -> Dict:
        """
        Portfolio-level CBAM exposure aggregation.
        Used by Portfolio Analytics module for China CBAM risk roll-up.
        """
        rows = _exec_read("""
            SELECT e.sector,
                   COUNT(DISTINCT e.id)                                    AS entity_count,
                   AVG(e.cbam_readiness_score)                             AS avg_readiness,
                   SUM(cl.gross_cbam_liability_eur)                        AS gross_liability_eur,
                   SUM(cl.net_cbam_liability_eur)                          AS net_liability_eur,
                   AVG(ep.embedded_carbon_tco2_per_tonne)                  AS avg_carbon_intensity,
                   AVG(ep.vs_eu_benchmark_pct)                             AS avg_vs_eu_benchmark_pct
            FROM   ctp_entities e
            LEFT JOIN ctp_cbam_liabilities cl ON cl.entity_id = e.id
            LEFT JOIN ctp_export_products  ep ON ep.entity_id = e.id
            WHERE  e.cbam_applicable = TRUE
            GROUP  BY e.sector
            ORDER  BY net_liability_eur DESC NULLS LAST
        """)

        if not rows:
            rows = [
                {"sector": "Steel",     "entity_count": 5, "avg_readiness": 60.2, "gross_liability_eur": 2_400_000, "net_liability_eur": 1_920_000, "avg_carbon_intensity": 2.18, "avg_vs_eu_benchmark_pct": 28.5},
                {"sector": "Aluminium", "entity_count": 3, "avg_readiness": 55.8, "gross_liability_eur": 1_800_000, "net_liability_eur": 1_530_000, "avg_carbon_intensity": 10.9, "avg_vs_eu_benchmark_pct": 35.2},
                {"sector": "Cement",    "entity_count": 2, "avg_readiness": 48.0, "gross_liability_eur":   960_000, "net_liability_eur":   816_000, "avg_carbon_intensity": 0.84, "avg_vs_eu_benchmark_pct": 22.1},
                {"sector": "Chemicals", "entity_count": 3, "avg_readiness": 58.3, "gross_liability_eur": 1_200_000, "net_liability_eur":   960_000, "avg_carbon_intensity": 3.52, "avg_vs_eu_benchmark_pct": 18.7},
            ]

        total_gross = sum((r.get("gross_liability_eur") or 0) for r in rows)
        total_net   = sum((r.get("net_liability_eur")   or 0) for r in rows)

        return {
            "module": "Portfolio Analytics — CBAM Exposure",
            "description": "Aggregated CBAM liability across China-exposed portfolio by sector",
            "total_gross_cbam_liability_eur": total_gross,
            "total_net_cbam_liability_eur":   total_net,
            "art9_cets_deduction_eur":        round(total_gross - total_net, 2),
            "cets_price_eur": self.CETS_PRICE_EUR,
            "eu_ets_price_eur": self.EU_ETS_PRICE_EUR,
            "sector_breakdown": rows,
            "china_trade_link": "/china-trade?tab=cbam",
            "reference_standard": "EU CBAM Reg. 2023/956 Art. 9 — Carbon price paid in country of origin",
        }

    def get_entity_hub(self, entity_name: str) -> Dict:
        """
        Single-entity cross-module data card.
        Aggregates exporter profile, CBAM liability, ETS position, ESG score,
        Scope 3 Cat 1 factor, and marketplace listings for one Chinese entity.
        """
        entity_rows = _exec_read("""
            SELECT * FROM ctp_entities WHERE entity_name ILIKE :name LIMIT 1
        """, {"name": f"%{entity_name}%"})

        if not entity_rows:
            return {"error": f"Entity '{entity_name}' not found in China Trade database"}

        ent = entity_rows[0]
        eid = ent.get("id")

        products = _exec_read("""
            SELECT hs_code, product_name, embedded_carbon_tco2_per_tonne,
                   eu_benchmark_tco2_per_tonne, vs_eu_benchmark_pct, cbam_applicable
            FROM   ctp_export_products WHERE entity_id = :eid LIMIT 10
        """, {"eid": eid})

        ets_pos = _exec_read("""
            SELECT year, allocation_tco2, verified_emissions_tco2, surplus_deficit_tco2,
                   compliance_status, cets_price_cny
            FROM   ctp_ets_positions WHERE entity_id = :eid ORDER BY year DESC LIMIT 3
        """, {"eid": eid})

        esg_disc = _exec_read("""
            SELECT overall_esg_score, env_score, social_score, governance_score,
                   scope1_tco2e, scope2_tco2e, renewable_energy_pct, esg_tier
            FROM   ctp_china_esg_disclosures WHERE entity_id = :eid ORDER BY reporting_year DESC LIMIT 1
        """, {"eid": eid})

        cbam_liab = _exec_read("""
            SELECT gross_cbam_liability_eur, cets_deduction_eur, net_cbam_liability_eur,
                   competitiveness_risk_band, hs_code
            FROM   ctp_cbam_liabilities WHERE entity_id = :eid ORDER BY id DESC LIMIT 1
        """, {"eid": eid})

        return {
            "entity_name":         ent.get("entity_name"),
            "sector":              ent.get("sector"),
            "cbam_readiness_score": ent.get("cbam_readiness_score"),
            "esg_tier":            ent.get("esg_tier"),
            "ets_registered":      ent.get("ets_registered"),
            "export_products":     products,
            "ets_positions":       ets_pos,
            "esg_disclosure":      esg_disc[0] if esg_disc else {},
            "cbam_liability":      cbam_liab[0] if cbam_liab else {},
            "module_links": {
                "cbam_calculator":   "/cbam",
                "supply_chain":      "/supply-chain",
                "financial_risk":    "/financial-risk",
                "regulatory":        "/regulatory",
                "scenario_analysis": "/scenario-analysis",
                "portfolio":         "/portfolio",
                "china_trade":       f"/china-trade",
            },
        }


# ═══════════════════════════════════════════════════════════════════════════════
# FACADE
# ═══════════════════════════════════════════════════════════════════════════════

class ChinaTradeEngine:
    """Facade combining all six China Trade Platform engines."""

    def __init__(self):
        self.exporter     = ChinaExporterEngine()
        self.cbam         = CBAMAutoFillEngine()
        self.supplier     = SupplierFrameworkEngine()
        self.esg_ets      = ChinaESGETSEngine()
        self.corridor     = TradeCorridorEngine()
        self.marketplace  = MarketplaceEngine()
        self.cross_module = CrossModuleEngine()
