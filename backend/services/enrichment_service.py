"""Enrichment service for uploaded data"""
import pandas as pd
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session


class EnrichmentService:
    """Service for enriching uploaded portfolio data"""
    
    # Default values based on sector
    SECTOR_DEFAULTS = {
        "Power Generation": {
            "base_pd": 0.025,
            "base_lgd": 0.40,
            "emissions_intensity": 1.2
        },
        "Oil & Gas": {
            "base_pd": 0.030,
            "base_lgd": 0.45,
            "emissions_intensity": 1.5
        },
        "Metals & Mining": {
            "base_pd": 0.035,
            "base_lgd": 0.50,
            "emissions_intensity": 1.0
        },
        "Automotive": {
            "base_pd": 0.020,
            "base_lgd": 0.42,
            "emissions_intensity": 0.8
        },
        "Airlines": {
            "base_pd": 0.040,
            "base_lgd": 0.55,
            "emissions_intensity": 1.3
        },
        "Real Estate": {
            "base_pd": 0.015,
            "base_lgd": 0.35,
            "emissions_intensity": 0.4
        }
    }
    
    # Rating to PD mapping (simplified)
    RATING_TO_PD = {
        "AAA": 0.0001, "AA+": 0.0002, "AA": 0.0003, "AA-": 0.0005,
        "A+": 0.0008, "A": 0.0012, "A-": 0.0018,
        "BBB+": 0.0025, "BBB": 0.0040, "BBB-": 0.0065,
        "BB+": 0.0105, "BB": 0.0170, "BB-": 0.0275,
        "B+": 0.0445, "B": 0.0720, "B-": 0.1165,
        "CCC+": 0.1885, "CCC": 0.3050, "CCC-": 0.4935,
        "CC": 0.7990, "C": 0.9500, "D": 1.0000
    }
    
    def __init__(self, db: Optional[Session] = None):
        self.db = db
    
    def enrich_row(self, row: pd.Series) -> pd.Series:
        """
        Enrich a single row with default/calculated values.
        
        Args:
            row: DataFrame row
            
        Returns:
            Enriched row
        """
        enriched = row.copy()
        
        # Get sector
        sector = enriched.get("sector")
        
        # Set default asset_type if missing
        if pd.isna(enriched.get("asset_type")):
            enriched["asset_type"] = "Bond"
        
        # Set default market_value if missing (use exposure_amount)
        if pd.isna(enriched.get("market_value")) and pd.notna(enriched.get("exposure_amount")):
            enriched["market_value"] = enriched["exposure_amount"]
        
        # Set default rating if missing
        if pd.isna(enriched.get("rating")):
            enriched["rating"] = "BBB"
        
        # Set default maturity if missing
        if pd.isna(enriched.get("maturity_years")):
            enriched["maturity_years"] = 5
        
        # Enrich PD based on rating or sector
        if pd.isna(enriched.get("base_pd")):
            rating = enriched.get("rating")
            if rating and rating in self.RATING_TO_PD:
                enriched["base_pd"] = self.RATING_TO_PD[rating]
            elif sector and sector in self.SECTOR_DEFAULTS:
                enriched["base_pd"] = self.SECTOR_DEFAULTS[sector]["base_pd"]
            else:
                enriched["base_pd"] = 0.025  # Default 2.5%
        
        # Enrich LGD based on sector
        if pd.isna(enriched.get("base_lgd")):
            if sector and sector in self.SECTOR_DEFAULTS:
                enriched["base_lgd"] = self.SECTOR_DEFAULTS[sector]["base_lgd"]
            else:
                enriched["base_lgd"] = 0.45  # Default 45%
        
        # Enrich emissions_intensity based on sector
        if pd.isna(enriched.get("emissions_intensity")):
            if sector and sector in self.SECTOR_DEFAULTS:
                enriched["emissions_intensity"] = self.SECTOR_DEFAULTS[sector]["emissions_intensity"]
            else:
                enriched["emissions_intensity"] = 0.8  # Default
        
        return enriched
    
    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Enrich entire DataFrame.
        
        Args:
            df: DataFrame to enrich
            
        Returns:
            Enriched DataFrame
        """
        enriched_df = df.copy()
        
        # Apply row-level enrichment
        for idx in enriched_df.index:
            enriched_df.loc[idx] = self.enrich_row(enriched_df.loc[idx])
        
        return enriched_df
    
    def match_counterparty(self, name: str, lei: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Match uploaded counterparty to existing database records.
        
        Args:
            name: Counterparty name
            lei: Legal Entity Identifier (optional)
            
        Returns:
            Matched counterparty dict or None
        """
        # TODO: Implement counterparty matching logic
        # This could query a counterparty database or external API
        return None
    
    def calculate_metrics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate portfolio metrics after enrichment.
        
        Args:
            df: Enriched DataFrame
            
        Returns:
            Dict with calculated metrics
        """
        metrics = {
            "total_holdings": len(df),
            "total_exposure": 0,
            "weighted_avg_pd": 0,
            "weighted_avg_lgd": 0,
            "expected_loss": 0
        }
        
        if "exposure_amount" in df.columns:
            total_exposure = df["exposure_amount"].sum()
            metrics["total_exposure"] = float(total_exposure)
            
            if total_exposure > 0:
                # Weighted average PD
                if "base_pd" in df.columns:
                    metrics["weighted_avg_pd"] = float(
                        (df["exposure_amount"] * df["base_pd"]).sum() / total_exposure
                    )
                
                # Weighted average LGD
                if "base_lgd" in df.columns:
                    metrics["weighted_avg_lgd"] = float(
                        (df["exposure_amount"] * df["base_lgd"]).sum() / total_exposure
                    )
                
                # Expected Loss = EAD * PD * LGD
                if "base_pd" in df.columns and "base_lgd" in df.columns:
                    df["expected_loss"] = df["exposure_amount"] * df["base_pd"] * df["base_lgd"]
                    metrics["expected_loss"] = float(df["expected_loss"].sum())
                    metrics["expected_loss_pct"] = float(
                        (metrics["expected_loss"] / total_exposure) * 100
                    )
        
        return metrics
