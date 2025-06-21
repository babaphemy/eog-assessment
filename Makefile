test-cart:
	uv run pytest py/tests/unit/test_cart_service.py
test-price:
	uv run pytest py/tests/unit/test_price_c.py
tests: test-cart test-price
