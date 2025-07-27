# Pipeline Overview & Incremental Processing for ChatMind

> **See also:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md), [DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md](DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md), [UserGuide.md](UserGuide.md)

---

## 🚀 Overview & Rationale

ChatMind uses a **unified smart pipeline** that automatically handles both first-time processing and incremental updates. This approach:
- Dramatically improves performance and reduces costs
- Ensures data integrity and consistency
- Makes it easy for open source users to add new data or reprocess as needed

---

## 🏗️ High-Level Structure & Flow

### Directory Structure
```
ai_memory/
├── chatmind/           # Main application modules
│   ├── api/           # FastAPI backend with dual layer support
│   ├── data_ingestion/ # Extract and flatten ChatGPT exports
│   ├── embedding/     # Generate embeddings and cluster messages
│   ├── tagger/        # Auto-tagging with post-processing
│   ├── semantic_positioning/ # UMAP positioning for topics and chats
│   ├── neo4j_loader/  # Dual layer graph loading
│   └── utilities/     # Database maintenance scripts
├── data/              # Data storage and processing
├── demos/             # Demo scripts for testing
├── scripts/           # Test and utility scripts
├── docs/              # Documentation
├── run_pipeline.py    # Unified smart pipeline runner
└── requirements.txt   # Dependencies
```

---

## 🔄 Step-by-Step Pipeline Behavior (with Incremental Logic)

### 1. Data Ingestion
- **Input:** New ZIP files in `data/raw/`
- **Process:** Content-based deduplication
- **Output:** Appends to `data/processed/chats.jsonl`
- **Smart:** Only processes new ZIP files

### 2. Embedding & Clustering
- **Input:** Messages from `chats.jsonl`
- **Process:** Only embeds NEW messages, reclusters everything
- **Output:** `data/embeddings/chunks_with_clusters.jsonl`
- **Smart:** Skips already embedded messages

### 3. Auto-Tagging
- **Input:** Chunks from `chunks_with_clusters.jsonl`
- **Process:** Only tags NEW chunks
- **Output:** `data/processed/tagged_chunks.jsonl`
- **Smart:** Skips already tagged chunks

### 3.5. Tag Post-Processing
- **Input:** `tagged_chunks.jsonl`, `tags_master_list.json`
- **Process:** Map tags to master list, normalize, deduplicate
- **Output:** `data/processed/processed_tagged_chunks.jsonl`
- **Smart:** Ensures tags are mapped and normalized

### 4. Semantic Positioning
- **Input:** `processed_tagged_chunks.jsonl`
- **Process:** Generate 2D coordinates for topics and chats (UMAP)
- **Output:** `data/processed/topics_with_coords.jsonl`, `data/processed/chats_with_coords.jsonl`
- **Smart:** Only processes when new tagged data exists

### 5. Neo4j Loading (Dual Layer)
- **Input:** `chats.jsonl`, `processed_tagged_chunks.jsonl`, topic/chat coordinates
- **Process:** Loads all processed data into Neo4j
- **Output:** Dual layer graph in Neo4j
- **Smart:** Only loads when new data exists

---

## 💻 Usage Patterns

### Run Complete Smart Pipeline
```bash
python run_pipeline.py
```

### Check What Needs Processing
```bash
python run_pipeline.py --check-only
```

### Force Reprocess Everything
```bash
python run_pipeline.py --force-reprocess
python run_pipeline.py --clear-state
```

### Skip Specific Steps
```bash
python run_pipeline.py --skip-tagging
python run_pipeline.py --skip-embedding
python run_pipeline.py --skip-ingestion
```

### Run Individual Steps (Advanced)
```bash
python chatmind/data_ingestion/extract_and_flatten.py
python chatmind/embedding/embed_and_cluster_direct_incremental.py
python chatmind/tagger/run_tagging_incremental.py
python chatmind/tagger/post_process_tags.py
python chatmind/semantic_positioning/apply_topic_layout.py
python chatmind/semantic_positioning/apply_chat_layout.py
python chatmind/neo4j_loader/load_graph.py
```

### Start Services
```bash
python scripts/start_services.py
```

### Run Demos
```bash
python demos/demo_auto_tagging.py
python demos/demo_semantic_chunking.py
python demos/demo_cost_tracking.py
python demos/demo_data_lake.py
```

### Database Maintenance
```bash
python chatmind/utilities/create_has_chunk_relationships.py
python chatmind/utilities/create_chat_similarity.py
```

---

## 🗂️ State Tracking & Data Files

- `data/processed/message_embedding_state.pkl` - Tracks embedded messages
- `data/processed/chunk_tagging_state.pkl` - Tracks tagged chunks
- `data/processed/content_hashes.pkl` - Tracks processed ZIP files
- `data/processed/chats.jsonl` - Flattened chat data
- `data/embeddings/chunks_with_clusters.jsonl` - Embedded and clustered messages
- `data/processed/tagged_chunks.jsonl` - Tagged chunks
- `data/processed/processed_tagged_chunks.jsonl` - Post-processed tags
- `data/processed/topics_with_coords.jsonl` - Topics with coordinates
- `data/processed/chats_with_coords.jsonl` - Chats with coordinates
- `data/tags/tags_master_list.json` - Master tag list
- `data/interim/tag_frequencies_final.json` - Tag frequencies
- `data/interim/missing_tags_report.json` - Unmapped tags
- `data/cost_tracker.db` - API usage tracking

---

## 📈 Performance & Statistics
- **Total Messages:** ~40,556
- **Total Chunks:** ~32,565
- **Total Chats:** ~1,714
- **Total Topics:** ~1,198
- **Master Tags:** 755
- **Active Tags:** 2,067
- **Tag Coverage:** 70.9%
- **Processing Time:** ~2.5 hours for full tagging
- **Smart Processing:** 90%+ time savings for incremental updates

---

## 🎯 Best Practices
- Add new ZIP files to `data/raw/` and run the pipeline
- Use `--check-only` to preview what will be processed
- Use `--force-reprocess` for major changes
- Skip expensive steps during development
- Keep state files unless you want to reprocess everything
- Always run tag post-processing before downstream steps
- Use processed files as input for downstream steps

---

## 🔮 Future Enhancements
- Incremental Neo4j loading
- Smarter clustering (only recluster when necessary)
- Batch and parallel processing
- Real-time progress tracking and cost estimation
- Performance metrics and monitoring

---

## 📚 References
- [API Documentation](API_DOCUMENTATION.md)
- [Dual Layer Graph Strategy & Implementation](DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)
- [User Guide](UserGuide.md)

---

*This document is the single source of truth for the ChatMind pipeline and incremental processing. For open source contributors and users, this guide provides everything needed to understand, run, and extend the pipeline.* 