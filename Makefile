.PHONY: venv install install-all test tree clean

venv:
	python3 -m venv .venv

install:
	.venv/bin/python -m pip install -U pip
	.venv/bin/python -m pip install -e .

install-all:
	.venv/bin/python -m pip install -U pip
	.venv/bin/python -m pip install -e ".[mesh,build123d,cadquery,dev]"

test:
	.venv/bin/python -m pytest -q

tree:
	find . -maxdepth 4 -not -path "./.git/*" -not -path "./.venv/*" | sort

clean:
	rm -rf .pytest_cache build dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
