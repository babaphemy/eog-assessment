"""Pytest configuration and shared fixtures."""

import pytest
import json
import tempfile
from pathlib import Path
from typing import List

from app.models.cart import ShoppingCart
from app.models.coupon import ShoppingCartCoupon


@pytest.fixture
def sample_cart_items() -> List[ShoppingCart]:
    """Fixture providing sample shopping cart items."""
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
            itemName="Test Item",
            sku=12345678,
            isTaxable=True,
            ownBrand=True,
            price=10.00,
        ),
    ]


@pytest.fixture
def sample_coupons() -> List[ShoppingCartCoupon]:
    """Fixture providing sample coupons."""
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
            couponName="Better Ice Cream Discount",  # Better discount for same item. Assumption: many coupons can apply to the same item.
            appliedSku=95422042,
            discountPrice=1.50,
        ),
    ]


@pytest.fixture
def temp_cart_file(sample_cart_items: List[ShoppingCart]) -> Path:
    """Fixture providing a temporary cart JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
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
        json.dump(cart_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def temp_coupons_file(sample_coupons: List[ShoppingCartCoupon]) -> Path:
    """Fixture providing a temporary coupons JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        coupon_data = [
            {
                "couponName": coupon.couponName,
                "appliedSku": coupon.appliedSku,
                "discountPrice": coupon.discountPrice,
            }
            for coupon in sample_coupons
        ]
        json.dump(coupon_data, f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def empty_json_file() -> Path:
    """Fixture providing an empty JSON file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        json.dump([], f)
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    if temp_path.exists():
        temp_path.unlink()
