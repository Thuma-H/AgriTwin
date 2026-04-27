"""
Reporting dashboard for AgriTwin-ZM.

Stores monthly simulation results and provides export functionality
in plain text, CSV, and JSON formats.
"""

from __future__ import annotations

import csv
import json
import os
from typing import Optional


class ReportingDashboard:
    """Collects simulation results and generates formatted reports.

    Stores a list of monthly result dicts and can export them to
    .txt, .csv, or .json files.

    Food security status labels:
        >80%  = 'Secure'
        60-80% = 'At Risk'
        <60%  = 'Crisis'
    """

    def __init__(self) -> None:
        """Initialise the dashboard with an empty results list."""
        self._results: list[dict] = []

    # ------------------------------------------------------------------
    # Data management
    # ------------------------------------------------------------------

    def add_monthly_result(self, result_dict: dict) -> None:
        """Append a monthly simulation result to the internal store.

        Args:
            result_dict: A dict produced by SupplyDemandEngine.run_monthly_simulation().

        Raises:
            TypeError: If result_dict is not a dict.
        """
        if not isinstance(result_dict, dict):
            raise TypeError(f"Expected a dict, got {type(result_dict).__name__}.")
        self._results.append(result_dict)

    @property
    def results(self) -> list[dict]:
        """Return a copy of the stored results list."""
        return list(self._results)

    # ------------------------------------------------------------------
    # Food security helpers
    # ------------------------------------------------------------------

    @staticmethod
    def food_security_label(percentage: float) -> str:
        """Return a human-readable food security status label.

        Args:
            percentage: Food security percentage (0-100).

        Returns:
            'Secure', 'At Risk', or 'Crisis'.
        """
        if percentage > 80:
            return "Secure"
        elif percentage >= 60:
            return "At Risk"
        else:
            return "Crisis"

    # ------------------------------------------------------------------
    # Summaries
    # ------------------------------------------------------------------

    def generate_monthly_summary(self, month: str) -> Optional[str]:
        """Generate and return a formatted summary for a specific month.

        Args:
            month: The month label to look up (e.g. "January").

        Returns:
            Formatted summary string, or None if the month is not found.
        """
        match = None
        for r in self._results:
            if r.get("month", "").lower() == month.lower():
                match = r
                break

        if match is None:
            return None

        fs_pct = match.get("food_security_percentage", 0)
        label = self.food_security_label(fs_pct)

        lines = [
            f"--- {match['month']} Summary ({match.get('commodity', 'N/A')}) ---",
            f"  Production   : {match.get('monthly_production', 0):>12,.2f} tons",
            f"  Demand       : {match.get('market_demand', 0):>12,.2f} tons",
            f"  Surplus      : {match.get('surplus', 0):>12,.2f} tons",
            f"  Shortage     : {match.get('shortage', 0):>12,.2f} tons",
            f"  Spoilage     : {match.get('spoilage_tons', 0):>12,.2f} tons",
            f"  Waste %      : {match.get('waste_percentage', 0):>11.2f}%",
            f"  Revenue      : ZMW {match.get('revenue_zmw', 0):>10,.2f}",
            f"  Food Security: {fs_pct:.1f}% [{label}]",
        ]
        summary = "\n".join(lines)
        print(summary)
        return summary

    # ------------------------------------------------------------------
    # Export methods
    # ------------------------------------------------------------------

    def export_to_txt(self, filename: str) -> None:
        """Save all monthly summaries to a plain text file.

        Args:
            filename: Path of the output .txt file.
        """
        with open(filename, "w", encoding="utf-8") as f:
            f.write("AGRITWIN-ZM SIMULATION REPORT\n")
            f.write("=" * 50 + "\n\n")
            for r in self._results:
                fs_pct = r.get("food_security_percentage", 0)
                label = self.food_security_label(fs_pct)
                f.write(f"--- {r.get('month', '?')} ({r.get('commodity', '?')}) ---\n")
                f.write(f"  Production   : {r.get('monthly_production', 0):,.2f} tons\n")
                f.write(f"  Demand       : {r.get('market_demand', 0):,.2f} tons\n")
                f.write(f"  Surplus      : {r.get('surplus', 0):,.2f} tons\n")
                f.write(f"  Shortage     : {r.get('shortage', 0):,.2f} tons\n")
                f.write(f"  Spoilage     : {r.get('spoilage_tons', 0):,.2f} tons\n")
                f.write(f"  Waste %      : {r.get('waste_percentage', 0):.2f}%\n")
                f.write(f"  Revenue      : ZMW {r.get('revenue_zmw', 0):,.2f}\n")
                f.write(f"  Food Security: {fs_pct:.1f}% [{label}]\n\n")

    def export_to_csv(self, filename: str) -> None:
        """Save all results to a CSV file.

        Args:
            filename: Path of the output .csv file.
        """
        if not self._results:
            return

        # Flatten price_adjustment dict into top-level keys
        flat_rows = []
        for r in self._results:
            row = {}
            for k, v in r.items():
                if k == "price_adjustment" and isinstance(v, dict):
                    for pk, pv in v.items():
                        row[f"price_{pk}"] = pv
                else:
                    row[k] = v
            flat_rows.append(row)

        fieldnames = list(flat_rows[0].keys())

        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(flat_rows)

    def export_to_json(self, filename: str) -> None:
        """Save all results to a JSON file.

        Args:
            filename: Path of the output .json file.
        """
        with open(filename, "w", encoding="utf-8") as f:
            json.dump({"simulations": self._results}, f, indent=2)

    def load_from_json(self, filename: str) -> None:
        """Load simulation data from a previously saved JSON file.

        Args:
            filename: Path of the .json file to load.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the JSON structure is unexpected.
        """
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")

        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "simulations" not in data:
            raise ValueError("JSON file must contain a 'simulations' key.")

        self._results = data["simulations"]

    # ------------------------------------------------------------------
    # Full report
    # ------------------------------------------------------------------

    def print_full_report(self) -> str:
        """Print all months in a formatted table to the console.

        Returns:
            The full report as a string.
        """
        if not self._results:
            msg = "No simulation results to display."
            print(msg)
            return msg

        # Header
        header = (
            f"{'Month':<12} {'Commodity':<8} {'Production':>12} {'Demand':>12} "
            f"{'Surplus':>10} {'Shortage':>10} {'Waste%':>7} "
            f"{'Revenue (ZMW)':>15} {'Food Sec%':>10} {'Status':<10}"
        )
        sep = "-" * len(header)
        lines = [
            "AGRITWIN-ZM FULL SIMULATION REPORT",
            "=" * 50,
            "",
            header,
            sep,
        ]

        for r in self._results:
            fs_pct = r.get("food_security_percentage", 0)
            label = self.food_security_label(fs_pct)
            lines.append(
                f"{r.get('month', '?'):<12} "
                f"{r.get('commodity', '?'):<8} "
                f"{r.get('monthly_production', 0):>12,.1f} "
                f"{r.get('market_demand', 0):>12,.1f} "
                f"{r.get('surplus', 0):>10,.1f} "
                f"{r.get('shortage', 0):>10,.1f} "
                f"{r.get('waste_percentage', 0):>6.1f}% "
                f"{r.get('revenue_zmw', 0):>15,.2f} "
                f"{fs_pct:>9.1f}% "
                f"{label:<10}"
            )

        lines.append(sep)
        report = "\n".join(lines)
        print(report)
        return report
