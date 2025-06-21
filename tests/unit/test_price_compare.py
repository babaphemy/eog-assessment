"""
Unit tests for the Pydantic-based price comparison service.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from pydantic import ValidationError

from app.services.price_compare import (
    PriceComparisonService,
    PlatformConfig,
    PlatformType,
    AppediaResponse,
    MicromazonResponse,
    GoogditResponse,
    PriceResult,
    ComparisonResult,
)
from app.models.platform import GoogditLocation


class TestPydanticModels:
    """Test Pydantic model validation."""

    def test_APPEDIA_response_valid(self):
        """Test valid Appedia response."""
        data = {"price": "$4.77", "stock": 7}
        response = AppediaResponse(**data)

        assert response.price == "$4.77"
        assert response.stock == 7
        assert response.price_float == 4.77
        assert response.in_stock is True

    def test_APPEDIA_response_invalid_price(self):
        """Test Appedia response with invalid price format."""
        data = {"price": "4.77", "stock": 7}  # Missing $ sign

        with pytest.raises(ValidationError) as exc_info:
            AppediaResponse(**data)

        assert "Price must start with $" in str(exc_info.value)

    def test_APPEDIA_response_out_of_stock(self):
        """Test Appedia response when out of stock."""
        data = {"price": "$4.77", "stock": 0}
        response = AppediaResponse(**data)

        assert response.in_stock is False

    def test_micromazon_response_valid(self):
        """Test valid Micromazon response."""
        data = {"available": True, "price": 5.67}
        response = MicromazonResponse(**data)

        assert response.available is True
        assert response.price == 5.67
        assert response.price_float == 5.67
        assert response.in_stock is True

    def test_micromazon_response_unavailable(self):
        """Test Micromazon response when unavailable."""
        data = {"available": False, "price": 5.67}
        response = MicromazonResponse(**data)

        assert response.in_stock is False

    def test_micromazon_response_invalid_price(self):
        """Test Micromazon response with invalid price."""
        data = {"available": True, "price": -1.0}

        with pytest.raises(ValidationError):
            MicromazonResponse(**data)

    def test_googdit_response_valid(self):
        """Test valid Googdit response."""
        data = {"a": [{"l": 8839, "q": 4}, {"l": 1292, "q": 0}], "p": 478000000}
        response = GoogditResponse(**data)

        assert len(response.a) == 2
        assert response.p == 478000000
        assert response.price_float == 4.78
        assert response.in_stock is True  # Has stock at location 8839

    def test_googdit_response_no_stock(self):
        """Test Googdit response with no stock."""
        data = {"a": [{"l": 8839, "q": 0}, {"l": 1292, "q": 0}], "p": 478000000}
        response = GoogditResponse(**data)

        assert response.in_stock is False

    def test_googdit_location_validation(self):
        """Test Googdit location validation."""
        # Valid location
        location = GoogditLocation(l=8839, q=4)
        assert location.l == 8839
        assert location.q == 4

        # Invalid quantity (negative)
        with pytest.raises(ValidationError):
            GoogditLocation(l=8839, q=-1)

    def test_price_result_valid(self):
        """Test valid price result."""
        result = PriceResult(
            platform=PlatformType.APPEDIA,
            url="https://example.com",  # Mock URL
            price=5.99,
            in_stock=True,
        )

        assert result.is_valid is True
        assert result.platform == PlatformType.APPEDIA

    def test_price_result_invalid_combinations(self):
        """Test invalid price result combinations."""
        # Out of stock
        result1 = PriceResult(
            platform=PlatformType.APPEDIA,
            url="https://example.com",
            price=5.99,
            in_stock=False,
        )
        assert result1.is_valid is False

        # Zero price
        result2 = PriceResult(
            platform=PlatformType.APPEDIA,
            url="https://example.com",
            price=0.0,
            in_stock=True,
        )
        assert result2.is_valid is False

        # Has error message
        result3 = PriceResult(
            platform=PlatformType.APPEDIA,
            url="https://example.com",
            price=5.99,
            in_stock=True,
            error_message="API Error",
        )
        assert result3.is_valid is False

    def test_price_result_comparison(self):
        """Test price result comparison for sorting."""
        result1 = PriceResult(
            platform=PlatformType.APPEDIA,
            url="https://example.com",
            price=5.99,
            in_stock=True,
        )

        result2 = PriceResult(
            platform=PlatformType.MICROMAZON,
            url="https://example.com",
            price=4.99,
            in_stock=True,
        )

        assert result2 < result1  # Lower price should be "less than"
        assert min([result1, result2]) == result2

    def test_platform_config_validation(self):
        """Test platform configuration validation."""
        # Valid config
        config = PlatformConfig(
            upc=101, url="https://example.com/api", platform=PlatformType.APPEDIA
        )
        assert config.upc == 101

        # Invalid UPC (zero or negative)
        with pytest.raises(ValidationError):
            PlatformConfig(
                upc=0, url="https://example.com/api", platform=PlatformType.APPEDIA
            )

        # Invalid URL
        with pytest.raises(ValidationError):
            PlatformConfig(upc=101, url="not-a-url", platform=PlatformType.APPEDIA)

    def test_comparison_result_model(self):
        """Test comparison result model."""
        result = ComparisonResult(
            upc=101,
            best_platform=PlatformType.APPEDIA,
            best_price=4.99,
            best_url="https://example.com",
            message="Best price found",
            all_results=[],
        )

        assert result.upc == 101
        assert result.best_platform == PlatformType.APPEDIA
        assert result.best_price == 4.99


class TestPriceComparisonService:
    """Test the main price comparison service with Pydantic models."""

    @pytest.fixture
    def service(self):
        """Create a price comparison service instance."""
        return PriceComparisonService()

    def test_service_initialization(self, service):
        """Test service initialization with default platforms."""
        assert len(service.platforms) == 3
        assert PlatformType.APPEDIA in service.platforms
        assert PlatformType.MICROMAZON in service.platforms
        assert PlatformType.GOOGDIT in service.platforms

    def test_add_remove_platform(self, service):
        """Test adding and removing platforms. Assuming this is acceptable."""
        # Create a new config
        new_config = PlatformConfig(
            upc=123,
            url="https://newplatform.com/api",
            platform=PlatformType.APPEDIA,  # Reusing existing enum
        )

        # Add platform
        initial_count = len(service.platforms)
        service.add_platform(new_config)

        # Should replace existing APPEDIA config
        assert len(service.platforms) == initial_count
        assert service.platforms[PlatformType.APPEDIA].upc == 123

        # Remove platform
        service.remove_platform(PlatformType.APPEDIA)
        assert PlatformType.APPEDIA not in service.platforms

    def test_get_platform_url(self, service):
        """Test URL generation for different platforms."""
        # Appedia
        url = service.get_platform_url(PlatformType.APPEDIA, 123)
        assert "upc=123" in url

        # Micromazon
        url = service.get_platform_url(PlatformType.MICROMAZON, 123)
        assert "/123/" in url

        # Googdit
        url = service.get_platform_url(PlatformType.GOOGDIT, 123)
        assert url.endswith("/123")

        # Non-existent platform
        service.remove_platform(PlatformType.APPEDIA)
        with pytest.raises(ValueError, match="Platform .* not configured"):
            service.get_platform_url(PlatformType.APPEDIA, 123)

    def test_parse_platform_response(self, service):
        """Test parsing platform-specific responses."""
        # Appedia
        heb_data = {"price": "$4.77", "stock": 7}
        price, in_stock = service._parse_platform_response(
            PlatformType.APPEDIA, heb_data
        )
        assert price == 4.77
        assert in_stock is True

        # Micromazon
        micro_data = {"available": True, "price": 5.67}
        price, in_stock = service._parse_platform_response(
            PlatformType.MICROMAZON, micro_data
        )
        assert price == 5.67
        assert in_stock is True

        # Googdit
        googdit_data = {"a": [{"l": 8839, "q": 4}], "p": 478000000}
        price, in_stock = service._parse_platform_response(
            PlatformType.GOOGDIT, googdit_data
        )
        assert price == 4.78
        assert in_stock is True

    @pytest.mark.asyncio
    async def test_fetch_data_success(self, service):
        """Test successful data fetching."""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"price": "$4.77", "stock": 7}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        result = await service.fetch_data_from_platform(
            PlatformType.APPEDIA, 101, mock_client
        )

        assert result.platform == PlatformType.APPEDIA
        assert result.price == 4.77
        assert result.in_stock is True
        assert result.is_valid is True

    @pytest.mark.asyncio
    async def test_fetch_data_404_error(self, service):
        """Test handling 404 errors."""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response

        result = await service.fetch_data_from_platform(
            PlatformType.APPEDIA, 999, mock_client
        )

        assert result.platform == PlatformType.APPEDIA
        assert result.is_valid is False
        assert "not found" in result.error_message.lower()

    def test_analyze_results_with_valid_prices(self, service):
        """Test analyzing results with valid prices."""
        results = [
            PriceResult(
                platform=PlatformType.APPEDIA, url="url1", price=5.99, in_stock=True
            ),
            PriceResult(
                platform=PlatformType.MICROMAZON,
                url="url2",
                price=4.99,  # This should be best
                in_stock=True,
            ),
        ]

        analysis = service._analyze_results(101, results)

        assert analysis.upc == 101
        assert analysis.best_platform == PlatformType.MICROMAZON
        assert analysis.best_price == 4.99
        assert "MICROMAZON" in analysis.message.upper()

    def test_analyze_results_no_valid_prices(self, service):
        """Test analyzing results with no valid prices."""
        results = [
            PriceResult(
                platform=PlatformType.APPEDIA,
                url="url1",
                price=0.0,
                in_stock=False,
                error_message="Error 1",
            ),
        ]

        analysis = service._analyze_results(101, results)

        assert analysis.upc == 101
        assert analysis.best_platform is None
        assert analysis.best_price is None
        assert "No valid prices found" in analysis.message

    def test_service_validation_errors(self):
        """Test service validation with invalid data."""
        # Invalid timeout
        with pytest.raises(ValidationError):
            PriceComparisonService(timeout=-1.0)

        # Service should accept valid timeout
        service = PriceComparisonService(timeout=5.0)
        assert service.timeout == 5.0


# Run tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
