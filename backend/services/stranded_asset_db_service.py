"""
Database service for Stranded Assets module.
Provides PostgreSQL-backed data access for reserves, power plants, and infrastructure.
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from uuid import UUID, uuid4
from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

# Database configuration
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://postgres.kytzcbipsghprsqoalvi:Zeek%40%402025%40%40@aws-1-us-east-2.pooler.supabase.com:5432/postgres')


def get_engine():
    """Get SQLAlchemy engine with connection pooling disabled for serverless."""
    return create_engine(DATABASE_URL, poolclass=NullPool)


class StrandedAssetDBService:
    """Database service for stranded asset data."""
    
    def __init__(self):
        self.engine = get_engine()
    
    # ================== RESERVES ==================
    
    def get_all_reserves(
        self,
        reserve_type: Optional[str] = None,
        reserve_category: Optional[str] = None,
        is_operating: Optional[bool] = True,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get all fossil fuel reserves with optional filtering."""
        with self.engine.connect() as conn:
            # Build query
            conditions = []
            params = {}
            
            if reserve_type:
                conditions.append("reserve_type = :reserve_type")
                params["reserve_type"] = reserve_type
            if reserve_category:
                conditions.append("reserve_category = :reserve_category")
                params["reserve_category"] = reserve_category
            if is_operating is not None:
                conditions.append("is_operating = :is_operating")
                params["is_operating"] = is_operating
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = str(user_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM fossil_fuel_reserve {where_clause}"
            total = conn.execute(text(count_query), params).scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset
            
            query = f"""
                SELECT 
                    id, user_id, asset_name, asset_location, latitude, longitude,
                    reserve_type, reserve_category, proven_reserves_mmBOE,
                    probable_reserves_mmBOE, possible_reserves_mmBOE,
                    breakeven_price_USD, lifting_cost_USD, remaining_capex_USD,
                    carbon_intensity_kgCO2_per_unit, methane_leakage_rate,
                    production_start_year, expected_depletion_year, license_expiry_year,
                    is_operating, created_at, updated_at
                FROM fossil_fuel_reserve
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(self._row_to_reserve_dict(row))
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    
    def get_reserve_by_id(self, reserve_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single reserve by ID."""
        with self.engine.connect() as conn:
            query = """
                SELECT * FROM fossil_fuel_reserve WHERE id = :id
            """
            result = conn.execute(text(query), {"id": str(reserve_id)})
            row = result.fetchone()
            
            if row:
                return self._row_to_reserve_dict(row)
            return None
    
    def create_reserve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new fossil fuel reserve."""
        with self.engine.connect() as conn:
            reserve_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO fossil_fuel_reserve (
                    id, user_id, asset_name, asset_location, latitude, longitude,
                    reserve_type, reserve_category, proven_reserves_mmBOE,
                    probable_reserves_mmBOE, possible_reserves_mmBOE,
                    breakeven_price_USD, lifting_cost_USD, remaining_capex_USD,
                    carbon_intensity_kgCO2_per_unit, methane_leakage_rate,
                    production_start_year, expected_depletion_year, license_expiry_year,
                    is_operating, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :asset_name, :asset_location, :latitude, :longitude,
                    :reserve_type, :reserve_category, :proven_reserves_mmBOE,
                    :probable_reserves_mmBOE, :possible_reserves_mmBOE,
                    :breakeven_price_USD, :lifting_cost_USD, :remaining_capex_USD,
                    :carbon_intensity_kgCO2_per_unit, :methane_leakage_rate,
                    :production_start_year, :expected_depletion_year, :license_expiry_year,
                    :is_operating, :created_at, :updated_at
                )
                RETURNING *
            """
            
            params = {
                "id": reserve_id,
                "user_id": data.get("user_id"),
                "asset_name": data.get("asset_name"),
                "asset_location": data.get("asset_location"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "reserve_type": data.get("reserve_type"),
                "reserve_category": data.get("reserve_category"),
                "proven_reserves_mmBOE": data.get("proven_reserves_mmBOE"),
                "probable_reserves_mmBOE": data.get("probable_reserves_mmBOE"),
                "possible_reserves_mmBOE": data.get("possible_reserves_mmBOE"),
                "breakeven_price_USD": data.get("breakeven_price_USD"),
                "lifting_cost_USD": data.get("lifting_cost_USD"),
                "remaining_capex_USD": data.get("remaining_capex_USD"),
                "carbon_intensity_kgCO2_per_unit": data.get("carbon_intensity_kgCO2_per_unit"),
                "methane_leakage_rate": data.get("methane_leakage_rate"),
                "production_start_year": data.get("production_start_year"),
                "expected_depletion_year": data.get("expected_depletion_year"),
                "license_expiry_year": data.get("license_expiry_year"),
                "is_operating": data.get("is_operating", True),
                "created_at": now,
                "updated_at": now
            }
            
            result = conn.execute(text(query), params)
            conn.commit()
            row = result.fetchone()
            
            return self._row_to_reserve_dict(row)
    
    def _row_to_reserve_dict(self, row) -> Dict[str, Any]:
        """Convert database row to reserve dictionary."""
        return {
            "id": str(row.id) if row.id else None,
            "user_id": str(row.user_id) if row.user_id else None,
            "counterparty_id": str(row.user_id) if row.user_id else None,  # For backward compatibility
            "counterparty_name": "Portfolio Owner",
            "asset_name": row.asset_name,
            "asset_location": row.asset_location,
            "latitude": Decimal(str(row.latitude)) if row.latitude else None,
            "longitude": Decimal(str(row.longitude)) if row.longitude else None,
            "reserve_type": row.reserve_type,
            "reserve_category": row.reserve_category,
            "proven_reserves_mmBOE": Decimal(str(row.proven_reserves_mmboe)) if row.proven_reserves_mmboe else Decimal("0"),
            "probable_reserves_mmBOE": Decimal(str(row.probable_reserves_mmboe)) if row.probable_reserves_mmboe else Decimal("0"),
            "possible_reserves_mmBOE": Decimal(str(row.possible_reserves_mmboe)) if row.possible_reserves_mmboe else Decimal("0"),
            "breakeven_price_USD": Decimal(str(row.breakeven_price_usd)) if row.breakeven_price_usd else Decimal("0"),
            "lifting_cost_USD": Decimal(str(row.lifting_cost_usd)) if row.lifting_cost_usd else Decimal("0"),
            "remaining_capex_USD": Decimal(str(row.remaining_capex_usd)) if row.remaining_capex_usd else Decimal("0"),
            "carbon_intensity_kgCO2_per_unit": Decimal(str(row.carbon_intensity_kgco2_per_unit)) if row.carbon_intensity_kgco2_per_unit else Decimal("0"),
            "methane_leakage_rate": Decimal(str(row.methane_leakage_rate)) if row.methane_leakage_rate else Decimal("0"),
            "production_start_year": row.production_start_year,
            "expected_depletion_year": row.expected_depletion_year,
            "license_expiry_year": row.license_expiry_year,
            "is_operating": row.is_operating if row.is_operating is not None else True,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
    
    # ================== POWER PLANTS ==================
    
    def get_all_plants(
        self,
        technology_type: Optional[str] = None,
        country_code: Optional[str] = None,
        is_operating: Optional[bool] = True,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get all power plants with optional filtering."""
        with self.engine.connect() as conn:
            conditions = []
            params = {}
            
            if technology_type:
                conditions.append("technology_type = :technology_type")
                params["technology_type"] = technology_type
            if country_code:
                conditions.append("country_code = :country_code")
                params["country_code"] = country_code
            if is_operating is not None:
                conditions.append("is_operating = :is_operating")
                params["is_operating"] = is_operating
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = str(user_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM power_plant {where_clause}"
            total = conn.execute(text(count_query), params).scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset
            
            query = f"""
                SELECT * FROM power_plant
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(self._row_to_plant_dict(row))
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    
    def get_plant_by_id(self, plant_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single power plant by ID."""
        with self.engine.connect() as conn:
            query = "SELECT * FROM power_plant WHERE id = :id"
            result = conn.execute(text(query), {"id": str(plant_id)})
            row = result.fetchone()
            
            if row:
                return self._row_to_plant_dict(row)
            return None
    
    def create_plant(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new power plant."""
        with self.engine.connect() as conn:
            plant_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO power_plant (
                    id, user_id, plant_name, plant_location, latitude, longitude,
                    country_code, technology_type, capacity_mw, commissioning_year,
                    original_retirement_year, technical_lifetime_years,
                    capacity_factor_baseline, capacity_factor_current,
                    heat_rate_btu_kwh, efficiency_percent, co2_intensity_tco2_mwh,
                    nox_emissions_kg_mwh, so2_emissions_kg_mwh, has_ccs,
                    ccs_capacity_mtpa, fixed_om_cost_usd_kw_year, variable_om_cost_usd_mwh,
                    fuel_cost_usd_mmbtu, fuel_type, offtake_type,
                    ppa_expiry_year, ppa_price_usd_mwh, grid_region, repurposing_option,
                    is_operating, created_at, updated_at
                ) VALUES (
                    :id, :user_id, :plant_name, :plant_location, :latitude, :longitude,
                    :country_code, :technology_type, :capacity_mw, :commissioning_year,
                    :original_retirement_year, :technical_lifetime_years,
                    :capacity_factor_baseline, :capacity_factor_current,
                    :heat_rate_btu_kwh, :efficiency_percent, :co2_intensity_tco2_mwh,
                    :nox_emissions_kg_mwh, :so2_emissions_kg_mwh, :has_ccs,
                    :ccs_capacity_mtpa, :fixed_om_cost_usd_kw_year, :variable_om_cost_usd_mwh,
                    :fuel_cost_usd_mmbtu, :fuel_type, :offtake_type,
                    :ppa_expiry_year, :ppa_price_usd_mwh, :grid_region, :repurposing_option,
                    :is_operating, :created_at, :updated_at
                )
                RETURNING *
            """
            
            params = {
                "id": plant_id,
                "user_id": data.get("user_id"),
                "plant_name": data.get("plant_name"),
                "plant_location": data.get("plant_location"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "country_code": data.get("country_code"),
                "technology_type": data.get("technology_type"),
                "capacity_mw": data.get("capacity_mw"),
                "commissioning_year": data.get("commissioning_year"),
                "original_retirement_year": data.get("original_retirement_year"),
                "technical_lifetime_years": data.get("technical_lifetime_years"),
                "capacity_factor_baseline": data.get("capacity_factor_baseline"),
                "capacity_factor_current": data.get("capacity_factor_current"),
                "heat_rate_btu_kwh": data.get("heat_rate_btu_kwh"),
                "efficiency_percent": data.get("efficiency_percent"),
                "co2_intensity_tco2_mwh": data.get("co2_intensity_tco2_mwh"),
                "nox_emissions_kg_mwh": data.get("nox_emissions_kg_mwh"),
                "so2_emissions_kg_mwh": data.get("so2_emissions_kg_mwh"),
                "has_ccs": data.get("has_ccs", False),
                "ccs_capacity_mtpa": data.get("ccs_capacity_mtpa"),
                "fixed_om_cost_usd_kw_year": data.get("fixed_om_cost_usd_kw_year"),
                "variable_om_cost_usd_mwh": data.get("variable_om_cost_usd_mwh"),
                "fuel_cost_usd_mmbtu": data.get("fuel_cost_usd_mmbtu"),
                "fuel_type": data.get("fuel_type"),
                "offtake_type": data.get("offtake_type"),
                "ppa_expiry_year": data.get("ppa_expiry_year"),
                "ppa_price_usd_mwh": data.get("ppa_price_usd_mwh"),
                "grid_region": data.get("grid_region"),
                "repurposing_option": data.get("repurposing_option"),
                "is_operating": data.get("is_operating", True),
                "created_at": now,
                "updated_at": now
            }
            
            result = conn.execute(text(query), params)
            conn.commit()
            row = result.fetchone()
            
            return self._row_to_plant_dict(row)
    
    def _row_to_plant_dict(self, row) -> Dict[str, Any]:
        """Convert database row to plant dictionary."""
        return {
            "id": str(row.id) if row.id else None,
            "user_id": str(row.user_id) if row.user_id else None,
            "counterparty_id": str(row.user_id) if row.user_id else None,
            "counterparty_name": "Portfolio Owner",
            "plant_name": row.plant_name,
            "plant_location": row.plant_location,
            "latitude": Decimal(str(row.latitude)) if row.latitude else None,
            "longitude": Decimal(str(row.longitude)) if row.longitude else None,
            "country_code": row.country_code,
            "technology_type": row.technology_type,
            "capacity_mw": Decimal(str(row.capacity_mw)) if row.capacity_mw else Decimal("0"),
            "commissioning_year": row.commissioning_year,
            "original_retirement_year": row.original_retirement_year,
            "technical_lifetime_years": row.technical_lifetime_years,
            "capacity_factor_baseline": Decimal(str(row.capacity_factor_baseline)) if row.capacity_factor_baseline else None,
            "capacity_factor_current": Decimal(str(row.capacity_factor_current)) if row.capacity_factor_current else None,
            "heat_rate_btu_kwh": Decimal(str(row.heat_rate_btu_kwh)) if row.heat_rate_btu_kwh else None,
            "efficiency_percent": Decimal(str(row.efficiency_percent)) if row.efficiency_percent else None,
            "co2_intensity_tco2_mwh": Decimal(str(row.co2_intensity_tco2_mwh)) if row.co2_intensity_tco2_mwh else None,
            "nox_emissions_kg_mwh": Decimal(str(row.nox_emissions_kg_mwh)) if row.nox_emissions_kg_mwh else None,
            "so2_emissions_kg_mwh": Decimal(str(row.so2_emissions_kg_mwh)) if row.so2_emissions_kg_mwh else None,
            "has_ccs": row.has_ccs if row.has_ccs is not None else False,
            "ccs_capacity_mtpa": Decimal(str(row.ccs_capacity_mtpa)) if row.ccs_capacity_mtpa else None,
            "fixed_om_cost_usd_kw_year": Decimal(str(row.fixed_om_cost_usd_kw_year)) if row.fixed_om_cost_usd_kw_year else None,
            "variable_om_cost_usd_mwh": Decimal(str(row.variable_om_cost_usd_mwh)) if row.variable_om_cost_usd_mwh else None,
            "fuel_cost_usd_mmbtu": Decimal(str(row.fuel_cost_usd_mmbtu)) if row.fuel_cost_usd_mmbtu else None,
            "fuel_type": row.fuel_type,
            "offtake_type": row.offtake_type,
            "ppa_expiry_year": row.ppa_expiry_year,
            "ppa_price_usd_mwh": Decimal(str(row.ppa_price_usd_mwh)) if row.ppa_price_usd_mwh else None,
            "grid_region": row.grid_region,
            "grid_carbon_intensity": None,
            "repurposing_option": row.repurposing_option,
            "repurposing_cost_usd_mw": None,
            "is_operating": row.is_operating if row.is_operating is not None else True,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
    
    # ================== INFRASTRUCTURE ==================
    
    def get_all_infrastructure(
        self,
        asset_type: Optional[str] = None,
        country_code: Optional[str] = None,
        is_operating: Optional[bool] = True,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get all infrastructure assets with optional filtering."""
        with self.engine.connect() as conn:
            conditions = []
            params = {}
            
            if asset_type:
                conditions.append("asset_type = :asset_type")
                params["asset_type"] = asset_type
            if country_code:
                conditions.append("country_code = :country_code")
                params["country_code"] = country_code
            if is_operating is not None:
                conditions.append("is_operating = :is_operating")
                params["is_operating"] = is_operating
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = str(user_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM infrastructure_asset {where_clause}"
            total = conn.execute(text(count_query), params).scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset
            
            query = f"""
                SELECT * FROM infrastructure_asset
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(self._row_to_infrastructure_dict(row))
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    
    def get_infrastructure_by_id(self, asset_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single infrastructure asset by ID."""
        with self.engine.connect() as conn:
            query = "SELECT * FROM infrastructure_asset WHERE id = :id"
            result = conn.execute(text(query), {"id": str(asset_id)})
            row = result.fetchone()
            
            if row:
                return self._row_to_infrastructure_dict(row)
            return None
    
    def create_infrastructure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new infrastructure asset."""
        with self.engine.connect() as conn:
            asset_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO infrastructure_asset (
                    id, user_id, asset_name, asset_type, asset_location,
                    latitude, longitude, country_code, design_capacity,
                    design_capacity_unit, current_capacity_utilized,
                    utilization_rate_percent, commissioning_year,
                    expected_retirement_year, remaining_book_value_usd,
                    replacement_cost_usd, contract_maturity_profile,
                    take_or_pay_exposure_usd, contracted_volume_percent,
                    hydrogen_ready, ammonia_ready, ccs_compatible,
                    regulatory_status, environmental_permits, is_operating,
                    created_at, updated_at
                ) VALUES (
                    :id, :user_id, :asset_name, :asset_type, :asset_location,
                    :latitude, :longitude, :country_code, :design_capacity,
                    :design_capacity_unit, :current_capacity_utilized,
                    :utilization_rate_percent, :commissioning_year,
                    :expected_retirement_year, :remaining_book_value_usd,
                    :replacement_cost_usd, :contract_maturity_profile,
                    :take_or_pay_exposure_usd, :contracted_volume_percent,
                    :hydrogen_ready, :ammonia_ready, :ccs_compatible,
                    :regulatory_status, :environmental_permits, :is_operating,
                    :created_at, :updated_at
                )
                RETURNING *
            """
            
            import json
            params = {
                "id": asset_id,
                "user_id": data.get("user_id"),
                "asset_name": data.get("asset_name"),
                "asset_type": data.get("asset_type"),
                "asset_location": data.get("asset_location"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "country_code": data.get("country_code"),
                "design_capacity": data.get("design_capacity"),
                "design_capacity_unit": data.get("design_capacity_unit"),
                "current_capacity_utilized": data.get("current_capacity_utilized"),
                "utilization_rate_percent": data.get("utilization_rate_percent"),
                "commissioning_year": data.get("commissioning_year"),
                "expected_retirement_year": data.get("expected_retirement_year"),
                "remaining_book_value_usd": data.get("remaining_book_value_usd"),
                "replacement_cost_usd": data.get("replacement_cost_usd"),
                "contract_maturity_profile": json.dumps(data.get("contract_maturity_profile")) if data.get("contract_maturity_profile") else None,
                "take_or_pay_exposure_usd": data.get("take_or_pay_exposure_usd"),
                "contracted_volume_percent": data.get("contracted_volume_percent"),
                "hydrogen_ready": data.get("hydrogen_ready", False),
                "ammonia_ready": data.get("ammonia_ready", False),
                "ccs_compatible": data.get("ccs_compatible", False),
                "regulatory_status": data.get("regulatory_status"),
                "environmental_permits": json.dumps(data.get("environmental_permits")) if data.get("environmental_permits") else None,
                "is_operating": data.get("is_operating", True),
                "created_at": now,
                "updated_at": now
            }
            
            result = conn.execute(text(query), params)
            conn.commit()
            row = result.fetchone()
            
            return self._row_to_infrastructure_dict(row)
    
    def _row_to_infrastructure_dict(self, row) -> Dict[str, Any]:
        """Convert database row to infrastructure dictionary."""
        return {
            "id": str(row.id) if row.id else None,
            "user_id": str(row.user_id) if row.user_id else None,
            "counterparty_id": str(row.user_id) if row.user_id else None,
            "counterparty_name": "Portfolio Owner",
            "asset_name": row.asset_name,
            "asset_type": row.asset_type,
            "asset_location": row.asset_location,
            "latitude": Decimal(str(row.latitude)) if row.latitude else None,
            "longitude": Decimal(str(row.longitude)) if row.longitude else None,
            "country_code": row.country_code,
            "design_capacity": row.design_capacity,
            "design_capacity_unit": row.design_capacity_unit,
            "current_capacity_utilized": row.current_capacity_utilized,
            "utilization_rate_percent": Decimal(str(row.utilization_rate_percent)) if row.utilization_rate_percent else None,
            "commissioning_year": row.commissioning_year,
            "expected_retirement_year": row.expected_retirement_year,
            "remaining_book_value_usd": Decimal(str(row.remaining_book_value_usd)) if row.remaining_book_value_usd else Decimal("0"),
            "replacement_cost_usd": Decimal(str(row.replacement_cost_usd)) if row.replacement_cost_usd else Decimal("0"),
            "contract_maturity_profile": row.contract_maturity_profile,
            "take_or_pay_exposure_usd": Decimal(str(row.take_or_pay_exposure_usd)) if row.take_or_pay_exposure_usd else Decimal("0"),
            "contracted_volume_percent": Decimal(str(row.contracted_volume_percent)) if row.contracted_volume_percent else None,
            "hydrogen_ready": row.hydrogen_ready if row.hydrogen_ready is not None else False,
            "ammonia_ready": row.ammonia_ready if row.ammonia_ready is not None else False,
            "ccs_compatible": row.ccs_compatible if row.ccs_compatible is not None else False,
            "regulatory_status": row.regulatory_status,
            "environmental_permits": row.environmental_permits,
            "is_operating": row.is_operating if row.is_operating is not None else True,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
    
    # ================== ENERGY TRANSITION PATHWAYS ==================
    
    def get_all_pathways(
        self,
        sector: Optional[str] = None,
        region: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get all energy transition pathways with optional filtering."""
        with self.engine.connect() as conn:
            conditions = ["is_active = TRUE"]
            params = {}
            
            if sector:
                conditions.append("sector = :sector")
                params["sector"] = sector
            if region:
                conditions.append("region = :region")
                params["region"] = region
            
            where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT * FROM energy_transition_pathway
                {where_clause}
                ORDER BY pathway_name
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(self._row_to_pathway_dict(row))
            
            return items
    
    def get_pathway_by_id(self, pathway_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single pathway by ID."""
        with self.engine.connect() as conn:
            query = "SELECT * FROM energy_transition_pathway WHERE id = :id"
            result = conn.execute(text(query), {"id": str(pathway_id)})
            row = result.fetchone()
            
            if row:
                return self._row_to_pathway_dict(row)
            return None
    
    def _row_to_pathway_dict(self, row) -> Dict[str, Any]:
        """Convert database row to pathway dictionary."""
        return {
            "id": str(row.id) if row.id else None,
            "pathway_name": row.pathway_name,
            "sector": row.sector,
            "region": row.region,
            "country_code": row.country_code,
            "scenario_id": str(row.scenario_id) if row.scenario_id else None,
            "base_year": row.base_year,
            "target_year": row.target_year,
            "demand_trajectory": row.demand_trajectory,
            "price_trajectory": row.price_trajectory,
            "capacity_trajectory": row.capacity_trajectory,
            "peak_demand_year": row.peak_demand_year,
            "net_zero_year": row.net_zero_year,
            "carbon_price_trajectory": row.carbon_price_trajectory,
            "policy_assumptions": row.policy_assumptions,
            "technology_assumptions": row.technology_assumptions,
            "source_document": row.source_document,
            "is_active": row.is_active,
            "created_at": row.created_at
        }
    
    # ================== DASHBOARD AGGREGATIONS ==================
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get aggregated dashboard metrics from all asset tables."""
        with self.engine.connect() as conn:
            # Count reserves
            reserves_count = conn.execute(text("SELECT COUNT(*) FROM fossil_fuel_reserve WHERE is_operating = TRUE")).scalar()
            
            # Count plants
            plants_count = conn.execute(text("SELECT COUNT(*) FROM power_plant WHERE is_operating = TRUE")).scalar()
            
            # Count infrastructure
            infra_count = conn.execute(text("SELECT COUNT(*) FROM infrastructure_asset WHERE is_operating = TRUE")).scalar()
            
            # Calculate total exposure from reserves (simplified: proven * price estimate)
            reserves_exposure = conn.execute(text("""
                SELECT COALESCE(SUM(proven_reserves_mmBOE * 50 * 1000000), 0) 
                FROM fossil_fuel_reserve WHERE is_operating = TRUE
            """)).scalar()
            
            # Calculate exposure from plants
            plants_exposure = conn.execute(text("""
                SELECT COALESCE(SUM(capacity_mw * 500000), 0) 
                FROM power_plant WHERE is_operating = TRUE
            """)).scalar()
            
            # Calculate exposure from infrastructure
            infra_exposure = conn.execute(text("""
                SELECT COALESCE(SUM(remaining_book_value_usd), 0) 
                FROM infrastructure_asset WHERE is_operating = TRUE
            """)).scalar()
            
            total_assets = reserves_count + plants_count + infra_count
            total_exposure = float(reserves_exposure) + float(plants_exposure) + float(infra_exposure)
            
            # Estimate stranded value (simplified risk calculation)
            stranded_value = total_exposure * 0.15  # 15% at risk estimate
            
            return {
                "total_assets": total_assets,
                "total_reserves_count": reserves_count,
                "total_plants_count": plants_count,
                "total_infrastructure_count": infra_count,
                "high_risk_assets": max(1, total_assets // 4),  # Simplified
                "critical_risk_assets": max(0, total_assets // 8),
                "total_exposure_usd": Decimal(str(round(total_exposure, 2))),
                "stranded_value_at_risk_usd": Decimal(str(round(stranded_value, 2))),
                "avg_stranding_risk_score": Decimal("0.52"),
                "assets_by_risk_category": {
                    "low": max(1, total_assets // 3),
                    "medium": max(1, total_assets // 3),
                    "high": max(1, total_assets // 4),
                    "critical": max(0, total_assets // 8)
                }
            }


# Singleton instance
_db_service = None

def get_stranded_asset_db_service() -> StrandedAssetDBService:
    """Get singleton instance of database service."""
    global _db_service
    if _db_service is None:
        _db_service = StrandedAssetDBService()
    return _db_service
