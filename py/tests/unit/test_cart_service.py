"""
Unit tests for ShoppingCartManager service.
"""

import pytest
import json
import tempfile
from pathlib import Path

from app.services.cart_service import ShoppingCartManager
from app.models.cart import ShoppingCart, ShoppingCartData
from app.models.coupon import ShoppingCartCoupon
from app.utils.constants import DEFAULT_TAX_RATE


class TestShoppingCartManager:
    """Test the fixed shopping cart manager."""

    @pytest.fixture
    def manager(self):
        """Create a shopping cart manager instance."""
        return ShoppingCartManager()

    @pytest.fixture
    def custom_tax_manager(self):
        """Create a shopping cart manager with custom tax rate."""
        return ShoppingCartManager(tax_rate=0.10)  # 10% tax

    @pytest.fixture
    def sample_cart_items(self):
        """Sample cart items for testing."""
        return [
            ShoppingCart(
                itemName="H-E-B Two Bite Brownies",
                sku=85294241,
                isTaxable=False,
                ownBrand=True,
                price=3.61,
            ),
            ShoppingCart(
                itemName="Halo Top Vanilla Bean Ice Cream",
                sku=95422042,
                isTaxable=True,
                ownBrand=False,
                price=3.31,
            ),
            ShoppingCart(
                itemName="Taxable Test Item",
                sku=12345678,
                isTaxable=True,
                ownBrand=True,
                price=10.00,
            ),
        ]

    @pytest.fixture
    def sample_coupons(self):
        """Sample coupons for testing."""
        return [
            ShoppingCartCoupon(
                couponName="Brownie Discount",
                appliedSku=85294241,
                discountPrice=0.79,
            ),
            ShoppingCartCoupon(
                couponName="Ice Cream Discount",
                appliedSku=95422042,
                discountPrice=1.00,
            ),
            ShoppingCartCoupon(
                couponName="Better Ice Cream Discount",  # Better discount for same item
                appliedSku=95422042,
                discountPrice=1.50,
            ),
        ]

    def test_initialization_default_tax(self, manager):
        """Test manager initialization with default tax rate."""
        assert manager.tax_rate == DEFAULT_TAX_RATE
        assert manager._cart_cache is None
        assert manager._coupons_cache is None
        assert manager._last_cart_path is None
        assert manager._last_coupons_path is None

    def test_initialization_custom_tax(self, custom_tax_manager):
        """Test manager initialization with custom tax rate."""
        assert custom_tax_manager.tax_rate == 0.10

    def test_calculate_subtotal_empty_cart(self, manager):
        """Test subtotal calculation with empty cart."""
        result = manager.calculate_subtotal([])
        assert result == 0.0

    def test_calculate_subtotal_with_items(self, manager, sample_cart_items):
        """Test subtotal calculation with items."""
        result = manager.calculate_subtotal(sample_cart_items)
        expected = 3.61 + 3.31 + 10.00  # 16.92
        assert result == expected

    def test_calculate_tax_no_taxable_items(self, manager):
        """Test tax calculation with no taxable items."""
        non_taxable_items = [
            ShoppingCart(
                itemName="Non-taxable Item",
                sku=123,
                isTaxable=False,
                ownBrand=True,
                price=5.00,
            )
        ]
        result = manager.calculate_tax(non_taxable_items)
        assert result == 0.0

    def test_calculate_tax_with_taxable_items(self, manager, sample_cart_items):
        """Test tax calculation with taxable items."""
        result = manager.calculate_tax(sample_cart_items)
        # Only items with isTaxable=True: 3.31 + 10.00 = 13.31
        # Tax: 13.31 * DEFAULT_TAX_RATE (0.0825) = 1.098075, rounded to 1.10
        taxable_total = 3.31 + 10.00  # 13.31
        expected = round(taxable_total * DEFAULT_TAX_RATE, 2)
        assert result == expected

    def test_calculate_tax_custom_rate(self, custom_tax_manager, sample_cart_items):
        """Test tax calculation with custom tax rate."""
        result = custom_tax_manager.calculate_tax(sample_cart_items)
        taxable_total = 3.31 + 10.00  # 13.31
        expected = round(taxable_total * 0.10, 2)  # 1.33
        assert result == expected

    def test_apply_coupon_to_item_no_applicable_coupons(
        self, manager, sample_cart_items, sample_coupons
    ):
        """Test applying coupon when no coupons apply to the item."""
        # Create an item with SKU that has no matching coupons
        item = ShoppingCart(
            itemName="No Coupon Item",
            sku=999999,
            isTaxable=False,
            ownBrand=True,
            price=5.00,
        )
        result = manager.apply_coupon_to_item(item, sample_coupons)
        assert result == 5.00  # Original price

    def test_apply_coupon_to_item_single_coupon(self, manager, sample_coupons):
        """Test applying single coupon to item."""
        item = ShoppingCart(
            itemName="Brownies",
            sku=85294241,
            isTaxable=False,
            ownBrand=True,
            price=3.61,
        )
        result = manager.apply_coupon_to_item(item, sample_coupons)
        expected = 3.61 - 0.79  # 2.82
        assert result == expected

    def test_apply_coupon_to_item_multiple_coupons_best_selected(
        self, manager, sample_coupons
    ):
        """Test applying best coupon when multiple coupons apply."""
        item = ShoppingCart(
            itemName="Ice Cream",
            sku=95422042,
            isTaxable=True,
            ownBrand=False,
            price=3.31,
        )
        result = manager.apply_coupon_to_item(item, sample_coupons)
        # Should use the better discount (1.50) not the smaller one (1.00)
        expected = 3.31 - 1.50  # 1.81
        assert result == expected

    def test_apply_coupon_prevents_negative_price(self, manager):
        """Test that coupon application doesn't result in negative price."""
        item = ShoppingCart(
            itemName="Cheap Item",
            sku=123,
            isTaxable=False,
            ownBrand=True,
            price=1.00,
        )
        large_coupon = [
            ShoppingCartCoupon(
                couponName="Large Discount",
                appliedSku=123,
                discountPrice=2.00,  # Larger than item price
            )
        ]
        result = manager.apply_coupon_to_item(item, large_coupon)
        assert result == 0.0  # Should not go below 0

    def test_apply_coupons_to_cart(self, manager, sample_cart_items, sample_coupons):
        """Test applying coupons to entire cart."""
        result = manager.apply_coupons_to_cart(sample_cart_items, sample_coupons)

        assert len(result) == len(sample_cart_items)
        assert isinstance(result[0], ShoppingCart)

        # Check specific discounted prices
        brownie_item = next(item for item in result if item.sku == 85294241)
        ice_cream_item = next(item for item in result if item.sku == 95422042)
        test_item = next(item for item in result if item.sku == 12345678)

        assert brownie_item.price == 3.61 - 0.79  # 2.82
        assert ice_cream_item.price == 3.31 - 1.50  # 1.81 (best coupon)
        assert test_item.price == 10.00  # No coupon applies

    def test_calculate_totals_empty_cart(self, manager):
        """Test total calculation with empty cart."""
        result = manager.calculate_totals([])
        assert result.subTotal == 0.0
        assert result.taxTotal == 0.0
        assert result.grandTotal == 0.0

    def test_calculate_totals_without_coupons(self, manager, sample_cart_items):
        """Test total calculation without coupons."""
        result = manager.calculate_totals(sample_cart_items)

        expected_subtotal = 16.92  # 3.61 + 3.31 + 10.00
        expected_tax = round(
            (3.31 + 10.00) * DEFAULT_TAX_RATE, 2
        )  # Tax on taxable items only
        expected_grand_total = round(expected_subtotal + expected_tax, 2)

        assert result.subTotal == expected_subtotal
        assert result.taxTotal == expected_tax
        assert result.grandTotal == expected_grand_total

    def test_calculate_totals_with_coupons(
        self, manager, sample_cart_items, sample_coupons
    ):
        """Test total calculation with coupons."""
        result = manager.calculate_totals(sample_cart_items, sample_coupons)

        # After coupons: 2.82 + 1.81 + 10.00 = 14.63
        expected_subtotal = 14.63
        # Tax on taxable items after coupons: (1.81 + 10.00) * 0.0825
        expected_tax = round((1.81 + 10.00) * DEFAULT_TAX_RATE, 2)
        expected_grand_total = round(expected_subtotal + expected_tax, 2)

        assert result.subTotal == expected_subtotal
        assert result.taxTotal == expected_tax
        assert result.grandTotal == expected_grand_total

    def test_calculate_totals_no_tax(self, manager, sample_cart_items):
        """Test Feature 1: Calculate total without tax."""
        result = manager.calculate_totals_no_tax(sample_cart_items)

        expected_subtotal = 16.92
        assert result.subTotal == expected_subtotal
        assert result.taxTotal == 0.0
        assert result.grandTotal == expected_subtotal

    def test_calculate_totals_tax_all(self, manager, sample_cart_items):
        """Test Feature 2: Calculate total with tax on all items."""
        result = manager.calculate_totals_tax_all(sample_cart_items)

        expected_subtotal = 16.92
        expected_tax = round(
            expected_subtotal * DEFAULT_TAX_RATE, 2
        )  # Tax on ALL items
        expected_grand_total = round(expected_subtotal + expected_tax, 2)

        assert result.subTotal == expected_subtotal
        assert result.taxTotal == expected_tax
        assert result.grandTotal == expected_grand_total

    def test_calculate_totals_tax_taxable_only(self, manager, sample_cart_items):
        """Test Feature 3: Calculate total with tax only on taxable items."""
        result = manager.calculate_totals_tax_taxable_only(sample_cart_items)

        expected_subtotal = 16.92
        expected_tax = round(
            (3.31 + 10.00) * DEFAULT_TAX_RATE, 2
        )  # Tax only on taxable
        expected_grand_total = round(expected_subtotal + expected_tax, 2)

        assert result.subTotal == expected_subtotal
        assert result.taxTotal == expected_tax
        assert result.grandTotal == expected_grand_total


