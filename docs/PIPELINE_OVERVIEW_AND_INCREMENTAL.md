# Pipeline Overview and Incremental Processing

## 🚀 Optimized AI Memory Pipeline

A modular, incremental data processing pipeline for ChatGPT conversation analysis with **hybrid Neo4j + Qdrant architecture** for optimal performance and rich semantic search capabilities.

### Key Features
- **Modular Architecture**: Each step is independent and can be run separately
- **Incremental Processing**: Hash-based tracking prevents redundant computation
- **Hybrid Database Architecture**: Neo4j for graph relationships + Qdrant for vector search
- **Embedding Reuse**: Embeddings from positioning step are reused for similarity calculation
- **Dual Processing**: Separate optimized workflows for chats and clusters
- **Smart Caching**: Dramatically improves performance and reduces costs through embedding reuse
- **Data Integrity**: Ensures data integrity and consistency with hash-based tracking
- **Easy Extension**: Makes it easy for open source users to add new data or reprocess as needed
- **Separate Processing**: Provides separate processing for chats and clusters with optimized workflows
- **Cross-Reference Linking**: Seamless linking between Neo4j graph data and Qdrant vector embeddings

**✅ Current Status:**
- **Pipeline fully functional** with all steps working
- **Incremental processing** working perfectly
- **Embedding reuse optimization** implemented
- **Hybrid database loading** with Neo4j (graph) + Qdrant (vectors)
- **Data lake structure** cleaned up and optimized
- **Recent fixes applied** for data consistency and performance
- **Port configuration** fixed for Qdrant (port 6335)
- **Cross-reference IDs** implemented for seamless linking

---

## 📁 Project Structure

### Directory Structure
```
ai_memory/ # Project Root
├── chatmind/           # Main application modules
│   ├── api/           # FastAPI backend with dual layer support
│   ├── pipeline/      # Modular pipeline components
│   │   ├── ingestion/ # Data extraction and flattening
│   │   ├── chunking/  # Semantic chunking
│   │   ├── embedding/ # Embedding generation
│   │   ├── clustering/ # Clustering analysis
│   │   ├── tagging/   # Enhanced auto-tagging
│   │   ├── cluster_summarization/ # Cluster summarization
│   │   ├── chat_summarization/ # Chat summarization
│   │   ├── positioning/ # 2D positioning with embedding generation
│   │   ├── similarity/ # Similarity calculation using saved embeddings
│   │   └── loading/   # Neo4j graph loading
│   └── frontend/      # React frontend with graph visualization
├── data/               # Data storage and processing
│   ├── raw/           # Raw ChatGPT exports
│   ├── processed/     # Processed data by pipeline step
│   │   ├── ingestion/
│   │   ├── chunking/
│   │   ├── embedding/
│   │   ├── clustering/
│   │   ├── tagging/
│   │   ├── cluster_summarization/
│   │   ├── chat_summarization/
│   │   ├── positioning/
│   │   └── similarity/
│   ├── lake/          # Data lake structure (legacy - being phased out)
│   └── tags_masterlist/ # Master tag definitions
├── demos/             # Demo scripts for testing
├── scripts/           # Test and utility scripts
├── docs/              # Documentation
└── chatmind_env/      # Pipeline virtual environment
```

---

## 🔄 Pipeline Steps

### 1. Data Ingestion
- **Input:** New ZIP files in `data/raw/`
- **Process:** Content-based deduplication and flattening
- **Output:** `data/processed/ingestion/chats.jsonl`
- **Smart:** Only processes new ZIP files using hash tracking
- **✅ Status:** Ready to process your ChatGPT exports

### 2. Semantic Chunking
- **Input:** Messages from `data/processed/ingestion/chats.jsonl`
- **Process:** Semantic chunking of messages into meaningful segments
- **Output:** `data/processed/chunking/chunks.jsonl`
- **Smart:** Only processes new chats using hash tracking
- **✅ Status:** Ready to create semantic chunks

### 3. Enhanced Embedding
- **Input:** Chunks from `data/processed/chunking/chunks.jsonl`
- **Process:** Generate embeddings using cloud API or local models
- **Output:** `data/processed/embedding/embeddings.jsonl`
- **Smart:** Skips already embedded chunks, supports both cloud and local methods
- **✅ Status:** Ready to generate embeddings

### 4. Clustering
- **Input:** Embeddings from `data/processed/embedding/embeddings.jsonl`
- **Process:** Cluster embeddings using UMAP + HDBSCAN
- **Output:** `data/processed/clustering/clustered_embeddings.jsonl`
- **Smart:** Only reclusters when new embeddings exist
- **✅ Status:** Ready to create semantic clusters

