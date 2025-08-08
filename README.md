# ChatMind - AI Memory System

## 🧠 Intelligent ChatGPT Conversation Analysis

ChatMind is a powerful AI memory system that transforms your ChatGPT conversations into a searchable, analyzable knowledge graph with semantic search capabilities.

> Authoritative setup & usage: see [docs/UserGuide.md](docs/UserGuide.md). This is the single source of truth. The README is a high‑level overview.

[![CI](https://img.shields.io/github/actions/workflow/status/rileylemm/chatmind/ci.yml?branch=main)](https://github.com/rileylemm/chatmind/actions)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

### ✨ Key Features

- **🔍 Semantic Search**: Find conversations by meaning, not just keywords
- **📊 Graph Visualization**: Interactive exploration of conversation relationships
- **🏷️ Auto-Tagging**: AI-powered semantic categorization
- **📈 Analytics Dashboard**: Insights into your conversation patterns
- **🔄 Incremental Processing**: Only process new data, save time and costs
- **🏗️ Hybrid Architecture**: Neo4j (graph) + Qdrant (vectors) for optimal performance

### 🏗️ Architecture

ChatMind uses a **hybrid database architecture** combining the best of both worlds:

- **Neo4j**: Rich graph relationships, semantic tags, clustering, metadata
- **Qdrant**: Fast vector search for semantic similarity (chunks + clusters + chat summaries)
- **Cross-References**: Seamless linking between graph and vector data

## 🚀 Quick Start (see full guide)

For complete instructions, environment variables, local models, troubleshooting, and performance notes, follow the single source of truth: [docs/UserGuide.md](docs/UserGuide.md).

Minimal run outline:

```bash
# Start databases (or use your own instances)
docker compose up -d neo4j qdrant

# Run the pipeline (details/options in UserGuide)
python3 chatmind/pipeline/run_pipeline.py --local

# Start API
cd chatmind/api && python main.py

# Start minimal frontend (new terminal)
cd chatmind/frontend && npm run dev
```

## 📁 Project Structure

```
ai_memory/
├── chatmind/           # Main application
│   ├── api/           # FastAPI backend
│   ├── pipeline/      # Data processing pipeline
│   └── frontend/      # React frontend (minimal, CLI-inspired)
├── data/              # Data storage
│   ├── raw/          # ChatGPT exports
│   ├── processed/    # Pipeline outputs
│   └── tags_masterlist/ # Tag master lists
├── docs/             # Documentation
└── scripts/          # Utilities and tests
```

## 📚 Documentation

- **[User Guide](docs/UserGuide.md)** — Single source of truth for setup/usage
- **[API Documentation](docs/API_DOCUMENTATION.md)** — Backend API reference
- **[Pipeline Overview](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)** — Architecture details
- **[Dual Layer Strategy](docs/DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)** — Design notes

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

- See `CONTRIBUTING.md` for dev setup and `CODE_OF_CONDUCT.md` for community standards.
- Security issues: follow `SECURITY.md`.

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

## 🗺️ Roadmap

See the dedicated roadmap: [docs/ROADMAP.md](docs/ROADMAP.md)

## ✅ Open‑Source Readiness Checklist

- **CI**: Lint + typecheck for backend/frontend via GitHub Actions
- **Security**: No secrets checked in; placeholders in `.env.example` and `docker-compose.yml`
- **Docs**: Clear `README.md`, `docs/` with User Guide and API docs
- **Community**: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, issue/PR templates
- **License**: Apache-2.0 