"""Corrected version of ShoppingCartManager with fixed bugs and improved design."""

from typing import List, Optional, Union
from pathlib import Path
import json
import logging
from pydantic import ValidationError

from ..models.cart import ShoppingCart, ShoppingCartData
from ..models.coupon import ShoppingCartCoupon
from ..utils.constants import DEFAULT_TAX_RATE

logger = logging.getLogger(__name__)


class ShoppingCartManagerFixed:
    """Fixed version of ShoppingCartManager with proper error handling and logic."""

    def __init__(self, tax_rate: float = DEFAULT_TAX_RATE):
        self.tax_rate = tax_rate
        # Caching attributes for file loading
        self._cart_cache: Optional[List[ShoppingCart]] = None
        self._coupons_cache: Optional[List[ShoppingCartCoupon]] = None
        self._last_cart_path: Optional[Path] = None
        self._last_coupons_path: Optional[Path] = None

    def calculate_subtotal(self, cart_items: List[ShoppingCart]) -> float:
        """Calculate the subtotal of the shopping cart."""
        if not cart_items:
            return 0.0
        return round(sum(item.price for item in cart_items), 2)

    def calculate_tax(self, cart_items: List[ShoppingCart]) -> float:
        """Calculate the tax for taxable items only."""
        taxable_items = [item for item in cart_items if item.isTaxable]
        return round(sum(item.price * self.tax_rate for item in taxable_items), 2)

    def apply_coupon_to_item(
        self, cart_item: ShoppingCart, coupons: List[ShoppingCartCoupon]
    ) -> float:
        """Apply the best applicable coupon to a single cart item."""
        applicable_coupons = [
            coupon for coupon in coupons if coupon.appliedSku == cart_item.sku
        ]

        if not applicable_coupons:
            return cart_item.price
        best_coupon = max(applicable_coupons, key=lambda x: x.discountPrice)
        discounted_price = max(0.0, cart_item.price - best_coupon.discountPrice)
        return round(discounted_price, 2)

    def apply_coupons_to_cart(
        self, cart_items: List[ShoppingCart], coupons: List[ShoppingCartCoupon]
    ) -> List[ShoppingCart]:
        """Apply coupons to all applicable items in the cart."""
        return [
            ShoppingCart(
                itemName=item.itemName,
                sku=item.sku,
                isTaxable=item.isTaxable,
                ownBrand=item.ownBrand,
                price=self.apply_coupon_to_item(item, coupons),
            )
            for item in cart_items
        ]

    def calculate_totals(
        self,
        cart_items: List[ShoppingCart],
        coupons: Optional[List[ShoppingCartCoupon]] = None,
    ) -> ShoppingCartData:
        """Calculate grand total with or without coupons."""
        if not cart_items:
            return ShoppingCartData(subTotal=0.0, taxTotal=0.0, grandTotal=0.0)

        if coupons:
            final_items = self.apply_coupons_to_cart(cart_items, coupons)
        else:
            final_items = cart_items

        # Calculate totals
        subtotal = self.calculate_subtotal(final_items)
        tax_total = self.calculate_tax(final_items)
        grand_total = round(subtotal + tax_total, 2)

        return ShoppingCartData(
            subTotal=subtotal, taxTotal=tax_total, grandTotal=grand_total
        )

    # Feature-specific methods for clarity
    def calculate_totals_no_tax(
        self, cart_items: List[ShoppingCart]
    ) -> ShoppingCartData:
        """Feature 1: Calculate total without tax."""
        subtotal = self.calculate_subtotal(cart_items)
        return ShoppingCartData(subTotal=subtotal, taxTotal=0.0, grandTotal=subtotal)

    def calculate_totals_tax_all(
        self, cart_items: List[ShoppingCart]
    ) -> ShoppingCartData:
        """Feature 2: Calculate total with tax on all items."""
        subtotal = self.calculate_subtotal(cart_items)
        tax_total = round(subtotal * self.tax_rate, 2)  # Tax on ALL items
        grand_total = round(subtotal + tax_total, 2)

        return ShoppingCartData(
            subTotal=subtotal, taxTotal=tax_total, grandTotal=grand_total
        )

    def calculate_totals_tax_taxable_only(
        self, cart_items: List[ShoppingCart]
    ) -> ShoppingCartData:
        """Feature 3: Calculate total with tax only on taxable items."""
        subtotal = self.calculate_subtotal(cart_items)
        tax_total = self.calculate_tax(cart_items)  # Tax only on taxable items
        grand_total = round(subtotal + tax_total, 2)

        return ShoppingCartData(
            subTotal=subtotal, taxTotal=tax_total, grandTotal=grand_total
        )

    # File loading methods
    def load_json_file(self, file_path: Union[str, Path], data_class) -> List:
        """Generic method to load JSON data and convert to Pydantic model instances."""
        path = Path(file_path)

        try:
            if not path.exists():
                logger.warning(f"File not found: {path}")
                return []

            if path.stat().st_size == 0:
                logger.warning(f"File is empty: {path}")
                return []

            with path.open("r", encoding="utf-8") as file:
                data = json.load(file)

                if not isinstance(data, list):
                    logger.error(f"Expected list in JSON file, got {type(data)}")
                    return []

                return [data_class(**item) for item in data]

        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from {path}: {e}")
            return []
        except ValidationError as e:
            logger.error(
                f"Pydantic validation error for {data_class.__name__} from {path}: {e}"
            )
            return []
        except (KeyError, TypeError) as e:
            logger.error(
                f"Error creating {data_class.__name__} objects from {path}: {e}"
            )
            return []
        except Exception as e:
            logger.error(f"Unexpected error loading {path}: {e}")
            return []

    def load_cart(self, file_path: Union[str, Path]) -> List[ShoppingCart]:
        """Load the shopping cart content from a JSON file with caching."""
        path = Path(file_path)

        # Use cache if available and file hasn't changed
        if (
            self._cart_cache is not None
            and self._last_cart_path == path
            and path.exists()
        ):
            return self._cart_cache

        self._cart_cache = self.load_json_file(path, ShoppingCart)
        self._last_cart_path = path
        return self._cart_cache

    def load_coupons(self, file_path: Union[str, Path]) -> List[ShoppingCartCoupon]:
        """Load the coupons from a JSON file with caching."""
        path = Path(file_path)

        # Use cache if available and file hasn't changed
        if (
            self._coupons_cache is not None
            and self._last_coupons_path == path
            and path.exists()
        ):
            return self._coupons_cache

        self._coupons_cache = self.load_json_file(path, ShoppingCartCoupon)
        self._last_coupons_path = path
        return self._coupons_cache

    def clear_cache(self):
        """Clear the internal cache."""
        self._cart_cache = None
        self._coupons_cache = None
        self._last_cart_path = None
        self._last_coupons_path = None

    # File-based convenience methods
    def calculate_totals_from_file(
        self,
        cart_file_path: Union[str, Path],
        coupon_file_path: Optional[Union[str, Path]] = None,
    ) -> ShoppingCartData:
        """Calculate totals by loading data from files."""
        cart_items = self.load_cart(cart_file_path)

        if coupon_file_path:
            coupons = self.load_coupons(coupon_file_path)
            return self.calculate_totals(cart_items, coupons)
        else:
            return self.calculate_totals(cart_items)

    def calculate_totals_tax_all_from_file(
        self, cart_file_path: Union[str, Path]
    ) -> ShoppingCartData:
        """Feature 2: Calculate total with tax on all items from file."""
        cart_items = self.load_cart(cart_file_path)
        return self.calculate_totals_tax_all(cart_items)

    def calculate_totals_tax_taxable_only_from_file(
        self, cart_file_path: Union[str, Path]
    ) -> ShoppingCartData:
        """Feature 3: Calculate total with tax only on taxable items from file."""
        cart_items = self.load_cart(cart_file_path)
        return self.calculate_totals_tax_taxable_only(cart_items)

    def calculate_totals_no_tax_from_file(
        self, cart_file_path: Union[str, Path]
    ) -> ShoppingCartData:
        """Feature 1: Calculate total without tax from file."""
        cart_items = self.load_cart(cart_file_path)
        return self.calculate_totals_no_tax(cart_items)


