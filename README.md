# callum

autonomous multimodal research operating system.

not a chatbot — a research collaborator for literature review, gap detection, experiment planning, knowledge graphs, and citation-verified reasoning.

## stack

- **web** — Next.js, React, TypeScript, Tailwind, Framer Motion, React Flow, Zustand
- **api** — FastAPI, LangGraph-ready agents, async pipelines
- **infra** — Postgres, Redis, Qdrant, MinIO (Docker Compose)

## quick start

### 1. api

```bash
cd apps/api
python -m venv .venv
# windows
.venv\\Scripts\\activate
# mac/linux
source .venv/bin/activate

pip install -e ".[dev]"
copy .env.example .env   # or: cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

### 2. web

```bash
cd apps/web
cp .env.example .env.local
npm install
npm run dev
```

open [http://localhost:3000](http://localhost:3000)

### 3. infrastructure (optional)

```bash
cd docker
docker compose up -d postgres redis qdrant minio
```

## product surface (mvp)

| area | status |
| --- | --- |
| workspace shell (lowercase macOS ui) | ready |
| project + document library | ready |
| multimodal upload ingest stub | ready |
| streaming research agent + citations | ready (demo stream) |
| knowledge graph explorer | ready |
| hybrid search endpoint | ready (lexical mvp) |
| literature review / gaps / experiments | agent modes wired |
| full multimodal parse (nougat/docling/whisper) | next |
| qdrant hybrid + cross-encoder rerank | next |
| celery workers + gpu embedding farm | next |

## design

lowercase · dark-first · macOS-minimal · quiet motion · glass-light materials · no dashboard clutter.

## monorepo

```text
callum/
  apps/web          next.js frontend
  apps/api          fastapi backend
  docker            compose stack
```

## principles

- verifiable citations (page + paragraph + confidence)
- refuse weak evidence instead of fabricating sources
- async everywhere, stream by default
- modular services, production-shaped from day one
