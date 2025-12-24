.PHONY: help build up down logs restart clean build-site deploy-site test

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Build all Docker images
	docker-compose build

up: ## Start the ingest API service
	docker-compose up -d ingest
	@echo "Ingest API started at http://localhost:8000"
	@echo "Health check: curl http://localhost:8000/health"

down: ## Stop all services
	docker-compose down

logs: ## View logs from the ingest service
	docker-compose logs -f ingest

restart: ## Restart the ingest service
	docker-compose restart ingest

clean: ## Remove all containers and images
	docker-compose down -v --rmi all

build-site: ## Generate the static site
	docker-compose --profile build run --rm site-builder
	@echo "Static site generated in site/docs/"

test: ## Test the ingest API health endpoint
	@curl -f http://localhost:8000/health && echo "\n✓ API is healthy" || echo "\n✗ API is not responding"

# Development helpers
dev-up: ## Start services and tail logs
	docker-compose up -d ingest
	docker-compose logs -f ingest

rebuild: ## Rebuild and restart the ingest service
	docker-compose up -d --build ingest

# Database
migrate: ## Run database migrations (requires local Python env)
	python run_migration.py

# Deployment
deploy-railway: ## Deploy ingest service to Railway (requires Railway CLI)
	cd ingest && railway up

deploy-fly: ## Deploy ingest service to Fly.io (requires Fly CLI)
	cd ingest && fly deploy

