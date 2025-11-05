# Makefile for QA-Kit operations with environment variable support

# -----------------------------
# Directories
# -----------------------------
TEST_DIR := tests/generated
SPEC_DIR := tests/specs
ALLURE_RESULTS := allure-results
ALLURE_REPORT := allure-report

# -----------------------------
# Environment defaults
# -----------------------------
QA_KIT_SSL_VERIFY ?= false
USE_WILDCARD ?= false
IGNORE_ASSERT ?= false

# -----------------------------
# Default target
# -----------------------------
.PHONY: all
all: full

# -----------------------------
# QA-Kit commands
# -----------------------------

# Run all tests
.PHONY: run_tests
run_tests:
	@echo "🚀 Running all tests with SSL_VERIFY=$(QA_KIT_SSL_VERIFY)..."
	@QA_KIT_SSL_VERIFY=$(QA_KIT_SSL_VERIFY) USE_WILDCARD=$(USE_WILDCARD) IGNORE_ASSERT=$(IGNORE_ASSERT) \
	qa_kit run -t $(TEST_DIR) -o

# Run specific test file/folder
.PHONY: run
run:
	@echo "🚀 Running tests in $(TEST_DIR)..."
	@QA_KIT_SSL_VERIFY=$(QA_KIT_SSL_VERIFY) USE_WILDCARD=$(USE_WILDCARD) IGNORE_ASSERT=$(IGNORE_ASSERT) \
	qa_kit run -t $(TEST_DIR) -o

# Generate tests from JSON specs
.PHONY: generate
generate:
	@echo "🧾 Generating tests from JSON specs in $(SPEC_DIR)..."
	@if [ ! -d $(SPEC_DIR) ]; then \
		echo "⚠️ Specs directory $(SPEC_DIR) does not exist."; \
	else \
		for spec in $(SPEC_DIR)/*.json; do \
			if [ -f $$spec ]; then \
				echo "🔹 Generating tests from $$spec"; \
				QA_KIT_SSL_VERIFY=$(QA_KIT_SSL_VERIFY) USE_WILDCARD=$(USE_WILDCARD) IGNORE_ASSERT=$(IGNORE_ASSERT) \
				qa_kit generate $$spec -o $(TEST_DIR); \
			fi; \
		done \
	fi

# Lint generated tests
.PHONY: lint
lint:
	@echo "📝 Linting tests in $(TEST_DIR)..."
	@qa_kit lint -t $(TEST_DIR)

# -----------------------------
# Formatting and code checks
# -----------------------------
.PHONY: format
format:
	@echo "🎨 Formatting Python code with Black..."
	@black .

.PHONY: sort
sort:
	@echo "📦 Sorting imports with isort..."
	@isort .

.PHONY: check
check: lint
	@echo "✅ Lint check passed!"

# -----------------------------
# Allure reporting
# -----------------------------
.PHONY: report
report:
	@echo "📊 Generating Allure report..."
	@if ! command -v allure >/dev/null 2>&1; then \
		echo "⚠️ Allure CLI not found. Please install it (brew install allure / apt install allure / scoop install allure)"; \
	elif [ ! -d $(ALLURE_RESULTS) ] || [ "`ls -A $(ALLURE_RESULTS)`" = "" ]; then \
		echo "⚠️ No results found in $(ALLURE_RESULTS). Run 'make run_tests' first."; \
	else \
		allure generate $(ALLURE_RESULTS) -o $(ALLURE_REPORT) --clean; \
		echo "✅ Report generated in $(ALLURE_REPORT)"; \
	fi

.PHONY: open
open:
	@echo "🌐 Opening Allure report..."
	@if [ ! -d $(ALLURE_REPORT) ]; then \
		echo "⚠️ Report not found. Run 'make report' first."; \
	else \
		allure open $(ALLURE_REPORT); \
	fi

# Clean Allure results and reports
.PHONY: clean
clean:
	@echo "🧹 Cleaning allure results and report..."
	rm -rf $(ALLURE_RESULTS) $(ALLURE_REPORT)
	@echo "✅ Cleaned."

# -----------------------------
# PyPI publishing
# -----------------------------

# Build package
.PHONY: build
build:
	@echo "📦 Building qa-kit package..."
	@poetry build

.PHONY: publish
publish:
	@echo "🚀 Publishing qa-kit to PyPI..."
	@if ! command -v poetry >/dev/null 2>&1; then \
		echo "⚠️ Poetry not found. Please install Poetry first (https://python-poetry.org/docs/#installation)"; \
	else \
		poetry build; \
		poetry publish; \
	fi

# Full workflow: clean → generate → run → report → open
.PHONY: full
full: clean generate run_tests report open

# -----------------------------
# Help
# -----------------------------
.PHONY: help
help:
	@echo "Usage: make <target> [VARIABLE=value]"
	@echo ""
	@echo "Environment variables (optional):"
	@echo "  QA_KIT_SSL_VERIFY=true|false   # Enable/disable SSL verification (default: false)"
	@echo "  USE_WILDCARD=true|false        # Enable recursive wildcard for ignore_keys (default: false)"
	@echo "  IGNORE_ASSERT=true|false       # Skip all JSON assertions (default: false)"
	@echo ""
	@echo "Targets:"
	@echo "  run_tests    Run all tests"
	@echo "  run          Run tests in $(TEST_DIR)"
	@echo "  generate     Generate tests from JSON specs in $(SPEC_DIR)"
	@echo "  lint         Lint generated tests"
	@echo "  format       Format Python code with Black"
	@echo "  sort         Sort imports with isort"
	@echo "  check        Run lint check"
	@echo "  report       Generate Allure HTML report"
	@echo "  open         Open Allure HTML report"
	@echo "  clean        Remove Allure results and report"
	@echo "  full         Clean → generate → run → report → open"
	@echo "  publish      Build and publish package to PyPI"
	@echo "  help         Show this help message"
