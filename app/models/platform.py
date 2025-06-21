"""Platform and price comparison related models."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator, HttpUrl


class PlatformType(str, Enum):
    """Supported platforms for price comparison."""

    APPEDIA = "Appedia"
    MICROMAZON = "Micromazon"
    GOOGDIT = "Googdit"


class Platform(BaseModel):
    """A price comparison platform."""

    url: HttpUrl = Field(..., description="Platform URL (must be valid HTTP/HTTPS)")
    name: str = Field(..., min_length=1, description="Platform name")
    platform_type: PlatformType = Field(..., description="Type of platform")

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """The platform name is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Platform name cannot be empty or just whitespace")
        return v.strip()


class PriceResult(BaseModel):
    """A price result from given platform."""

    price: float = Field(..., ge=0, description="Price (cannot be negative)")
    available: bool = Field(..., description="Whether the item is available")
    platform: str = Field(..., min_length=1, description="Platform name")
    raw_data: Optional[str] = Field(None, description="Raw response data")
    error_message: Optional[str] = Field(None, description="Error message if any")

    @field_validator("platform")
    @classmethod
    def validate_platform(cls, v: str) -> str:
        """The platform name is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Platform name cannot be empty or just whitespace")
        return v.strip()

    @property
    def is_valid(self) -> bool:
        """Check if price result is valid for comparison."""
        return self.available and self.price > 0 and self.error_message is None

    @property
    def display_price(self) -> str:
        """Get formatted price for display."""
        if not self.available:
            return "Not available"
        if self.price == 0:
            return "Free"
        return f"${self.price:.2f}"

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
