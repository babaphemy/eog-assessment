from pathlib import Path
import logging
import json
from pydantic import ValidationError
from app.utils.constants import DEFAULT_TAX_RATE
from app.models.cart import ShoppingCart, ShoppingCartData
from app.models.coupon import ShoppingCartCoupon


logger = logging.getLogger(__name__)


class ShoppingCartManager:
    """Manages shopping cart features."""

    def __init__(self, tax_rate: float = DEFAULT_TAX_RATE):
        self.tax_rate = tax_rate
        # Caching for file loading
        self._cart_cache: list[ShoppingCart] | None = None
        self._coupons_cache: list[ShoppingCartCoupon] | None = None
        self._last_cart_path: Path | None = None
        self._last_coupons_path: Path | None = None

    def calculate_subtotal(self, cart_items: list[ShoppingCart]) -> float:
        """Calculate the subtotal of the shopping cart.
        Args:
            cart_items: List of shopping cart items.
        Returns:
            The subtotal , rounded to 2 decimal places. 0 if the cart is empty.
        """
        if not cart_items:
            return 0.0
        return round(sum(item.price for item in cart_items), 2)

    def calculate_tax(self, cart_items: list[ShoppingCart]) -> float:
        """Calculate tax for taxable items only.
        Args:
            cart_items: List of shopping cart items.
        Returns:
            The total tax amount for taxable items, rounded to 2 decimal places.
        """
        taxable_items = [item for item in cart_items if item.isTaxable]
        return round(sum(item.price * self.tax_rate for item in taxable_items), 2)

    def apply_coupon_to_item(
        self, cart_item: ShoppingCart, coupons: list[ShoppingCartCoupon]
    ) -> float:
        """Apply the best applicable coupon to a cart item.
        Args:
            cart_item: The shopping cart item to apply coupon to.
            coupons: List of available coupons.
        Returns:
            The discounted price after coupon, rounded to decimal places.
            If no applicable coupon, return original price.
            If discount exceeds price, return 0.0.
        """
        applicable_coupons = [
            coupon for coupon in coupons if coupon.appliedSku == cart_item.sku
        ]

        if not applicable_coupons:
            return cart_item.price
        best_coupon = max(applicable_coupons, key=lambda x: x.discountPrice)
        discounted_price = max(0.0, cart_item.price - best_coupon.discountPrice)
        return round(discounted_price, 2)

    def apply_coupons_to_cart(
        self, cart_items: list[ShoppingCart], coupons: list[ShoppingCartCoupon]
    ) -> list[ShoppingCart]:
        """Apply coupons to all applicable items in the cart.
        Args:
            cart_items: List of given shopping cart items.
            coupons: List of available coupons.
        Returns:
            Discounted shopping cart items.
        """
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
        cart_items: list[ShoppingCart],
        coupons: list[ShoppingCartCoupon] | None = None,
    ) -> ShoppingCartData:
        """Calculate grand total with or without coupons.
        Args:
            cart_items: List of shopping cart items.
            coupons: Available coupons. Optional.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        if not cart_items:
            return ShoppingCartData(subTotal=0.0, taxTotal=0.0, grandTotal=0.0)

        if coupons:
            final_items = self.apply_coupons_to_cart(cart_items, coupons)
        else:
            final_items = cart_items

        # Calculate totals
        subtotal = self.calculate_subtotal(final_items)
        tax_total = self.calculate_tax(final_items)
        grand_total = self.round_to_two_decimals(subtotal + tax_total)

        return ShoppingCartData(
            subTotal=subtotal, taxTotal=tax_total, grandTotal=grand_total
        )

    # Feature-specific methods
    def calculate_totals_no_tax(
        self, cart_items: list[ShoppingCart]
    ) -> ShoppingCartData:
        """Feature 1: Calculate total without tax.
        Args:
            cart_items: List of shopping cart items.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        subtotal = self.calculate_subtotal(cart_items)
        return ShoppingCartData(subTotal=subtotal, taxTotal=0.0, grandTotal=subtotal)

    def calculate_totals_tax_all(
        self, cart_items: list[ShoppingCart]
    ) -> ShoppingCartData:
        """Feature 2: Calculate total with tax on all items.
        Args:
            cart_items: List of shopping cart items.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        subtotal = self.calculate_subtotal(cart_items)
        tax_total = round(subtotal * self.tax_rate, 2)
        grand_total = round(subtotal + tax_total, 2)

        return ShoppingCartData(
            subTotal=subtotal, taxTotal=tax_total, grandTotal=grand_total
        )

    def calculate_totals_tax_taxable_only(
        self, cart_items: list[ShoppingCart]
    ) -> ShoppingCartData:
        """Feature 3: Calculate total with tax only on taxable items.
        Args:
            cart_items: List of shopping cart items.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        subtotal = self.calculate_subtotal(cart_items)
        tax_total = self.calculate_tax(cart_items)
        grand_total = round(subtotal + tax_total, 2)

        return ShoppingCartData(
            subTotal=subtotal, taxTotal=tax_total, grandTotal=grand_total
        )

    # File loading
    def load_json_file(self, file_path: str, data_class) -> list:
        """Generic method to load JSON data and convert to Pydantic instances.
        Args:
            file_path: Path to the static JSON file.
            data_class: Pydantic model to validate and convert JSON.
        Returns:
            List of instances of the pydantic model.
            Empty list if file is not found, or invalid.
        Raises:
            JSONDecodeError: If the file is invalid.
            ValidationError: If there is data mismatch or validation error.

        """
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

    def load_cart(self, file_path: str) -> list[ShoppingCart]:
        """Load the shopping cart content from a JSON file with caching.
            Applies caching to avoid reloadng unchanged files.
        Args:
            file_path: Path to the JSON file.
        Returns:
            List of shopping cart items.
            Empty list if file is nt found, or invalid.
        """
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

    def load_coupons(self, file_path: str) -> list[ShoppingCartCoupon]:
        """Load the coupons from a JSON file with caching.
        Args:
            file_path: Path to the static JSON data.
        Returns:
            List of available coupons.
            Empty list if file is not found, or invalid.
        """
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

    # File-based
    def calculate_totals_from_file(
        self,
        cart_file_path: str,
        coupon_file_path: str | None = None,
    ) -> ShoppingCartData:
        """Calculate totals by loading data from files.
            This is a utility method.
        Args:
            cart_file_path: Path to the static JSON file.
            coupon_file_path: Path to the static coupons. Optional.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        cart_items = self.load_cart(cart_file_path)

        if coupon_file_path:
            coupons = self.load_coupons(coupon_file_path)
            return self.calculate_totals(cart_items, coupons)
        else:
            return self.calculate_totals(cart_items)

    def calculate_totals_tax_all_from_file(
        self, cart_file_path: str
    ) -> ShoppingCartData:
        """Feature 2: Calculate total with tax on all items from file.
            Utitlity method to load cart and calculate totals.
        Args:
            cart_file_path: Path to the static JSON file.
        Returns:
            Shopping cart result with sub total,tax total and grand total.

        """
        cart_items = self.load_cart(cart_file_path)
        return self.calculate_totals_tax_all(cart_items)

    def calculate_totals_tax_taxable_only_from_file(
        self, cart_file_path: str
    ) -> ShoppingCartData:
        """Feature 3: Calculate total with tax only on taxable items from file.
        Args:
            cart_file_path: Path to the static JSON file.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        cart_items = self.load_cart(cart_file_path)
        return self.calculate_totals_tax_taxable_only(cart_items)

    def calculate_totals_no_tax_from_file(
        self, cart_file_path: str
    ) -> ShoppingCartData:
        """Feature 1: Calculate total without tax from file.
        Args:
            cart_file_path: Path to the static JSOn file.
        Returns:
            Shopping cart result with sub total, tax total and grand total.
        """
        cart_items = self.load_cart(cart_file_path)
        return self.calculate_totals_no_tax(cart_items)
