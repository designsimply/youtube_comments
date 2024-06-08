
# Create a dev environment
install:
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r requirements.txt

# Run the tests
format:
	source .venv/bin/activate && black .

# Help text
help:
	@echo "install: Create a dev environment"
	@echo "format: Run the tests"


PHONY: install format help
.DEFAULT_GOAL := help
