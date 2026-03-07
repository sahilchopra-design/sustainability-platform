"""
GDELT BigQuery connector + controversy scoring ingester.

Fetches events from the GDELT Project (Global Database of Events, Language,
and Tone) via the GDELT 2.0 DOC API / BigQuery public dataset, then computes
entity-level controversy scores for ESG screening.

Falls back to curated sample data when BigQuery / GDELT API is unavailable.

Source ID: gdelt-events
Tables loaded: dh_gdelt_events, dh_gdelt_gkg, dh_controversy_scores

BigQuery dataset (when available):
  gdelt-bq.gdeltv2.events        — 300M+ event records
  gdelt-bq.gdeltv2.gkg           — Global Knowledge Graph
"""

from __future__ import annotations

import hashlib
import logging
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from ingestion.base_ingester import BaseIngester, IngestionResult

logger = logging.getLogger(__name__)


def _uuid5(namespace: str, *parts) -> str:
    key = "|".join(str(p) for p in parts)
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"{namespace}:{key}"))


# ── CAMEO event code mapping ──────────────────────────────────────────────────
CAMEO_ROOT_CODES = {
    "01": "Make public statement",
    "02": "Appeal",
    "03": "Express intent to cooperate",
    "04": "Consult",
    "05": "Engage in diplomatic cooperation",
    "06": "Engage in material cooperation",
    "07": "Provide aid",
    "08": "Yield",
    "09": "Investigate",
    "10": "Demand",
    "11": "Disapprove",
    "12": "Reject",
    "13": "Threaten",
    "14": "Protest",
    "15": "Exhibit military posture",
    "16": "Reduce relations",
    "17": "Coerce",
    "18": "Assault",
    "19": "Fight",
    "20": "Engage in unconventional mass violence",
}

# ESG-relevant GDELT themes for controversy detection
ESG_THEMES = {
    "E": [
        "ENV_OIL", "ENV_SPILL", "ENV_DEFORESTATION", "ENV_POLLUTION",
        "ENV_CLIMATECHANGE", "ENV_COAL", "ENV_MINING", "ENV_WATER",
        "ENV_NUCLEAR", "ENV_TOXIC", "ENV_EMISSIONS", "ENV_BIODIVERSITY",
    ],
    "S": [
        "HUMAN_RIGHTS", "LABOR", "FORCED_LABOR", "CHILD_LABOR",
        "DISCRIMINATION", "HEALTH_PANDEMIC", "PROTEST", "CORRUPTION",
        "CRIME_FRAUD", "TAX_EVASION", "PRIVACY", "DATA_BREACH",
    ],
    "G": [
        "CORRUPTION", "BRIBERY", "FRAUD", "TAX_EVASION", "SANCTIONS",
        "REGULATORY", "ANTITRUST", "MONEY_LAUNDERING", "INSIDER_TRADING",
    ],
}


# ── Sample events data ────────────────────────────────────────────────────────

