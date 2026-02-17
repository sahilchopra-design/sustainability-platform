"""
Database service for Real Estate Valuation module.
Provides PostgreSQL-backed data access for properties and comparables.
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


class RealEstateDBService:
    """Database service for real estate valuation data."""
    
    def __init__(self):
        self.engine = get_engine()
    
    # ================== PROPERTIES ==================
    
    def get_all_properties(
        self,
        property_type: Optional[str] = None,
        city: Optional[str] = None,
        user_id: Optional[UUID] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get all properties with optional filtering."""
        with self.engine.connect() as conn:
            conditions = []
            params = {}
            
            if property_type:
                conditions.append("property_type = :property_type")
                params["property_type"] = property_type
            if city:
                conditions.append("city = :city")
                params["city"] = city
            if user_id:
                conditions.append("user_id = :user_id")
                params["user_id"] = str(user_id)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM properties {where_clause}"
            total = conn.execute(text(count_query), params).scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset
            
            query = f"""
                SELECT * FROM properties
                {where_clause}
                ORDER BY created_at DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(self._row_to_property_dict(row))
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    
    def get_property_by_id(self, property_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single property by ID."""
        with self.engine.connect() as conn:
            query = "SELECT * FROM properties WHERE id = :id"
            result = conn.execute(text(query), {"id": str(property_id)})
            row = result.fetchone()
            
            if row:
                return self._row_to_property_dict(row)
            return None
    
    def create_property(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new property."""
        with self.engine.connect() as conn:
            property_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO properties (
                    id, user_id, property_name, property_type, subcategory,
                    address, city, state_province, country, postal_code,
                    latitude, longitude, year_built, gross_floor_area_m2,
                    rentable_area_sf, land_area_acres, num_floors, num_units,
                    construction_type, quality_rating, condition_rating,
                    effective_age, total_economic_life, market_value,
                    replacement_value, land_value, annual_rental_income,
                    potential_gross_income, effective_gross_income,
                    operating_expenses, noi, cap_rate, discount_rate,
                    vacancy_rate, collection_loss_rate, expense_ratio,
                    epc_rating, epc_score, energy_intensity_kwh_m2,
                    created_at, updated_at
                ) VALUES (
                    :id, :user_id, :property_name, :property_type, :subcategory,
                    :address, :city, :state_province, :country, :postal_code,
                    :latitude, :longitude, :year_built, :gross_floor_area_m2,
                    :rentable_area_sf, :land_area_acres, :num_floors, :num_units,
                    :construction_type, :quality_rating, :condition_rating,
                    :effective_age, :total_economic_life, :market_value,
                    :replacement_value, :land_value, :annual_rental_income,
                    :potential_gross_income, :effective_gross_income,
                    :operating_expenses, :noi, :cap_rate, :discount_rate,
                    :vacancy_rate, :collection_loss_rate, :expense_ratio,
                    :epc_rating, :epc_score, :energy_intensity_kwh_m2,
                    :created_at, :updated_at
                )
                RETURNING *
            """
            
            params = {
                "id": property_id,
                "user_id": data.get("user_id"),
                "property_name": data.get("property_name"),
                "property_type": data.get("property_type"),
                "subcategory": data.get("subcategory"),
                "address": data.get("address"),
                "city": data.get("city"),
                "state_province": data.get("state_province"),
                "country": data.get("country"),
                "postal_code": data.get("postal_code"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "year_built": data.get("year_built"),
                "gross_floor_area_m2": data.get("gross_floor_area_m2"),
                "rentable_area_sf": data.get("rentable_area_sf"),
                "land_area_acres": data.get("land_area_acres"),
                "num_floors": data.get("num_floors"),
                "num_units": data.get("num_units"),
                "construction_type": data.get("construction_type"),
                "quality_rating": data.get("quality_rating"),
                "condition_rating": data.get("condition_rating"),
                "effective_age": data.get("effective_age"),
                "total_economic_life": data.get("total_economic_life"),
                "market_value": data.get("market_value"),
                "replacement_value": data.get("replacement_value"),
                "land_value": data.get("land_value"),
                "annual_rental_income": data.get("annual_rental_income"),
                "potential_gross_income": data.get("potential_gross_income"),
                "effective_gross_income": data.get("effective_gross_income"),
                "operating_expenses": data.get("operating_expenses"),
                "noi": data.get("noi"),
                "cap_rate": data.get("cap_rate"),
                "discount_rate": data.get("discount_rate"),
                "vacancy_rate": data.get("vacancy_rate"),
                "collection_loss_rate": data.get("collection_loss_rate"),
                "expense_ratio": data.get("expense_ratio"),
                "epc_rating": data.get("epc_rating"),
                "epc_score": data.get("epc_score"),
                "energy_intensity_kwh_m2": data.get("energy_intensity_kwh_m2"),
                "created_at": now,
                "updated_at": now
            }
            
            result = conn.execute(text(query), params)
            conn.commit()
            row = result.fetchone()
            
            return self._row_to_property_dict(row)
    
    def _row_to_property_dict(self, row) -> Dict[str, Any]:
        """Convert database row to property dictionary."""
        return {
            "id": str(row.id) if row.id else None,
            "user_id": str(row.user_id) if row.user_id else None,
            "property_name": row.property_name,
            "property_type": row.property_type,
            "subcategory": row.subcategory,
            "address": row.address,
            "city": row.city,
            "state_province": row.state_province,
            "country": row.country,
            "postal_code": row.postal_code,
            "latitude": Decimal(str(row.latitude)) if row.latitude else None,
            "longitude": Decimal(str(row.longitude)) if row.longitude else None,
            "year_built": row.year_built,
            "gross_floor_area_m2": Decimal(str(row.gross_floor_area_m2)) if row.gross_floor_area_m2 else None,
            "rentable_area_sf": Decimal(str(row.rentable_area_sf)) if row.rentable_area_sf else Decimal("0"),
            "land_area_acres": Decimal(str(row.land_area_acres)) if row.land_area_acres else None,
            "num_floors": row.num_floors,
            "num_units": row.num_units,
            "construction_type": row.construction_type,
            "quality_rating": row.quality_rating,
            "condition_rating": row.condition_rating,
            "effective_age": row.effective_age,
            "total_economic_life": row.total_economic_life,
            "market_value": Decimal(str(row.market_value)) if row.market_value else Decimal("0"),
            "replacement_value": Decimal(str(row.replacement_value)) if row.replacement_value else None,
            "land_value": Decimal(str(row.land_value)) if row.land_value else None,
            "annual_rental_income": Decimal(str(row.annual_rental_income)) if row.annual_rental_income else None,
            "potential_gross_income": Decimal(str(row.potential_gross_income)) if row.potential_gross_income else None,
            "effective_gross_income": Decimal(str(row.effective_gross_income)) if row.effective_gross_income else None,
            "operating_expenses": Decimal(str(row.operating_expenses)) if row.operating_expenses else None,
            "noi": Decimal(str(row.noi)) if row.noi else Decimal("0"),
            "cap_rate": Decimal(str(row.cap_rate)) if row.cap_rate else Decimal("0"),
            "discount_rate": Decimal(str(row.discount_rate)) if row.discount_rate else None,
            "vacancy_rate": Decimal(str(row.vacancy_rate)) if row.vacancy_rate else None,
            "collection_loss_rate": Decimal(str(row.collection_loss_rate)) if row.collection_loss_rate else None,
            "expense_ratio": Decimal(str(row.expense_ratio)) if row.expense_ratio else None,
            "epc_rating": row.epc_rating,
            "epc_score": Decimal(str(row.epc_score)) if row.epc_score else None,
            "energy_intensity_kwh_m2": Decimal(str(row.energy_intensity_kwh_m2)) if row.energy_intensity_kwh_m2 else None,
            "created_at": row.created_at,
            "updated_at": row.updated_at
        }
    
    # ================== COMPARABLE SALES ==================
    
    def get_all_comparables(
        self,
        property_type: Optional[str] = None,
        city: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get all comparable sales with optional filtering."""
        with self.engine.connect() as conn:
            conditions = []
            params = {}
            
            if property_type:
                conditions.append("property_type = :property_type")
                params["property_type"] = property_type
            if city:
                conditions.append("city = :city")
                params["city"] = city
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            # Get total count
            count_query = f"SELECT COUNT(*) FROM comparable_sales {where_clause}"
            total = conn.execute(text(count_query), params).scalar()
            
            # Get paginated results
            offset = (page - 1) * page_size
            params["limit"] = page_size
            params["offset"] = offset
            
            query = f"""
                SELECT * FROM comparable_sales
                {where_clause}
                ORDER BY sale_date DESC
                LIMIT :limit OFFSET :offset
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            items = []
            for row in rows:
                items.append(self._row_to_comparable_dict(row))
            
            return {
                "items": items,
                "total": total,
                "page": page,
                "page_size": page_size
            }
    
    def get_comparable_by_id(self, comp_id: UUID) -> Optional[Dict[str, Any]]:
        """Get a single comparable sale by ID."""
        with self.engine.connect() as conn:
            query = "SELECT * FROM comparable_sales WHERE id = :id"
            result = conn.execute(text(query), {"id": str(comp_id)})
            row = result.fetchone()
            
            if row:
                return self._row_to_comparable_dict(row)
            return None
    
    def get_comparables_for_property(
        self,
        property_type: str,
        city: Optional[str] = None,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get comparable sales for a property type and city."""
        with self.engine.connect() as conn:
            conditions = ["property_type = :property_type"]
            params = {"property_type": property_type, "limit": limit}
            
            if city:
                conditions.append("city = :city")
                params["city"] = city
            
            where_clause = "WHERE " + " AND ".join(conditions)
            
            query = f"""
                SELECT * FROM comparable_sales
                {where_clause}
                ORDER BY sale_date DESC
                LIMIT :limit
            """
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            return [self._row_to_comparable_dict(row) for row in rows]
    
    def create_comparable(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new comparable sale."""
        with self.engine.connect() as conn:
            comp_id = str(uuid4())
            now = datetime.now(timezone.utc)
            
            query = """
                INSERT INTO comparable_sales (
                    id, property_type, address, city, state_province, country,
                    latitude, longitude, sale_date, sale_price, size_sf,
                    price_per_sf, year_built, num_units, occupancy_rate,
                    quality_rating, condition_rating, location_type,
                    data_source, verified, created_at
                ) VALUES (
                    :id, :property_type, :address, :city, :state_province, :country,
                    :latitude, :longitude, :sale_date, :sale_price, :size_sf,
                    :price_per_sf, :year_built, :num_units, :occupancy_rate,
                    :quality_rating, :condition_rating, :location_type,
                    :data_source, :verified, :created_at
                )
                RETURNING *
            """
            
            params = {
                "id": comp_id,
                "property_type": data.get("property_type"),
                "address": data.get("address"),
                "city": data.get("city"),
                "state_province": data.get("state_province"),
                "country": data.get("country"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "sale_date": data.get("sale_date"),
                "sale_price": data.get("sale_price"),
                "size_sf": data.get("size_sf"),
                "price_per_sf": data.get("price_per_sf"),
                "year_built": data.get("year_built"),
                "num_units": data.get("num_units"),
                "occupancy_rate": data.get("occupancy_rate"),
                "quality_rating": data.get("quality_rating"),
                "condition_rating": data.get("condition_rating"),
                "location_type": data.get("location_type"),
                "data_source": data.get("data_source"),
                "verified": data.get("verified", False),
                "created_at": now
            }
            
            result = conn.execute(text(query), params)
            conn.commit()
            row = result.fetchone()
            
            return self._row_to_comparable_dict(row)
    
    def _row_to_comparable_dict(self, row) -> Dict[str, Any]:
        """Convert database row to comparable dictionary."""
        return {
            "id": str(row.id) if row.id else None,
            "property_type": row.property_type,
            "address": row.address,
            "city": row.city,
            "state_province": row.state_province,
            "country": row.country,
            "latitude": Decimal(str(row.latitude)) if row.latitude else None,
            "longitude": Decimal(str(row.longitude)) if row.longitude else None,
            "sale_date": row.sale_date,
            "sale_price": Decimal(str(row.sale_price)) if row.sale_price else Decimal("0"),
            "size_sf": Decimal(str(row.size_sf)) if row.size_sf else Decimal("0"),
            "price_per_sf": Decimal(str(row.price_per_sf)) if row.price_per_sf else Decimal("0"),
            "year_built": row.year_built,
            "num_units": row.num_units,
            "occupancy_rate": Decimal(str(row.occupancy_rate)) if row.occupancy_rate else None,
            "quality_rating": row.quality_rating,
            "condition_rating": row.condition_rating,
            "location_type": row.location_type,
            "data_source": row.data_source,
            "verified": row.verified if row.verified is not None else False,
            "created_at": row.created_at
        }
    
    # ================== DASHBOARD AGGREGATIONS ==================
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get aggregated dashboard metrics for real estate valuation."""
        with self.engine.connect() as conn:
            # Get property counts and values
            props_result = conn.execute(text("""
                SELECT 
                    COUNT(*) as total,
                    COALESCE(SUM(market_value), 0) as total_value,
                    COALESCE(AVG(cap_rate), 0) as avg_cap_rate,
                    COALESCE(AVG(market_value / NULLIF(rentable_area_sf, 0)), 0) as avg_value_per_sf
                FROM properties
            """))
            props = props_result.fetchone()
            
            # Count by property type
            type_result = conn.execute(text("""
                SELECT property_type, COUNT(*) as count
                FROM properties
                GROUP BY property_type
            """))
            types = {row.property_type: row.count for row in type_result.fetchall()}
            
            # Count total valuations (if table exists)
            try:
                val_count = conn.execute(text("SELECT COUNT(*) FROM valuations")).scalar()
            except Exception:
                val_count = 0
            
            return {
                "total_properties": props.total if props else 0,
                "total_portfolio_value": Decimal(str(props.total_value)) if props else Decimal("0"),
                "avg_cap_rate": Decimal(str(round(float(props.avg_cap_rate or 0), 4))),
                "avg_value_per_sf": Decimal(str(round(float(props.avg_value_per_sf or 0), 2))),
                "total_valuations": val_count,
                "properties_by_type": types
            }


# Singleton instance
_db_service = None

def get_real_estate_db_service() -> RealEstateDBService:
    """Get singleton instance of database service."""
    global _db_service
    if _db_service is None:
        _db_service = RealEstateDBService()
    return _db_service
