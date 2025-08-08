### ChatMind – AI Entry Point

This document is a fast lane for an AI assistant/agent to understand, navigate, and operate this repository safely and effectively.

---

### TL;DR (What this project is)
- Hybrid knowledge system for personal/work chat data
- Pipeline (Python) → processes data into structured artifacts
- Databases → Neo4j (graph) + Qdrant (vectors)
- API (FastAPI) → queries hybrid data
- Frontend (Vite React) → visualizes and searches

---

### Core Services and Ports
- Neo4j: HTTP `7474`, Bolt `7687`
- Qdrant: HTTP `6335` (host), gRPC `6336` (host)
- API (FastAPI): `8000`
- Frontend (Vite dev): `5173`

All are started together with the top-level `docker-compose.yml`.

---

### Quick Commands (Use these first)
- Start stack: `docker compose up -d` (or `make up`)
- Run pipeline (local models): `chatmind --local` (or `make pipeline`)
- Run API: `make api`
- Run Frontend: `make frontend`
- Stop stack: `docker compose down` (or `make down`)
- Preview docs site: `make docs`

Prereqs: Python 3.10+, Node 20+, Docker.

---

### Directory Map (What lives where)
- `chatmind/pipeline/` – modular data pipeline
  - Orchestrator: `run_pipeline.py` (exposed as CLI `chatmind`)
  - Steps: `ingestion`, `chunking`, `embedding`, `clustering`, `tagging`, `chat_summarization`, `cluster_summarization`, `positioning`, `similarity`, `loading`
  - Databases compose: `chatmind/pipeline/docker-compose.yml` (dev convenience); prefer root compose for OSS
- `chatmind/api/` – FastAPI service (Dockerfile included)
- `chatmind/frontend/` – Vite React frontend (Dockerfile included)
- `docs/` – project docs (this file, overviews, plans)
- `data/` – sample/raw/processed data (avoid committing real data)
- Root utilities: `Makefile`, `docker-compose.yml`, `pyproject.toml`, GitHub Actions under `.github/`

---

### Environment and Config
- Pipeline env: root `.env` + `chatmind/pipeline/.env` (pipeline overrides root)
- API env: environment variables (`NEO4J_*`, `QDRANT_*`, `API_*`)
- Frontend env: `VITE_API_URL`

Key defaults
- `NEO4J_URI=bolt://localhost:7687`
- `QDRANT_URL=http://localhost:6335` (pipeline loaders)
- API expects: `QDRANT_HOST`, `QDRANT_PORT=6335` when connecting from host
- Frontend expects: `VITE_API_URL=http://localhost:8000`

---

### Pipeline Data Contracts (What files to expect)
`data/processed/` (rooted relative to project)
- `ingestion/chats.jsonl` – flattened chats
- `chunking/chunks.jsonl` – chunked text with IDs
- `embedding/embeddings.jsonl` – chunk vectors (local or cloud)
- `clustering/clustered_embeddings.jsonl` – HDBSCAN labels + UMAP 2D per chunk
- `tagging/tags.jsonl` and `tagging/processed_tags.jsonl` – raw + normalized tags
- `cluster_summarization/cluster_summaries.json` – cluster summaries
- `chat_summarization/chat_summaries.json` – chat summaries
- `positioning/cluster_summary_embeddings.jsonl` – vectors for clusters
- `positioning/chat_summary_embeddings.jsonl` – vectors for chats
- `positioning/cluster_positions.jsonl` – includes `umap_x`, `umap_y`
- `positioning/chat_positions.jsonl` – includes `umap_x`, `umap_y`
- `similarity/chat_similarities.jsonl`, `similarity/cluster_similarities.jsonl`

Neo4j loader expectations
- Position properties read from `umap_x`/`umap_y`
- Unique identifiers: `chat_hash` (Chat), `message_id/hash` (Message), `chunk_id/hash` (Chunk), `cluster_id` (Cluster)

Qdrant loader expectations
- Host URL: `http://localhost:6335`
- Collection: `chatmind_embeddings`
- Points: chunks + cluster/chat summary vectors with cross-reference payloads

---

### CLI and Orchestration
- Pipeline CLI: `chatmind` (from `pyproject.toml`)
  - Examples:
    - Full run (local): `chatmind --local`
    - Specific steps: `chatmind --steps ingestion chunking embedding`
    - Force reprocess: `chatmind --force`
    - Check setup only: `chatmind --check-only`
- Makefile tasks:
  - `make up/down/pipeline/api/frontend/docs/lint/fmt/e2e`
- Root compose (`docker-compose.yml`) runs DBs + API + Frontend consistently

---

### Agent Operating Guidance (Safe defaults)
- Prefer local-first: use `--local` to avoid external API costs
- Use `--check-only` before heavy runs to validate setup quickly
- Respect ports and env defaults (Qdrant is 6335 on host)
- Do not commit secrets or real data; use `.env.example` patterns
- If editing pipeline paths, keep everything under `data/processed/`
- When writing position files, preserve `umap_x`/`umap_y`

---

### Common Tasks (Agent Cheat Sheet)
- Verify services up: `make up` then curl `:8000/api/health`, open Neo4j `:7474`
- Run end-to-end: `make pipeline` → then call API search → open frontend
- Load to Qdrant only: `python chatmind/pipeline/loading/load_qdrant.py`
- Load to Neo4j only: `python chatmind/pipeline/loading/load_graph.py`
- Standardize ports in docs/scripts if adding new references

---

### CI, Style, and Docs
- GitHub Actions: builds Python, frontend, and docs on push/PR
- Pre-commit (optional): ruff + basic hygiene hooks
- Docs site: `mkdocs.yml` (preview with `make docs`)

---

### Historical Pitfalls (fixed in repo defaults)
Note: These were issues in earlier iterations. Current defaults are correct; keep these in mind only if you customize steps or copy external snippets.
- Qdrant host port must be `6335` (compose maps host 6335 → container 6333)
- Positioning mismatch breaks Neo4j visualization unless using `umap_x/umap_y`
- Avoid brittle relative paths; resolve via project root and `data/processed`
- OpenAI embeddings require `OPENAI_API_KEY` and now use `OpenAI()` client

---

### Extending the System (How to add a step)
- Create a new directory under `chatmind/pipeline/<new_step>/`
- Write a script that:
  - Reads prior step outputs
  - Produces JSON/JSONL artifacts under `data/processed/<new_step>/`
  - Writes a simple `metadata.json` with stats
- Add invocation in `run_pipeline.py` and update docs

---

### API and Frontend Touchpoints
- API (FastAPI): available at `http://localhost:8000`
  - Docs: `/docs`
  - Typical paths: `/api/health`, `/api/search`, `/api/search/hybrid`, `/api/graph`
- Frontend (Vite): dev server `http://localhost:5173`
  - Configure `VITE_API_URL` for backend base URL

---

### Minimal Verification Flow (5 minutes)
1) `docker compose up -d`
2) `chatmind --local` (or `make pipeline`)
3) Open `http://localhost:7474` (Neo4j) and `http://localhost:8000/docs` (API)
4) `curl http://localhost:8000/api/health`
5) Start UI: `make frontend`, then open `http://localhost:5173`

If any step fails, run `chatmind --check-only` and verify env variables/ports. 