def _generate_sample_events() -> List[Dict]:
    """Curated GDELT-style events for major ESG-relevant corporate incidents."""
    events = [
        # Environmental events
        {
            "global_event_id": "GE20230415001", "event_date": "2023-04-15",
            "actor1_name": "TOTALENERGIES", "actor1_country": "FRA", "actor1_type": "COP",
            "actor2_name": "MOZAMBIQUE_GOVERNMENT", "actor2_country": "MOZ", "actor2_type": "GOV",
            "event_code": "14", "event_base_code": "140", "event_root_code": "14",
            "quad_class": 3, "goldstein_scale": -6.5,
            "num_mentions": 245, "num_sources": 87, "num_articles": 312,
            "avg_tone": -4.82,
            "action_geo_country": "MOZ", "action_geo_name": "Cabo Delgado, Mozambique",
            "action_geo_lat": -12.25, "action_geo_lon": 40.17,
            "matched_entity_name": "TotalEnergies SE",
        },
        {
            "global_event_id": "GE20230622002", "event_date": "2023-06-22",
            "actor1_name": "SHELL", "actor1_country": "GBR", "actor1_type": "COP",
            "actor2_name": "NIGERIAN_COMMUNITIES", "actor2_country": "NGA", "actor2_type": "CVL",
            "event_code": "11", "event_base_code": "112", "event_root_code": "11",
            "quad_class": 3, "goldstein_scale": -5.0,
            "num_mentions": 189, "num_sources": 63, "num_articles": 198,
            "avg_tone": -5.14,
            "action_geo_country": "NGA", "action_geo_name": "Niger Delta, Nigeria",
            "action_geo_lat": 5.32, "action_geo_lon": 6.45,
            "matched_entity_name": "Shell plc",
        },
        {
            "global_event_id": "GE20230801003", "event_date": "2023-08-01",
            "actor1_name": "VALE", "actor1_country": "BRA", "actor1_type": "COP",
            "actor2_name": "BRAZIL_ENVIRONMENT_AGENCY", "actor2_country": "BRA", "actor2_type": "GOV",
            "event_code": "12", "event_base_code": "122", "event_root_code": "12",
            "quad_class": 3, "goldstein_scale": -4.0,
            "num_mentions": 156, "num_sources": 48, "num_articles": 172,
            "avg_tone": -3.67,
            "action_geo_country": "BRA", "action_geo_name": "Para, Brazil",
            "action_geo_lat": -6.0, "action_geo_lon": -50.27,
            "matched_entity_name": "Vale S.A.",
        },
        # Social events
        {
            "global_event_id": "GE20230315004", "event_date": "2023-03-15",
            "actor1_name": "AMAZON", "actor1_country": "USA", "actor1_type": "COP",
            "actor2_name": "LABOR_UNIONS", "actor2_country": "USA", "actor2_type": "LAB",
            "event_code": "14", "event_base_code": "141", "event_root_code": "14",
            "quad_class": 3, "goldstein_scale": -5.5,
            "num_mentions": 412, "num_sources": 156, "num_articles": 534,
            "avg_tone": -3.92,
            "action_geo_country": "USA", "action_geo_name": "Staten Island, New York, USA",
            "action_geo_lat": 40.58, "action_geo_lon": -74.15,
            "matched_entity_name": "Amazon.com Inc",
        },
        {
            "global_event_id": "GE20230910005", "event_date": "2023-09-10",
            "actor1_name": "META_PLATFORMS", "actor1_country": "USA", "actor1_type": "COP",
            "actor2_name": "EU_REGULATORS", "actor2_country": "EUR", "actor2_type": "GOV",
            "event_code": "12", "event_base_code": "121", "event_root_code": "12",
            "quad_class": 3, "goldstein_scale": -4.5,
            "num_mentions": 367, "num_sources": 132, "num_articles": 445,
            "avg_tone": -4.21,
            "action_geo_country": "IRL", "action_geo_name": "Dublin, Ireland",
            "action_geo_lat": 53.35, "action_geo_lon": -6.26,
            "matched_entity_name": "Meta Platforms Inc",
        },
        {
            "global_event_id": "GE20231105006", "event_date": "2023-11-05",
            "actor1_name": "NIKE", "actor1_country": "USA", "actor1_type": "COP",
            "actor2_name": "UYGHUR_ADVOCACY", "actor2_country": "CHN", "actor2_type": "CVL",
            "event_code": "11", "event_base_code": "111", "event_root_code": "11",
            "quad_class": 3, "goldstein_scale": -5.0,
            "num_mentions": 198, "num_sources": 72, "num_articles": 231,
            "avg_tone": -5.33,
            "action_geo_country": "CHN", "action_geo_name": "Xinjiang, China",
            "action_geo_lat": 41.75, "action_geo_lon": 87.62,
            "matched_entity_name": "Nike Inc",
        },
        # Governance events
        {
            "global_event_id": "GE20230205007", "event_date": "2023-02-05",
            "actor1_name": "ADANI_GROUP", "actor1_country": "IND", "actor1_type": "COP",
            "actor2_name": "HINDENBURG_RESEARCH", "actor2_country": "USA", "actor2_type": "MNC",
            "event_code": "11", "event_base_code": "113", "event_root_code": "11",
            "quad_class": 3, "goldstein_scale": -7.0,
            "num_mentions": 823, "num_sources": 298, "num_articles": 1245,
            "avg_tone": -6.15,
            "action_geo_country": "IND", "action_geo_name": "Mumbai, India",
            "action_geo_lat": 19.08, "action_geo_lon": 72.88,
            "matched_entity_name": "Adani Enterprises Limited",
        },
        {
            "global_event_id": "GE20230718008", "event_date": "2023-07-18",
            "actor1_name": "CREDIT_SUISSE", "actor1_country": "CHE", "actor1_type": "COP",
            "actor2_name": "SWISS_FINMA", "actor2_country": "CHE", "actor2_type": "GOV",
            "event_code": "09", "event_base_code": "091", "event_root_code": "09",
            "quad_class": 3, "goldstein_scale": -3.5,
            "num_mentions": 534, "num_sources": 201, "num_articles": 678,
            "avg_tone": -4.56,
            "action_geo_country": "CHE", "action_geo_name": "Zurich, Switzerland",
            "action_geo_lat": 47.37, "action_geo_lon": 8.54,
            "matched_entity_name": "Credit Suisse Group AG",
        },
        # Positive/cooperative events
        {
            "global_event_id": "GE20231201009", "event_date": "2023-12-01",
            "actor1_name": "ORSTED", "actor1_country": "DNK", "actor1_type": "COP",
            "actor2_name": "DENMARK_GOVERNMENT", "actor2_country": "DNK", "actor2_type": "GOV",
            "event_code": "06", "event_base_code": "061", "event_root_code": "06",
            "quad_class": 2, "goldstein_scale": 6.0,
            "num_mentions": 145, "num_sources": 54, "num_articles": 167,
            "avg_tone": 3.45,
            "action_geo_country": "DNK", "action_geo_name": "Esbjerg, Denmark",
            "action_geo_lat": 55.47, "action_geo_lon": 8.45,
            "matched_entity_name": "Orsted A/S",
        },
        {
            "global_event_id": "GE20230520010", "event_date": "2023-05-20",
            "actor1_name": "MICROSOFT", "actor1_country": "USA", "actor1_type": "COP",
            "actor2_name": "CLIMATE_FUND", "actor2_country": "USA", "actor2_type": "NGO",
            "event_code": "07", "event_base_code": "072", "event_root_code": "07",
            "quad_class": 2, "goldstein_scale": 7.0,
            "num_mentions": 234, "num_sources": 89, "num_articles": 289,
            "avg_tone": 4.12,
            "action_geo_country": "USA", "action_geo_name": "Redmond, Washington, USA",
            "action_geo_lat": 47.67, "action_geo_lon": -122.12,
            "matched_entity_name": "Microsoft Corporation",
        },
        # Additional conflict events
        {
            "global_event_id": "GE20230901011", "event_date": "2023-09-01",
            "actor1_name": "GLENCORE", "actor1_country": "CHE", "actor1_type": "COP",
            "actor2_name": "UK_SFO", "actor2_country": "GBR", "actor2_type": "GOV",
            "event_code": "17", "event_base_code": "173", "event_root_code": "17",
            "quad_class": 4, "goldstein_scale": -7.0,
            "num_mentions": 312, "num_sources": 118, "num_articles": 387,
            "avg_tone": -5.78,
            "action_geo_country": "GBR", "action_geo_name": "London, United Kingdom",
            "action_geo_lat": 51.51, "action_geo_lon": -0.13,
            "matched_entity_name": "Glencore plc",
        },
        {
            "global_event_id": "GE20231015012", "event_date": "2023-10-15",
            "actor1_name": "VOLKSWAGEN", "actor1_country": "DEU", "actor1_type": "COP",
            "actor2_name": "GERMAN_PROSECUTORS", "actor2_country": "DEU", "actor2_type": "GOV",
            "event_code": "09", "event_base_code": "091", "event_root_code": "09",
            "quad_class": 3, "goldstein_scale": -4.0,
            "num_mentions": 267, "num_sources": 95, "num_articles": 312,
            "avg_tone": -3.89,
            "action_geo_country": "DEU", "action_geo_name": "Wolfsburg, Germany",
            "action_geo_lat": 52.42, "action_geo_lon": 10.78,
            "matched_entity_name": "Volkswagen AG",
        },
        {
            "global_event_id": "GE20230412013", "event_date": "2023-04-12",
            "actor1_name": "BP", "actor1_country": "GBR", "actor1_type": "COP",
            "actor2_name": "ENVIRONMENTAL_NGO", "actor2_country": "GBR", "actor2_type": "NGO",
            "event_code": "14", "event_base_code": "143", "event_root_code": "14",
            "quad_class": 3, "goldstein_scale": -5.0,
            "num_mentions": 178, "num_sources": 67, "num_articles": 201,
            "avg_tone": -4.45,
            "action_geo_country": "GBR", "action_geo_name": "London, United Kingdom",
            "action_geo_lat": 51.51, "action_geo_lon": -0.13,
            "matched_entity_name": "BP plc",
        },
        {
            "global_event_id": "GE20230630014", "event_date": "2023-06-30",
            "actor1_name": "EXXONMOBIL", "actor1_country": "USA", "actor1_type": "COP",
            "actor2_name": "US_SEC", "actor2_country": "USA", "actor2_type": "GOV",
            "event_code": "09", "event_base_code": "093", "event_root_code": "09",
            "quad_class": 3, "goldstein_scale": -3.0,
            "num_mentions": 289, "num_sources": 104, "num_articles": 356,
            "avg_tone": -3.21,
            "action_geo_country": "USA", "action_geo_name": "Washington D.C., USA",
            "action_geo_lat": 38.90, "action_geo_lon": -77.04,
            "matched_entity_name": "Exxon Mobil Corporation",
        },
        {
            "global_event_id": "GE20231120015", "event_date": "2023-11-20",
            "actor1_name": "RIO_TINTO", "actor1_country": "AUS", "actor1_type": "COP",
            "actor2_name": "INDIGENOUS_COMMUNITIES", "actor2_country": "AUS", "actor2_type": "CVL",
            "event_code": "11", "event_base_code": "111", "event_root_code": "11",
            "quad_class": 3, "goldstein_scale": -6.0,
            "num_mentions": 201, "num_sources": 75, "num_articles": 245,
            "avg_tone": -5.67,
            "action_geo_country": "AUS", "action_geo_name": "Western Australia",
            "action_geo_lat": -26.0, "action_geo_lon": 121.0,
            "matched_entity_name": "Rio Tinto Group",
        },
    ]
    return events


