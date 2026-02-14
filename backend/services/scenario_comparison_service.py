"""
Scenario Comparison & Analysis Service.

Provides: multi-scenario comparison, gap analysis, consistency checks.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import statistics

from db.models.data_hub import (
    DataHubScenario, DataHubTrajectory, DataHubComparison,
    GapAnalysis, ConsistencyCheck, ScenarioAlert,
)


class ScenarioComparisonService:
    def __init__(self, db: Session):
        self.db = db

    # ---- Comparison CRUD ----

    def create_comparison(self, data: dict) -> DataHubComparison:
        comp = DataHubComparison(**data)
        self.db.add(comp)
        self.db.commit()
        self.db.refresh(comp)
        return comp

    def get_comparison(self, comp_id: str) -> Optional[DataHubComparison]:
        return self.db.get(DataHubComparison, comp_id)

    def list_comparisons(self):
        return self.db.query(DataHubComparison).order_by(DataHubComparison.created_at.desc()).all()

    def delete_comparison(self, comp_id: str) -> bool:
        comp = self.db.get(DataHubComparison, comp_id)
        if not comp:
            return False
        # Also delete associated gap analyses
        self.db.query(GapAnalysis).filter(GapAnalysis.comparison_id == comp_id).delete()
        self.db.delete(comp)
        self.db.commit()
        return True

    # ---- Build Comparison Data ----

    def build_comparison_data(self, comp_id: str) -> Dict[str, Any]:
        """Build the full comparison dataset for a saved comparison."""
        comp = self.db.get(DataHubComparison, comp_id)
        if not comp:
            raise ValueError("Comparison not found")

        all_ids = [comp.base_scenario_id] + (comp.compare_scenario_ids or [])
        all_ids = [i for i in all_ids if i]
        return self._build_data(all_ids, comp.variable_filter, comp.region_filter, comp.time_range)

    def build_adhoc_comparison(self, scenario_ids: List[str],
                                variables: List[str] = None,
                                regions: List[str] = None,
                                time_range: dict = None) -> Dict[str, Any]:
        """Build comparison data on-the-fly without saving."""
        return self._build_data(scenario_ids, variables, regions, time_range)

    def _build_data(self, scenario_ids: List[str], variables: List[str] = None,
                    regions: List[str] = None, time_range: dict = None) -> Dict[str, Any]:
        """Core: fetch trajectories for given scenarios, align and compute stats."""
        scenarios = self.db.query(DataHubScenario).filter(
            DataHubScenario.id.in_(scenario_ids)
        ).all()

        scenario_map = {}
        for sc in scenarios:
            scenario_map[sc.id] = {
                "id": sc.id, "name": sc.name,
                "display_name": sc.display_name or sc.name,
                "source_name": sc.source.name if sc.source else None,
                "temperature_target": sc.temperature_target,
                "category": sc.category, "model": sc.model,
            }

        # Fetch all trajectories
        q = self.db.query(DataHubTrajectory).filter(
            DataHubTrajectory.scenario_id.in_(scenario_ids)
        )
        if variables:
            q = q.filter(DataHubTrajectory.variable_name.in_(variables))
        if regions:
            q = q.filter(DataHubTrajectory.region.in_(regions))
        trajs = q.all()

        # Group by variable + region
        grouped = {}
        for t in trajs:
            key = (t.variable_name, t.region)
            if key not in grouped:
                grouped[key] = {"variable": t.variable_name, "region": t.region, "unit": t.unit, "series": []}
            ts = t.time_series or {}
            # Filter by time_range
            if time_range:
                start = time_range.get("start_year", 0)
                end = time_range.get("end_year", 9999)
                ts = {y: v for y, v in ts.items() if start <= int(y) <= end}
            grouped[key]["series"].append({
                "scenario_id": t.scenario_id,
                "scenario_name": scenario_map.get(t.scenario_id, {}).get("display_name", "?"),
                "data": ts,
            })

        # Build chart-ready data + stats for each group
        chart_groups = []
        for (var, region), grp in sorted(grouped.items()):
            # Collect all years
            all_years = set()
            for s in grp["series"]:
                all_years.update(s["data"].keys())
            years_sorted = sorted(all_years, key=int)

            # Build chart rows
            chart_data = []
            for year in years_sorted:
                row = {"year": year}
                for s in grp["series"]:
                    row[s["scenario_name"]] = s["data"].get(year)
                chart_data.append(row)

            # Compute statistics
            stats = self._compute_stats(grp["series"], years_sorted)

            chart_groups.append({
                "variable": var,
                "region": region,
                "unit": grp["unit"],
                "scenarios": [s["scenario_name"] for s in grp["series"]],
                "chart_data": chart_data,
                "statistics": stats,
            })

        return {
            "scenarios": list(scenario_map.values()),
            "groups": chart_groups,
            "total_groups": len(chart_groups),
        }

    def _compute_stats(self, series_list, years) -> Dict[str, Any]:
        """Compute statistics across scenarios for each year."""
        if not years or not series_list:
            return {}

        # Differences from first scenario (base)
        base = series_list[0]
        diffs = []
        for other in series_list[1:]:
            diff_data = {}
            for y in years:
                bv = base["data"].get(y)
                ov = other["data"].get(y)
                if bv is not None and ov is not None and bv != 0:
                    diff_data[y] = {
                        "absolute": round(ov - bv, 4),
                        "pct": round((ov - bv) / abs(bv) * 100, 2),
                    }
            diffs.append({
                "scenario": other["scenario_name"],
                "vs_base": base["scenario_name"],
                "diff": diff_data,
            })

        # Summary across all scenarios for last available year
        last_year = years[-1] if years else None
        summary = {}
        if last_year:
            vals = [s["data"].get(last_year) for s in series_list if s["data"].get(last_year) is not None]
            if vals:
                summary = {
                    "year": last_year,
                    "min": round(min(vals), 4),
                    "max": round(max(vals), 4),
                    "mean": round(statistics.mean(vals), 4),
                    "spread": round(max(vals) - min(vals), 4),
                    "spread_pct": round((max(vals) - min(vals)) / abs(statistics.mean(vals)) * 100, 2) if statistics.mean(vals) != 0 else 0,
                }

        return {"differences": diffs, "summary": summary}

    # ---- Gap Analysis ----

    def run_gap_analysis(self, comparison_id: str) -> List[Dict]:
        """Run gap analysis for a comparison. Compares base scenario to each compared scenario."""
        comp = self.db.get(DataHubComparison, comparison_id)
        if not comp or not comp.base_scenario_id:
            raise ValueError("Comparison or base scenario not found")

        # Delete existing analyses for this comparison
        self.db.query(GapAnalysis).filter(GapAnalysis.comparison_id == comparison_id).delete()

        base_id = comp.base_scenario_id
        compare_ids = comp.compare_scenario_ids or []
        variables = comp.variable_filter or []

        # Fetch base trajectories
        q_base = self.db.query(DataHubTrajectory).filter(DataHubTrajectory.scenario_id == base_id)
        if variables:
            q_base = q_base.filter(DataHubTrajectory.variable_name.in_(variables))
        base_trajs = {(t.variable_name, t.region): t for t in q_base.all()}

        results = []
        for cid in compare_ids:
            q_comp = self.db.query(DataHubTrajectory).filter(DataHubTrajectory.scenario_id == cid)
            if variables:
                q_comp = q_comp.filter(DataHubTrajectory.variable_name.in_(variables))

            sc = self.db.get(DataHubScenario, cid)
            sc_name = (sc.display_name or sc.name) if sc else "?"

            for t in q_comp.all():
                key = (t.variable_name, t.region)
                base_t = base_trajs.get(key)
                if not base_t:
                    continue

                # Compare at key years
                for year_str in ["2030", "2040", "2050"]:
                    bv = base_t.time_series.get(year_str)
                    cv = t.time_series.get(year_str)
                    if bv is None or cv is None:
                        continue

                    gap_val = cv - bv
                    gap_pct = (gap_val / abs(bv) * 100) if bv != 0 else 0

                    # Determine gap type
                    vl = t.variable_name.lower()
                    if "emission" in vl:
                        gap_type = "ambition" if gap_val > 0 else "policy"
                    elif "price" in vl and "carbon" in vl:
                        gap_type = "policy"
                    else:
                        gap_type = "implementation"

                    gap = GapAnalysis(
                        comparison_id=comparison_id,
                        gap_type=gap_type,
                        variable=t.variable_name,
                        region=t.region,
                        base_value=round(bv, 4),
                        target_value=round(cv, 4),
                        gap_value=round(gap_val, 4),
                        gap_pct=round(gap_pct, 2),
                        gap_unit=t.unit,
                        year=int(year_str),
                        confidence_level=0.7,
                        required_action=self._suggest_action(gap_type, t.variable_name, gap_pct),
                    )
                    self.db.add(gap)
                    results.append({
                        "gap_type": gap_type, "variable": t.variable_name,
                        "region": t.region, "year": int(year_str),
                        "base_value": round(bv, 4), "target_value": round(cv, 4),
                        "gap_value": round(gap_val, 4), "gap_pct": round(gap_pct, 2),
                        "gap_unit": t.unit,
                        "required_action": gap.required_action,
                        "scenario": sc_name,
                    })

        self.db.commit()
        return results

    def _suggest_action(self, gap_type, variable, gap_pct):
        if abs(gap_pct) < 5:
            return "Minor gap - on track"
        vl = variable.lower()
        if "emission" in vl:
            if gap_pct > 0:
                return f"Emissions {abs(gap_pct):.0f}% above target — accelerate decarbonization policies"
            return f"Emissions {abs(gap_pct):.0f}% below baseline — strong mitigation in place"
        if "price" in vl and "carbon" in vl:
            return f"Carbon price gap of {abs(gap_pct):.0f}% — adjust carbon pricing mechanism"
        if "energy" in vl:
            return f"Energy transition gap of {abs(gap_pct):.0f}% — increase renewable deployment"
        return f"{gap_type.title()} gap of {abs(gap_pct):.0f}% — review policy alignment"

    def get_gap_analyses(self, comparison_id: str):
        return self.db.query(GapAnalysis).filter(
            GapAnalysis.comparison_id == comparison_id
        ).order_by(GapAnalysis.year, GapAnalysis.variable).all()

    # ---- Consistency Checks ----

    def run_consistency_check(self, scenario_id: str) -> List[Dict]:
        """Run consistency checks on a scenario's trajectories."""
        sc = self.db.get(DataHubScenario, scenario_id)
        if not sc:
            raise ValueError("Scenario not found")

        # Delete old checks
        self.db.query(ConsistencyCheck).filter(ConsistencyCheck.scenario_id == scenario_id).delete()

        trajs = self.db.query(DataHubTrajectory).filter(
            DataHubTrajectory.scenario_id == scenario_id
        ).all()
        traj_map = {(t.variable_name, t.region): t for t in trajs}

        checks = []

        # 1. Carbon Budget check
        checks.append(self._check_carbon_budget(scenario_id, traj_map, sc))

        # 2. Energy Balance
        checks.append(self._check_energy_balance(scenario_id, traj_map))

        # 3. Technology deployment rates
        checks.append(self._check_tech_deployment(scenario_id, traj_map))

        # 4. Economic feasibility
        checks.append(self._check_economic_feasibility(scenario_id, traj_map, sc))

        self.db.commit()
        return [c for c in checks if c]

    def _check_carbon_budget(self, scenario_id, traj_map, scenario):
        emissions = traj_map.get(("Emissions|CO2", "World"))
        if not emissions:
            # Try alternative names
            for key in traj_map:
                if "emission" in key[0].lower() and "co2" in key[0].lower() and key[1] == "World":
                    emissions = traj_map[key]
                    break
        if not emissions:
            return self._save_check(scenario_id, "carbon_budget", "warning", 0.5,
                                    ["No CO2 emissions data found for World region"])

        ts = emissions.time_series
        years = sorted(ts.keys(), key=int)
        if len(years) < 2:
            return self._save_check(scenario_id, "carbon_budget", "warning", 0.5,
                                    ["Insufficient time series data"])

        # Check if emissions decline for scenarios targeting < 2C
        last_val = ts.get(years[-1], 0)
        first_val = ts.get(years[0], 0)
        issues = []
        temp = scenario.temperature_target

        if temp and temp < 2.0 and last_val > first_val * 0.5:
            issues.append(f"Emissions in {years[-1]} ({last_val:.1f}) not consistent with {temp}C target — should decline >50% from {years[0]}")
            status, score = "warning", 0.4
        elif temp and temp < 1.5 and last_val > 0:
            issues.append(f"Net-zero not achieved by {years[-1]} for 1.5C target")
            status, score = "warning", 0.3
        else:
            status, score = "pass", 0.9

        return self._save_check(scenario_id, "carbon_budget", status, score, issues,
                                {"first_year": years[0], "last_year": years[-1],
                                 "first_value": round(first_val, 2), "last_value": round(last_val, 2)})

    def _check_energy_balance(self, scenario_id, traj_map):
        total = traj_map.get(("Primary Energy", "World"))
        coal = traj_map.get(("Primary Energy|Coal", "World"))
        gas = traj_map.get(("Primary Energy|Gas", "World"))
        issues = []

        if not total:
            return self._save_check(scenario_id, "energy_balance", "warning", 0.5,
                                    ["No Primary Energy data found"])

        if coal and gas and total:
            # Check that parts don't exceed total at any year
            for y in total.time_series:
                t_val = total.time_series.get(y, 0)
                c_val = coal.time_series.get(y, 0) if coal else 0
                g_val = gas.time_series.get(y, 0) if gas else 0
                if t_val > 0 and (c_val + g_val) > t_val * 1.1:
                    issues.append(f"Year {y}: Coal+Gas ({c_val+g_val:.1f}) exceeds total energy ({t_val:.1f})")

        status = "fail" if len(issues) > 2 else ("warning" if issues else "pass")
        score = max(0.1, 1.0 - len(issues) * 0.2)
        return self._save_check(scenario_id, "energy_balance", status, round(score, 2), issues)

    def _check_tech_deployment(self, scenario_id, traj_map):
        issues = []
        for key, traj in traj_map.items():
            var, region = key
            if region != "World":
                continue
            vl = var.lower()
            if "solar" in vl or "wind" in vl or "capacity" in vl:
                ts = traj.time_series
                years = sorted(ts.keys(), key=int)
                if len(years) >= 2:
                    first, last = ts[years[0]], ts[years[-1]]
                    if first > 0:
                        growth = (last / first - 1) * 100
                        span = int(years[-1]) - int(years[0])
                        annual = growth / span if span > 0 else 0
                        if annual > 20:
                            issues.append(f"{var}: {annual:.1f}%/yr growth may be unrealistic (> 20%/yr)")

        status = "warning" if issues else "pass"
        score = max(0.2, 1.0 - len(issues) * 0.25)
        return self._save_check(scenario_id, "tech_deployment", status, round(score, 2), issues)

    def _check_economic_feasibility(self, scenario_id, traj_map, scenario):
        issues = []
        carbon = None
        for key in traj_map:
            if "price" in key[0].lower() and "carbon" in key[0].lower() and key[1] == "World":
                carbon = traj_map[key]
                break

        if carbon:
            ts = carbon.time_series
            years = sorted(ts.keys(), key=int)
            for i in range(1, len(years)):
                prev, curr = ts[years[i-1]], ts[years[i]]
                if prev > 0:
                    jump = (curr - prev) / prev * 100
                    if jump > 100:
                        issues.append(f"Carbon price jumps {jump:.0f}% from {years[i-1]} to {years[i]} — may cause economic shock")

        status = "warning" if issues else "pass"
        score = max(0.3, 1.0 - len(issues) * 0.2)
        return self._save_check(scenario_id, "economic_feasibility", status, round(score, 2), issues)

    def _save_check(self, scenario_id, check_type, status, score, issues, details=None):
        check = ConsistencyCheck(
            scenario_id=scenario_id, check_type=check_type,
            status=status, score=score, issues=issues or [],
            details=details or {},
        )
        self.db.add(check)
        return {
            "check_type": check_type, "status": status,
            "score": score, "issues": issues or [],
            "details": details or {},
        }

    def get_consistency_checks(self, scenario_id: str):
        return self.db.query(ConsistencyCheck).filter(
            ConsistencyCheck.scenario_id == scenario_id
        ).order_by(ConsistencyCheck.check_type).all()

    # ---- Alerts ----

    def list_alerts(self, user_id: str = "default_user", unread_only: bool = False):
        q = self.db.query(ScenarioAlert).filter(ScenarioAlert.user_id == user_id)
        if unread_only:
            q = q.filter(ScenarioAlert.is_read.is_(False))
        return q.order_by(ScenarioAlert.created_at.desc()).limit(50).all()

    def mark_alert_read(self, alert_id: str):
        alert = self.db.get(ScenarioAlert, alert_id)
        if alert:
            alert.is_read = True
            self.db.commit()
        return alert

    def create_alert(self, data: dict):
        alert = ScenarioAlert(**data)
        self.db.add(alert)
        self.db.commit()
        self.db.refresh(alert)
        return alert
