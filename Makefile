
# Create a dev environment
install:
	python3 -m venv .venv
	source .venv/bin/activate && pip install -r requirements.txt

# Format the code. The code will be formatted in place.
format:
	source .venv/bin/activate && black .

# Help text
help:
	@echo "make {command}  # for commands see file"

PHONY: install format help
.DEFAULT_GOAL := help