def _generate_sample_gkg() -> List[Dict]:
    """Curated GDELT GKG-style records for controversy detection."""
    records = [
        {
            "gkg_record_id": "GKG20230415001", "publish_date": "2023-04-15T08:30:00Z",
            "source_name": "Reuters", "document_tone": -4.82,
            "positive_score": 1.2, "negative_score": 6.0, "polarity": 7.2,
            "themes": "ENV_OIL;PROTEST;ENV_CLIMATECHANGE;HUMAN_RIGHTS",
            "organizations": "TotalEnergies;Mozambique LNG",
            "esg_relevance_score": 0.92, "esg_category": "E",
            "controversy_flag": True, "matched_entity_name": "TotalEnergies SE",
        },
        {
            "gkg_record_id": "GKG20230315002", "publish_date": "2023-03-15T14:00:00Z",
            "source_name": "The Guardian", "document_tone": -3.92,
            "positive_score": 1.8, "negative_score": 5.7, "polarity": 7.5,
            "themes": "LABOR;PROTEST;HUMAN_RIGHTS;DISCRIMINATION",
            "organizations": "Amazon;Amazon Labor Union",
            "esg_relevance_score": 0.88, "esg_category": "S",
            "controversy_flag": True, "matched_entity_name": "Amazon.com Inc",
        },
        {
            "gkg_record_id": "GKG20230205003", "publish_date": "2023-02-05T06:00:00Z",
            "source_name": "Financial Times", "document_tone": -6.15,
            "positive_score": 0.5, "negative_score": 6.65, "polarity": 7.15,
            "themes": "FRAUD;CORRUPTION;REGULATORY;SANCTIONS",
            "organizations": "Adani Group;Hindenburg Research",
            "esg_relevance_score": 0.95, "esg_category": "G",
            "controversy_flag": True, "matched_entity_name": "Adani Enterprises Limited",
        },
        {
            "gkg_record_id": "GKG20230910004", "publish_date": "2023-09-10T10:00:00Z",
            "source_name": "Bloomberg", "document_tone": -4.21,
            "positive_score": 1.5, "negative_score": 5.7, "polarity": 7.2,
            "themes": "PRIVACY;DATA_BREACH;REGULATORY;ANTITRUST",
            "organizations": "Meta Platforms;EU Commission;DPC Ireland",
            "esg_relevance_score": 0.85, "esg_category": "G",
            "controversy_flag": True, "matched_entity_name": "Meta Platforms Inc",
        },
        {
            "gkg_record_id": "GKG20230901005", "publish_date": "2023-09-01T16:00:00Z",
            "source_name": "BBC News", "document_tone": -5.78,
            "positive_score": 0.8, "negative_score": 6.58, "polarity": 7.38,
            "themes": "BRIBERY;CORRUPTION;MONEY_LAUNDERING;ENV_MINING",
            "organizations": "Glencore;UK Serious Fraud Office",
            "esg_relevance_score": 0.94, "esg_category": "G",
            "controversy_flag": True, "matched_entity_name": "Glencore plc",
        },
        {
            "gkg_record_id": "GKG20231201006", "publish_date": "2023-12-01T09:00:00Z",
            "source_name": "Clean Energy Wire", "document_tone": 3.45,
            "positive_score": 4.9, "negative_score": 1.45, "polarity": 6.35,
            "themes": "ENV_CLIMATECHANGE;RENEWABLE_ENERGY;ENV_WIND",
            "organizations": "Orsted;Danish Government",
            "esg_relevance_score": 0.72, "esg_category": "E",
            "controversy_flag": False, "matched_entity_name": "Orsted A/S",
        },
        {
            "gkg_record_id": "GKG20230520007", "publish_date": "2023-05-20T12:00:00Z",
            "source_name": "TechCrunch", "document_tone": 4.12,
            "positive_score": 5.3, "negative_score": 1.18, "polarity": 6.48,
            "themes": "ENV_CLIMATECHANGE;CARBON_CAPTURE;RENEWABLE_ENERGY",
            "organizations": "Microsoft;Breakthrough Energy;Climate Fund",
            "esg_relevance_score": 0.68, "esg_category": "E",
            "controversy_flag": False, "matched_entity_name": "Microsoft Corporation",
        },
        {
            "gkg_record_id": "GKG20231105008", "publish_date": "2023-11-05T11:00:00Z",
            "source_name": "Associated Press", "document_tone": -5.33,
            "positive_score": 0.9, "negative_score": 6.23, "polarity": 7.13,
            "themes": "FORCED_LABOR;HUMAN_RIGHTS;CHILD_LABOR;DISCRIMINATION",
            "organizations": "Nike;Uyghur Human Rights Project",
            "esg_relevance_score": 0.91, "esg_category": "S",
            "controversy_flag": True, "matched_entity_name": "Nike Inc",
        },
        {
            "gkg_record_id": "GKG20231120009", "publish_date": "2023-11-20T07:00:00Z",
            "source_name": "Sydney Morning Herald", "document_tone": -5.67,
            "positive_score": 0.7, "negative_score": 6.37, "polarity": 7.07,
            "themes": "HUMAN_RIGHTS;ENV_MINING;INDIGENOUS_RIGHTS;ENV_BIODIVERSITY",
            "organizations": "Rio Tinto;Traditional Owners Alliance",
            "esg_relevance_score": 0.90, "esg_category": "S",
            "controversy_flag": True, "matched_entity_name": "Rio Tinto Group",
        },
        {
            "gkg_record_id": "GKG20230622010", "publish_date": "2023-06-22T15:00:00Z",
            "source_name": "Al Jazeera", "document_tone": -5.14,
            "positive_score": 0.6, "negative_score": 5.74, "polarity": 6.34,
            "themes": "ENV_OIL;ENV_POLLUTION;ENV_SPILL;HUMAN_RIGHTS",
            "organizations": "Shell;MOSOP;Niger Delta",
            "esg_relevance_score": 0.93, "esg_category": "E",
            "controversy_flag": True, "matched_entity_name": "Shell plc",
        },
    ]
    return records


