.PHONY: help install test test-cov run-send run-listen docs-build docs-serve build clean

VENV ?= venv
PYTHON ?= $(VENV)/bin/python
HATCH ?= hatch

## Show available commands
help:
	@echo "Available targets:"
	@grep -E '^## ' $(MAKEFILE_LIST) | sed 's/## //' 

## Setup: create venv and install dependencies
install:
	python -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

## Install the package in editable mode (also installs console scripts)
install-dev:
	$(PYTHON) -m pip install -e .

## Run unit tests via Hatch
test:
	$(HATCH) run test

## Run unit tests with coverage report via Hatch
test-cov:
	$(HATCH) run test:test

## Test a single test or keyword filter, e.g. make test-filter K=-k send
test-filter:
	$(HATCH) run test $(K)

## Send a message, e.g. make run-send MSG="**Hello**" or make run-send MSG="hi" MODE=plain
run-send:
	$(HATCH) run send $(MSG) --mode $(or $(MODE),markdown)

## Listen for messages (optionally trigger scripts, e.g. SCRIPTS="a.py b.py")
run-listen:
	$(HATCH) run listen $(if $(SCRIPTS),--scripts $(SCRIPTS))

## Build documentation site
docs-build:
	$(HATCH) run docs:build

## Serve documentation locally at http://localhost:8000
docs-serve:
	$(HATCH) run docs:serve

## Build a distributable package
build:
	$(HATCH) build

## Remove build artifacts and caches
clean:
	$(HATCH) env prune
	rm -rf site/ .pytest_cache/ build/ dist/ *.egg-info/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +