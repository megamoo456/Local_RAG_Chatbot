# Local RAG Chatbot

A production-grade, fully local Retrieval-Augmented Generation chatbot built with modern open-source technologies.

## Architecture

- **Backend**: FastAPI + SQLAlchemy (async) + Alembic
- **Frontend**: Next.js 15 (App Router) + shadcn/ui + TailwindCSS
- **LLM**: Ollama (qwen3.5:9b)
- **Vector DB**: Qdrant (hybrid search with dense + sparse vectors)
- **Embeddings**: BAAI/bge-m3 (via FlagEmbedding)
- **Reranker**: BAAI/bge-reranker-v2-m3
- **Document Parsing**: Docling
- **Database**: PostgreSQL 16

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Git

### Setup

```bash
# Clone and configure
cp .env.example .env

# Start all services
docker compose up --build

# Run database migrations
make migrate
```

### Access

| Service   | URL                          |
|-----------|------------------------------|
| Frontend  | http://localhost:3000         |
| Backend   | http://localhost:8000         |
| API Docs  | http://localhost:8000/docs    |
| Qdrant UI | http://localhost:6333/dashboard |

## Development

```bash
make up          # Start all services
make down        # Stop all services
make logs        # Tail all logs
make migrate     # Run database migrations
make test        # Run backend tests
make shell       # Shell into backend container
```

## Project Structure

```
├── backend/          # FastAPI application
│   ├── app/          # Application code
│   │   ├── api/      # REST endpoints
│   │   ├── core/     # Config, DB, security
│   │   ├── models/   # SQLAlchemy ORM models
│   │   ├── schemas/  # Pydantic DTOs
│   │   ├── services/ # Business logic
│   │   ├── repositories/ # Data access
│   │   ├── rag/      # RAG pipeline components
│   │   └── utils/    # Logging, timing, helpers
│   ├── alembic/      # Database migrations
│   └── tests/        # Test suite
├── frontend/         # Next.js application
└── docker-compose.yml
```

## License

Private — All rights reserved.
