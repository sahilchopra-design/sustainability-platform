"""Upload service for file parsing and processing"""
import pandas as pd
import json
import uuid
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import io
from datetime import datetime
from difflib import get_close_matches


class UploadService:
    """Service for handling file uploads and parsing"""
    
    # Column mapping definitions
    REQUIRED_FIELDS = [
        "counterparty_name",  # OR lei
        "exposure_amount",
        "currency"
    ]
    
    OPTIONAL_FIELDS = [
        "lei",
        "sector",
        "country_code",
        "asset_type",
        "market_value",
        "base_pd",
        "base_lgd",
        "rating",
        "maturity_years",
        "emissions_intensity",
        "subsector",
        "isin",
        "cusip"
    ]
    
    # Standard field aliases for auto-mapping
    FIELD_ALIASES = {
        "counterparty_name": ["counterparty", "company", "company_name", "entity", "name"],
        "lei": ["legal_entity_identifier", "lei_code"],
        "exposure_amount": ["exposure", "amount", "ead", "notional"],
        "currency": ["ccy", "curr"],
        "sector": ["industry", "industry_sector"],
        "country_code": ["country", "jurisdiction", "domicile"],
        "asset_type": ["type", "instrument_type", "instrument"],
        "market_value": ["mv", "market_val", "value"],
        "base_pd": ["pd", "probability_of_default"],
        "base_lgd": ["lgd", "loss_given_default"],
        "rating": ["credit_rating", "grade"],
        "maturity_years": ["maturity", "tenor", "term"],
        "emissions_intensity": ["emissions", "carbon_intensity", "co2_intensity"]
    }
    
    def __init__(self, upload_dir: str = "/tmp/uploads"):
        self.upload_dir = Path(upload_dir)
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    def save_file(self, file_content: bytes, filename: str, upload_id: str) -> str:
        """Save uploaded file to disk"""
        file_path = self.upload_dir / f"{upload_id}_{filename}"
        with open(file_path, "wb") as f:
            f.write(file_content)
        return str(file_path)
    
    def parse_file(self, file_path: str, file_format: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Parse uploaded file and return DataFrame.
        
        Returns:
            Tuple of (DataFrame, metadata dict)
        """
        metadata = {
            "total_rows": 0,
            "columns": [],
            "detected_format": file_format
        }
        
        try:
            if file_format == "csv":
                df = pd.read_csv(file_path)
            elif file_format in ["xlsx", "xls"]:
                df = pd.read_excel(file_path)
            elif file_format == "json":
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            # Clean column names
            df.columns = [str(col).strip().lower().replace(" ", "_") for col in df.columns]
            
            metadata["total_rows"] = len(df)
            metadata["columns"] = list(df.columns)
            
            return df, metadata
            
        except Exception as e:
            raise ValueError(f"Failed to parse file: {str(e)}")
    
    def auto_map_columns(self, columns: List[str]) -> Dict[str, Optional[str]]:
        """
        Automatically map uploaded columns to standard fields using fuzzy matching.
        
        Args:
            columns: List of column names from uploaded file
            
        Returns:
            Dict mapping standard field names to uploaded column names
        """
        mapping = {}
        used_columns = set()
        
        # First pass: exact matches
        for standard_field in self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS:
            if standard_field in columns:
                mapping[standard_field] = standard_field
                used_columns.add(standard_field)
        
        # Second pass: alias matching
        for standard_field, aliases in self.FIELD_ALIASES.items():
            if standard_field in mapping:
                continue
            
            for alias in aliases:
                if alias in columns and alias not in used_columns:
                    mapping[standard_field] = alias
                    used_columns.add(alias)
                    break
        
        # Third pass: fuzzy matching
        remaining_columns = [col for col in columns if col not in used_columns]
        
        for standard_field in self.REQUIRED_FIELDS + self.OPTIONAL_FIELDS:
            if standard_field in mapping:
                continue
            
            # Get all possible names for this field
            search_terms = [standard_field] + self.FIELD_ALIASES.get(standard_field, [])
            
            for term in search_terms:
                matches = get_close_matches(term, remaining_columns, n=1, cutoff=0.7)
                if matches:
                    match = matches[0]
                    mapping[standard_field] = match
                    remaining_columns.remove(match)
                    break
        
        return mapping
    
    def apply_mapping(self, df: pd.DataFrame, mapping: Dict[str, str]) -> pd.DataFrame:
        """
        Apply column mapping to DataFrame.
        
        Args:
            df: Original DataFrame
            mapping: Dict mapping standard field names to uploaded column names
            
        Returns:
            DataFrame with renamed columns
        """
        # Create reverse mapping (uploaded col -> standard field)
        reverse_mapping = {v: k for k, v in mapping.items() if v is not None}
        
        # Rename columns
        df_mapped = df.rename(columns=reverse_mapping)
        
        # Add missing optional columns with None
        for field in self.OPTIONAL_FIELDS:
            if field not in df_mapped.columns:
                df_mapped[field] = None
        
        return df_mapped
    
    def get_preview(self, df: pd.DataFrame, max_rows: int = 100) -> List[Dict[str, Any]]:
        """
        Get preview of first N rows.
        
        Args:
            df: DataFrame to preview
            max_rows: Maximum number of rows to return
            
        Returns:
            List of row dictionaries
        """
        preview_df = df.head(max_rows)
        
        # Convert to list of dicts, handling NaN values
        records = preview_df.fillna("").to_dict(orient="records")
        
        # Add row numbers
        for i, record in enumerate(records, 1):
            record["_row_number"] = i
        
        return records
    
    def convert_to_holdings(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Convert DataFrame to list of holding dictionaries.
        
        Args:
            df: Mapped and validated DataFrame
            
        Returns:
            List of holding dicts ready for database insertion
        """
        holdings = []
        
        for idx, row in df.iterrows():
            holding = {
                "company_name": row.get("counterparty_name"),
                "company_sector": row.get("sector", "Power Generation"),  # Default
                "company_subsector": row.get("subsector"),
                "asset_type": row.get("asset_type", "Bond"),  # Default
                "exposure": float(row.get("exposure_amount", 0)),
                "market_value": float(row.get("market_value", row.get("exposure_amount", 0))),
                "base_pd": float(row.get("base_pd", 0.02)),  # Default 2%
                "base_lgd": float(row.get("base_lgd", 0.45)),  # Default 45%
                "rating": row.get("rating", "BBB"),  # Default
                "maturity_years": int(row.get("maturity_years", 5)),  # Default 5 years
            }
            
            # Add optional fields if present
            if pd.notna(row.get("lei")):
                holding["lei"] = row.get("lei")
            if pd.notna(row.get("country_code")):
                holding["country_code"] = row.get("country_code")
            if pd.notna(row.get("emissions_intensity")):
                holding["emissions_intensity"] = float(row.get("emissions_intensity"))
            
            holdings.append(holding)
        
        return holdings
    
    def detect_duplicates(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Detect duplicate rows based on key fields.
        
        Args:
            df: DataFrame to check
            
        Returns:
            List of duplicate info dicts
        """
        duplicates = []
        
        # Check for duplicates based on counterparty_name + exposure_amount
        if "counterparty_name" in df.columns and "exposure_amount" in df.columns:
            dup_mask = df.duplicated(subset=["counterparty_name", "exposure_amount"], keep=False)
            dup_rows = df[dup_mask]
            
            if not dup_rows.empty:
                for idx, row in dup_rows.iterrows():
                    duplicates.append({
                        "row_number": idx + 1,
                        "counterparty_name": row.get("counterparty_name"),
                        "exposure_amount": row.get("exposure_amount"),
                        "type": "exact_duplicate"
                    })
        
        return duplicates
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Calculate statistics for the uploaded data.
        
        Args:
            df: DataFrame to analyze
            
        Returns:
            Dict with statistics
        """
        stats = {
            "total_rows": len(df),
            "total_exposure": 0,
            "sector_distribution": {},
            "currency_distribution": {},
            "rating_distribution": {},
        }
        
        if "exposure_amount" in df.columns:
            stats["total_exposure"] = float(df["exposure_amount"].sum())
            stats["avg_exposure"] = float(df["exposure_amount"].mean())
            stats["max_exposure"] = float(df["exposure_amount"].max())
            stats["min_exposure"] = float(df["exposure_amount"].min())
        
        if "sector" in df.columns:
            stats["sector_distribution"] = df["sector"].value_counts().to_dict()
        
        if "currency" in df.columns:
            stats["currency_distribution"] = df["currency"].value_counts().to_dict()
        
        if "rating" in df.columns:
            stats["rating_distribution"] = df["rating"].value_counts().to_dict()
        
        return stats
