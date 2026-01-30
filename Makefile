.PHONY: install lint format typecheck test cov

install:
	python -m pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff format .

typecheck:
	mypy src

test:
	pytest -q

cov:
	pytest -q --cov=src --cov-report=term-missing
