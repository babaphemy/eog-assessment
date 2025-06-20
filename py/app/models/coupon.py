"""Coupon related models."""

from pydantic import BaseModel, Field, field_validator


class ShoppingCartCoupon(BaseModel):
    """Represents available coupon for the shopping cart."""

    couponName: str = Field(..., min_length=1, description="Name of the coupon")
    appliedSku: int = Field(..., gt=0, description="SKU this coupon applies to")
    discountPrice: float = Field(..., ge=0, description="Discount amount")

    @field_validator("couponName")
    @classmethod
    def validate_coupon_name(cls, v: str) -> str:
        """Validate that coupon name is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Coupon name cannot be empty or just whitespace")
        return v.strip()

    def is_applicable_to(self, sku: int) -> bool:
        """Check if this coupon is applicable to the given SKU."""
        return self.appliedSku == sku

    def apply_discount(self, original_price: float) -> float:
        """Apply the coupon discount to the original price."""
        if original_price < 0:
            raise ValueError("Original price cannot be negative")

        discounted_price = max(0.0, original_price - self.discountPrice)
        return discounted_price
