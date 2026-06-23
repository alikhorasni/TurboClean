.PHONY: install lint format typecheck test bench docs

install:
	pip install -e ".[all,dev]"

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src

test:
	pytest tests --cov=turboclean

bench:
	python benchmarks/vs_pandas.py

docs:
	@echo "Open docs/index.md or serve with MkDocs"
