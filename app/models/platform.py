"""Platform and price comparison related models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl, ConfigDict
from app.utils.constants import GOOGDIT_PRICE_DIVISOR


class PlatformType(str, Enum):
    """Supported platforms for price comparison."""

    APPEDIA = "Appedia"
    MICROMAZON = "Micromazon"
    GOOGDIT = "Googdit"


class PlatformConfig(BaseModel):
    """Platform configuration."""

    upc: int = Field(..., gt=0, description="Universal Product Code")
    url: HttpUrl = Field(..., description="API endpoint URL")
    platform: PlatformType = Field(..., description="Platform type")

    model_config = ConfigDict(
        use_enum_values=True,
    )


class AppediaResponse(BaseModel):
    """API response model."""

    price: str = Field(..., description="Price as string with $ sign")
    stock: int = Field(..., ge=0, description="Stock quantity")

    @field_validator("price")
    @classmethod
    def validate_price(cls, v):
        """Validate and clean price string."""
        if not v.startswith("$"):
            raise ValueError("Price must start with $")
        return v

    @property
    def price_float(self) -> float:
        """Convert price string to float."""
        return float(self.price.replace("$", "").replace(",", ""))

    @property
    def in_stock(self) -> bool:
        """Check if item is in stock."""
        return self.stock > 0


class MicromazonResponse(BaseModel):
    """Micromazon API response model."""

    available: bool = Field(..., description="Availability status")
    price: float = Field(..., gt=0, description="Price as float")

    @property
    def price_float(self) -> float:
        """Get price as float."""
        return self.price

    @property
    def in_stock(self) -> bool:
        """Check if item is in stock."""
        return self.available


class GoogditLocation(BaseModel):
    """Googdit location data."""

    l: int = Field(..., description="Location ID")
    q: int = Field(..., ge=0, description="Quantity available")


class GoogditResponse(BaseModel):
    """Googdit API response model."""

    a: list[GoogditLocation] = Field(..., description="Availability array")
    p: int = Field(..., gt=0, description="Price in microcents")

    @property
    def price_float(self) -> float:
        """Convert microcents to dollars."""
        return self.p / GOOGDIT_PRICE_DIVISOR

    @property
    def in_stock(self) -> bool:
        """Check if item is in stock at any location."""
        return any(location.q > 0 for location in self.a)


class PriceResult(BaseModel):
    """Standardized price result."""

    platform: PlatformType
    url: str
    price: float = Field(..., ge=0)
    in_stock: bool
    raw_data: dict = Field(default_factory=dict)
    error_message: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Check if this is a valid result."""
        return self.error_message is None and self.in_stock and self.price > 0

    def __lt__(self, other):
        """Enable comparison for finding minimum price."""
        if not isinstance(other, PriceResult):
            return NotImplemented
        return self.price < other.price

    model_config = ConfigDict(use_enum_values=True)


class ComparisonResult(BaseModel):
    """Result of price comparison across platforms."""

    upc: int
    best_platform: Optional[PlatformType] = None
    best_price: Optional[float] = None
    best_url: Optional[str] = None
    message: str
    all_results: list[PriceResult] = Field(default_factory=list)

    model_config = ConfigDict(
        use_enum_values=True,
    )

    @property
    def display_price(self) -> str:
        """Get formatted price for display."""
        if self.best_price is None or self.best_price <= 0:
            return "Not available"
        if self.best_price == 0:
            return "Free"
        return f"${self.best_price:.2f}"

    def __lt__(self, other: "PriceResult") -> bool:
        """Comparison between PriceResult objects."""
        if not isinstance(other, PriceResult):
            return NotImplemented

        # Invalid results are always "greater" (worse)
        if not self.is_valid and not other.is_valid:
            return False
        if not self.is_valid:
            return False
        if not other.is_valid:
            return True

        return self.price < other.price
