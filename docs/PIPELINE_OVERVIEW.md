# ChatMind Pipeline Overview

## 🏗️ **Current Pipeline Structure**

### **📁 Root Directory**
```
ai_memory/
├── chatmind/           # Main application modules
├── data/              # Data storage and processing
├── demos/             # Demo scripts for testing
├── scripts/           # Utility scripts
├── docs/              # Documentation
├── run_pipeline.py    # Unified smart pipeline runner
├── scripts/           # Utility scripts
└── requirements.txt   # Dependencies
```

## 🔄 **Core Pipeline Flow**

### **1. Data Ingestion** (`chatmind/data_ingestion/`)
- **Purpose:** Extract and flatten ChatGPT exports
- **Input:** Raw ChatGPT export files
- **Output:** `data/processed/chats.jsonl`
- **Script:** `extract_and_flatten.py`
- **Smart:** Only processes new ZIP files

### **2. Embedding & Clustering** (`chatmind/embedding/`)
- **Purpose:** Generate embeddings and cluster similar messages
- **Input:** Messages from `chats.jsonl`
- **Output:** `data/embeddings/chunks_with_clusters.jsonl`
- **Script:** `embed_and_cluster_direct_incremental.py`
- **Smart:** Only embeds new messages, reclusters everything

### **3. Auto-Tagging** (`chatmind/tagger/`)
- **Purpose:** Tag chunks with semantic hashtags
- **Input:** Clustered chunks
- **Output:** `data/processed/tagged_chunks.jsonl`
- **Script:** `run_tagging_incremental.py`
- **Smart:** Only tags new chunks

### **4. Neo4j Loading** (`chatmind/neo4j_loader/`)
- **Purpose:** Load processed data into graph database
- **Input:** Tagged chunks
- **Output:** Neo4j graph database
- **Script:** `load_graph.py`
- **Smart:** Only loads when new tagged data exists

### **5. API & Frontend** (`chatmind/api/` & `chatmind/frontend/`)
- **Purpose:** Visualization and interaction
- **API:** FastAPI backend
- **Frontend:** React + TypeScript + Material-UI

## 📊 **Data Files**

### **Raw Data**
- `data/raw/` - ChatGPT export ZIP files
- `data/processed/chats.jsonl` - Flattened chat data

### **Processed Data**
- `data/embeddings/chunks_with_clusters.jsonl` - Messages with embeddings and clusters
- `data/processed/tagged_chunks.jsonl` - Tagged chunks

### **Tag Management**
- `data/tags/tags_master_list.json` - Master tag list (755 tags)
- `data/interim/tag_frequencies_final.json` - Final tag frequencies

### **State Tracking**
- `data/processed/message_embedding_state.pkl` - Tracks embedded messages
- `data/processed/chunk_tagging_state.pkl` - Tracks tagged chunks
- `data/processed/content_hashes.pkl` - Tracks processed ZIP files

### **Cost Tracking**
- `data/cost_tracker.db` - API usage tracking

## 🎯 **Key Components**

### **✅ Active & Used**
- `chatmind/` - Main application modules
- `run_pipeline.py` - Unified smart pipeline runner
- `scripts/` - Utility scripts (setup, services)
- `demos/` - Useful demo scripts
- `scripts/extract_tags.py` - Tag extraction utility

### **🗑️ Removed (Unused/Duplicate)**
- `src/` - Old frontend (duplicate of `chatmind/frontend/`)
- `demo_tag_filtering.py` - Unused demo
- `demo_incremental.py` - Unused demo  
- `demo_url_mapping.py` - Unused demo
- `test_overlapping_exports.py` - Test script
- `run_pipeline_incremental.py` - Replaced by unified pipeline
- Temporary cleanup scripts

## 🚀 **Usage**

### **Run Complete Smart Pipeline**
```bash
python run_pipeline.py
```

### **Check What Needs Processing**
```bash
python run_pipeline.py --check-only
```

### **Run Individual Steps**
```bash
# Data ingestion
python chatmind/data_ingestion/extract_and_flatten.py

# Embedding & clustering
python chatmind/embedding/embed_and_cluster_direct_incremental.py

# Auto-tagging
python chatmind/tagger/run_tagging_incremental.py

# Neo4j loading
python chatmind/neo4j_loader/load_graph.py
```

### **Start Services**
```bash
python scripts/start_services.py
```

### **Run Demos**
```bash
# Test auto-tagging
python demos/demo_auto_tagging.py

# Test semantic chunking
python demos/demo_semantic_chunking.py

# Test cost tracking
python demos/demo_cost_tracking.py

# Test data lake
python demos/demo_data_lake.py
```

## 📈 **Pipeline Statistics**

- **Total Messages:** ~32,392 (user + assistant)
- **Master Tags:** 755 unique tags
- **Tag Coverage:** 70.9% mapping rate
- **Processing Time:** ~2.5 hours for full tagging
- **Smart Processing:** 90%+ time savings for incremental updates

## 🎯 **Current Status**

✅ **Pipeline is unified and smart**  
✅ **All components are actively used**  
✅ **Demo scripts organized in `demos/`**  
✅ **Tag system normalized and consistent**  
✅ **Ready for production use**  
✅ **Automatic incremental processing** 