# Example usage and comparison
if __name__ == "__main__":
    manager = ShoppingCartManagerFixed()

    # Load data from JSON files
    try:
        cart_items = manager.load_cart("cart.json")
        coupons = manager.load_coupons("coupons.json")
        print(
            f"✅ Loaded {len(cart_items)} cart items and {len(coupons)} coupons from files"
        )
    except Exception as e:
        print(f"❌ Failed to load from files: {e}")
        # Fallback to sample data
        cart_items = [
            ShoppingCart(
                itemName="Brownies",
                sku=85294241,
                isTaxable=False,
                ownBrand=True,
                price=3.61,
            ),
            ShoppingCart(
                itemName="Shampoo",
                sku=12345678,
                isTaxable=True,
                ownBrand=False,
                price=8.99,
            ),
        ]

        coupons = [
            ShoppingCartCoupon(
                couponName="Brownie Discount", appliedSku=85294241, discountPrice=0.79
            )
        ]
        print("📝 Using fallback sample data")

    # Test different features
    print("Feature 1 (No tax):", manager.calculate_totals_no_tax(cart_items))
    print("Feature 2 (Tax all):", manager.calculate_totals_tax_all(cart_items))
    print(
        "Feature 3 (Tax taxable only):",
        manager.calculate_totals_tax_taxable_only(cart_items),
    )
    print("With coupons:", manager.calculate_totals(cart_items, coupons))

    # Test file-based calculations (assuming JSON files are correctly formatted)
    print("File-based calculations:")
    print(
        "Feature 1 (No tax) from file:",
        manager.calculate_totals_no_tax_from_file("path/to/cart.json"),
    )
    print(
        "Feature 2 (Tax all) from file:",
        manager.calculate_totals_tax_all_from_file("path/to/cart.json"),
    )
    print(
        "Feature 3 (Tax taxable only) from file:",
        manager.calculate_totals_tax_taxable_only_from_file("path/to/cart.json"),
    )
    print(
        "With coupons from file:",
        manager.calculate_totals_from_file("path/to/cart.json", "path/to/coupons.json"),
    )
