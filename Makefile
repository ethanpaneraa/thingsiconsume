.PHONY: help build up down logs restart clean build-site deploy-site test

help:
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build:
	docker-compose build

up:
	docker-compose up -d ingest
	@echo "Ingest API started at http://localhost:8000"
	@echo "Health check: curl http://localhost:8000/health"

down:
	docker-compose down

logs:
	docker-compose logs -f ingest

restart:
	docker-compose restart ingest

clean:
	docker-compose down -v --rmi all

build-site:
	docker-compose --profile build run --rm site-builder
	@echo "Static site generated in site/docs/"

test:
	@curl -f http://localhost:8000/health && echo "\n✓ API is healthy" || echo "\n✗ API is not responding"

dev-up:
	docker-compose up -d ingest
	docker-compose logs -f ingest

rebuild:
	docker-compose up -d --build ingest

migrate:
	python scripts/run_migration.py

deploy-railway:
	cd ingest && railway up

deploy-fly:
	cd ingest && fly deploy