class TestFileOperations:
    """Test file loading and caching functionality."""

    @pytest.fixture
    def manager(self):
        """Create a shopping cart manager instance."""
        return ShoppingCartManager()

    @pytest.fixture
    def temp_cart_file(self, sample_cart_items):
        """Create a temporary cart JSON file."""
        cart_data = [
            {
                "itemName": item.itemName,
                "sku": item.sku,
                "isTaxable": item.isTaxable,
                "ownBrand": item.ownBrand,
                "price": item.price,
            }
            for item in sample_cart_items
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(cart_data, f)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def temp_coupons_file(self, sample_coupons):
        """Create a temporary coupons JSON file."""
        coupon_data = [
            {
                "couponName": coupon.couponName,
                "appliedSku": coupon.appliedSku,
                "discountPrice": coupon.discountPrice,
            }
            for coupon in sample_coupons
        ]

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(coupon_data, f)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def sample_cart_items(self):
        """Sample cart items for file tests."""
        return [
            ShoppingCart(
                itemName="Test Item 1",
                sku=111,
                isTaxable=True,
                ownBrand=False,
                price=5.99,
            ),
            ShoppingCart(
                itemName="Test Item 2",
                sku=222,
                isTaxable=False,
                ownBrand=True,
                price=3.50,
            ),
        ]

    @pytest.fixture
    def sample_coupons(self):
        """Sample coupons for file tests."""
        return [
            ShoppingCartCoupon(
                couponName="Test Coupon",
                appliedSku=111,
                discountPrice=1.00,
            )
        ]

    def test_load_cart_success(self, manager, temp_cart_file):
        """Test successful cart loading from file."""
        result = manager.load_cart(temp_cart_file)

        assert len(result) == 2
        assert isinstance(result[0], ShoppingCart)
        assert result[0].itemName == "Test Item 1"
        assert result[1].itemName == "Test Item 2"

    def test_load_coupons_success(self, manager, temp_coupons_file):
        """Test successful coupons loading from file."""
        result = manager.load_coupons(temp_coupons_file)

        assert len(result) == 1
        assert isinstance(result[0], ShoppingCartCoupon)
        assert result[0].couponName == "Test Coupon"

    def test_load_cart_file_not_exists(self, manager):
        """Test loading cart when file doesn't exist."""
        result = manager.load_cart("nonexistent_file.json")
        assert result == []

    def test_load_cart_empty_file(self, manager):
        """Test loading cart from empty file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = Path(f.name)

        try:
            result = manager.load_cart(temp_path)
            assert result == []
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_cart_invalid_json(self, manager):
        """Test loading cart from file with invalid JSON."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("invalid json content")
            temp_path = Path(f.name)

        try:
            result = manager.load_cart(temp_path)
            assert result == []
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_cart_not_list(self, manager):
        """Test loading cart from file that doesn't contain a list."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"not": "a list"}, f)
            temp_path = Path(f.name)

        try:
            result = manager.load_cart(temp_path)
            assert result == []
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_load_cart_validation_error(self, manager):
        """Test loading cart with invalid data that fails Pydantic validation."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Missing required fields
            invalid_data = [{"itemName": "Test", "invalid": "data"}]
            json.dump(invalid_data, f)
            temp_path = Path(f.name)

        try:
            result = manager.load_cart(temp_path)
            assert result == []
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_cart_caching(self, manager, temp_cart_file):
        """Test that cart loading uses caching."""
        # First load
        result1 = manager.load_cart(temp_cart_file)
        assert len(result1) == 2
        assert manager._cart_cache is not None
        assert manager._last_cart_path == temp_cart_file

        # Second load should use cache
        result2 = manager.load_cart(temp_cart_file)
        assert result2 is manager._cart_cache  # Same object reference

    def test_coupons_caching(self, manager, temp_coupons_file):
        """Test that coupons loading uses caching."""
        # First load
        result1 = manager.load_coupons(temp_coupons_file)
        assert len(result1) == 1
        assert manager._coupons_cache is not None
        assert manager._last_coupons_path == temp_coupons_file

        # Second load should use cache
        result2 = manager.load_coupons(temp_coupons_file)
        assert result2 is manager._coupons_cache  # Same object reference

    def test_clear_cache(self, manager, temp_cart_file, temp_coupons_file):
        """Test cache clearing."""
        # Load data to populate cache
        manager.load_cart(temp_cart_file)
        manager.load_coupons(temp_coupons_file)

        assert manager._cart_cache is not None
        assert manager._coupons_cache is not None

        # Clear cache
        manager.clear_cache()

        assert manager._cart_cache is None
        assert manager._coupons_cache is None
        assert manager._last_cart_path is None
        assert manager._last_coupons_path is None

    def test_calculate_totals_from_file(
        self, manager, temp_cart_file, temp_coupons_file
    ):
        """Test calculating totals directly from files."""
        result = manager.calculate_totals_from_file(temp_cart_file, temp_coupons_file)

        assert isinstance(result, ShoppingCartData)
        assert result.subTotal > 0
        assert result.grandTotal > 0

    def test_calculate_totals_from_file_no_coupons(self, manager, temp_cart_file):
        """Test calculating totals from file without coupons."""
        result = manager.calculate_totals_from_file(temp_cart_file)

        assert isinstance(result, ShoppingCartData)
        assert result.subTotal > 0

    def test_calculate_totals_no_tax_from_file(self, manager, temp_cart_file):
        """Test Feature 1 calculation from file."""
        result = manager.calculate_totals_no_tax_from_file(temp_cart_file)

        assert isinstance(result, ShoppingCartData)
        assert result.taxTotal == 0.0
        assert result.subTotal == result.grandTotal

    def test_calculate_totals_tax_all_from_file(self, manager, temp_cart_file):
        """Test Feature 2 calculation from file."""
        result = manager.calculate_totals_tax_all_from_file(temp_cart_file)

        assert isinstance(result, ShoppingCartData)
        assert result.taxTotal > 0
        assert result.grandTotal > result.subTotal

    def test_calculate_totals_tax_taxable_only_from_file(self, manager, temp_cart_file):
        """Test Feature 3 calculation from file."""
        result = manager.calculate_totals_tax_taxable_only_from_file(temp_cart_file)

        assert isinstance(result, ShoppingCartData)
        # Tax should be calculated (since we have taxable items in sample data)
        assert result.grandTotal >= result.subTotal


class TestEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.fixture
    def manager(self):
        """Create a shopping cart manager instance."""
        return ShoppingCartManager()

    def test_calculate_totals_with_zero_price_items(self, manager):
        """Test calculation with zero-price items."""
        items = [
            ShoppingCart(
                itemName="Free Item",
                sku=123,
                isTaxable=False,
                ownBrand=True,
                price=0.0,
            ),
            ShoppingCart(
                itemName="Regular Item",
                sku=456,
                isTaxable=True,
                ownBrand=False,
                price=5.00,
            ),
        ]

        result = manager.calculate_totals(items)
        assert result.subTotal == 5.00
        assert result.taxTotal == round(5.00 * DEFAULT_TAX_RATE, 2)

    def test_rounding_precision(self, manager):
        """Test that calculations handle rounding correctly."""
        items = [
            ShoppingCart(
                itemName="Precision Test",
                sku=123,
                isTaxable=True,
                ownBrand=True,
                price=10.33333,  # Will test rounding
            )
        ]

        result = manager.calculate_totals(items)
        # All values should be rounded to 2 decimal places
        assert len(str(result.subTotal).split(".")[-1]) <= 2
        assert len(str(result.taxTotal).split(".")[-1]) <= 2
        assert len(str(result.grandTotal).split(".")[-1]) <= 2

    def test_large_numbers(self, manager):
        """Test calculations with large numbers."""
        items = [
            ShoppingCart(
                itemName="Expensive Item",
                sku=123,
                isTaxable=True,
                ownBrand=True,
                price=999999.99,
            )
        ]

        result = manager.calculate_totals(items)
        assert result.subTotal == 999999.99
        assert result.grandTotal > result.subTotal

    def test_many_items_performance(self, manager):
        """Test performance with many items."""
        # Create 1000 items (add 1 to avoid sku=0)
        items = [
            ShoppingCart(
                itemName=f"Item {i}",
                sku=i + 1,  # Add 1 to ensure sku > 0
                isTaxable=i % 2 == 0,  # Every other item is taxable
                ownBrand=True,
                price=1.99,
            )
            for i in range(1000)  # This creates SKUs 1-1000
        ]

        result = manager.calculate_totals(items)
        assert result.subTotal == 1000 * 1.99  # 1990.0
        # Should calculate without issues
        assert isinstance(result, ShoppingCartData)