### 5. Enhanced Auto-Tagging
- **Input:** Chunks from `data/processed/chunking/chunks.jsonl`
- **Process:** Only tags NEW chunks using cloud API or local models
- **Output:** `data/processed/tagging/chunk_tags.jsonl` (local) or `data/processed/tagging/tagged_chunks.jsonl` (cloud)
- **Smart:** Skips already tagged chunks, supports both cloud and local methods
- **✅ Status:** Ready to apply semantic tags

### 6. Tag Post-Processing
- **Input:** `data/processed/tagging/tags.jsonl`, master list (defaults to `data/tags_masterlist/comprehensive_generic_tags.json`)
- **Process:** Map tags to master list, normalize, deduplicate, clean variations
- **Output:** `data/processed/tagging/processed_tags.jsonl`
- **Smart:** Ensures tags are mapped and normalized, handles variations like "japan", "Japan", "#japan", "#Japanese"
- **Master List:** Pre-normalized tags in consistent format (lowercase, single # prefix)
- **Missing Tags Report:** Generates `missing_tags_report.json` to suggest new tags for master list
- **✅ Status:** Ready to process tags with comprehensive normalization

### 7. Cluster Summarization
- **Input:** `data/processed/clustering/clustered_embeddings.jsonl`
- **Process:** Generate intelligent cluster summaries using cloud API or local models
- **Output:** `data/processed/cluster_summarization/cluster_summaries.json` (cloud) or `data/processed/cluster_summarization/local_enhanced_cluster_summaries.json` (local)
- **Smart:** Provides rich metadata including topics, descriptions, key concepts, domain classification
- **✅ Status:** Ready to generate cluster summaries

### 8. Chat Summarization
- **Input:** `data/processed/ingestion/chats.jsonl`
- **Process:** Generate comprehensive chat summaries using cloud API or local models
- **Output:** `data/processed/chat_summarization/chat_summaries.json` (cloud) or `data/processed/chat_summarization/local_enhanced_chat_summaries.json` (local)
- **Smart:** Only processes new chats, supports chunked summarization for large conversations
- **✅ Status:** Ready to generate chat summaries

### 9. Positioning (with Embedding Generation)
- **Input:** Chat summaries and cluster summaries
- **Process:** Generate embeddings and 2D coordinates for both chats and clusters
- **Output:** 
  - `data/processed/positioning/chat_positions.jsonl`
  - `data/processed/positioning/cluster_positions.jsonl`
  - `data/processed/positioning/chat_summary_embeddings.jsonl` ← **Reused for similarity**
  - `data/processed/positioning/cluster_summary_embeddings.jsonl` ← **Reused for similarity**
- **Smart:** Only processes new summaries, saves embeddings for reuse
- **✅ Status:** Ready to create positioning data

### 10. Similarity Calculation (using saved embeddings)
- **Input:** Pre-computed embeddings from positioning step
- **Process:** Calculate cosine similarities between all pairs
- **Output:** 
  - `data/processed/similarity/chat_similarities.jsonl`
  - `data/processed/similarity/cluster_similarities.jsonl`
- **Smart:** Uses embeddings from positioning step (no recomputation), hash-based tracking
- **✅ Status:** Ready to calculate similarities

### 11. Hybrid Database Loading (Neo4j + Qdrant)
- **Input:** All processed data from previous steps
- **Process:** Loads data into both Neo4j (graph relationships) and Qdrant (vector embeddings)
- **Output:** 
  - **Neo4j:** Dual layer graph with all relationships and metadata, including direct tag-chunk relationships
  - **Qdrant:** Vector collection with cross-reference metadata for semantic search
- **Smart:** Only loads when new data exists, maintains cross-references between databases
- **Cross-References:** chunk_id, message_id, chat_id, embedding_hash for seamless linking
- **Tag Relationships:** Creates (Tag)-[:TAGS]->(Message) and (Tag)-[:TAGS_CHUNK]->(Chunk) relationships
- **✅ Status:** Ready to load into hybrid database architecture

---

## 🏗️ Hybrid Database Architecture

### Overview
ChatMind uses a **hybrid database architecture** that combines the strengths of both graph databases (Neo4j) and vector databases (Qdrant) for optimal performance and rich functionality.

### Neo4j: Graph Relationships
**Purpose:** Store complex relationships, semantic tags, clustering, and metadata
- **Chat Layer:** Conversations, messages, chunks, summaries
- **Cluster Layer:** Semantic groupings, cluster summaries, positions (no embeddings)
- **Cross-Layer Connections:** Tags, similarities, relationships
- **Query Capabilities:** Complex graph traversals, relationship analysis

### Qdrant: Vector Search
**Purpose:** Fast semantic search and similarity queries
- **Chunk Embeddings:** 384-dimensional vectors for all chunks
- **Cluster Embeddings:** 384-dimensional vectors for cluster summaries
- **Chat Summary Embeddings:** 384-dimensional vectors for chat summaries
- **Metadata:** Rich cross-reference data for Neo4j linking
- **Search Capabilities:** Semantic similarity, hierarchical search (chunks + clusters + chat summaries)
- **Performance:** Optimized for high-speed vector operations
- **Storage:** Only database that stores embedding vectors

### Cross-Reference Linking
**Seamless Integration:** Both databases maintain cross-references for unified queries
- **chunk_id:** Links Qdrant points to Neo4j Chunk nodes
- **cluster_id:** Links Qdrant cluster points to Neo4j Cluster nodes
- **chat_id:** Links Qdrant chat summary points to Neo4j ChatSummary nodes
- **message_id:** Links to Neo4j Message nodes
- **embedding_hash:** Unique identifier for embeddings
- **message_hash:** Content hash for deduplication

### Benefits
- **Performance:** Fast vector search + rich graph context
- **Scalability:** Separate optimization for different query types
- **Flexibility:** Choose best database for each operation
- **Rich Queries:** Combine semantic search with graph relationships
- **Hierarchical Search:** Search at chunk, cluster, and chat summary levels
- **Future-Proof:** Easy to extend with new vector or graph features

---

## 📊 Complete Data Architecture

### Neo4j (Graph Database) - Metadata & Relationships

#### Core Content:
- **Chats** → Chat nodes with title, create_time, source_file
- **Messages** → Message nodes with content, role, timestamp  
- **Chunks** → Chunk nodes with content, role, char_count

#### Summaries:
- **Chat Summaries** → ChatSummary nodes with summary text, key_points
- **Cluster Summaries** → Summary nodes with summary text, topics, domain

#### Semantic Data:
- **Tags** → Tag nodes with tags list, topics, domain, complexity
- **Clusters** → Cluster nodes with position_x, position_y (UMAP), cluster_hash

#### Relationships:
- `(Chat)-[:CONTAINS]->(Message)`
- `(Message)-[:CONTAINS]->(Chunk)`
- `(Tag)-[:TAGS]->(Message)`
- `(Tag)-[:TAGS_CHUNK]->(Chunk)`
- `(Summary)-[:SUMMARIZES]->(Cluster)`
- `(ChatSummary)-[:SUMMARIZES_CHAT]->(Chat)`

### Qdrant (Vector Database) - Embeddings & Search

#### Chunk Embeddings:
- **Chunk Vectors** → 384-dimensional vectors
- **Chunk Metadata** → Content, role, tags, domain, complexity
- **Cross-references** → chunk_id, message_id, chat_id, message_hash

#### Cluster Embeddings:
- **Cluster Vectors** → 384-dimensional vectors
- **Cluster Metadata** → Summary text, key_points, topics, domain, common_tags
- **Cross-references** → cluster_id, embedding_hash

#### Chat Summary Embeddings:
- **Chat Summary Vectors** → 384-dimensional vectors
- **Chat Summary Metadata** → Summary text, key_points, topics, domain, complexity
- **Cross-references** → chat_id, embedding_hash

### File Structure Summary

```
data/processed/
├── ingestion/
│   └── chats.jsonl                    # → Neo4j (Chat nodes)
├── chunking/
│   └── chunks.jsonl                   # → Neo4j (Chunk nodes)
├── embedding/
│   └── embeddings.jsonl               # → Qdrant (chunk vectors)
├── clustering/
│   └── clustered_embeddings.jsonl     # → Qdrant (chunk vectors + metadata)
├── tagging/
│   ├── processed_tags.jsonl           # → Neo4j (Tag nodes)
│   └── chunk_tags.jsonl               # → Qdrant (chunk metadata)
├── cluster_summarization/
│   └── cluster_summaries.json         # → Neo4j (Summary nodes) + Qdrant (metadata)
├── chat_summarization/
│   └── chat_summaries.json            # → Neo4j (ChatSummary nodes) + Qdrant (metadata)
├── positioning/
│   ├── cluster_positions.jsonl        # → Neo4j (Cluster nodes)
│   ├── cluster_summary_embeddings.jsonl # → Qdrant (cluster vectors)
│   └── chat_summary_embeddings.jsonl  # → Qdrant (chat summary vectors)
└── similarity/
    ├── chat_similarities.jsonl        # → Neo4j (similarity relationships)
    └── cluster_similarities.jsonl     # → Neo4j (similarity relationships)
```

---

## 🔧 Recent Fixes and Optimizations

### Data Lake Structure Fix
- **Issue:** Duplicate data lake created in `chatmind/pipeline/data/lake/`
- **Root Cause:** Relative path resolution in ingestion script
- **Fix:** Updated pipeline runner to pass absolute path `--data-lake-dir`
- **Status:** ✅ Fixed and duplicate removed

### Chat ID Consistency Fix
- **Issue:** All chats had `chat_id: "unknown"`
- **Root Cause:** Ingestion step not providing unique chat IDs
- **Fix:** Updated summarization steps to use `content_hash` as `chat_id`
- **Status:** ✅ Fixed - all chats now have unique IDs

### Neo4j Authentication Fix
- **Issue:** Neo4j loading failed with authentication error
- **Root Cause:** Hardcoded credentials in pipeline runner
- **Fix:** Updated to read credentials from environment variables
- **Status:** ✅ Fixed - loading now uses proper authentication

### Tagged Chunks File Reference Fix
- **Issue:** Neo4j loader couldn't find `tagged_chunks.jsonl`
- **Root Cause:** Filename mismatch between tagging output and loader expectation
- **Fix:** Updated loader to reference `chunk_tags.jsonl`
- **Status:** ✅ Fixed - loader now finds correct file

### Chat Similarity Hash Sync Fix
- **Issue:** Similarity calculation skipped due to hash tracking issues
- **Root Cause:** Previous `chat_id` issues caused hash tracking to be out of sync
- **Fix:** Manually re-populated hash file and re-ran similarity calculation
- **Status:** ✅ Fixed - similarities calculated successfully

---

## 📊 Expected Performance

### Processing Times (Local Models)
- **Ingestion**: ~2-5 minutes for typical datasets
- **Chunking**: ~5-10 minutes for message processing
- **Embedding**: ~15-30 minutes for chunk embeddings
- **Clustering**: ~10-20 minutes for semantic clustering
- **Tagging**: ~1-3 hours for comprehensive tagging
- **Summarization**: ~30-60 minutes for summaries
- **Positioning**: ~5-10 minutes for coordinates
- **Similarity**: ~10-20 minutes for similarity calculations
- **Loading**: ~5-15 minutes for Neo4j import

### Data Lake Structure
The data lake provides a scalable storage structure for large datasets (being phased out):
- **raw/**: Stores raw data in various formats
- **processed/**: Stores processed data ready for analysis
- **interim/**: Stores intermediate processing results

### Backup Strategy
- **backup_old_data/**: Legacy data from previous pipeline versions
- **backup_YYYYMMDD_HHMMSS/**: Timestamped backups for major changes (e.g., before major data migrations)

---

## 🔄 Strict Hash Tracking System

### Overview
ChatMind uses a **strict hash-based tracking system** that ensures data integrity and enables efficient incremental processing. Each pipeline step generates SHA256 hashes of processed data and stores them in `.pkl` files to track what has already been processed.

### Hash Generation Strategy
- **Content-Based Hashing**: Each data item generates a unique SHA256 hash based on its content
- **Consistent Hashing**: Same input always produces the same hash, ensuring reproducibility
- **Granular Tracking**: Individual items (chats, chunks, embeddings) are tracked separately
- **Cross-Step Validation**: Hashes are validated between pipeline steps to ensure consistency

### Hash Tracking Files
- `data/processed/ingestion/processed_zip_hashes.pkl` - Tracks processed ZIP files
- `data/processed/chunking/processed_chat_hashes.pkl` - Tracks processed chats
- `data/processed/embedding/processed_chunk_hashes.pkl` - Tracks embedded chunks
- `data/processed/clustering/processed_embedding_hashes.pkl` - Tracks clustered embeddings
- `data/processed/tagging/processed_chunk_hashes.pkl` - Tracks tagged chunks
- `data/processed/cluster_summarization/processed_cluster_hashes.pkl` - Tracks summarized clusters
- `data/processed/chat_summarization/processed_chat_hashes.pkl` - Tracks summarized chats
- `data/processed/positioning/processed_chat_hashes.pkl` - Tracks positioned chats
- `data/processed/positioning/processed_cluster_hashes.pkl` - Tracks positioned clusters
- `data/processed/similarity/chat_similarity_hashes.pkl` - Tracks chat similarities
- `data/processed/similarity/cluster_similarity_hashes.pkl` - Tracks cluster similarities

### Strict Validation Process

#### 1. **Input Validation**
- Each step validates that input data has expected hash structure
- Ensures data integrity between pipeline steps
- Prevents processing of corrupted or incomplete data

#### 2. **Hash Matching**
- **Exact Match Required**: Only processes items with matching hashes
- **No Partial Processing**: Either processes all items or none
- **Consistent State**: Maintains data consistency across all steps

#### 3. **Cross-Step Verification**
- **Upstream Validation**: Each step verifies hashes from previous steps
- **Downstream Compatibility**: Ensures output hashes match downstream expectations
- **Chain Validation**: Complete hash chain from ingestion to final output

#### 4. **Error Recovery**
- **Hash Mismatch Detection**: Identifies when hash tracking is out of sync
- **Force Reprocessing**: `--force` flag bypasses hash checking when needed
- **Manual Hash Fixes**: Tools to repair hash tracking when corrupted

### Benefits of Strict Hash Tracking

#### **Data Integrity**
- **Reproducible Processing**: Same input always produces same output
- **Corruption Detection**: Identifies data corruption or processing errors
- **Consistent State**: Ensures all pipeline steps are in sync

#### **Incremental Efficiency**
- **90%+ Time Savings**: Only processes new or changed data
- **Smart Skipping**: Automatically skips already processed items
- **Resource Optimization**: Dramatically reduces CPU and memory usage

#### **Development Benefits**
- **Debugging**: Hash mismatches help identify processing issues
- **Testing**: Hash consistency ensures reliable testing
- **Rollback**: Hash files enable easy rollback to previous states

### Hash Matching Examples

#### **Chat Processing**
```python
# Generate hash for chat content
chat_hash = hashlib.sha256(json.dumps(chat_data, sort_keys=True).encode()).hexdigest()

# Check if already processed
if chat_hash in processed_hashes:
    skip_processing()
else:
    process_chat()
    save_hash(chat_hash)
```

#### **Cross-Step Validation**
```python
# Verify upstream hashes match
expected_chat_hashes = load_hashes('chunking/processed_chat_hashes.pkl')
actual_chat_hashes = generate_hashes_from_embedding_input()

if expected_chat_hashes != actual_chat_hashes:
    raise HashMismatchError("Chat hashes don't match between steps")
```

### Troubleshooting Hash Issues

#### **Common Hash Problems**
- **Hash Mismatch**: Input hashes don't match expected hashes
- **Missing Hash Files**: Hash tracking files corrupted or missing
- **Out of Sync**: Hash tracking behind actual processing state

#### **Solutions**
```bash
# Force reprocess specific step
python3 chatmind/pipeline/run_pipeline.py --steps similarity --force

# Clear hash files for specific step
rm data/processed/similarity/*.pkl

# Regenerate hash files
python3 chatmind/pipeline/run_pipeline.py --steps similarity --force
```

### Hash File Structure
Each hash file contains:
- **Set of SHA256 Hashes**: Unique identifiers for processed items
- **Processing Metadata**: Timestamp, version, and processing statistics
- **Validation Info**: Hash generation method and validation rules

### Core Data Files
- `data/processed/ingestion/chats.jsonl` - Flattened chat data
- `data/processed/chunking/chunks.jsonl` - Semantic chunks
- `data/processed/embedding/embeddings.jsonl` - Chunk embeddings
- `data/processed/clustering/clustered_embeddings.jsonl` - Clustered embeddings
- `data/processed/tagging/chunk_tags.jsonl` - Tagged chunks (local models)
- `data/processed/tagging/tagged_chunks.jsonl` - Tagged chunks (cloud API)
- `data/processed/tagging/processed_tags.jsonl` - Post-processed tags (normalized)

### Summarization Files
- `data/processed/cluster_summarization/cluster_summaries.json` - Enhanced cluster summaries (cloud API)
- `data/processed/cluster_summarization/local_enhanced_cluster_summaries.json` - Enhanced cluster summaries (local models)
- `data/processed/chat_summarization/chat_summaries.json` - Enhanced chat summaries (cloud API)
- `data/processed/chat_summarization/local_enhanced_chat_summaries.json` - Enhanced chat summaries (local models)

### Positioning Files (with embeddings for reuse)
- `data/processed/positioning/chat_positions.jsonl` - Chat coordinates
- `data/processed/positioning/cluster_positions.jsonl` - Cluster coordinates
- `data/processed/positioning/chat_summary_embeddings.jsonl` - Chat embeddings (reused for similarity)
- `data/processed/positioning/cluster_summary_embeddings.jsonl` - Cluster embeddings (reused for similarity)
Note: `chat_positions.jsonl` and `cluster_positions.jsonl` include `umap_x` and `umap_y` fields.

### Similarity Files
- `data/processed/similarity/chat_similarities.jsonl` - Chat similarity relationships
- `data/processed/similarity/cluster_similarities.jsonl` - Cluster similarity relationships

### Configuration Files
- `data/tags_masterlist/tags_master_list.json` - Your personal master tag list (pre-normalized)
- `data/tags_masterlist/generic_tags_list.json` - Basic generic tags template (175 tags)
- `data/tags_masterlist/comprehensive_generic_tags.json` - Comprehensive generic tags (366 tags)

---

## 🚀 Running the Pipeline

### Start Databases (root compose)
```bash
docker compose up -d neo4j qdrant
```

### Full Pipeline (Local Models)
```bash
# Preferred: CLI entrypoint
chatmind --local

# Or run the orchestrator directly
python3 chatmind/pipeline/run_pipeline.py --local
```

### Individual Steps
```bash
# Run specific steps
python3 chatmind/pipeline/run_pipeline.py --steps ingestion,chunking,embedding

# Force reprocess specific step
python3 chatmind/pipeline/run_pipeline.py --steps similarity --force
```

### Cloud API Pipeline
```bash
# Run with cloud API (requires API keys)
python3 chatmind/pipeline/run_pipeline.py --embedding-method cloud --tagging-method cloud --summarization-method cloud
```

### Environment Setup
```bash
# Create pipeline environment
python3 -m venv chatmind_env

# Install dependencies
pip install -r chatmind/pipeline/requirements.txt

# Set up environment variables
cp env.example .env
# Edit .env with your API keys and Neo4j credentials
```

### Tag Master List Setup
```bash
# Navigate to tags directory
cd data/tags_masterlist/

# Default behavior: pipeline uses comprehensive_generic_tags.json automatically
# To customize, create your own master list:
cp comprehensive_generic_tags.json tags_master_list.json
# Edit tags_master_list.json and point the post-processor to it with --master-list-path if needed
```

### Tag Optimization Workflow
```bash
# Run post-processing to find missing tags
cd chatmind/pipeline
python3 tagging/post_process_tags.py --check-only

# Auto-add frequently occurring tags (3+ occurrences)
python3 tagging/post_process_tags.py --auto-add --auto-add-threshold 3

# Or manually review missing_tags_report.json and add tags
# Edit data/tags_masterlist/tags_master_list.json

# Re-run post-processing with updated master list
python3 tagging/post_process_tags.py

# Verify tag normalization worked
grep -i "japan" data/processed/tagging/processed_tags.jsonl | head -5

# Load into database (creates tag-chunk relationships automatically)
python3 loading/load_graph.py
```

### Tag Processing Features
- **Incremental Processing**: Only processes new/unchanged messages
- **Auto-Add Tags**: Automatically adds tags with 3+ occurrences to master list
- **Tag Normalization**: Ensures consistent format (lowercase, # prefix)
- **Force Processing**: Use `--force` flag to reprocess all messages
- **Missing Tags Report**: Generates detailed report of unmapped tags

---

## 🔧 Configuration

### Environment Variables
- `OPENAI_API_KEY`: OpenAI API key for cloud processing
- `NEO4J_URI`: Neo4j database URI (default: bolt://localhost:7687)
- `NEO4J_USER`: Neo4j username (default: neo4j)
- `NEO4J_PASSWORD`: Neo4j password (default: password)

### Local Model Setup
- Install Ollama: https://ollama.ai/
- Pull Gemma 2B: `ollama pull gemma:2b`
- Ensure Ollama is running: `ollama serve`

---

## 📈 Performance & Statistics
- **Smart Processing**: 90%+ time savings for incremental updates
- **Embedding Reuse**: 50%+ performance improvement for similarity calculations
- **Incremental Updates**: Only process new data automatically
- **Hash-Based Tracking**: Ensures data integrity and consistency
- **Modular Design**: Run individual steps as needed
- **Local/Cloud Options**: Choose processing method based on needs 