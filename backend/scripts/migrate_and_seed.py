"""
Database migrations for Stranded Assets and Real Estate Valuation
Creates tables without FK constraints to missing counterparty table
Seeds with sample data
"""

import os
import uuid
from datetime import datetime, date
from decimal import Decimal

os.environ['DATABASE_URL'] = 'postgresql://postgres.kytzcbipsghprsqoalvi:Zeek%40%402025%40%40@aws-1-us-east-2.pooler.supabase.com:5432/postgres'

from sqlalchemy import create_engine, text, Column, String, Integer, Numeric, Boolean, DateTime, Date, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool

engine = create_engine(os.environ['DATABASE_URL'], poolclass=NullPool)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def create_stranded_asset_tables():
    """Create stranded asset tables using raw SQL (no FK to counterparty)."""
    
    with engine.connect() as conn:
        # Check if tables already exist
        result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'fossil_fuel_reserve')"))
        if result.scalar():
            print("✅ Stranded asset tables already exist")
            return True
        
        print("Creating stranded asset tables...")
        
        # 1. Fossil Fuel Reserves
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS fossil_fuel_reserve (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                asset_name VARCHAR(255) NOT NULL,
                asset_location VARCHAR(100),
                latitude NUMERIC(10, 6),
                longitude NUMERIC(10, 6),
                reserve_type VARCHAR(50) NOT NULL,
                reserve_category VARCHAR(50),
                proven_reserves_mmBOE NUMERIC(15, 4),
                probable_reserves_mmBOE NUMERIC(15, 4),
                possible_reserves_mmBOE NUMERIC(15, 4),
                breakeven_price_USD NUMERIC(10, 2),
                lifting_cost_USD NUMERIC(10, 2),
                remaining_capex_USD NUMERIC(15, 2),
                carbon_intensity_kgCO2_per_unit NUMERIC(10, 4),
                methane_leakage_rate NUMERIC(5, 4),
                production_start_year INTEGER,
                expected_depletion_year INTEGER,
                license_expiry_year INTEGER,
                is_operating BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reserve_type ON fossil_fuel_reserve(reserve_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_reserve_location ON fossil_fuel_reserve(latitude, longitude)"))
        
        # 2. Power Plants
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS power_plant (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                plant_name VARCHAR(255) NOT NULL,
                plant_location VARCHAR(100),
                latitude NUMERIC(10, 6),
                longitude NUMERIC(10, 6),
                country_code VARCHAR(2),
                technology_type VARCHAR(50) NOT NULL,
                capacity_mw NUMERIC(10, 2) NOT NULL,
                commissioning_year INTEGER,
                original_retirement_year INTEGER,
                technical_lifetime_years INTEGER,
                capacity_factor_baseline NUMERIC(5, 4),
                capacity_factor_current NUMERIC(5, 4),
                heat_rate_btu_kwh NUMERIC(10, 2),
                efficiency_percent NUMERIC(5, 2),
                co2_intensity_tco2_mwh NUMERIC(8, 4),
                nox_emissions_kg_mwh NUMERIC(8, 4),
                so2_emissions_kg_mwh NUMERIC(8, 4),
                has_ccs BOOLEAN DEFAULT FALSE,
                ccs_capacity_mtpa NUMERIC(8, 4),
                fixed_om_cost_usd_kw_year NUMERIC(10, 2),
                variable_om_cost_usd_mwh NUMERIC(8, 2),
                fuel_cost_usd_mmbtu NUMERIC(8, 4),
                fuel_type VARCHAR(50),
                offtake_type VARCHAR(50),
                ppa_expiry_year INTEGER,
                ppa_price_usd_mwh NUMERIC(8, 2),
                grid_region VARCHAR(100),
                repurposing_option VARCHAR(100),
                is_operating BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_plant_technology ON power_plant(technology_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_plant_location ON power_plant(latitude, longitude)"))
        
        # 3. Infrastructure Assets
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS infrastructure_asset (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                asset_name VARCHAR(255) NOT NULL,
                asset_type VARCHAR(50) NOT NULL,
                asset_location VARCHAR(100),
                latitude NUMERIC(10, 6),
                longitude NUMERIC(10, 6),
                country_code VARCHAR(2),
                design_capacity VARCHAR(100),
                design_capacity_unit VARCHAR(20),
                current_capacity_utilized VARCHAR(100),
                utilization_rate_percent NUMERIC(5, 2),
                commissioning_year INTEGER,
                expected_retirement_year INTEGER,
                remaining_book_value_usd NUMERIC(15, 2),
                replacement_cost_usd NUMERIC(15, 2),
                contract_maturity_profile JSONB,
                take_or_pay_exposure_usd NUMERIC(15, 2),
                contracted_volume_percent NUMERIC(5, 2),
                hydrogen_ready BOOLEAN DEFAULT FALSE,
                ammonia_ready BOOLEAN DEFAULT FALSE,
                ccs_compatible BOOLEAN DEFAULT FALSE,
                regulatory_status VARCHAR(50),
                environmental_permits JSONB,
                is_operating BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_infra_type ON infrastructure_asset(asset_type)"))
        
        # 4. Energy Transition Pathways
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS energy_transition_pathway (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                pathway_name VARCHAR(100) NOT NULL,
                sector VARCHAR(50) NOT NULL,
                region VARCHAR(50),
                country_code VARCHAR(2),
                scenario_id UUID,
                base_year INTEGER NOT NULL,
                target_year INTEGER NOT NULL,
                demand_trajectory JSONB,
                price_trajectory JSONB,
                capacity_trajectory JSONB,
                peak_demand_year INTEGER,
                net_zero_year INTEGER,
                carbon_price_trajectory JSONB,
                policy_assumptions JSONB,
                technology_assumptions JSONB,
                source_document VARCHAR(255),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_pathway_sector ON energy_transition_pathway(sector, region)"))
        
        conn.commit()
        print("✅ Stranded asset tables created successfully")
        return True


def create_real_estate_tables():
    """Create real estate valuation tables using raw SQL."""
    
    with engine.connect() as conn:
        # Check if tables already exist
        result = conn.execute(text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'properties')"))
        if result.scalar():
            print("✅ Real estate tables already exist")
            return True
        
        print("Creating real estate valuation tables...")
        
        # 1. Properties Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS properties (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID,
                property_name VARCHAR(255) NOT NULL,
                property_type VARCHAR(50) NOT NULL,
                subcategory VARCHAR(100),
                address TEXT,
                city VARCHAR(100),
                state_province VARCHAR(100),
                country VARCHAR(100),
                postal_code VARCHAR(20),
                latitude NUMERIC(10, 8),
                longitude NUMERIC(11, 8),
                year_built INTEGER,
                gross_floor_area_m2 NUMERIC(10, 2),
                rentable_area_sf NUMERIC(10, 2),
                land_area_acres NUMERIC(8, 4),
                num_floors INTEGER,
                num_units INTEGER,
                construction_type VARCHAR(50),
                quality_rating VARCHAR(20),
                condition_rating VARCHAR(20),
                effective_age INTEGER,
                total_economic_life INTEGER,
                market_value NUMERIC(15, 2),
                replacement_value NUMERIC(15, 2),
                land_value NUMERIC(15, 2),
                annual_rental_income NUMERIC(12, 2),
                potential_gross_income NUMERIC(12, 2),
                effective_gross_income NUMERIC(12, 2),
                operating_expenses NUMERIC(12, 2),
                noi NUMERIC(12, 2),
                cap_rate NUMERIC(5, 4),
                discount_rate NUMERIC(5, 4),
                vacancy_rate NUMERIC(5, 4),
                collection_loss_rate NUMERIC(5, 4),
                expense_ratio NUMERIC(5, 4),
                epc_rating VARCHAR(10),
                epc_score NUMERIC(5, 2),
                energy_intensity_kwh_m2 NUMERIC(8, 2),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_properties_property_type ON properties(property_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_properties_city ON properties(city)"))
        
        # 2. Valuations Table
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS valuations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_id UUID REFERENCES properties(id) ON DELETE CASCADE,
                valuation_date DATE NOT NULL,
                income_approach_value NUMERIC(15, 2),
                income_method VARCHAR(20),
                pgi NUMERIC(12, 2),
                egi NUMERIC(12, 2),
                noi NUMERIC(12, 2),
                cap_rate_used NUMERIC(5, 4),
                dcf_npv NUMERIC(15, 2),
                dcf_irr NUMERIC(5, 4),
                cost_approach_value NUMERIC(15, 2),
                land_value NUMERIC(15, 2),
                rcn NUMERIC(15, 2),
                physical_depreciation NUMERIC(15, 2),
                functional_obsolescence NUMERIC(15, 2),
                external_obsolescence NUMERIC(15, 2),
                total_depreciation NUMERIC(15, 2),
                depreciated_improvements NUMERIC(15, 2),
                sales_comparison_value NUMERIC(15, 2),
                num_comparables_used INTEGER,
                avg_adjustment_pct NUMERIC(5, 2),
                reconciled_base_value NUMERIC(15, 2),
                income_weight NUMERIC(3, 2),
                cost_weight NUMERIC(3, 2),
                sales_weight NUMERIC(3, 2),
                adjusted_value NUMERIC(15, 2),
                value_per_sf NUMERIC(10, 2),
                confidence_range_low NUMERIC(15, 2),
                confidence_range_high NUMERIC(15, 2),
                calculation_inputs JSONB,
                calculation_details JSONB,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_valuations_property_id ON valuations(property_id)"))
        
        # 3. Comparable Sales
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS comparable_sales (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                property_type VARCHAR(50) NOT NULL,
                address TEXT,
                city VARCHAR(100),
                state_province VARCHAR(100),
                country VARCHAR(100),
                latitude NUMERIC(10, 8),
                longitude NUMERIC(11, 8),
                sale_date DATE,
                sale_price NUMERIC(15, 2),
                size_sf NUMERIC(10, 2),
                price_per_sf NUMERIC(10, 2),
                year_built INTEGER,
                num_units INTEGER,
                occupancy_rate NUMERIC(5, 4),
                quality_rating VARCHAR(20),
                condition_rating VARCHAR(20),
                location_type VARCHAR(50),
                data_source VARCHAR(100),
                verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comparable_sales_property_type ON comparable_sales(property_type)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS ix_comparable_sales_city ON comparable_sales(city)"))
        
        conn.commit()
        print("✅ Real estate valuation tables created successfully")
        return True


def seed_stranded_asset_data():
    """Seed stranded asset tables with sample data."""
    
    with engine.connect() as conn:
        # Check if data exists
        result = conn.execute(text("SELECT COUNT(*) FROM fossil_fuel_reserve"))
        if result.scalar() > 0:
            print("✅ Stranded asset data already seeded")
            return True
        
        print("Seeding stranded asset sample data...")
        
        # Seed Fossil Fuel Reserves
        reserves = [
            {
                "asset_name": "North Sea Oil Field Alpha",
                "asset_location": "North Sea",
                "latitude": 58.5,
                "longitude": 1.5,
                "reserve_type": "oil",
                "reserve_category": "2P",
                "proven_reserves_mmBOE": 150.0,
                "probable_reserves_mmBOE": 75.0,
                "breakeven_price_USD": 55.0,
                "lifting_cost_USD": 18.0,
                "remaining_capex_USD": 500000000.0,
                "carbon_intensity_kgCO2_per_unit": 420.0,
                "methane_leakage_rate": 0.015,
                "production_start_year": 2010,
                "expected_depletion_year": 2045,
            },
            {
                "asset_name": "Permian Basin Gas Field",
                "asset_location": "Texas, USA",
                "latitude": 31.5,
                "longitude": -102.5,
                "reserve_type": "gas",
                "reserve_category": "1P",
                "proven_reserves_mmBOE": 80.0,
                "probable_reserves_mmBOE": 40.0,
                "breakeven_price_USD": 3.5,
                "lifting_cost_USD": 12.0,
                "remaining_capex_USD": 200000000.0,
                "carbon_intensity_kgCO2_per_unit": 55.0,
                "methane_leakage_rate": 0.025,
                "production_start_year": 2015,
                "expected_depletion_year": 2040,
            },
            {
                "asset_name": "Queensland Coal Mine",
                "asset_location": "Queensland, Australia",
                "latitude": -23.5,
                "longitude": 148.0,
                "reserve_type": "coal",
                "reserve_category": "2P",
                "proven_reserves_mmBOE": 200.0,
                "probable_reserves_mmBOE": 100.0,
                "breakeven_price_USD": 65.0,
                "lifting_cost_USD": 25.0,
                "remaining_capex_USD": 300000000.0,
                "carbon_intensity_kgCO2_per_unit": 2450.0,
                "methane_leakage_rate": 0.008,
                "production_start_year": 2008,
                "expected_depletion_year": 2038,
            },
        ]
        
        for r in reserves:
            conn.execute(text("""
                INSERT INTO fossil_fuel_reserve (
                    asset_name, asset_location, latitude, longitude, reserve_type,
                    reserve_category, proven_reserves_mmBOE, probable_reserves_mmBOE,
                    breakeven_price_USD, lifting_cost_USD, remaining_capex_USD,
                    carbon_intensity_kgCO2_per_unit, methane_leakage_rate,
                    production_start_year, expected_depletion_year
                ) VALUES (
                    :asset_name, :asset_location, :latitude, :longitude, :reserve_type,
                    :reserve_category, :proven_reserves_mmBOE, :probable_reserves_mmBOE,
                    :breakeven_price_USD, :lifting_cost_USD, :remaining_capex_USD,
                    :carbon_intensity_kgCO2_per_unit, :methane_leakage_rate,
                    :production_start_year, :expected_depletion_year
                )
            """), r)
        
        # Seed Power Plants
        plants = [
            {
                "plant_name": "Drax Coal Power Station",
                "plant_location": "Yorkshire, UK",
                "latitude": 53.75,
                "longitude": -0.99,
                "country_code": "GB",
                "technology_type": "coal",
                "capacity_mw": 2600.0,
                "commissioning_year": 1986,
                "original_retirement_year": 2035,
                "technical_lifetime_years": 50,
                "capacity_factor_baseline": 0.55,
                "co2_intensity_tco2_mwh": 0.92,
                "fixed_om_cost_usd_kw_year": 35.0,
                "variable_om_cost_usd_mwh": 4.5,
                "fuel_cost_usd_mmbtu": 2.5,
                "fuel_type": "coal",
                "offtake_type": "merchant",
            },
            {
                "plant_name": "Pembroke CCGT",
                "plant_location": "Wales, UK",
                "latitude": 51.68,
                "longitude": -4.99,
                "country_code": "GB",
                "technology_type": "gas_ccgt",
                "capacity_mw": 2200.0,
                "commissioning_year": 2012,
                "original_retirement_year": 2047,
                "technical_lifetime_years": 35,
                "capacity_factor_baseline": 0.58,
                "co2_intensity_tco2_mwh": 0.38,
                "fixed_om_cost_usd_kw_year": 18.0,
                "variable_om_cost_usd_mwh": 2.8,
                "fuel_cost_usd_mmbtu": 4.5,
                "fuel_type": "natural_gas",
                "offtake_type": "ppa",
            },
            {
                "plant_name": "Ratcliffe-on-Soar",
                "plant_location": "Nottinghamshire, UK",
                "latitude": 52.86,
                "longitude": -1.25,
                "country_code": "GB",
                "technology_type": "gas_ocgt",
                "capacity_mw": 500.0,
                "commissioning_year": 1998,
                "original_retirement_year": 2028,
                "technical_lifetime_years": 30,
                "capacity_factor_baseline": 0.15,
                "co2_intensity_tco2_mwh": 0.52,
                "fixed_om_cost_usd_kw_year": 12.0,
                "variable_om_cost_usd_mwh": 5.5,
                "fuel_cost_usd_mmbtu": 4.5,
                "fuel_type": "natural_gas",
                "offtake_type": "merchant",
            },
        ]
        
        for p in plants:
            conn.execute(text("""
                INSERT INTO power_plant (
                    plant_name, plant_location, latitude, longitude, country_code,
                    technology_type, capacity_mw, commissioning_year, original_retirement_year,
                    technical_lifetime_years, capacity_factor_baseline, co2_intensity_tco2_mwh,
                    fixed_om_cost_usd_kw_year, variable_om_cost_usd_mwh, fuel_cost_usd_mmbtu,
                    fuel_type, offtake_type
                ) VALUES (
                    :plant_name, :plant_location, :latitude, :longitude, :country_code,
                    :technology_type, :capacity_mw, :commissioning_year, :original_retirement_year,
                    :technical_lifetime_years, :capacity_factor_baseline, :co2_intensity_tco2_mwh,
                    :fixed_om_cost_usd_kw_year, :variable_om_cost_usd_mwh, :fuel_cost_usd_mmbtu,
                    :fuel_type, :offtake_type
                )
            """), p)
        
        # Seed Infrastructure Assets
        infrastructure = [
            {
                "asset_name": "Trans-Alaska Pipeline",
                "asset_type": "pipeline_oil",
                "asset_location": "Alaska, USA",
                "latitude": 64.5,
                "longitude": -149.0,
                "country_code": "US",
                "design_capacity": "2.1",
                "design_capacity_unit": "mbpd",
                "utilization_rate_percent": 45.0,
                "commissioning_year": 1977,
                "expected_retirement_year": 2040,
                "remaining_book_value_usd": 2500000000.0,
                "replacement_cost_usd": 12000000000.0,
                "take_or_pay_exposure_usd": 500000000.0,
                "hydrogen_ready": False,
                "ammonia_ready": False,
                "ccs_compatible": False,
            },
            {
                "asset_name": "Nord Stream 1",
                "asset_type": "pipeline_gas",
                "asset_location": "Baltic Sea",
                "latitude": 54.5,
                "longitude": 13.5,
                "country_code": "DE",
                "design_capacity": "55",
                "design_capacity_unit": "bcm/year",
                "utilization_rate_percent": 0.0,
                "commissioning_year": 2011,
                "expected_retirement_year": 2050,
                "remaining_book_value_usd": 4000000000.0,
                "replacement_cost_usd": 8000000000.0,
                "take_or_pay_exposure_usd": 1200000000.0,
                "hydrogen_ready": True,
                "ammonia_ready": False,
                "ccs_compatible": False,
            },
            {
                "asset_name": "Sabine Pass LNG Terminal",
                "asset_type": "lng_terminal",
                "asset_location": "Louisiana, USA",
                "latitude": 29.73,
                "longitude": -93.86,
                "country_code": "US",
                "design_capacity": "30",
                "design_capacity_unit": "mtpa",
                "utilization_rate_percent": 95.0,
                "commissioning_year": 2016,
                "expected_retirement_year": 2056,
                "remaining_book_value_usd": 15000000000.0,
                "replacement_cost_usd": 22000000000.0,
                "take_or_pay_exposure_usd": 3500000000.0,
                "hydrogen_ready": False,
                "ammonia_ready": True,
                "ccs_compatible": True,
            },
        ]
        
        for i in infrastructure:
            conn.execute(text("""
                INSERT INTO infrastructure_asset (
                    asset_name, asset_type, asset_location, latitude, longitude,
                    country_code, design_capacity, design_capacity_unit, utilization_rate_percent,
                    commissioning_year, expected_retirement_year, remaining_book_value_usd,
                    replacement_cost_usd, take_or_pay_exposure_usd, hydrogen_ready,
                    ammonia_ready, ccs_compatible
                ) VALUES (
                    :asset_name, :asset_type, :asset_location, :latitude, :longitude,
                    :country_code, :design_capacity, :design_capacity_unit, :utilization_rate_percent,
                    :commissioning_year, :expected_retirement_year, :remaining_book_value_usd,
                    :replacement_cost_usd, :take_or_pay_exposure_usd, :hydrogen_ready,
                    :ammonia_ready, :ccs_compatible
                )
            """), i)
        
        # Seed Energy Transition Pathways
        pathways = [
            {
                "pathway_name": "IEA Net Zero by 2050",
                "sector": "oil",
                "region": "global",
                "base_year": 2025,
                "target_year": 2050,
                "demand_trajectory": {"2025": 100, "2030": 88, "2035": 72, "2040": 55, "2045": 35, "2050": 24},
                "peak_demand_year": 2023,
                "net_zero_year": 2050,
                "carbon_price_trajectory": {"2025": 85, "2030": 130, "2035": 180, "2040": 230, "2045": 280, "2050": 250},
            },
            {
                "pathway_name": "IEA Announced Pledges",
                "sector": "gas",
                "region": "global",
                "base_year": 2025,
                "target_year": 2050,
                "demand_trajectory": {"2025": 100, "2030": 102, "2035": 98, "2040": 90, "2045": 80, "2050": 70},
                "peak_demand_year": 2030,
                "net_zero_year": None,
                "carbon_price_trajectory": {"2025": 85, "2030": 100, "2035": 120, "2040": 145, "2045": 170, "2050": 200},
            },
            {
                "pathway_name": "IEA STEPS",
                "sector": "coal",
                "region": "global",
                "base_year": 2025,
                "target_year": 2050,
                "demand_trajectory": {"2025": 100, "2030": 95, "2035": 85, "2040": 75, "2045": 65, "2050": 55},
                "peak_demand_year": 2023,
                "net_zero_year": None,
                "carbon_price_trajectory": {"2025": 50, "2030": 60, "2035": 75, "2040": 90, "2045": 105, "2050": 120},
            },
        ]
        
        import json
        for pw in pathways:
            conn.execute(text("""
                INSERT INTO energy_transition_pathway (
                    pathway_name, sector, region, base_year, target_year,
                    demand_trajectory, peak_demand_year, net_zero_year, carbon_price_trajectory
                ) VALUES (
                    :pathway_name, :sector, :region, :base_year, :target_year,
                    :demand_trajectory, :peak_demand_year, :net_zero_year, :carbon_price_trajectory
                )
            """), {
                **pw,
                "demand_trajectory": json.dumps(pw["demand_trajectory"]),
                "carbon_price_trajectory": json.dumps(pw["carbon_price_trajectory"]),
            })
        
        conn.commit()
        print("✅ Stranded asset data seeded successfully")
        return True


def seed_real_estate_data():
    """Seed real estate tables with sample data."""
    
    with engine.connect() as conn:
        # Check if data exists
        result = conn.execute(text("SELECT COUNT(*) FROM properties"))
        if result.scalar() > 0:
            print("✅ Real estate data already seeded")
            return True
        
        print("Seeding real estate sample data...")
        
        # Seed Properties
        properties = [
            {
                "property_name": "Downtown Office Tower",
                "property_type": "office",
                "address": "100 Main Street",
                "city": "New York",
                "state_province": "NY",
                "country": "USA",
                "latitude": 40.7128,
                "longitude": -74.0060,
                "year_built": 2005,
                "rentable_area_sf": 450000.0,
                "land_area_acres": 1.5,
                "num_floors": 35,
                "num_units": None,
                "construction_type": "steel_frame",
                "quality_rating": "class_a",
                "condition_rating": "excellent",
                "effective_age": 12,
                "total_economic_life": 50,
                "market_value": 450000000.0,
                "noi": 24750000.0,
                "cap_rate": 0.055,
                "vacancy_rate": 0.08,
                "expense_ratio": 0.35,
            },
            {
                "property_name": "Suburban Retail Center",
                "property_type": "retail",
                "address": "500 Shopping Plaza Drive",
                "city": "Los Angeles",
                "state_province": "CA",
                "country": "USA",
                "latitude": 34.0522,
                "longitude": -118.2437,
                "year_built": 2010,
                "rentable_area_sf": 180000.0,
                "land_area_acres": 12.0,
                "num_floors": 2,
                "num_units": None,
                "construction_type": "concrete",
                "quality_rating": "class_b",
                "condition_rating": "good",
                "effective_age": 10,
                "total_economic_life": 40,
                "market_value": 85000000.0,
                "noi": 5950000.0,
                "cap_rate": 0.070,
                "vacancy_rate": 0.12,
                "expense_ratio": 0.28,
            },
            {
                "property_name": "Industrial Distribution Center",
                "property_type": "industrial",
                "address": "2000 Logistics Way",
                "city": "Chicago",
                "state_province": "IL",
                "country": "USA",
                "latitude": 41.8781,
                "longitude": -87.6298,
                "year_built": 2018,
                "rentable_area_sf": 750000.0,
                "land_area_acres": 25.0,
                "num_floors": 1,
                "num_units": None,
                "construction_type": "prefabricated",
                "quality_rating": "class_a",
                "condition_rating": "excellent",
                "effective_age": 5,
                "total_economic_life": 35,
                "market_value": 120000000.0,
                "noi": 6600000.0,
                "cap_rate": 0.055,
                "vacancy_rate": 0.03,
                "expense_ratio": 0.18,
            },
            {
                "property_name": "Urban Multifamily Complex",
                "property_type": "multifamily",
                "address": "800 Residential Blvd",
                "city": "Seattle",
                "state_province": "WA",
                "country": "USA",
                "latitude": 47.6062,
                "longitude": -122.3321,
                "year_built": 2015,
                "rentable_area_sf": 320000.0,
                "land_area_acres": 3.5,
                "num_floors": 12,
                "num_units": 280,
                "construction_type": "concrete",
                "quality_rating": "class_a",
                "condition_rating": "excellent",
                "effective_age": 7,
                "total_economic_life": 50,
                "market_value": 175000000.0,
                "noi": 8750000.0,
                "cap_rate": 0.050,
                "vacancy_rate": 0.05,
                "expense_ratio": 0.38,
            },
        ]
        
        for prop in properties:
            conn.execute(text("""
                INSERT INTO properties (
                    property_name, property_type, address, city, state_province,
                    country, latitude, longitude, year_built, rentable_area_sf,
                    land_area_acres, num_floors, num_units, construction_type,
                    quality_rating, condition_rating, effective_age, total_economic_life,
                    market_value, noi, cap_rate, vacancy_rate, expense_ratio
                ) VALUES (
                    :property_name, :property_type, :address, :city, :state_province,
                    :country, :latitude, :longitude, :year_built, :rentable_area_sf,
                    :land_area_acres, :num_floors, :num_units, :construction_type,
                    :quality_rating, :condition_rating, :effective_age, :total_economic_life,
                    :market_value, :noi, :cap_rate, :vacancy_rate, :expense_ratio
                )
            """), prop)
        
        # Seed Comparable Sales
        comparables = [
            {
                "property_type": "office",
                "address": "200 Financial District",
                "city": "New York",
                "state_province": "NY",
                "country": "USA",
                "sale_date": "2024-06-15",
                "sale_price": 380000000.0,
                "size_sf": 400000.0,
                "price_per_sf": 950.0,
                "year_built": 2003,
                "quality_rating": "class_a",
                "condition_rating": "good",
                "location_type": "cbd",
                "verified": True,
            },
            {
                "property_type": "office",
                "address": "150 Park Avenue",
                "city": "New York",
                "state_province": "NY",
                "country": "USA",
                "sale_date": "2024-03-20",
                "sale_price": 425000000.0,
                "size_sf": 380000.0,
                "price_per_sf": 1118.42,
                "year_built": 2008,
                "quality_rating": "class_a",
                "condition_rating": "excellent",
                "location_type": "cbd_prime",
                "verified": True,
            },
            {
                "property_type": "retail",
                "address": "450 Commerce Center",
                "city": "Los Angeles",
                "state_province": "CA",
                "country": "USA",
                "sale_date": "2024-08-10",
                "sale_price": 72000000.0,
                "size_sf": 160000.0,
                "price_per_sf": 450.0,
                "year_built": 2012,
                "quality_rating": "class_b",
                "condition_rating": "good",
                "location_type": "suburban",
                "verified": True,
            },
            {
                "property_type": "industrial",
                "address": "3000 Warehouse Road",
                "city": "Chicago",
                "state_province": "IL",
                "country": "USA",
                "sale_date": "2024-09-05",
                "sale_price": 95000000.0,
                "size_sf": 680000.0,
                "price_per_sf": 139.71,
                "year_built": 2020,
                "quality_rating": "class_a",
                "condition_rating": "excellent",
                "location_type": "suburban",
                "verified": True,
            },
            {
                "property_type": "multifamily",
                "address": "950 Urban Living",
                "city": "Seattle",
                "state_province": "WA",
                "country": "USA",
                "sale_date": "2024-07-22",
                "sale_price": 155000000.0,
                "size_sf": 290000.0,
                "price_per_sf": 534.48,
                "year_built": 2016,
                "num_units": 250,
                "quality_rating": "class_a",
                "condition_rating": "excellent",
                "location_type": "urban",
                "verified": True,
            },
        ]
        
        for comp in comparables:
            conn.execute(text("""
                INSERT INTO comparable_sales (
                    property_type, address, city, state_province, country,
                    sale_date, sale_price, size_sf, price_per_sf, year_built,
                    num_units, quality_rating, condition_rating, location_type, verified
                ) VALUES (
                    :property_type, :address, :city, :state_province, :country,
                    :sale_date, :sale_price, :size_sf, :price_per_sf, :year_built,
                    :num_units, :quality_rating, :condition_rating, :location_type, :verified
                )
            """), comp)
        
        conn.commit()
        print("✅ Real estate data seeded successfully")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("Database Migration & Seeding Script")
    print("=" * 60)
    
    # Create tables
    create_stranded_asset_tables()
    create_real_estate_tables()
    
    # Seed data
    seed_stranded_asset_data()
    seed_real_estate_data()
    
    print("=" * 60)
    print("✅ All migrations and seeding complete!")
    print("=" * 60)
