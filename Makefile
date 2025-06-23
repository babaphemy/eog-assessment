test-cart:
	uv run pytest tests/unit/test_cart_service.py
test-price:
	uv run pytest tests/unit/test_price_compare.py
run:
	PYTHONPATH=. uv run python app/client/main.py
tests: test-cart test-price
