"""
Maize commodity model for AgriTwin-ZM.

Represents maize production, storage, and loss characteristics
specific to Zambia's agricultural context.
"""

from __future__ import annotations


class Maize:
    """Model representing maize as a commodity in Zambia's agricultural system.

    Attributes:
        production_volume: Total production volume in metric tons.
        storage_capacity: Maximum storage capacity in metric tons.
        moisture_level: Grain moisture content as a percentage (0-100).
        price_per_ton: Market price per metric ton in Zambian Kwacha (ZMW).
        loss_percentage_per_month: Expected storage loss rate per month as a
            percentage (0-100).
    """

    def __init__(
        self,
        production_volume: float,
        storage_capacity: float,
        moisture_level: float,
        price_per_ton: float,
        loss_percentage_per_month: float,
    ) -> None:
        """Initialise a Maize commodity instance.

        Args:
            production_volume: Total production volume in metric tons.
            storage_capacity: Maximum storage capacity in metric tons.
            moisture_level: Grain moisture content as a percentage (0-100).
            price_per_ton: Market price per metric ton in ZMW.
            loss_percentage_per_month: Monthly storage loss rate as a
                percentage (0-100).

        Raises:
            ValueError: If any numeric value is negative, or if percentage
                values are outside the 0-100 range.
            TypeError: If any argument is not a numeric type.
        """
        self._validate_inputs(
            production_volume,
            storage_capacity,
            moisture_level,
            price_per_ton,
            loss_percentage_per_month,
        )

        self.production_volume: float = float(production_volume)
        self.storage_capacity: float = float(storage_capacity)
        self.moisture_level: float = float(moisture_level)
        self.price_per_ton: float = float(price_per_ton)
        self.loss_percentage_per_month: float = float(loss_percentage_per_month)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_inputs(
        production_volume: float,
        storage_capacity: float,
        moisture_level: float,
        price_per_ton: float,
        loss_percentage_per_month: float,
    ) -> None:
        """Validate all constructor inputs.

        Raises:
            TypeError: If any argument is not int or float.
            ValueError: If any value is negative or percentages are out of
                the 0-100 range.
        """
        params = {
            "production_volume": production_volume,
            "storage_capacity": storage_capacity,
            "moisture_level": moisture_level,
            "price_per_ton": price_per_ton,
            "loss_percentage_per_month": loss_percentage_per_month,
        }

        for name, value in params.items():
            if not isinstance(value, (int, float)):
                raise TypeError(
                    f"'{name}' must be a numeric type (int or float), "
                    f"got {type(value).__name__}."
                )
            if value < 0:
                raise ValueError(
                    f"'{name}' must be non-negative, got {value}."
                )

        # Percentage bounds
        if not 0 <= moisture_level <= 100:
            raise ValueError(
                f"'moisture_level' must be between 0 and 100, "
                f"got {moisture_level}."
            )
        if not 0 <= loss_percentage_per_month <= 100:
            raise ValueError(
                f"'loss_percentage_per_month' must be between 0 and 100, "
                f"got {loss_percentage_per_month}."
            )

    # ------------------------------------------------------------------
    # Core methods
    # ------------------------------------------------------------------

    def calculate_monthly_loss(self) -> float:
        """Calculate the tonnage lost in a single month due to storage loss.

        The loss is computed as a simple percentage of the current
        production volume.

        Returns:
            The number of metric tons lost in one month.
        """
        return self.production_volume * (self.loss_percentage_per_month / 100)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialise the Maize instance to a plain dictionary.

        Returns:
            A dictionary containing all attributes, suitable for JSON
            serialisation.
        """
        return {
            "commodity": "Maize",
            "production_volume": self.production_volume,
            "storage_capacity": self.storage_capacity,
            "moisture_level": self.moisture_level,
            "price_per_ton": self.price_per_ton,
            "loss_percentage_per_month": self.loss_percentage_per_month,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Maize":
        """Create a Maize instance from a dictionary.

        Args:
            data: Dictionary with keys matching the constructor parameters.

        Returns:
            A new Maize instance.

        Raises:
            KeyError: If a required key is missing from the dictionary.
            ValueError: If the dictionary values fail validation.
            TypeError: If the dictionary values are not numeric.
        """
        required_keys = [
            "production_volume",
            "storage_capacity",
            "moisture_level",
            "price_per_ton",
            "loss_percentage_per_month",
        ]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: '{key}'.")

        return cls(
            production_volume=data["production_volume"],
            storage_capacity=data["storage_capacity"],
            moisture_level=data["moisture_level"],
            price_per_ton=data["price_per_ton"],
            loss_percentage_per_month=data["loss_percentage_per_month"],
        )

    # ------------------------------------------------------------------
    # Dunder methods
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return an unambiguous string representation of the Maize instance."""
        return (
            f"Maize("
            f"production_volume={self.production_volume}, "
            f"storage_capacity={self.storage_capacity}, "
            f"moisture_level={self.moisture_level}%, "
            f"price_per_ton={self.price_per_ton} ZMW, "
            f"loss_percentage_per_month={self.loss_percentage_per_month}%"
            f")"
        )

