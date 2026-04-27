"""
Unit tests for AgriTwin-ZM v1.0

Covers all six core classes with normal inputs, edge cases, and
invalid input validation.
"""

import json
import os
import tempfile
import unittest

from models.maize import Maize
from models.tomato import Tomato
from engines.supply_demand import SupplyDemandEngine
from engines.storage_loss import StorageLossSimulator
from engines.policy import PolicyEngine
from reports.dashboard import ReportingDashboard


# ===================================================================
# Maize Tests
# ===================================================================

class TestMaize(unittest.TestCase):
    """Tests for the Maize commodity model."""

    def setUp(self):
        self.maize = Maize(10_000, 15_000, 13.5, 4_500, 3.0)

    # Normal inputs
    def test_calculate_monthly_loss(self):
        loss = self.maize.calculate_monthly_loss()
        self.assertAlmostEqual(loss, 300.0)

    def test_to_dict_contains_all_keys(self):
        d = self.maize.to_dict()
        self.assertEqual(d["commodity"], "Maize")
        self.assertEqual(d["production_volume"], 10_000)
        self.assertEqual(d["moisture_level"], 13.5)

    def test_from_dict_round_trip(self):
        d = self.maize.to_dict()
        restored = Maize.from_dict(d)
        self.assertEqual(restored.production_volume, self.maize.production_volume)
        self.assertEqual(restored.price_per_ton, self.maize.price_per_ton)

    # Edge cases
    def test_zero_production(self):
        m = Maize(0, 1000, 10, 4000, 5)
        self.assertEqual(m.calculate_monthly_loss(), 0.0)

    def test_zero_loss_percentage(self):
        m = Maize(5000, 5000, 12, 3000, 0)
        self.assertEqual(m.calculate_monthly_loss(), 0.0)

    # Invalid inputs
    def test_negative_production_raises(self):
        with self.assertRaises(ValueError):
            Maize(-100, 500, 13, 4500, 3)

    def test_string_price_raises(self):
        with self.assertRaises(TypeError):
            Maize(1000, 500, 13, "expensive", 3)

    def test_moisture_over_100_raises(self):
        with self.assertRaises(ValueError):
            Maize(1000, 500, 110, 4500, 3)

    def test_from_dict_missing_key_raises(self):
        with self.assertRaises(KeyError):
            Maize.from_dict({"production_volume": 1000})


# ===================================================================
# Tomato Tests
# ===================================================================

class TestTomato(unittest.TestCase):
    """Tests for the Tomato commodity model."""

    def setUp(self):
        self.tomato = Tomato(500, 14, "cold", 1.5, 120)

    # Normal inputs
    def test_calculate_spoilage_7_days(self):
        result = self.tomato.calculate_spoilage(7)
        self.assertEqual(result["days_stored"], 7)
        self.assertGreater(result["total_spoilage_tons"], 0)
        self.assertLess(result["remaining_volume_tons"], 500)

    def test_crates_from_production(self):
        # 500 tons = 500,000 kg / 15 kg = 33,333.33 crates
        self.assertAlmostEqual(self.tomato.crates_from_production, 33333.33, places=1)

    def test_to_dict_from_dict_round_trip(self):
        d = self.tomato.to_dict()
        restored = Tomato.from_dict(d)
        self.assertEqual(restored.production_volume, self.tomato.production_volume)
        self.assertEqual(restored.storage_type, self.tomato.storage_type)

    # Edge cases
    def test_zero_days_spoilage(self):
        result = self.tomato.calculate_spoilage(0)
        self.assertEqual(result["total_spoilage_tons"], 0)
        self.assertEqual(result["remaining_volume_tons"], 500)

    def test_full_spoilage_many_days(self):
        result = self.tomato.calculate_spoilage(500)
        # After 500 days at 1.5%/day, almost everything is gone
        self.assertLess(result["remaining_volume_tons"], 1.0)
        self.assertGreater(result["total_spoilage_percentage"], 99)

    # Invalid inputs
    def test_invalid_storage_type_raises(self):
        with self.assertRaises(ValueError):
            Tomato(500, 14, "fridge", 1.5, 120)

    def test_negative_spoilage_rate_raises(self):
        with self.assertRaises(ValueError):
            Tomato(500, 14, "cold", -5, 120)

    def test_spoilage_negative_days_raises(self):
        with self.assertRaises(ValueError):
            self.tomato.calculate_spoilage(-3)

    def test_spoilage_string_days_raises(self):
        with self.assertRaises(TypeError):
            self.tomato.calculate_spoilage("five")


# ===================================================================
# SupplyDemandEngine Tests
# ===================================================================