# ── Controversy score computation ─────────────────────────────────────────────

def _compute_controversy_scores(events: List[Dict], gkg: List[Dict]) -> List[Dict]:
    """Aggregate events + GKG into per-entity controversy scores."""
    from collections import defaultdict
    import statistics

    entity_data = defaultdict(lambda: {
        "events": [], "gkg": [], "tones": [], "goldsteins": [],
        "mentions": 0, "negative": 0, "positive": 0,
        "env_flags": 0, "social_flags": 0, "gov_flags": 0,
    })

    # Accumulate events
    for ev in events:
        name = ev.get("matched_entity_name")
        if not name:
            continue
        bucket = entity_data[name]
        bucket["events"].append(ev)
        tone = ev.get("avg_tone", 0)
        bucket["tones"].append(tone)
        bucket["goldsteins"].append(ev.get("goldstein_scale", 0))
        bucket["mentions"] += ev.get("num_mentions", 0)
        if ev.get("quad_class", 0) >= 3:
            bucket["negative"] += 1
        else:
            bucket["positive"] += 1

    # Accumulate GKG
    for gkg_rec in gkg:
        name = gkg_rec.get("matched_entity_name")
        if not name:
            continue
        bucket = entity_data[name]
        bucket["gkg"].append(gkg_rec)
        cat = gkg_rec.get("esg_category")
        if gkg_rec.get("controversy_flag"):
            if cat == "E":
                bucket["env_flags"] += 1
            elif cat == "S":
                bucket["social_flags"] += 1
            elif cat == "G":
                bucket["gov_flags"] += 1

    scores = []
    period_start = date(2023, 1, 1)
    period_end = date(2023, 12, 31)

    for entity_name, data in entity_data.items():
        total = len(data["events"])
        neg = data["negative"]
        pos = data["positive"]
        avg_tone = statistics.mean(data["tones"]) if data["tones"] else 0
        avg_gold = statistics.mean(data["goldsteins"]) if data["goldsteins"] else 0

        # Composite score: 0-100 based on negative ratio, tone severity, event volume
        neg_ratio = neg / max(total, 1)
        tone_severity = max(0, min(1, abs(avg_tone) / 10))
        volume_factor = min(1, data["mentions"] / 1000)
        raw_score = (neg_ratio * 40) + (tone_severity * 35) + (volume_factor * 25)
        controversy_score = round(min(100, max(0, raw_score * 100 / 100)), 1)

        # ESG breakdown
        total_flags = data["env_flags"] + data["social_flags"] + data["gov_flags"]
        env_score = round((data["env_flags"] / max(total_flags, 1)) * controversy_score, 1)
        social_score = round((data["social_flags"] / max(total_flags, 1)) * controversy_score, 1)
        gov_score = round((data["gov_flags"] / max(total_flags, 1)) * controversy_score, 1)

        # Severity
        if controversy_score >= 75:
            severity = "Critical"
        elif controversy_score >= 50:
            severity = "High"
        elif controversy_score >= 25:
            severity = "Medium"
        else:
            severity = "Low"

        # Top themes from GKG
        all_themes = []
        for g in data["gkg"]:
            if g.get("themes"):
                all_themes.extend(g["themes"].split(";"))
        theme_counts = defaultdict(int)
        for t in all_themes:
            theme_counts[t.strip()] += 1
        top_themes = ",".join(
            k for k, _ in sorted(theme_counts.items(), key=lambda x: -x[1])[:5]
        )

        # Guess sector from events
        first_ev = data["events"][0] if data["events"] else {}

        scores.append({
            "entity_name": entity_name,
            "country_iso3": first_ev.get("actor1_country", ""),
            "sector": _guess_sector(entity_name),
            "period_start": str(period_start),
            "period_end": str(period_end),
            "controversy_score": controversy_score,
            "severity_level": severity,
            "trend": "Stable",
            "env_score": env_score,
            "social_score": social_score,
            "governance_score": gov_score,
            "total_events": total,
            "negative_events": neg,
            "positive_events": pos,
            "avg_tone": round(avg_tone, 4),
            "avg_goldstein": round(avg_gold, 2),
            "media_mentions": data["mentions"],
            "top_themes": top_themes,
        })

    return scores


