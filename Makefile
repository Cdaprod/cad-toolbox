.PHONY: venv install install-all test lint tree clean smoke

venv:
	python3 -m venv .venv

install:
	.venv/bin/python -m pip install -U pip
	.venv/bin/python -m pip install -e .

install-all:
	.venv/bin/python -m pip install -U pip
	.venv/bin/python -m pip install -e ".[all]"

test:
	.venv/bin/python -m pytest -q

lint:
	.venv/bin/python -m ruff check src tests scripts recipes

smoke:
	.venv/bin/cad --help
	.venv/bin/cad backend

tree:
	find . -maxdepth 4 -not -path "./.git/*" -not -path "./.venv/*" | sort

clean:
	rm -rf .pytest_cache .ruff_cache build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