class TestSupplyDemandEngine(unittest.TestCase):
    """Tests for the SupplyDemandEngine."""

    def setUp(self):
        self.maize = Maize(10_000, 15_000, 13, 4_500, 3)
        self.tomato = Tomato(500, 14, "cold", 1.5, 120)

    # Normal inputs
    def test_surplus_when_production_exceeds_demand(self):
        engine = SupplyDemandEngine(self.maize, 10_000, 8_000)
        self.assertEqual(engine.calculate_surplus(), 2_000)
        self.assertEqual(engine.calculate_shortage(), 0)

    def test_shortage_when_demand_exceeds_production(self):
        engine = SupplyDemandEngine(self.maize, 5_000, 8_000)
        self.assertEqual(engine.calculate_shortage(), 3_000)
        self.assertEqual(engine.calculate_surplus(), 0)

    def test_revenue_maize(self):
        engine = SupplyDemandEngine(self.maize, 10_000, 8_000)
        # sells 8000 tons at 4500 ZMW each
        self.assertEqual(engine.calculate_revenue(), 8_000 * 4_500)

    def test_run_monthly_simulation_keys(self):
        engine = SupplyDemandEngine(self.maize, 10_000, 10_000)
        result = engine.run_monthly_simulation("January", 100)
        expected_keys = {"month", "commodity", "monthly_production",
                         "market_demand", "surplus", "shortage",
                         "spoilage_tons", "waste_percentage", "revenue_zmw",
                         "price_adjustment", "demand_met",
                         "food_security_percentage"}
        self.assertEqual(set(result.keys()), expected_keys)

    # Edge cases
    def test_zero_production_zero_demand(self):
        engine = SupplyDemandEngine(self.maize, 0, 0)
        self.assertEqual(engine.calculate_surplus(), 0)
        self.assertEqual(engine.calculate_shortage(), 0)
        self.assertEqual(engine.calculate_waste(0), 0)

    def test_price_drops_on_large_surplus(self):
        engine = SupplyDemandEngine(self.maize, 20_000, 10_000)
        adj = engine.adjust_price()
        self.assertEqual(adj["adjustment"], "-15%")

    def test_price_rises_on_large_shortage(self):
        engine = SupplyDemandEngine(self.maize, 5_000, 20_000)
        adj = engine.adjust_price()
        self.assertEqual(adj["adjustment"], "+20%")

    # Invalid inputs
    def test_invalid_commodity_raises(self):
        with self.assertRaises(TypeError):
            SupplyDemandEngine("not_a_commodity", 1000, 1000)

    def test_negative_production_raises(self):
        with self.assertRaises(ValueError):
            SupplyDemandEngine(self.maize, -100, 1000)

    def test_negative_spoilage_raises(self):
        engine = SupplyDemandEngine(self.maize, 1000, 1000)
        with self.assertRaises(ValueError):
            engine.calculate_waste(-50)


# ===================================================================
# StorageLossSimulator Tests
# ===================================================================

class TestStorageLossSimulator(unittest.TestCase):
    """Tests for the StorageLossSimulator."""

    def setUp(self):
        self.sim = StorageLossSimulator()

    # Normal inputs
    def test_maize_storage_returns_correct_length(self):
        results = self.sim.simulate_maize_storage(10_000, 3.0, 6)
        self.assertEqual(len(results), 6)

    def test_maize_stock_decreases_each_month(self):
        results = self.sim.simulate_maize_storage(10_000, 5.0, 3)
        for i in range(1, len(results)):
            self.assertLess(results[i]["stock_remaining"],
                            results[i - 1]["stock_remaining"])

    def test_tomato_storage_cold_vs_open(self):
        cold = self.sim.simulate_tomato_storage(100, "cold", 7)
        open_ = self.sim.simulate_tomato_storage(100, "open", 7)
        # Open storage should lose more
        self.assertGreater(open_[-1]["total_spoilage_pct"],
                           cold[-1]["total_spoilage_pct"])

    def test_generate_loss_summary_maize(self):
        self.sim.simulate_maize_storage(5000, 2, 3)
        summary = self.sim.generate_loss_summary("maize")
        self.assertIn("MAIZE", summary)

    # Edge cases
    def test_zero_months(self):
        results = self.sim.simulate_maize_storage(10_000, 3.0, 0)
        self.assertEqual(len(results), 0)

    def test_zero_initial_stock(self):
        results = self.sim.simulate_maize_storage(0, 3.0, 3)
        for r in results:
            self.assertEqual(r["loss_this_month"], 0)

    # Invalid inputs
    def test_negative_stock_raises(self):
        with self.assertRaises(ValueError):
            self.sim.simulate_maize_storage(-100, 3, 6)

    def test_invalid_storage_type_raises(self):
        with self.assertRaises(ValueError):
            self.sim.simulate_tomato_storage(100, "fridge", 7)

    def test_no_simulation_summary_raises(self):
        fresh_sim = StorageLossSimulator()
        with self.assertRaises(ValueError):
            fresh_sim.generate_loss_summary("maize")


# ===================================================================
# PolicyEngine Tests
# ===================================================================

