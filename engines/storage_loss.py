"""Storage loss simulator for AgriTwin-ZM.

Simulates compound storage losses for maize (monthly) and
tomatoes (daily) under different storage conditions.
"""

from __future__ import annotations


class StorageLossSimulator:
    """Simulates storage losses over time for maize and tomato commodities.

    Provides month-by-month simulation for maize and day-by-day simulation
    for tomatoes, with configurable loss rates and storage conditions.
    """

    def __init__(self) -> None:
        """Initialise the simulator with empty result stores."""
        self._maize_results: list[dict] = []
        self._tomato_results: list[dict] = []

    # ------------------------------------------------------------------
    # Maize storage simulation
    # ------------------------------------------------------------------

    def simulate_maize_storage(
        self,
        initial_stock: float,
        monthly_loss_pct: float,
        months: int,
    ) -> list[dict]:
        """Simulate compound monthly storage loss for maize.

        Args:
            initial_stock: Starting stock in metric tons.
            monthly_loss_pct: Loss rate per month as a percentage (e.g. 3.0 for 3%).
            months: Number of months to simulate.

        Returns:
            List of dicts, one per month, each containing:
                month, stock_remaining, loss_this_month, cumulative_loss.

        Raises:
            TypeError: If arguments are the wrong type.
            ValueError: If arguments are negative or out of range.
        """
        self._validate_maize_inputs(initial_stock, monthly_loss_pct, months)

        results: list[dict] = []
        remaining = float(initial_stock)
        cumulative = 0.0
        rate = monthly_loss_pct / 100

        for m in range(1, months + 1):
            loss = remaining * rate
            remaining -= loss
            cumulative += loss
            results.append({
                "month": m,
                "stock_remaining": round(remaining, 4),
                "loss_this_month": round(loss, 4),
                "cumulative_loss": round(cumulative, 4),
            })

        self._maize_results = results
        return results

    # ------------------------------------------------------------------
    # Tomato storage simulation
    # ------------------------------------------------------------------

    def simulate_tomato_storage(
        self,
        initial_volume: float,
        storage_type: str,
        days: int,
    ) -> list[dict]:
        """Simulate daily spoilage for tomatoes under a given storage type.

        Spoilage rates:
            - cold storage: 1.5% per day
            - open storage: 4.0% per day

        Args:
            initial_volume: Starting volume in metric tons.
            storage_type: 'cold' or 'open'.
            days: Number of days to simulate.

        Returns:
            List of dicts, one per day, each containing:
                day, volume_remaining, spoilage_today, total_spoilage_pct.

        Raises:
            TypeError: If arguments are the wrong type.
            ValueError: If arguments are negative or storage_type is invalid.
        """
        self._validate_tomato_inputs(initial_volume, storage_type, days)

        rate_map = {"cold": 1.5, "open": 4.0}
        daily_rate = rate_map[storage_type.lower().strip()] / 100

        results: list[dict] = []
        remaining = float(initial_volume)

        for d in range(1, days + 1):
            loss_today = remaining * daily_rate
            remaining -= loss_today
            total_pct = (
                round(((initial_volume - remaining) / initial_volume) * 100, 2)
                if initial_volume > 0
                else 0.0
            )
            results.append({
                "day": d,
                "volume_remaining": round(remaining, 4),
                "spoilage_today": round(loss_today, 4),
                "total_spoilage_pct": total_pct,
            })

        self._tomato_results = results
        return results

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def generate_loss_summary(self, commodity_type: str = "maize") -> str:
        """Generate a human-readable summary of the most recent simulation.

        Args:
            commodity_type: 'maize' or 'tomato'.

        Returns:
            Formatted string summarising the simulation results.

        Raises:
            ValueError: If commodity_type is invalid or no simulation has been run.
        """
        commodity_type = commodity_type.lower().strip()

        if commodity_type == "maize":
            if not self._maize_results:
                raise ValueError("No maize simulation has been run yet.")
            data = self._maize_results
            header = "MAIZE STORAGE LOSS SUMMARY"
            lines = [header, "=" * len(header)]
            for row in data:
                lines.append(
                    f"  Month {row['month']:>2}: "
                    f"Remaining = {row['stock_remaining']:>12,.2f} tons | "
                    f"Lost = {row['loss_this_month']:>10,.2f} tons | "
                    f"Cumulative = {row['cumulative_loss']:>10,.2f} tons"
                )
            final = data[-1]
            first_stock = data[0]["stock_remaining"] + data[0]["loss_this_month"]
            total_pct = round((final["cumulative_loss"] / first_stock) * 100, 2) if first_stock > 0 else 0
            lines.append(f"\n  Total loss over {len(data)} months: "
                         f"{final['cumulative_loss']:,.2f} tons ({total_pct}%)")
            return "\n".join(lines)

        elif commodity_type == "tomato":
            if not self._tomato_results:
                raise ValueError("No tomato simulation has been run yet.")
            data = self._tomato_results
            header = "TOMATO STORAGE SPOILAGE SUMMARY"
            lines = [header, "=" * len(header)]
            for row in data:
                lines.append(
                    f"  Day {row['day']:>3}: "
                    f"Remaining = {row['volume_remaining']:>12,.2f} tons | "
                    f"Spoiled = {row['spoilage_today']:>10,.4f} tons | "
                    f"Total spoilage = {row['total_spoilage_pct']:>6.2f}%"
                )
            final = data[-1]
            lines.append(f"\n  Total spoilage after {len(data)} days: {final['total_spoilage_pct']}%")
            return "\n".join(lines)

        else:
            raise ValueError(f"commodity_type must be 'maize' or 'tomato', got '{commodity_type}'.")

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_maize_inputs(
        initial_stock: float, monthly_loss_pct: float, months: int
    ) -> None:
        """Validate inputs for maize storage simulation."""
        if not isinstance(initial_stock, (int, float)):
            raise TypeError(f"'initial_stock' must be numeric, got {type(initial_stock).__name__}.")
        if not isinstance(monthly_loss_pct, (int, float)):
            raise TypeError(f"'monthly_loss_pct' must be numeric, got {type(monthly_loss_pct).__name__}.")
        if not isinstance(months, int):
            raise TypeError(f"'months' must be an integer, got {type(months).__name__}.")
        if initial_stock < 0:
            raise ValueError(f"'initial_stock' must be non-negative, got {initial_stock}.")
        if not 0 <= monthly_loss_pct <= 100:
            raise ValueError(f"'monthly_loss_pct' must be between 0 and 100, got {monthly_loss_pct}.")
        if months < 0:
            raise ValueError(f"'months' must be non-negative, got {months}.")

    @staticmethod
    def _validate_tomato_inputs(
        initial_volume: float, storage_type: str, days: int
    ) -> None:
        """Validate inputs for tomato storage simulation."""
        if not isinstance(initial_volume, (int, float)):
            raise TypeError(f"'initial_volume' must be numeric, got {type(initial_volume).__name__}.")
        if not isinstance(storage_type, str):
            raise TypeError(f"'storage_type' must be a string, got {type(storage_type).__name__}.")
        if not isinstance(days, int):
            raise TypeError(f"'days' must be an integer, got {type(days).__name__}.")
        if initial_volume < 0:
            raise ValueError(f"'initial_volume' must be non-negative, got {initial_volume}.")
        normalised = storage_type.lower().strip()
        if normalised not in ("cold", "open"):
            raise ValueError(f"'storage_type' must be 'cold' or 'open', got '{storage_type}'.")
        if days < 0:
            raise ValueError(f"'days' must be non-negative, got {days}.")
