"""Validation service for uploaded data"""
import pandas as pd
import re
from typing import List, Dict, Any, Tuple
from datetime import datetime


class ValidationService:
    """Service for validating uploaded portfolio data"""
    
    # Validation rules
    VALID_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD"]
    
    VALID_SECTORS = [
        "Power Generation",
        "Oil & Gas",
        "Metals & Mining",
        "Automotive",
        "Airlines",
        "Real Estate"
    ]
    
    VALID_ASSET_TYPES = ["Bond", "Loan", "Equity"]
    
    VALID_RATINGS = [
        "AAA", "AA+", "AA", "AA-",
        "A+", "A", "A-",
        "BBB+", "BBB", "BBB-",
        "BB+", "BB", "BB-",
        "B+", "B", "B-",
        "CCC+", "CCC", "CCC-",
        "CC", "C", "D"
    ]
    
    # ISO 3166-1 alpha-2 country codes (subset)
    VALID_COUNTRY_CODES = [
        "US", "GB", "DE", "FR", "IT", "ES", "NL", "BE", "CH",
        "JP", "CN", "IN", "BR", "CA", "AU", "MX", "KR", "SG"
    ]
    
    def __init__(self):
        self.errors = []
        self.warnings = []
    
    def validate_row(self, row: pd.Series, row_number: int) -> List[Dict[str, Any]]:
        """
        Validate a single row of data.
        
        Args:
            row: DataFrame row
            row_number: Row number (1-indexed)
            
        Returns:
            List of validation errors for this row
        """
        row_errors = []
        
        # Required field validation
        if pd.isna(row.get("counterparty_name")) and pd.isna(row.get("lei")):
            row_errors.append({
                "row_number": row_number,
                "column_name": "counterparty_name",
                "error_type": "missing_required",
                "error_message": "Either counterparty_name or LEI is required",
                "severity": "error",
                "original_value": None
            })
        
        if pd.isna(row.get("exposure_amount")):
            row_errors.append({
                "row_number": row_number,
                "column_name": "exposure_amount",
                "error_type": "missing_required",
                "error_message": "Exposure amount is required",
                "severity": "error",
                "original_value": None
            })
        
        if pd.isna(row.get("currency")):
            row_errors.append({
                "row_number": row_number,
                "column_name": "currency",
                "error_type": "missing_required",
                "error_message": "Currency is required",
                "severity": "error",
                "original_value": None
            })
        
        # LEI format validation
        if pd.notna(row.get("lei")):
            lei = str(row.get("lei"))
            if not self.validate_lei_format(lei):
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "lei",
                    "error_type": "invalid_format",
                    "error_message": "Invalid LEI format (should be 20 alphanumeric characters)",
                    "severity": "error",
                    "original_value": lei
                })
        
        # Currency validation
        if pd.notna(row.get("currency")):
            currency = str(row.get("currency")).upper()
            if currency not in self.VALID_CURRENCIES:
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "currency",
                    "error_type": "invalid_value",
                    "error_message": f"Invalid currency. Must be one of: {', '.join(self.VALID_CURRENCIES)}",
                    "severity": "error",
                    "original_value": currency
                })
        
        # Sector validation
        if pd.notna(row.get("sector")):
            sector = str(row.get("sector"))
            if sector not in self.VALID_SECTORS:
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "sector",
                    "error_type": "invalid_value",
                    "error_message": f"Invalid sector. Must be one of: {', '.join(self.VALID_SECTORS)}",
                    "severity": "warning",
                    "original_value": sector
                })
        
        # Asset type validation
        if pd.notna(row.get("asset_type")):
            asset_type = str(row.get("asset_type"))
            if asset_type not in self.VALID_ASSET_TYPES:
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "asset_type",
                    "error_type": "invalid_value",
                    "error_message": f"Invalid asset type. Must be one of: {', '.join(self.VALID_ASSET_TYPES)}",
                    "severity": "warning",
                    "original_value": asset_type
                })
        
        # Country code validation
        if pd.notna(row.get("country_code")):
            country = str(row.get("country_code")).upper()
            if len(country) != 2 or country not in self.VALID_COUNTRY_CODES:
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "country_code",
                    "error_type": "invalid_value",
                    "error_message": "Invalid country code (use ISO 3166-1 alpha-2)",
                    "severity": "warning",
                    "original_value": country
                })
        
        # Rating validation
        if pd.notna(row.get("rating")):
            rating = str(row.get("rating")).upper()
            if rating not in self.VALID_RATINGS:
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "rating",
                    "error_type": "invalid_value",
                    "error_message": "Invalid credit rating",
                    "severity": "warning",
                    "original_value": rating
                })
        
        # Numeric validations
        if pd.notna(row.get("exposure_amount")):
            try:
                exposure = float(row.get("exposure_amount"))
                if exposure <= 0:
                    row_errors.append({
                        "row_number": row_number,
                        "column_name": "exposure_amount",
                        "error_type": "invalid_value",
                        "error_message": "Exposure amount must be positive",
                        "severity": "error",
                        "original_value": str(exposure)
                    })
            except (ValueError, TypeError):
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "exposure_amount",
                    "error_type": "invalid_format",
                    "error_message": "Exposure amount must be a number",
                    "severity": "error",
                    "original_value": str(row.get("exposure_amount"))
                })
        
        # PD validation (0-1 range)
        if pd.notna(row.get("base_pd")):
            try:
                pd_val = float(row.get("base_pd"))
                if pd_val < 0 or pd_val > 1:
                    row_errors.append({
                        "row_number": row_number,
                        "column_name": "base_pd",
                        "error_type": "invalid_value",
                        "error_message": "PD must be between 0 and 1",
                        "severity": "error",
                        "original_value": str(pd_val)
                    })
            except (ValueError, TypeError):
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "base_pd",
                    "error_type": "invalid_format",
                    "error_message": "PD must be a number",
                    "severity": "error",
                    "original_value": str(row.get("base_pd"))
                })
        
        # LGD validation (0-1 range)
        if pd.notna(row.get("base_lgd")):
            try:
                lgd_val = float(row.get("base_lgd"))
                if lgd_val < 0 or lgd_val > 1:
                    row_errors.append({
                        "row_number": row_number,
                        "column_name": "base_lgd",
                        "error_type": "invalid_value",
                        "error_message": "LGD must be between 0 and 1",
                        "severity": "error",
                        "original_value": str(lgd_val)
                    })
            except (ValueError, TypeError):
                row_errors.append({
                    "row_number": row_number,
                    "column_name": "base_lgd",
                    "error_type": "invalid_format",
                    "error_message": "LGD must be a number",
                    "severity": "error",
                    "original_value": str(row.get("base_lgd"))
                })
        
        return row_errors
    
    def validate_dataframe(self, df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Validate entire DataFrame.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            Tuple of (list of errors, summary dict)
        """
        all_errors = []
        
        # Row-level validation
        for idx, row in df.iterrows():
            row_errors = self.validate_row(row, idx + 1)
            all_errors.extend(row_errors)
        
        # Portfolio-level validation
        portfolio_errors = self.validate_portfolio_level(df)
        all_errors.extend(portfolio_errors)
        
        # Create summary
        error_count = len([e for e in all_errors if e["severity"] == "error"])
        warning_count = len([e for e in all_errors if e["severity"] == "warning"])
        
        summary = {
            "total_errors": error_count,
            "total_warnings": warning_count,
            "is_valid": error_count == 0,
            "error_types": {},
            "affected_rows": len(set(e["row_number"] for e in all_errors if "row_number" in e))
        }
        
        # Count error types
        for error in all_errors:
            error_type = error["error_type"]
            summary["error_types"][error_type] = summary["error_types"].get(error_type, 0) + 1
        
        return all_errors, summary
    
    def validate_portfolio_level(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Perform portfolio-level validations.
        
        Args:
            df: DataFrame to validate
            
        Returns:
            List of portfolio-level validation errors
        """
        errors = []
        
        # Check concentration risk
        if "exposure_amount" in df.columns and "counterparty_name" in df.columns:
            total_exposure = df["exposure_amount"].sum()
            
            # Single name concentration
            top_exposures = df.groupby("counterparty_name")["exposure_amount"].sum().sort_values(ascending=False)
            
            if len(top_exposures) > 0:
                top_exposure_pct = (top_exposures.iloc[0] / total_exposure) * 100
                
                if top_exposure_pct > 25:
                    errors.append({
                        "row_number": None,
                        "column_name": "exposure_amount",
                        "error_type": "concentration_risk",
                        "error_message": f"Single name concentration risk: {top_exposures.index[0]} represents {top_exposure_pct:.1f}% of total exposure",
                        "severity": "warning",
                        "original_value": str(top_exposure_pct)
                    })
        
        # Check sector concentration
        if "sector" in df.columns and "exposure_amount" in df.columns:
            total_exposure = df["exposure_amount"].sum()
            sector_exposures = df.groupby("sector")["exposure_amount"].sum()
            
            for sector, exposure in sector_exposures.items():
                sector_pct = (exposure / total_exposure) * 100
                if sector_pct > 40:
                    errors.append({
                        "row_number": None,
                        "column_name": "sector",
                        "error_type": "concentration_risk",
                        "error_message": f"Sector concentration risk: {sector} represents {sector_pct:.1f}% of total exposure",
                        "severity": "warning",
                        "original_value": str(sector_pct)
                    })
        
        return errors
    
    @staticmethod
    def validate_lei_format(lei: str) -> bool:
        """
        Validate LEI format.
        
        LEI is 20 alphanumeric characters.
        """
        if len(lei) != 20:
            return False
        return bool(re.match(r'^[A-Z0-9]{20}$', lei.upper()))
