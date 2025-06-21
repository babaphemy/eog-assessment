test-cart:
	uv run pytest tests/unit/test_cart_service.py
test-price:
	uv run pytest tests/unit/test_price_compare.py
run:
	uv run python app/client/main.py
tests: test-cart test-price
