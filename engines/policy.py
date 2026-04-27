"""
Policy simulation engine for AgriTwin-ZM.

Implements rule-based policy checks for Zambia's agricultural sector,
including FRA reserve levels, export restrictions, and storage limits.
"""

from __future__ import annotations


class PolicyEngine:
    """Evaluates agricultural policy rules for Zambian food security.

    All checks use simple conditional logic (no ML). Each method returns
    a standardised dict with: status, alert_level, message, recommendation.

    Alert levels: 'OK', 'WARNING', 'CRITICAL'.
    """

    def __init__(self) -> None:
        """Initialise the policy engine with an empty alerts list."""
        self._alerts: list[dict] = []

    def check_fra_reserve(
        self, current_stock_tons: float, threshold: float = 500_000
    ) -> dict:
        """Check if FRA (Food Reserve Agency) stock meets the minimum threshold.

        Args:
            current_stock_tons: Current national reserve stock in tons.
            threshold: Minimum acceptable reserve level (default 500,000 tons).

        Returns:
            Policy result dict with status, alert_level, message, recommendation.

        Raises:
            TypeError: If arguments are not numeric.
            ValueError: If arguments are negative.
        """
        self._validate_numeric("current_stock_tons", current_stock_tons)
        self._validate_numeric("threshold", threshold)

        if current_stock_tons >= threshold:
            result = {
                "status": "PASS",
                "alert_level": "OK",
                "message": f"FRA reserve at {current_stock_tons:,.0f} tons meets the "
                           f"{threshold:,.0f}-ton threshold.",
                "recommendation": "No action required.",
            }
        elif current_stock_tons >= threshold * 0.5:
            result = {
                "status": "BELOW_THRESHOLD",
                "alert_level": "WARNING",
                "message": f"FRA reserve at {current_stock_tons:,.0f} tons is below the "
                           f"{threshold:,.0f}-ton threshold.",
                "recommendation": "Consider restricting exports and increasing local procurement.",
            }
        else:
            result = {
                "status": "CRITICAL_LOW",
                "alert_level": "CRITICAL",
                "message": f"FRA reserve at {current_stock_tons:,.0f} tons is critically low "
                           f"(below 50% of {threshold:,.0f}-ton threshold).",
                "recommendation": "Immediately restrict all exports. Activate emergency "
                                  "procurement and consider food imports.",
            }

        self._alerts.append(result)
        return result

    def check_export_restriction(
        self, surplus_tons: float, fra_reserve_met: bool
    ) -> dict:
        """Determine whether commodity exports should be allowed.

        Rules:
            - If FRA reserve is not met, block all exports.
            - If surplus exists and reserve is met, allow exports.
            - Otherwise, allow limited exports with monitoring.

        Args:
            surplus_tons: Current surplus in metric tons.
            fra_reserve_met: Whether the FRA reserve threshold is satisfied.

        Returns:
            Policy result dict.

        Raises:
            TypeError: If surplus_tons is not numeric or fra_reserve_met is not bool.
            ValueError: If surplus_tons is negative.
        """
        self._validate_numeric("surplus_tons", surplus_tons)
        if not isinstance(fra_reserve_met, bool):
            raise TypeError(f"'fra_reserve_met' must be a boolean, got {type(fra_reserve_met).__name__}.")

        if not fra_reserve_met:
            result = {
                "status": "BLOCKED",
                "alert_level": "CRITICAL",
                "message": "Exports blocked: FRA reserve has not met the minimum threshold.",
                "recommendation": "Do not approve any export permits until reserves are replenished.",
            }
        elif surplus_tons > 0:
            result = {
                "status": "ALLOWED",
                "alert_level": "OK",
                "message": f"Exports allowed. Surplus of {surplus_tons:,.0f} tons available.",
                "recommendation": f"Approve export permits for up to {surplus_tons:,.0f} tons.",
            }
        else:
            result = {
                "status": "LIMITED",
                "alert_level": "WARNING",
                "message": "No surplus available for export.",
                "recommendation": "Monitor supply closely. Only allow exports if surplus develops.",
            }

        self._alerts.append(result)
        return result

    def check_max_storage_time(
        self,
        commodity_type: str,
        days_stored: int,
        shelf_life_days: int = 14,
    ) -> dict:
        """Check whether storage time exceeds safe limits.

        Limits:
            - Maize: maximum 180 days
            - Tomato: maximum is the provided shelf_life_days (default 14)

        Args:
            commodity_type: 'maize' or 'tomato'.
            days_stored: How many days the commodity has been stored.
            shelf_life_days: Shelf life for tomatoes (ignored for maize).

        Returns:
            Policy result dict.

        Raises:
            TypeError: If arguments are the wrong type.
            ValueError: If commodity_type is invalid or days_stored is negative.
        """
        if not isinstance(commodity_type, str):
            raise TypeError(f"'commodity_type' must be a string, got {type(commodity_type).__name__}.")
        if not isinstance(days_stored, int):
            raise TypeError(f"'days_stored' must be an integer, got {type(days_stored).__name__}.")
        if days_stored < 0:
            raise ValueError(f"'days_stored' must be non-negative, got {days_stored}.")

        ct = commodity_type.lower().strip()

        if ct == "maize":
            max_days = 180
        elif ct == "tomato":
            max_days = shelf_life_days
        else:
            raise ValueError(f"'commodity_type' must be 'maize' or 'tomato', got '{commodity_type}'.")

        if days_stored <= max_days * 0.7:
            result = {
                "status": "WITHIN_LIMIT",
                "alert_level": "OK",
                "message": f"{ct.title()} stored for {days_stored} days (limit: {max_days} days). Safe.",
                "recommendation": "No action needed.",
            }
        elif days_stored <= max_days:
            result = {
                "status": "APPROACHING_LIMIT",
                "alert_level": "WARNING",
                "message": f"{ct.title()} stored for {days_stored} days, approaching the "
                           f"{max_days}-day limit.",
                "recommendation": "Prioritise sale or distribution to avoid losses.",
            }
        else:
            result = {
                "status": "EXCEEDED",
                "alert_level": "CRITICAL",
                "message": f"{ct.title()} has been stored for {days_stored} days, exceeding the "
                           f"{max_days}-day limit by {days_stored - max_days} days.",
                "recommendation": "Immediately inspect stock quality. Consider discounting or "
                                  "diverting to animal feed / processing.",
            }

        self._alerts.append(result)
        return result

    def generate_policy_report(self) -> list[str]:
        """Return all active policy alerts as a list of formatted strings.

        Returns:
            List of alert strings with level and message.
        """
        if not self._alerts:
            return ["No policy checks have been run yet."]

        lines: list[str] = []
        for i, alert in enumerate(self._alerts, start=1):
            lines.append(
                f"[{i}] [{alert['alert_level']}] {alert['message']} "
                f">> {alert['recommendation']}"
            )
        return lines

    def clear_alerts(self) -> None:
        """Clear all stored policy alerts."""
        self._alerts.clear()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_numeric(name: str, value: float) -> None:
        """Check that a value is numeric and non-negative."""
        if not isinstance(value, (int, float)):
            raise TypeError(f"'{name}' must be numeric, got {type(value).__name__}.")
        if value < 0:
            raise ValueError(f"'{name}' must be non-negative, got {value}.")
