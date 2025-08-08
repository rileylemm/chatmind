### Pipeline Improvements: Optional and Longer-term

- Correctness/bugs (beyond the quick wins):
  - Normalize ID fields across steps (e.g., ensure `cluster_id` consistently string-typed).
  - Ensure all loaders gracefully handle missing optional files with actionable logs.
  - Add schema validation for JSON/JSONL inputs and outputs.

- Consistency/UX:
  - Centralize path resolution helpers to avoid brittle relative paths.
  - Standardize metadata files and naming across steps.
  - Align property names between Neo4j nodes and pipeline outputs (e.g., `position_x/position_y`).

- Performance/scale:
  - Batch operations in loaders (Neo4j, Qdrant) with tunable batch size.
  - Cache sentence-transformers models and add model selection via config.
  - Add optional multiprocessing for CPU-bound steps (chunking, tagging post-process).

- Reliability/observability:
  - Structured logging with step-scoped correlation IDs.
  - Prometheus-friendly metrics for throughput/latency per step.
  - Health checks for external services before running dependent steps.

- Security:
  - Support Qdrant API keys and TLS.
  - Secrets management via environment or OS keychain, not plaintext files.
  - Least-privilege creds for Neo4j with role-based constraints.

- Developer experience:
  - Makefile or task runner aliases for common flows.
  - CI job to run a smoke pipeline on sample data on PRs.
  - Type hints and mypy in pipeline code; add lightweight unit tests for utilities.

- Data quality:
  - Deduplication across ingestion sources with heuristics.
  - Drift detection on embeddings and summary lengths over time.
  - Tag taxonomy sync script to surface deltas against master list.

- Product features:
  - Incremental cluster updates without full recluster.
  - Time-sliced positioning for timeline views.
  - Multi-model embedding support with automatic dimension handling. 