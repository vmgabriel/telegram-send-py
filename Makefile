.PHONY: help install install-dev test test-cov test-filter lint format build \
        completion run-send run-listen docs-build docs-serve clean

# Every tool is invoked through Hatch so the commands always run against the
# environment declared in pyproject.toml, never against a stray virtualenv.
HATCH ?= hatch
COMPLETIONS_DIR ?= completions

help: ## Show available targets
	@echo "Usage: make <target>"
	@echo
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Create the runtime Hatch environment
	$(HATCH) env create

install-dev: ## Install editable with the dev and docs extras
	$(HATCH) run python -m pip install -e ".[dev,docs]"

test: ## Run the test suite
	$(HATCH) run test

test-cov: ## Run the test suite with a coverage report
	$(HATCH) run test:test

test-filter: ## Run a subset of tests, e.g. make test-filter K="-k send"
	$(HATCH) run test $(K)

lint: ## Check code style with Ruff and types with mypy
	$(HATCH) run ruff check src tests
	$(HATCH) run mypy src/telegram_integration

format: ## Auto-format the code with Ruff
	$(HATCH) run ruff format src tests
	$(HATCH) run ruff check --fix src tests

build: ## Build the sdist and wheel into dist/
	$(HATCH) build

completion: ## Generate Bash, Zsh and Fish completion scripts into completions/
	@mkdir -p $(COMPLETIONS_DIR)
	$(HATCH) run telegram-integration completion bash > $(COMPLETIONS_DIR)/telegram-integration.bash
	$(HATCH) run telegram-integration completion zsh  > $(COMPLETIONS_DIR)/_telegram-integration
	$(HATCH) run telegram-integration completion fish > $(COMPLETIONS_DIR)/telegram-integration.fish
	@echo "Completion scripts written to $(COMPLETIONS_DIR)/"

run-send: ## Send a message, e.g. make run-send MSG="**Hello**" MODE=plain
	$(HATCH) run send $(MSG) --mode $(or $(MODE),markdown)

run-listen: ## Listen for messages, e.g. make run-listen SCRIPTS="a.py b.py"
	$(HATCH) run listen $(if $(SCRIPTS),--scripts $(SCRIPTS))

docs-build: ## Build the documentation site
	$(HATCH) run docs:build

docs-serve: ## Serve the documentation locally at http://localhost:8000
	$(HATCH) run docs:serve

clean: ## Remove build artifacts, caches and generated files
	$(HATCH) env prune
	rm -rf dist/ build/ site/ $(COMPLETIONS_DIR)/ htmlcov/ .coverage \
	       .pytest_cache/ .mypy_cache/ .ruff_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
