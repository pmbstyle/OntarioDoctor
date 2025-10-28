.PHONY: help up down logs restart clean ingest-sample smoke-test venv

help: ## Show this help message
	@echo "OntarioDoctor - Makefile Commands"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Docker Compose Commands
up: ## Start all services
	@echo "🚀 Starting OntarioDoctor services..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo ""
	@echo "📍 Service URLs:"
	@echo "   Frontend:     http://localhost:5173"
	@echo "   API Gateway:  http://localhost:8080"
	@echo "   RAG Service:  http://localhost:8001"
	@echo "   Orchestrator: http://localhost:8002"
	@echo "   vLLM:         http://localhost:8000"
	@echo "   Qdrant:       http://localhost:6333"

down: ## Stop all services
	@echo "🛑 Stopping OntarioDoctor services..."
	docker-compose down
	@echo "✅ Services stopped!"

logs: ## Show logs from all services
	docker-compose logs -f

restart: ## Restart all services
	@make down
	@make up

clean: ## Stop services and remove volumes
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	rm -rf qdrant_data
	@echo "✅ Cleanup complete!"

# Backend Setup
venv: ## Set up Python virtual environment
	@echo "🐍 Setting up Python virtual environment..."
	cd backend && chmod +x setup_venv.sh && ./setup_venv.sh
	@echo "✅ Virtual environment ready!"
	@echo ""
	@echo "To activate:"
	@echo "   cd backend && source venv/bin/activate"

# Data Ingestion
generate-sample-json: ## Generate sample_data.json from rag-data-sources
	@echo "📄 Generating sample_data.json from rag-data-sources..."
	python3 scripts/ingest_rag_data.py --generate-json --output scripts/sample_data.json
	@echo "✅ JSON file generated!"

ingest-sample: ## Ingest sample medical data from rag-data-sources
	@echo "📚 Generating and ingesting sample data..."
	@echo "🔄 Generating JSON from rag-data-sources..."
	python3 scripts/ingest_rag_data.py --generate-json --output scripts/sample_data.json
	@echo ""
	@echo "📤 Ingesting data into RAG system..."
	curl -X POST http://localhost:8080/ingest \
		-H "Content-Type: application/json" \
		-d @scripts/sample_data.json
	@echo ""
	@echo "✅ Sample data ingested!"

# Testing
smoke-test: ## Run smoke tests
	@echo "🧪 Running smoke tests..."
	@bash scripts/smoke_test.sh

# Health Checks
health: ## Check health of all services
	@echo "🏥 Checking service health..."
	@echo ""
	@echo "Gateway:"
	@curl -s http://localhost:8080/health | python3 -m json.tool || echo "❌ Gateway unhealthy"
	@echo ""
	@echo "RAG:"
	@curl -s http://localhost:8001/health | python3 -m json.tool || echo "❌ RAG unhealthy"
	@echo ""
	@echo "Orchestrator:"
	@curl -s http://localhost:8002/health | python3 -m json.tool || echo "❌ Orchestrator unhealthy"
	@echo ""
	@echo "vLLM:"
	@curl -s http://localhost:8000/health | python3 -m json.tool || echo "❌ vLLM unhealthy"
	@echo ""
	@echo "Qdrant:"
	@curl -s http://localhost:6333/health | python3 -m json.tool || echo "❌ Qdrant unhealthy"

# Frontend
frontend-dev: ## Run frontend dev server (without Docker)
	cd frontend && pnpm dev

frontend-build: ## Build frontend for production
	cd frontend && pnpm build

# Development
dev-backend: ## Run backend services locally (requires venv)
	@echo "Starting backend services..."
	@echo "Make sure you have activated the venv: cd backend && source venv/bin/activate"
	@echo ""
	@echo "Terminal 1: cd backend && python -m uvicorn rag.main:app --reload --port 8001"
	@echo "Terminal 2: cd backend && python -m uvicorn orchestrator.main:app --reload --port 8002"
	@echo "Terminal 3: cd backend && python -m uvicorn gateway.main:app --reload --port 8000"

# Quick Start
quickstart: venv up ## Quick start: setup venv and start all services
	@echo ""
	@echo "🎉 OntarioDoctor is ready!"
	@echo ""
	@echo "📍 Access the app at: http://localhost:5173"
	@echo ""
	@echo "📚 Next steps:"
	@echo "   1. Ingest sample data: make ingest-sample"
	@echo "   2. Run smoke tests: make smoke-test"
