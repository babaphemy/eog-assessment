"""
Price comparison service using Pydantic models for data validation.
"""

import asyncio
import logging
from typing import Dict, List, Optional
from app.utils.constants import GOOGDIT_PRICE_DIVISOR
from app.models.platform import PlatformType

import httpx
from pydantic import BaseModel, HttpUrl, Field, field_validator, ConfigDict

logger = logging.getLogger(__name__)


class PlatformConfig(BaseModel):
    """Platformm configuration."""

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

    a: List[GoogditLocation] = Field(..., description="Availability array")
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
    raw_data: Dict = Field(default_factory=dict)
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
    all_results: List[PriceResult] = Field(default_factory=list)

    model_config = ConfigDict(
        use_enum_values=True,
    )


class PriceComparisonService(BaseModel):
    """Service for comparing prices across multiple platforms using Pydantic models."""

    timeout: float = Field(default=10.0, gt=0, description="Request timeout in seconds")
    platforms: Dict[PlatformType, PlatformConfig] = Field(default_factory=dict)

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, **data):
        super().__init__(**data)
        self._initialize_default_platforms()

    def _initialize_default_platforms(self):
        """Initialize default platform configurations."""
        default_configs = [
            PlatformConfig(
                upc=101,
                url="https://appedia.heb-platform-interview.hebdigital-prd.com/api/v1/itemdata?upc=101",
                platform=PlatformType.APPEDIA,
            ),
            PlatformConfig(
                upc=101,
                url="https://micromazon.heb-platform-interview.hebdigital-prd.com/101/productinfo",
                platform=PlatformType.MICROMAZON,
            ),
            PlatformConfig(
                upc=101,
                url="https://googdit.heb-platform-interview.hebdigital-prd.com/101",
                platform=PlatformType.GOOGDIT,
            ),
        ]

        for config in default_configs:
            self.platforms[config.platform] = config

    def add_platform(self, config: PlatformConfig):
        """Add a new platform configuration."""
        self.platforms[config.platform] = config

    def remove_platform(self, platform: PlatformType):
        """Remove a platform configuration."""
        self.platforms.pop(platform, None)

    def get_platform_url(self, platform: PlatformType, upc: int) -> str:
        """Generate URL for a platform with given UPC."""
        if platform not in self.platforms:
            raise ValueError(f"Platform {platform} not configured")

        base_config = self.platforms[platform]
        url_str = str(base_config.url)

        # Replace the UPC in the URL
        if platform == PlatformType.APPEDIA:
            return url_str.replace("upc=101", f"upc={upc}")
        elif platform == PlatformType.MICROMAZON:
            return url_str.replace("/101/", f"/{upc}/")
        elif platform == PlatformType.GOOGDIT:
            return url_str.replace("/101", f"/{upc}")

        return url_str

    def _parse_platform_response(
        self, platform: PlatformType, data: dict
    ) -> tuple[float, bool]:
        """Parse platform-specific response data."""
        try:
            if platform == PlatformType.APPEDIA:
                response = AppediaResponse(
                    **data
                )  # Note: use model_validate if their are unnecesary links that may be copied
                return response.price_float, response.in_stock

            elif platform == PlatformType.MICROMAZON:
                response = MicromazonResponse(**data)
                return response.price_float, response.in_stock

            elif platform == PlatformType.GOOGDIT:
                response = GoogditResponse(**data)
                return response.price_float, response.in_stock

            else:
                raise ValueError(f"Unknown platform: {platform}")

        except Exception as e:
            logger.error(f"Error parsing {platform} response: {e}")
            raise

    async def fetch_data_from_platform(
        self, platform: PlatformType, upc: int, client: httpx.AsyncClient
    ) -> PriceResult:
        """Fetch data from a given platform."""
        url = self.get_platform_url(platform, upc)

        try:
            response = await client.get(url, timeout=self.timeout)

            if response.status_code == 404:
                return PriceResult(
                    platform=platform,
                    url=url,
                    price=0.0,
                    in_stock=False,
                    error_message=f"Product with UPC {upc} not found on {platform}",
                )

            response.raise_for_status()
            data = response.json()

            price, in_stock = self._parse_platform_response(platform, data)

            return PriceResult(
                platform=platform,
                url=url,
                price=price,
                in_stock=in_stock,
                raw_data=data,
            )

        except httpx.HTTPStatusError as e:
            error_msg = f"HTTP {e.response.status_code} error from {platform}"
            logger.warning(error_msg)
            return PriceResult(
                platform=platform,
                url=url,
                price=0.0,
                in_stock=False,
                error_message=error_msg,
            )

        except Exception as e:
            error_msg = f"Error fetching from {platform}: {str(e)}"
            logger.error(error_msg)
            return PriceResult(
                platform=platform,
                url=url,
                price=0.0,
                in_stock=False,
                error_message=error_msg,
            )

    async def compare_prices_async(self, upc: int) -> ComparisonResult:
        """Compare prices across all platforms asynchronously."""
        async with httpx.AsyncClient() as client:
            # Fetch from all platforms concurrently
            tasks = [
                self.fetch_data_from_platform(platform, upc, client)
                for platform in self.platforms.keys()
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Filter out exceptions
            price_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Task failed with exception: {result}")
                    continue
                price_results.append(result)

        return self._analyze_results(upc, price_results)

    def compare_prices_sync(self, upc: int) -> ComparisonResult:
        """Synchronous wrapper for price comparison."""
        return asyncio.run(self.compare_prices_async(upc))

    def _analyze_results(
        self, upc: int, price_results: List[PriceResult]
    ) -> ComparisonResult:
        """Analyze price results and find the best option."""
        valid_results = [result for result in price_results if result.is_valid]

        if not valid_results:
            return ComparisonResult(
                upc=upc,
                message="No valid prices found - all platforms either out of stock or returned errors",
                all_results=price_results,
            )

        # Find the result with the lowest price
        best_result = min(valid_results)

        return ComparisonResult(
            upc=upc,
            best_platform=best_result.platform,
            best_price=best_result.price,
            best_url=best_result.url,
            message=f"Best price found: ${best_result.price:.2f} on {best_result.platform}",
            all_results=price_results,
        )

    def find_best_price(self, upc: int) -> ComparisonResult:
        """Main method to find the best price for a UPC."""
        return self.compare_prices_sync(upc)
