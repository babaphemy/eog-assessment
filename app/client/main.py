from app.models.cart import ShoppingCart
from app.models.coupon import ShoppingCartCoupon
from app.services.cart_service import ShoppingCartManager

if __name__ == "__main__":
    manager = ShoppingCartManager()

    # Load data from JSON file
    try:
        cart_items = manager.load_cart("data/cart.json")
        coupons = manager.load_coupons("data/coupons.json")
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
        manager.calculate_totals_no_tax_from_file("data/cart.json"),
    )
    print(
        "Feature 2 (Tax all) from file:",
        manager.calculate_totals_tax_all_from_file("data/cart.json"),
    )
    print(
        "Feature 3 (Tax taxable only) from file:",
        manager.calculate_totals_tax_taxable_only_from_file("data/cart.json"),
    )
    print(
        "With coupons from file:",
        manager.calculate_totals_from_file("data/cart.json", "data/coupons.json"),
    )