class TestPolicyEngine(unittest.TestCase):
    """Tests for the PolicyEngine."""

    def setUp(self):
        self.pe = PolicyEngine()

    # Normal inputs
    def test_fra_reserve_pass(self):
        result = self.pe.check_fra_reserve(600_000)
        self.assertEqual(result["alert_level"], "OK")

    def test_fra_reserve_warning(self):
        result = self.pe.check_fra_reserve(300_000)
        self.assertEqual(result["alert_level"], "WARNING")

    def test_fra_reserve_critical(self):
        result = self.pe.check_fra_reserve(100_000)
        self.assertEqual(result["alert_level"], "CRITICAL")

    def test_export_blocked_when_reserve_not_met(self):
        result = self.pe.check_export_restriction(5000, False)
        self.assertEqual(result["status"], "BLOCKED")

    def test_export_allowed_with_surplus(self):
        result = self.pe.check_export_restriction(5000, True)
        self.assertEqual(result["status"], "ALLOWED")

    def test_storage_time_within_limit(self):
        result = self.pe.check_max_storage_time("maize", 50)
        self.assertEqual(result["alert_level"], "OK")

    def test_storage_time_exceeded(self):
        result = self.pe.check_max_storage_time("maize", 200)
        self.assertEqual(result["alert_level"], "CRITICAL")

    # Edge cases
    def test_generate_report_empty(self):
        fresh = PolicyEngine()
        report = fresh.generate_policy_report()
        self.assertEqual(len(report), 1)
        self.assertIn("No policy checks", report[0])

    def test_clear_alerts(self):
        self.pe.check_fra_reserve(100)
        self.pe.clear_alerts()
        report = self.pe.generate_policy_report()
        self.assertIn("No policy checks", report[0])

    # Invalid inputs
    def test_negative_stock_raises(self):
        with self.assertRaises(ValueError):
            self.pe.check_fra_reserve(-1000)

    def test_invalid_commodity_type_raises(self):
        with self.assertRaises(ValueError):
            self.pe.check_max_storage_time("wheat", 30)

    def test_non_bool_reserve_met_raises(self):
        with self.assertRaises(TypeError):
            self.pe.check_export_restriction(1000, "yes")


# ===================================================================
# ReportingDashboard Tests
# ===================================================================

class TestReportingDashboard(unittest.TestCase):
    """Tests for the ReportingDashboard."""

    def _sample_result(self, month="January"):
        return {
            "month": month,
            "commodity": "Maize",
            "monthly_production": 10_000,
            "market_demand": 8_000,
            "surplus": 2_000,
            "shortage": 0,
            "spoilage_tons": 300,
            "waste_percentage": 3.0,
            "revenue_zmw": 36_000_000,
            "price_adjustment": {
                "original_price": 4500,
                "adjusted_price": 3825,
                "adjustment": "-15%",
                "reason": "Surplus",
            },
            "demand_met": 8_000,
            "food_security_percentage": 100.0,
        }

    def setUp(self):
        self.db = ReportingDashboard()

    # Normal inputs
    def test_add_and_retrieve_result(self):
        self.db.add_monthly_result(self._sample_result())
        self.assertEqual(len(self.db.results), 1)

    def test_food_security_label_secure(self):
        self.assertEqual(ReportingDashboard.food_security_label(90), "Secure")

    def test_food_security_label_at_risk(self):
        self.assertEqual(ReportingDashboard.food_security_label(70), "At Risk")

    def test_food_security_label_crisis(self):
        self.assertEqual(ReportingDashboard.food_security_label(50), "Crisis")

    def test_generate_monthly_summary_found(self):
        self.db.add_monthly_result(self._sample_result("March"))
        summary = self.db.generate_monthly_summary("March")
        self.assertIsNotNone(summary)
        self.assertIn("March", summary)

    def test_generate_monthly_summary_not_found(self):
        result = self.db.generate_monthly_summary("December")
        self.assertIsNone(result)

    # JSON round-trip test
    def test_json_save_load_round_trip(self):
        self.db.add_monthly_result(self._sample_result("January"))
        self.db.add_monthly_result(self._sample_result("February"))

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.db.export_to_json(tmp_path)

            new_db = ReportingDashboard()
            new_db.load_from_json(tmp_path)

            self.assertEqual(len(new_db.results), 2)
            self.assertEqual(new_db.results[0]["month"], "January")
            self.assertEqual(new_db.results[1]["month"], "February")
        finally:
            os.unlink(tmp_path)

    # Edge cases
    def test_print_full_report_empty(self):
        report = self.db.print_full_report()
        self.assertIn("No simulation results", report)

    def test_export_csv_empty_no_error(self):
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name
        try:
            self.db.export_to_csv(tmp_path)  # should not crash
        finally:
            os.unlink(tmp_path)

    # Invalid inputs
    def test_add_non_dict_raises(self):
        with self.assertRaises(TypeError):
            self.db.add_monthly_result("not a dict")

    def test_load_missing_file_raises(self):
        with self.assertRaises(FileNotFoundError):
            self.db.load_from_json("nonexistent_file_xyz.json")

    def test_load_bad_json_structure_raises(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json",
                                         delete=False) as tmp:
            json.dump({"wrong_key": []}, tmp)
            tmp_path = tmp.name
        try:
            with self.assertRaises(ValueError):
                self.db.load_from_json(tmp_path)
        finally:
            os.unlink(tmp_path)


if __name__ == "__main__":
    unittest.main()
