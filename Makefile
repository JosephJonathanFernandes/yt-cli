.PHONY: install dev test lint run clean

install:
	pip install -e .

dev:
	pip install -e ".[extra,dev]"

test:
	pytest -q

run:
	ytdownloader

clean:
	rm -rf build dist *.egg-info .pytest_cache
	find . -type d -name __pycache__ -exec rm -rf {} +
