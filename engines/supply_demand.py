"""
Supply and demand simulation engine for AgriTwin-ZM.

Handles surplus/shortage calculations, waste analysis, revenue
estimation, and basic price adjustment for Zambian commodities.
"""

from __future__ import annotations
from typing import Union

from models.maize import Maize
from models.tomato import Tomato


class SupplyDemandEngine:
    """Simulates supply and demand dynamics for a given commodity.

    Takes a commodity object (Maize or Tomato), monthly production, and
    market demand, then calculates surplus, shortage, waste, revenue,
    and adjusted pricing.

    Attributes:
        commodity: A Maize or Tomato instance.
        monthly_production: Monthly production volume in metric tons.
        market_demand: Monthly market demand in metric tons.
    """

    def __init__(
        self,
        commodity: Union[Maize, Tomato],
        monthly_production: float,
        market_demand: float,
    ) -> None:
        """Initialise the supply-demand engine.

        Args:
            commodity: A Maize or Tomato commodity instance.
            monthly_production: Production volume for the month in tons.
            market_demand: Market demand for the month in tons.

        Raises:
            TypeError: If commodity is not Maize or Tomato, or if numeric
                args are not numeric.
            ValueError: If numeric args are negative.
        """
        if not isinstance(commodity, (Maize, Tomato)):
            raise TypeError(
                f"'commodity' must be a Maize or Tomato instance, "
                f"got {type(commodity).__name__}."
            )
        for name, val in [("monthly_production", monthly_production),
                          ("market_demand", market_demand)]:
            if not isinstance(val, (int, float)):
                raise TypeError(f"'{name}' must be numeric, got {type(val).__name__}.")
            if val < 0:
                raise ValueError(f"'{name}' must be non-negative, got {val}.")

        self.commodity = commodity
        self.monthly_production: float = float(monthly_production)
        self.market_demand: float = float(market_demand)

    def calculate_surplus(self) -> float:
        """Return surplus tons (production minus demand, floored at 0)."""
        return max(0.0, self.monthly_production - self.market_demand)

    def calculate_shortage(self) -> float:
        """Return shortage tons (demand minus production, floored at 0)."""
        return max(0.0, self.market_demand - self.monthly_production)

    def calculate_waste(self, spoilage_tons: float) -> float:
        """Return waste as a percentage of total production.

        Args:
            spoilage_tons: Tonnage lost to spoilage or storage loss.

        Returns:
            Waste percentage (0-100). Returns 0 if production is zero.
        """
        if not isinstance(spoilage_tons, (int, float)):
            raise TypeError(f"'spoilage_tons' must be numeric, got {type(spoilage_tons).__name__}.")
        if spoilage_tons < 0:
            raise ValueError(f"'spoilage_tons' must be non-negative, got {spoilage_tons}.")
        if self.monthly_production == 0:
            return 0.0
        return round((spoilage_tons / self.monthly_production) * 100, 2)

    def calculate_revenue(self) -> float:
        """Calculate revenue based on units sold (the lesser of supply and demand).

        For Maize, revenue = tons_sold * price_per_ton.
        For Tomato, revenue = crates_sold * market_price_per_crate.

        Returns:
            Estimated revenue in ZMW.
        """
        tons_sold = min(self.monthly_production, self.market_demand)

        if isinstance(self.commodity, Maize):
            return round(tons_sold * self.commodity.price_per_ton, 2)
        else:
            # Convert tons sold to crates (1 ton = 1000 kg, 1 crate = 15 kg)
            crates_sold = (tons_sold * 1000) / Tomato.CRATE_WEIGHT_KG
            return round(crates_sold * self.commodity.market_price_per_crate, 2)

    def adjust_price(self) -> dict:
        """Adjust commodity price based on surplus/shortage conditions.

        Rules:
            - If surplus > 20% of demand: reduce price by 15%
            - If shortage > 20% of demand: raise price by 20%
            - Otherwise: price stays stable

        Returns:
            Dict with keys: original_price, adjusted_price, adjustment, reason.
        """
        if self.market_demand == 0:
            if isinstance(self.commodity, Maize):
                price = self.commodity.price_per_ton
            else:
                price = self.commodity.market_price_per_crate
            return {
                "original_price": price,
                "adjusted_price": price,
                "adjustment": "0%",
                "reason": "No demand recorded",
            }

        surplus = self.calculate_surplus()
        shortage = self.calculate_shortage()
        threshold = self.market_demand * 0.20

        if isinstance(self.commodity, Maize):
            original = self.commodity.price_per_ton
        else:
            original = self.commodity.market_price_per_crate

        if surplus > threshold:
            adjusted = round(original * 0.85, 2)
            return {
                "original_price": original,
                "adjusted_price": adjusted,
                "adjustment": "-15%",
                "reason": f"Surplus of {surplus:.1f} tons exceeds 20% of demand",
            }
        elif shortage > threshold:
            adjusted = round(original * 1.20, 2)
            return {
                "original_price": original,
                "adjusted_price": adjusted,
                "adjustment": "+20%",
                "reason": f"Shortage of {shortage:.1f} tons exceeds 20% of demand",
            }
        else:
            return {
                "original_price": original,
                "adjusted_price": original,
                "adjustment": "0%",
                "reason": "Market is balanced",
            }

    def run_monthly_simulation(
        self, month_name: str, spoilage_tons: float
    ) -> dict:
        """Run a full monthly simulation and return a summary.

        Args:
            month_name: Label for the month (e.g. "January").
            spoilage_tons: Tons lost to spoilage/storage this month.

        Returns:
            Dictionary with all simulation results for the month.
        """
        surplus = self.calculate_surplus()
        shortage = self.calculate_shortage()
        waste_pct = self.calculate_waste(spoilage_tons)
        revenue = self.calculate_revenue()
        price_info = self.adjust_price()
        demand_met = min(self.monthly_production, self.market_demand)
        food_security = (
            round((demand_met / self.market_demand) * 100, 2)
            if self.market_demand > 0
            else 100.0
        )

        return {
            "month": month_name,
            "commodity": type(self.commodity).__name__,
            "monthly_production": self.monthly_production,
            "market_demand": self.market_demand,
            "surplus": surplus,
            "shortage": shortage,
            "spoilage_tons": spoilage_tons,
            "waste_percentage": waste_pct,
            "revenue_zmw": revenue,
            "price_adjustment": price_info,
            "demand_met": demand_met,
            "food_security_percentage": food_security,
        }
