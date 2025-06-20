"""Shopping cart related models."""

from typing import Self
from pydantic import BaseModel, Field, field_validator, model_validator


class ShoppingCart(BaseModel):
    """Represents items in a shopping cart."""

    itemName: str = Field(..., min_length=1, description="Name of the item")
    sku: int = Field(..., gt=0, description="Stock Keeping Unit (must be positive)")
    isTaxable: bool = Field(..., description="Whether the item is subject to tax")
    ownBrand: bool = Field(..., description="Whether this is an own-brand item")
    price: float = Field(
        ..., ge=0, description="Price of the item (cannot be negative)"
    )

    @field_validator("itemName")
    @classmethod
    def validate_item_name(cls, v: str) -> str:
        """Validate that item name is not empty after stripping whitespace."""
        if not v.strip():
            raise ValueError("Item name cannot be empty or just whitespace")
        return v.strip()


class ShoppingCartData(BaseModel):
    """Represents the shopping cart data with calculated totals."""

    subTotal: float = Field(..., ge=0, description="Subtotal before tax")
    taxTotal: float = Field(..., ge=0, description="Total tax amount")
    grandTotal: float = Field(..., ge=0, description="Final total including tax")

    @model_validator(mode="after")
    def validate_totals_consistency(self) -> Self:
        """Validate that grand total matches subTotal + taxTotal."""
        expected_grand_total = self.subTotal + self.taxTotal
        if (
            abs(self.grandTotal - expected_grand_total) > 0.01
        ):  # Allow small rounding differences
            raise ValueError(
                f"Grand total {self.grandTotal} doesn't match subTotal + taxTotal "
                f"({self.subTotal} + {self.taxTotal} = {expected_grand_total})"
            )
        return self
