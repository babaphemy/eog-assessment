"""Shopping Cart Models."""

from pydantic import BaseModel, Field, model_validator


class ShoppingCart(BaseModel):
    """Items in a shopping cart."""

    itemName: str = Field(..., min_length=1, description="Name of the cart item.")
    sku: int = Field(..., gt=0, description="SKU of the cart item.")
    isTaxable: bool = Field(
        ..., description="Tax determinant. True if item is taxable."
    )
    ownBrand: bool = Field(
        ..., description="Determinant for own brand items. True if item is own brand."
    )
    price: float = Field(..., ge=0, description="Price of the cart item.")


class ShoppingCartData(BaseModel):
    """Shopping Cart Response Data."""

    subTotal: float = Field(
        ..., ge=0, description="Subtotal of cart items. Before tax."
    )
    taxTotal: float = Field(..., ge=0, description="Total tax amount.")
    grandTotal: float = Field(
        ..., ge=0, description="Total amount after tax and discounts."
    )

    @model_validator(mode="after")
    def validate_total(self):
        """Validates grand total matches subtotal + tax total.
        Raises:
            ValueError: if grand total does not match total after tax.
        Returns:
            Validated instance.
        """
        expected_total = self.subTotal + self.taxTotal
        if abs(self.grandTotal - expected_total) > 0.01:
            raise ValueError(
                f"Grand total {self.grandTotal} does not match expected total {expected_total}"
            )

        return self
