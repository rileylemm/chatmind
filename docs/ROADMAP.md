# ChatMind Roadmap

This roadmap outlines near-term goals and areas where contributors can help.

## Scope
A lightweight plan focusing on making the current MVP useful while inviting contributors.

## Pipeline
- Add Markdown (.md) ingestion (single files and directories)
- Batch processing CLI flags: `--batch-size`, `--resume`, `--since <date>`
- Scheduler-friendly runs: idempotent `run_pipeline.py --non-interactive`
- Clear progress + metrics outputs per step

## Data Sources
- Markdown files (.md)
- Slack export (channels + DMs)
- Notion export (Markdown/CSV)
- Generic JSONL adapter interface

## API
- Pagination for list endpoints (`limit`, `cursor`)
- Consistent result shapes for search endpoints
- Error conventions and status codes doc

## Frontend
- Keep CLI-inspired minimal UI
- Keyboard navigation polish (j/k, x to expand, / to search)
- Deep-link to message in ChatView
- Compact one-line mode toggle

## Infrastructure
- Dockerize API and frontend services (compose) — for now, compose runs only DBs
- Minimal seeds/sample data loading script

## Community
- Contribution guide, issue templates, labels
- “Good first issue” backlog
- Small demo dataset and seed script

## Milestones
- 0.1.0: Minimal UI + docs ready (current)
- 0.2.0: .md ingestion + batch pipeline
- 0.3.0: Pagination + UI polish + sample dataset 