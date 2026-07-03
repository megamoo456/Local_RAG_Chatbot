# ==============================================================================
# Local RAG Chatbot — Makefile
# ==============================================================================
# Common development commands. Run `make help` to see all available targets.
# ==============================================================================

.PHONY: help up down build rebuild logs test migrate shell lint format clean pull-model

# Default target
help: ## Show this help message
	@echo "Local RAG Chatbot — Development Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ------------------------------------------------------------------------------
# Docker Compose
# ------------------------------------------------------------------------------

up: ## Start all services
	docker compose up -d

up-build: ## Start all services (rebuild images)
	docker compose up -d --build

down: ## Stop all services
	docker compose down

rebuild: ## Rebuild and restart all services
	docker compose down
	docker compose up -d --build

logs: ## Tail logs from all services
	docker compose logs -f

logs-backend: ## Tail backend logs
	docker compose logs -f backend

logs-frontend: ## Tail frontend logs
	docker compose logs -f frontend

ps: ## Show running services
	docker compose ps

# ------------------------------------------------------------------------------
# Database
# ------------------------------------------------------------------------------

migrate: ## Run database migrations
	docker compose exec backend alembic upgrade head

migrate-create: ## Create a new migration (usage: make migrate-create MSG="add users table")
	docker compose exec backend alembic revision --autogenerate -m "$(MSG)"

migrate-down: ## Rollback last migration
	docker compose exec backend alembic downgrade -1

migrate-history: ## Show migration history
	docker compose exec backend alembic history

# ------------------------------------------------------------------------------
# Backend
# ------------------------------------------------------------------------------

shell: ## Shell into backend container
	docker compose exec backend bash

test: ## Run backend tests
	docker compose exec backend pytest -v

test-cov: ## Run backend tests with coverage
	docker compose exec backend pytest --cov=app --cov-report=term-missing -v

lint: ## Lint backend code
	docker compose exec backend ruff check app/ tests/

format: ## Format backend code
	docker compose exec backend ruff format app/ tests/

# ------------------------------------------------------------------------------
# Ollama
# ------------------------------------------------------------------------------

pull-model: ## Pull the default LLM model
	docker compose exec ollama ollama pull qwen3.5:9b-q4_K_M

list-models: ## List available Ollama models
	docker compose exec ollama ollama list

# ------------------------------------------------------------------------------
# Maintenance
# ------------------------------------------------------------------------------

clean: ## Remove all containers, volumes, and cached data
	docker compose down -v --remove-orphans
	docker system prune -f

health: ## Check health of all services
	@echo "Backend:  $$(curl -s http://localhost:8000/api/v1/health | python -m json.tool 2>/dev/null || echo 'UNREACHABLE')"
	@echo "Frontend: $$(curl -s -o /dev/null -w '%{http_code}' http://localhost:3000 || echo 'UNREACHABLE')"
	@echo "Qdrant:   $$(curl -s http://localhost:6333/healthz || echo 'UNREACHABLE')"
	@echo "Ollama:   $$(curl -s http://localhost:11434/api/tags | python -m json.tool 2>/dev/null || echo 'UNREACHABLE')"
