.PHONY: help install install-dev test test-cov lint format clean run-server run-client build docker-build docker-run pre-commit docs docs-serve

help: ## Show this help message
	@echo "Usage: make [target]"
	@echo ""
	@echo "Available targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pip install -e .
	pre-commit install

test: ## Run tests
	pytest tests/ -v

test-cov: ## Run tests with coverage
	pytest tests/ --cov=src --cov-report=term-missing --cov-report=html:coverage/htmlcov --cov-report=xml:coverage/coverage.xml

test-watch: ## Run tests in watch mode
	pytest-watch tests/ -v

lint: ## Run linting checks
	@echo "Running flake8..."
	flake8 src/ tests/
	@echo "Running mypy..."
	mypy src/
	@echo "Running ruff..."
	ruff check src/ tests/

format: ## Format code with black and isort
	black src/ tests/
	isort src/ tests/
	ruff check --fix src/ tests/

clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	rm -rf coverage/
	rm -rf htmlcov/
	rm -f coverage.xml coverage.json .coverage
	rm -rf dist/ build/ *.egg-info src/*.egg-info

run-server: ## Run the WebSocket server
	python src/pubsub_ws.py

run-client: ## Run the client
	python src/client.py

build: ## Build the package
	python -m build

docker-build: ## Build Docker image
	docker build -t python.publisher.subscriber:latest .

docker-run: ## Run Docker container
	docker run -p 5000:5000 python.publisher.subscriber:latest

pre-commit: ## Run pre-commit hooks
	pre-commit run --all-files

docs: ## Generate documentation
	cd docs && make html

docs-serve: ## Serve documentation locally
	cd docs && python -m http.server --directory _build/html 8000