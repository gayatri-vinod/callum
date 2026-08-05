.PHONY: api web infra

api:
	cd apps/api && .venv/Scripts/uvicorn app.main:app --reload --port 8000

web:
	cd apps/web && npm run dev -- --port 3000

infra:
	cd docker && docker compose up -d postgres redis qdrant minio
