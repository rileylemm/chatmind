# ChatMind User Guide for Riley

This document guides you through installing, running, and extending the ChatMind pipeline, including recent enhancements:
  - **Unified smart pipeline** that automatically handles incremental processing
  - GPT-driven auto-tagging
  - Direct Chat→Topic edges in Neo4j
  - Chat↔Chat similarity edges

## 1. Prerequisites
1. Python 3.8 or higher
2. Node.js & npm (for frontend)
3. Neo4j (Desktop or Docker)
4. OpenAI API key (optional, for auto-tagging)

## 2. Setup & Installation
```bash
# Clone repository
git clone <your-repo-url>
cd <your-repo>

# Python dependencies
pip install -r requirements.txt

# Copy and configure environment variables
cp env.example .env  # edit: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY

# Frontend dependencies
cd chatmind/frontend
npm install
cd ../..
```

## 3. Data Processing Pipeline
The unified pipeline automatically handles both first-time processing and incremental updates.

### 3.1 Smart Pipeline (Recommended)
```bash
# Run complete pipeline (automatically handles incremental)
python run_pipeline.py

# Check what needs processing
python run_pipeline.py --check-only

# Force reprocess everything
python run_pipeline.py --force-reprocess
```

### 3.2 Individual Steps (Advanced)
```bash
# Data ingestion (already incremental)
python chatmind/data_ingestion/extract_and_flatten.py \
  --raw-dir data/raw \
  --processed-dir data/processed

# Embedding & clustering (incremental)
python chatmind/embedding/embed_and_cluster_direct_incremental.py

# Auto-tagging (incremental)
python chatmind/tagger/run_tagging_incremental.py

# Neo4j loading
python chatmind/neo4j_loader/load_graph.py \
  --clear \
  --chat-similarity \
  --similarity-threshold 0.8
```

### 3.3 Pipeline Options
```bash
# Skip expensive steps during development
python run_pipeline.py --skip-tagging --skip-embedding

# Clear all state and start fresh
python run_pipeline.py --clear-state

# Only check what needs processing
python run_pipeline.py --check-only
```

## 4. Starting Services
```bash
# All-in-one
python scripts/start_services.py

# Or separately
python chatmind/api/main.py       # API at http://localhost:8000
cd chatmind/frontend && npm start # UI at http://localhost:3000
```

## 5. Access & Explore
- Frontend: http://localhost:3000
- API Docs: http://localhost:8000/docs

## 6. Iterative Development
The unified pipeline makes development much easier:

```bash
# Add new ZIP files
cp new_export.zip data/raw/

# Run pipeline (automatically processes only new data)
python run_pipeline.py

# Check what was processed
python run_pipeline.py --check-only
```

## 7. Inspecting Data
```bash
# View tagged chunks
jq -c '{chat_id, message_id, tags, category}' data/processed/tagged_chunks.jsonl | head -n 10

# View embeddings
jq -c '{chat_id, content, cluster_id}' data/embeddings/chunks_with_clusters.jsonl | head -n 10

# Check state files
ls -la data/processed/*.pkl
```

## 8. Troubleshooting

### **Pipeline Issues:**
- **No tags?** Ensure `OPENAI_API_KEY` is set
- **Processing everything?** Check if state files exist: `ls data/processed/*.pkl`
- **Force reprocess:** Use `--force-reprocess` flag

### **Neo4j Issues:**
- **Connection errors?** Verify `.env` and Neo4j status
- **Clear database:** Use `--clear` flag with loader

### **Frontend Issues:**
- **CORS errors?** Check FastAPI CORS settings for `localhost:3000`
- **Build errors?** Run `npm install` in `chatmind/frontend/`

### **State Management:**
```bash
# Clear specific state
rm data/processed/message_embedding_state.pkl  # Clear embedding state
rm data/processed/chunk_tagging_state.pkl     # Clear tagging state

# Clear all state
python run_pipeline.py --clear-state
```

## 9. Advanced Usage

### **Development Workflow:**
```bash
# Quick iteration (skip expensive steps)
python run_pipeline.py --skip-tagging --skip-embedding

# Test specific step
python chatmind/tagger/run_tagging_incremental.py --force

# Check processing status
python run_pipeline.py --check-only
```

### **Production Workflow:**
```bash
# Add new data
cp new_export.zip data/raw/

# Run full pipeline (smart incremental)
python run_pipeline.py

# Start services
python scripts/start_services.py
```

---

**🎉 Your pipeline is now unified and smart - one command handles everything!**