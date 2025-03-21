.PHONY: setup run test clean format lint help

# Variables
PYTHON = python
ENV_NAME = har-api-env
ENV_FILE = .env
PIP = pip

# Default target
.DEFAULT_GOAL := help

# Help target
help:
	@echo "HAR API Reverse Engineer - Backend Makefile"
	@echo "----------------------------------------"
	@echo "setup       - Create conda environment and install dependencies"
	@echo "run         - Run the FastAPI server"
	@echo "test        - Run tests"
	@echo "clean       - Remove __pycache__ directories"
	@echo "format      - Format code with black"
	@echo "lint        - Run linter checks"
	@echo "help        - Show this help message"

# Setup environment
setup:
	@echo "Creating conda environment..."
	conda env create -f environment.yml
	@echo "Creating .env file if it doesn't exist..."
	@test -f $(ENV_FILE) || cp .env.template $(ENV_FILE)
	@echo "Setup complete. Remember to add your OpenAI API key to .env"

# Run the server
run:
	@echo "Starting FastAPI server..."
	$(PYTHON) main.py

# Run tests
test:
	@echo "Running tests..."
	pytest

# Clean up generated files
clean:
	@echo "Cleaning up generated files..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Format code
format:
	@echo "Formatting code with black..."
	black .

# Lint code
lint:
	@echo "Linting code..."
	flake8 .

# Activate environment - helper message
activate:
	@echo "To activate the environment, run: conda activate $(ENV_NAME)"