def _guess_sector(name: str) -> str:
    """Simple sector mapping for known sample entities."""
    mapping = {
        "TotalEnergies SE": "Energy",
        "Shell plc": "Energy",
        "BP plc": "Energy",
        "Exxon Mobil Corporation": "Energy",
        "Vale S.A.": "Mining",
        "Rio Tinto Group": "Mining",
        "Glencore plc": "Mining",
        "Amazon.com Inc": "Technology",
        "Meta Platforms Inc": "Technology",
        "Microsoft Corporation": "Technology",
        "Nike Inc": "Consumer Goods",
        "Adani Enterprises Limited": "Conglomerate",
        "Credit Suisse Group AG": "Financial Services",
        "Volkswagen AG": "Automotive",
        "Orsted A/S": "Energy",
    }
    return mapping.get(name, "Unknown")


# ── Ingester class ────────────────────────────────────────────────────────────

class GdeltIngester(BaseIngester):
    """
    GDELT BigQuery connector with fallback to curated sample data.

    When BigQuery credentials are available, queries the GDELT v2 public
    dataset for recent ESG-relevant events. Otherwise falls back to
    curated sample data covering major corporate controversies.
    """

    source_id = "gdelt-events"
    display_name = "GDELT Event Database"
    default_schedule = "daily"

    def fetch(self, db: Session) -> List[Dict]:
        """Try BigQuery first, fall back to sample data."""
        try:
            return self._fetch_bigquery()
        except Exception as e:
            logger.info(f"BigQuery not available ({e}); using sample data")
            return self._fetch_sample()

    def _fetch_bigquery(self) -> List[Dict]:
        """Query GDELT v2 via BigQuery public dataset."""
        try:
            from google.cloud import bigquery
        except ImportError:
            raise RuntimeError("google-cloud-bigquery not installed")

        client = bigquery.Client()
        # Query recent events with ESG-relevant CAMEO codes
        query = """
        SELECT
            CAST(GLOBALEVENTID AS STRING) AS global_event_id,
            PARSE_DATE('%Y%m%d', CAST(SQLDATE AS STRING)) AS event_date,
            Year AS year, MonthYear AS month,
            Actor1Name AS actor1_name, Actor1CountryCode AS actor1_country,
            Actor1Type1Code AS actor1_type,
            Actor2Name AS actor2_name, Actor2CountryCode AS actor2_country,
            Actor2Type1Code AS actor2_type,
            EventCode AS event_code, EventBaseCode AS event_base_code,
            EventRootCode AS event_root_code,
            QuadClass AS quad_class, GoldsteinScale AS goldstein_scale,
            NumMentions AS num_mentions, NumSources AS num_sources,
            NumArticles AS num_articles, AvgTone AS avg_tone,
            ActionGeo_CountryCode AS action_geo_country,
            ActionGeo_Lat AS action_geo_lat, ActionGeo_Long AS action_geo_lon,
            ActionGeo_FullName AS action_geo_name,
            SOURCEURL AS source_url, DATEADDED AS date_added
        FROM `gdelt-bq.gdeltv2.events`
        WHERE Year >= 2023
          AND QuadClass IN (3, 4)
          AND NumMentions >= 50
          AND (Actor1Type1Code = 'COP' OR Actor2Type1Code = 'COP')
        ORDER BY NumMentions DESC
        LIMIT 500
        """
        result = client.query(query).result()
        rows = []
        for row in result:
            rows.append(dict(row))
        return rows

    def _fetch_sample(self) -> List[Dict]:
        """Return curated sample events + GKG data."""
        events = _generate_sample_events()
        gkg = _generate_sample_gkg()
        return [{"_type": "events", "data": events}, {"_type": "gkg", "data": gkg}]

    def validate(self, raw_data: List[Dict]) -> List[Dict]:
        """Pass through — sample data is pre-validated."""
        return raw_data

    def transform(self, validated: List[Dict]) -> List[Dict]:
        """Transform into load-ready rows for all three tables."""
        rows = []

        # Check if this is sample data (has _type keys) or BigQuery rows
        if validated and isinstance(validated[0], dict) and "_type" in validated[0]:
            events_raw = []
            gkg_raw = []
            for item in validated:
                if item["_type"] == "events":
                    events_raw = item["data"]
                elif item["_type"] == "gkg":
                    gkg_raw = item["data"]

            # Transform events
            for ev in events_raw:
                rows.append({
                    "_table": "dh_gdelt_events",
                    "id": _uuid5("gdelt-event", ev["global_event_id"]),
                    "global_event_id": ev["global_event_id"],
                    "event_date": ev["event_date"],
                    "year": int(ev["event_date"][:4]),
                    "month": int(ev["event_date"][5:7]),
                    "actor1_name": ev.get("actor1_name"),
                    "actor1_country": ev.get("actor1_country"),
                    "actor1_type": ev.get("actor1_type"),
                    "actor2_name": ev.get("actor2_name"),
                    "actor2_country": ev.get("actor2_country"),
                    "actor2_type": ev.get("actor2_type"),
                    "event_code": ev.get("event_code"),
                    "event_base_code": ev.get("event_base_code"),
                    "event_root_code": ev.get("event_root_code"),
                    "quad_class": ev.get("quad_class"),
                    "goldstein_scale": ev.get("goldstein_scale"),
                    "num_mentions": ev.get("num_mentions"),
                    "num_sources": ev.get("num_sources"),
                    "num_articles": ev.get("num_articles"),
                    "avg_tone": ev.get("avg_tone"),
                    "action_geo_country": ev.get("action_geo_country"),
                    "action_geo_lat": ev.get("action_geo_lat"),
                    "action_geo_lon": ev.get("action_geo_lon"),
                    "action_geo_name": ev.get("action_geo_name"),
                    "matched_entity_name": ev.get("matched_entity_name"),
                })

            # Transform GKG
            for g in gkg_raw:
                rows.append({
                    "_table": "dh_gdelt_gkg",
                    "id": _uuid5("gdelt-gkg", g["gkg_record_id"]),
                    "gkg_record_id": g["gkg_record_id"],
                    "publish_date": g.get("publish_date"),
                    "source_name": g.get("source_name"),
                    "document_tone": g.get("document_tone"),
                    "positive_score": g.get("positive_score"),
                    "negative_score": g.get("negative_score"),
                    "polarity": g.get("polarity"),
                    "themes": g.get("themes"),
                    "organizations": g.get("organizations"),
                    "esg_relevance_score": g.get("esg_relevance_score"),
                    "esg_category": g.get("esg_category"),
                    "controversy_flag": g.get("controversy_flag", False),
                    "matched_entity_name": g.get("matched_entity_name"),
                })

            # Compute and transform controversy scores
            scores = _compute_controversy_scores(events_raw, gkg_raw)
            for sc in scores:
                rows.append({
                    "_table": "dh_controversy_scores",
                    "id": _uuid5("controversy", sc["entity_name"], sc["period_start"], sc["period_end"]),
                    **sc,
                })
        else:
            # BigQuery rows — just events (no GKG in this path)
            for ev in validated:
                rows.append({
                    "_table": "dh_gdelt_events",
                    "id": _uuid5("gdelt-event", ev.get("global_event_id", "")),
                    **ev,
                })

        return rows

    def load(self, db: Session, transformed: List[Dict]) -> Dict:
        """Upsert into dh_gdelt_events, dh_gdelt_gkg, dh_controversy_scores."""
        stats = {"inserted": 0, "updated": 0, "skipped": 0, "failed": 0}

        events = [r for r in transformed if r.get("_table") == "dh_gdelt_events"]
        gkg = [r for r in transformed if r.get("_table") == "dh_gdelt_gkg"]
        scores = [r for r in transformed if r.get("_table") == "dh_controversy_scores"]

        # Load events
        for row in events:
            try:
                r = {k: v for k, v in row.items() if k != "_table"}
                db.execute(text("""
                    INSERT INTO dh_gdelt_events (
                        id, global_event_id, event_date, year, month,
                        actor1_name, actor1_country, actor1_type,
                        actor2_name, actor2_country, actor2_type,
                        event_code, event_base_code, event_root_code,
                        quad_class, goldstein_scale,
                        num_mentions, num_sources, num_articles, avg_tone,
                        action_geo_country, action_geo_lat, action_geo_lon, action_geo_name,
                        matched_entity_name
                    ) VALUES (
                        :id, :global_event_id, :event_date, :year, :month,
                        :actor1_name, :actor1_country, :actor1_type,
                        :actor2_name, :actor2_country, :actor2_type,
                        :event_code, :event_base_code, :event_root_code,
                        :quad_class, :goldstein_scale,
                        :num_mentions, :num_sources, :num_articles, :avg_tone,
                        :action_geo_country, :action_geo_lat, :action_geo_lon, :action_geo_name,
                        :matched_entity_name
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        num_mentions = EXCLUDED.num_mentions,
                        num_sources = EXCLUDED.num_sources,
                        num_articles = EXCLUDED.num_articles,
                        avg_tone = EXCLUDED.avg_tone,
                        updated_at = now()
                """), r)
                stats["inserted"] += 1
            except Exception as e:
                logger.warning(f"Event load error: {e}")
                stats["failed"] += 1

        # Load GKG
        for row in gkg:
            try:
                r = {k: v for k, v in row.items() if k != "_table"}
                db.execute(text("""
                    INSERT INTO dh_gdelt_gkg (
                        id, gkg_record_id, publish_date, source_name,
                        document_tone, positive_score, negative_score, polarity,
                        themes, organizations,
                        esg_relevance_score, esg_category, controversy_flag,
                        matched_entity_name
                    ) VALUES (
                        :id, :gkg_record_id, :publish_date, :source_name,
                        :document_tone, :positive_score, :negative_score, :polarity,
                        :themes, :organizations,
                        :esg_relevance_score, :esg_category, :controversy_flag,
                        :matched_entity_name
                    )
                    ON CONFLICT (id) DO UPDATE SET
                        document_tone = EXCLUDED.document_tone,
                        esg_relevance_score = EXCLUDED.esg_relevance_score,
                        controversy_flag = EXCLUDED.controversy_flag,
                        updated_at = now()
                """), r)
                stats["inserted"] += 1
            except Exception as e:
                logger.warning(f"GKG load error: {e}")
                stats["failed"] += 1

        # Load controversy scores
        for row in scores:
            try:
                r = {k: v for k, v in row.items() if k != "_table"}
                db.execute(text("""
                    INSERT INTO dh_controversy_scores (
                        id, entity_name, country_iso3, sector,
                        period_start, period_end,
                        controversy_score, severity_level, trend,
                        env_score, social_score, governance_score,
                        total_events, negative_events, positive_events,
                        avg_tone, avg_goldstein, media_mentions, top_themes
                    ) VALUES (
                        :id, :entity_name, :country_iso3, :sector,
                        :period_start, :period_end,
                        :controversy_score, :severity_level, :trend,
                        :env_score, :social_score, :governance_score,
                        :total_events, :negative_events, :positive_events,
                        :avg_tone, :avg_goldstein, :media_mentions, :top_themes
                    )
                    ON CONFLICT (entity_name, period_start, period_end) DO UPDATE SET
                        controversy_score = EXCLUDED.controversy_score,
                        severity_level = EXCLUDED.severity_level,
                        env_score = EXCLUDED.env_score,
                        social_score = EXCLUDED.social_score,
                        governance_score = EXCLUDED.governance_score,
                        total_events = EXCLUDED.total_events,
                        negative_events = EXCLUDED.negative_events,
                        positive_events = EXCLUDED.positive_events,
                        avg_tone = EXCLUDED.avg_tone,
                        avg_goldstein = EXCLUDED.avg_goldstein,
                        media_mentions = EXCLUDED.media_mentions,
                        top_themes = EXCLUDED.top_themes,
                        updated_at = now()
                """), r)
                stats["inserted"] += 1
            except Exception as e:
                logger.warning(f"Controversy score load error: {e}")
                stats["failed"] += 1

        db.commit()
        return stats
