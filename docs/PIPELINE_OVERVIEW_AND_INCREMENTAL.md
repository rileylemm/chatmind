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
│   ├── tagger/        # Auto-tagging with cloud/local options
│   │   ├── cloud_api/ # Enhanced tagger using OpenAI API
│   │   ├── local/     # Enhanced tagger using local models
│   │   └── deprecated/ # Original basic tagger
│   ├── summarizer/    # Cluster summarization with cloud/local options
│   │   ├── cloud_api/ # Enhanced summarizer using OpenAI API
│   │   ├── local/     # Enhanced summarizer using local models
│   │   └── deprecated/ # Original basic summarizer
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

### 2. Enhanced Embedding & Clustering
- **Input:** Messages from `chats.jsonl`
- **Process:** Only embeds NEW messages using cloud API or local models, reclusters everything
- **Output:** `data/embeddings/chunks_with_clusters.jsonl`
- **Smart:** Skips already embedded messages, supports both cloud and local methods

### 3. Enhanced Auto-Tagging
- **Input:** Chunks from `chunks_with_clusters.jsonl`
- **Process:** Only tags NEW chunks using cloud API or local models
- **Output:** `data/processed/tagged_chunks.jsonl` (cloud) or `data/processed/local_enhanced_tagged_chunks.jsonl` (local)
- **Smart:** Skips already tagged chunks, supports both cloud and local methods

### 3.5. Tag Post-Processing
- **Input:** `tagged_chunks.jsonl`, `tags_master_list.json`
- **Process:** Map tags to master list, normalize, deduplicate
- **Output:** `data/processed/processed_tagged_chunks.jsonl`
- **Smart:** Ensures tags are mapped and normalized

### 3.6. Enhanced Cluster Summarization
- **Input:** `chunks_with_clusters.jsonl`
- **Process:** Generate intelligent cluster summaries using cloud API or local models
- **Output:** `data/embeddings/enhanced_cluster_summaries.json` (cloud) or `data/embeddings/local_enhanced_cluster_summaries.json` (local)
- **Smart:** Provides rich metadata including topics, descriptions, key concepts, domain classification, and sample questions

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
# Use default methods (local embedding, cloud tagging/summarization)
python run_pipeline.py

# Use cloud API for all AI components (fast, high quality, costs money)
python run_pipeline.py --cloud

# Use local models for all AI components (free, slower, good quality)
python run_pipeline.py --local
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
# Skip expensive steps during development
python run_pipeline.py --skip-tagging
python run_pipeline.py --skip-embedding
python run_pipeline.py --skip-ingestion

# Combine with method selection
python run_pipeline.py --local --skip-tagging
python run_pipeline.py --cloud --skip-summarization
```

### Run Individual Steps (Advanced)
```bash
# Data ingestion
python chatmind/data_ingestion/extract_and_flatten.py

# Enhanced embedding and clustering (choose method)
python chatmind/embedding/run_embedding.py --method cloud
python chatmind/embedding/run_embedding.py --method local

# Enhanced tagging (choose method)
python chatmind/tagger/run_tagging.py --method cloud
python chatmind/tagger/run_tagging.py --method local

# Tag post-processing
python chatmind/tagger/post_process_tags.py

# Enhanced cluster summarization (choose method)
python chatmind/summarizer/run_cluster_summaries.py --method cloud
python chatmind/summarizer/run_cluster_summaries.py --method local

# Semantic positioning
python chatmind/semantic_positioning/apply_topic_layout.py
python chatmind/semantic_positioning/apply_chat_layout.py

# Neo4j loading
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
- `data/processed/tagged_chunks.jsonl` - Tagged chunks (cloud API)
- `data/processed/local_enhanced_tagged_chunks.jsonl` - Tagged chunks (local models)
- `data/processed/processed_tagged_chunks.jsonl` - Post-processed tags
- `data/embeddings/enhanced_cluster_summaries.json` - Enhanced cluster summaries (cloud API)
- `data/embeddings/local_enhanced_cluster_summaries.json` - Enhanced cluster summaries (local models)
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

### Method Selection
- **Quick Start**: Use `--cloud` for fast, high-quality processing (costs money)
- **Cost-Effective**: Use `--local` for free processing with good quality
- **Mixed Approach**: Use individual method flags for custom combinations
- **Development**: Use `--local --skip-tagging` for fast iteration

### Cost Comparison
- **Cloud API**: ~$57-100 total for 32K messages (embedding + tagging + summarization)
- **Local Models**: $0 total (free processing with local models)
- **Mixed**: Varies based on which components use cloud vs local

- Test setup with `--check-only` before running expensive operations

---

## 🔮 Future Enhancements
- Incremental Neo4j loading
- Smarter clustering (only recluster when necessary)
- Batch and parallel processing
- Real-time progress tracking and cost estimation
- Performance metrics and monitoring
- Hybrid approaches (combine cloud and local models)
- Additional local model support
- Enhanced cluster summary visualization

---

## 📚 References
- [API Documentation](API_DOCUMENTATION.md)
- [Dual Layer Graph Strategy & Implementation](DUAL_LAYER_GRAPH_STRATEGY_AND_IMPLEMENTATION.md)
- [User Guide](UserGuide.md)

---

*This document is the single source of truth for the ChatMind pipeline and incremental processing. For open source contributors and users, this guide provides everything needed to understand, run, and extend the pipeline.* 