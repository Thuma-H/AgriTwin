"""
Tomato commodity model for AgriTwin-ZM.

Represents tomato production, spoilage, and market characteristics
specific to Zambia's agricultural context.
"""

from __future__ import annotations


class Tomato:
    """Model representing tomatoes as a commodity in Zambia's agricultural system.

    Attributes:
        production_volume: Total production volume in metric tons.
        shelf_life_days: Expected shelf life in days under stated storage
            conditions.
        storage_type: Type of storage, either ``'cold'`` or ``'open'``.
        spoilage_rate: Daily spoilage rate as a percentage (0-100).
        market_price_per_crate: Market price per crate in Zambian Kwacha (ZMW).

    Class Constants:
        CRATE_WEIGHT_KG: Weight of a single crate in kilograms (15 kg).
        VALID_STORAGE_TYPES: Allowed values for *storage_type*.
    """

    CRATE_WEIGHT_KG: float = 15.0
    VALID_STORAGE_TYPES: tuple[str, ...] = ("cold", "open")

    def __init__(
        self,
        production_volume: float,
        shelf_life_days: int,
        storage_type: str,
        spoilage_rate: float,
        market_price_per_crate: float,
    ) -> None:
        """Initialise a Tomato commodity instance.

        Args:
            production_volume: Total production volume in metric tons.
            shelf_life_days: Expected shelf life in days (positive integer).
            storage_type: ``'cold'`` or ``'open'``.
            spoilage_rate: Daily spoilage rate as a percentage (0-100).
            market_price_per_crate: Price per 15 kg crate in ZMW.

        Raises:
            ValueError: If numeric values are negative, percentages are out of
                range, or *storage_type* is invalid.
            TypeError: If arguments are of incorrect types.
        """
        self._validate_inputs(
            production_volume,
            shelf_life_days,
            storage_type,
            spoilage_rate,
            market_price_per_crate,
        )

        self.production_volume: float = float(production_volume)
        self.shelf_life_days: int = int(shelf_life_days)
        self.storage_type: str = storage_type.lower().strip()
        self.spoilage_rate: float = float(spoilage_rate)
        self.market_price_per_crate: float = float(market_price_per_crate)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @classmethod
    def _validate_inputs(
        cls,
        production_volume: float,
        shelf_life_days: int,
        storage_type: str,
        spoilage_rate: float,
        market_price_per_crate: float,
    ) -> None:
        """Validate all constructor inputs.

        Raises:
            TypeError: If arguments are of incorrect types.
            ValueError: If values are out of acceptable range.
        """
        # Type checks
        if not isinstance(production_volume, (int, float)):
            raise TypeError(
                f"'production_volume' must be numeric, "
                f"got {type(production_volume).__name__}."
            )
        if not isinstance(shelf_life_days, (int, float)):
            raise TypeError(
                f"'shelf_life_days' must be an integer, "
                f"got {type(shelf_life_days).__name__}."
            )
        if not isinstance(storage_type, str):
            raise TypeError(
                f"'storage_type' must be a string, "
                f"got {type(storage_type).__name__}."
            )
        if not isinstance(spoilage_rate, (int, float)):
            raise TypeError(
                f"'spoilage_rate' must be numeric, "
                f"got {type(spoilage_rate).__name__}."
            )
        if not isinstance(market_price_per_crate, (int, float)):
            raise TypeError(
                f"'market_price_per_crate' must be numeric, "
                f"got {type(market_price_per_crate).__name__}."
            )

        # Value checks
        if production_volume < 0:
            raise ValueError(
                f"'production_volume' must be non-negative, "
                f"got {production_volume}."
            )
        if shelf_life_days < 0:
            raise ValueError(
                f"'shelf_life_days' must be non-negative, "
                f"got {shelf_life_days}."
            )
        if not 0 <= spoilage_rate <= 100:
            raise ValueError(
                f"'spoilage_rate' must be between 0 and 100, "
                f"got {spoilage_rate}."
            )
        if market_price_per_crate < 0:
            raise ValueError(
                f"'market_price_per_crate' must be non-negative, "
                f"got {market_price_per_crate}."
            )

        # Storage type validation
        normalised = storage_type.lower().strip()
        if normalised not in cls.VALID_STORAGE_TYPES:
            raise ValueError(
                f"'storage_type' must be one of {cls.VALID_STORAGE_TYPES}, "
                f"got '{storage_type}'."
            )

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def calculate_spoilage(self, days_stored: int) -> dict:
        """Calculate spoilage after a given number of days in storage.

        Uses compound daily spoilage: each day, the remaining volume is
        reduced by ``spoilage_rate`` percent.

        Args:
            days_stored: Number of days the tomatoes have been stored.

        Returns:
            A dictionary containing:
                - ``days_stored`` (int): The input days.
                - ``initial_volume_tons`` (float): Starting volume.
                - ``remaining_volume_tons`` (float): Volume after spoilage.
                - ``total_spoilage_tons`` (float): Total tonnage lost.
                - ``total_spoilage_percentage`` (float): Loss as % of initial.

        Raises:
            TypeError: If *days_stored* is not an integer.
            ValueError: If *days_stored* is negative.
        """
        if not isinstance(days_stored, (int, float)):
            raise TypeError(
                f"'days_stored' must be an integer, "
                f"got {type(days_stored).__name__}."
            )
        if days_stored < 0:
            raise ValueError(
                f"'days_stored' must be non-negative, got {days_stored}."
            )

        days_stored = int(days_stored)
        remaining = self.production_volume
        daily_rate = self.spoilage_rate / 100

        for _ in range(days_stored):
            remaining -= remaining * daily_rate

        total_lost = self.production_volume - remaining
        spoilage_pct = (
            (total_lost / self.production_volume * 100)
            if self.production_volume > 0
            else 0.0
        )

        return {
            "days_stored": days_stored,
            "initial_volume_tons": self.production_volume,
            "remaining_volume_tons": round(remaining, 4),
            "total_spoilage_tons": round(total_lost, 4),
            "total_spoilage_percentage": round(spoilage_pct, 2),
        }

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @property
    def crates_from_production(self) -> float:
        """Calculate the number of crates produced from the total volume.

        Returns:
            Number of 15 kg crates (production volume is in metric tons,
            so 1 ton = 1 000 kg).
        """
        total_kg = self.production_volume * 1_000
        return total_kg / self.CRATE_WEIGHT_KG

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise the Tomato instance to a plain dictionary.

        Returns:
            A dictionary containing all attributes, suitable for JSON
            serialisation.
        """
        return {
            "commodity": "Tomato",
            "production_volume": self.production_volume,
            "shelf_life_days": self.shelf_life_days,
            "storage_type": self.storage_type,
            "spoilage_rate": self.spoilage_rate,
            "market_price_per_crate": self.market_price_per_crate,
            "crate_weight_kg": self.CRATE_WEIGHT_KG,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Tomato":
        """Create a Tomato instance from a dictionary.

        Args:
            data: Dictionary with keys matching the constructor parameters.

        Returns:
            A new Tomato instance.

        Raises:
            KeyError: If a required key is missing from the dictionary.
            ValueError: If the dictionary values fail validation.
            TypeError: If the dictionary values are of incorrect types.
        """
        required_keys = [
            "production_volume",
            "shelf_life_days",
            "storage_type",
            "spoilage_rate",
            "market_price_per_crate",
        ]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: '{key}'.")

        return cls(
            production_volume=data["production_volume"],
            shelf_life_days=data["shelf_life_days"],
            storage_type=data["storage_type"],
            spoilage_rate=data["spoilage_rate"],
            market_price_per_crate=data["market_price_per_crate"],
        )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous string representation of the Tomato instance."""
        return (
            f"Tomato("
            f"production_volume={self.production_volume}, "
            f"shelf_life_days={self.shelf_life_days}, "
            f"storage_type='{self.storage_type}', "
            f"spoilage_rate={self.spoilage_rate}%, "
            f"market_price_per_crate={self.market_price_per_crate} ZMW"
            f")"
        )

