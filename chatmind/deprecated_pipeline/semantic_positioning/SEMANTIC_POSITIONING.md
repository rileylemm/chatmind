# Semantic Positioning Module

This module provides 2D coordinate generation for both **topic nodes** and **chat nodes** using UMAP dimensionality reduction. This enables clean layouts in the frontend without requiring runtime calculations.

## 🎯 Purpose

Attach 2D coordinates (x, y) to topic and chat nodes based on their semantic content, preparing the data for clean layout in the frontend. Chats are positioned relative to their associated topics, creating a hierarchical visualization.

## 🔧 How It Works

### **Topic Positioning**
1. **Load Tagged Chunks**
   - Reads from `data/processed/processed_tagged_chunks.jsonl`
   - Extracts all tagged message chunks

2. **Aggregate Topics**
   - Groups chunks by topic/cluster
   - Combines all related text per topic
   - Creates topic summaries with combined content

3. **Compute Embeddings**
   - Uses TF-IDF vectorization for topic texts
   - Creates high-dimensional feature vectors
   - Handles text preprocessing and feature extraction

4. **Apply UMAP Reduction**
   - Reduces high-dimensional embeddings to 2D
   - Uses UMAP algorithm for semantic preservation
   - Falls back to TSNE or random coordinates if needed

5. **Attach Coordinates**
   - Adds x/y coordinates to topic nodes
   - Saves to `data/processed/topics_with_coords.jsonl`

### **Chat Positioning (NEW)**
1. **Load Processed Chunks & Topic Coordinates**
   - Reads from `data/processed/processed_tagged_chunks.jsonl`
   - Loads topic coordinates from `data/processed/topics_with_coords.jsonl`

2. **Aggregate Chats by Topic**
   - Groups chunks by chat, then by topic
   - Collects all message embeddings for each chat
   - Determines topic association for each chat

3. **Compute Chat Embeddings**
   - **Averages message embeddings** for each chat (efficient approach)
   - Creates a single embedding vector per chat
   - Handles token limits by using existing message embeddings

4. **Apply Semantic Positioning per Topic**
   - For each topic, applies UMAP to its associated chats
   - Positions chats semantically relative to each other
   - Offsets chat coordinates by the topic's anchor position

5. **Save Chat Coordinates**
   - Saves to `data/processed/chats_with_coords.jsonl`
   - Each chat gets (x, y) coordinates relative to its topic

### **Neo4j Integration**
- Updated Neo4j loader reads both topic and chat coordinates
- Sets `t.x` and `t.y` properties on Topic nodes
- Sets `c.x` and `c.y` properties on Chat nodes

## 🚀 Usage

### Run as Part of Pipeline
```bash
python run_pipeline.py
```

### Run Topic Positioning Standalone
```bash
python chatmind/semantic_positioning/apply_topic_layout.py
```

### Run Chat Positioning Standalone
```bash
python chatmind/semantic_positioning/apply_chat_layout.py
```

### Test the Module
```bash
python chatmind/semantic_positioning/test_positioning.py
```

## 📊 Output Format

### Topic Coordinates
Each topic in `topics_with_coords.jsonl` contains:
```json
{
  "topic_id": "cluster_123",
  "combined_text": "All text from this topic...",
  "chunk_count": 45,
  "tags": ["tag1", "tag2", "tag3"],
  "cluster_id": 123,
  "x": 0.234,
  "y": -0.567
}
```

### Chat Coordinates (NEW)
Each chat in `chats_with_coords.jsonl` contains:
```json
{
  "chat_id": "abc123",
  "topic_id": "cluster_123",
  "x": 123.45,
  "y": 67.89
}
```

## 🔄 Pipeline Integration

The semantic positioning steps are integrated into the main pipeline:

1. **Data Ingestion** → `chats.jsonl`
2. **Embedding & Clustering** → `chunks_with_clusters.jsonl`
3. **Auto-Tagging** → `tagged_chunks.jsonl`
4. **Tag Post-Processing** → `processed_tagged_chunks.jsonl`
5. **🗺️ Topic Positioning** → `topics_with_coords.jsonl`
6. **🗺️ Chat Positioning** → `chats_with_coords.jsonl` ← **NEW STEP**
7. **Neo4j Loading** → Database with coordinates

## 🎯 Chat Positioning Strategy

### **Hierarchical Layout**
- **Topics** are positioned globally using their semantic content
- **Chats** are positioned locally within their topic's coordinate space
- Creates a "web" of semantically related chats around each topic

### **Semantic Clustering**
- Chats within the same topic are positioned based on their semantic similarity
- Similar chats appear closer together in the topic's coordinate space
- Uses averaged message embeddings for efficient computation

### **Coordinate System**
- Chat coordinates are **relative to their topic's position**
- Each topic acts as an anchor point for its associated chats
- Enables zoom-in/zoom-out visualization patterns

## 🛠️ Dependencies

- `scikit-learn`: TF-IDF vectorization and TSNE fallback
- `umap-learn`: Dimensionality reduction
- `numpy`: Numerical operations
- `jsonlines`: File I/O
- `tqdm`: Progress tracking

## ⚙️ Configuration

### UMAP Parameters (Topics)
- `n_components=2`: 2D output
- `random_state=42`: Reproducible results
- `n_neighbors=15`: Local neighborhood size
- `min_dist=0.1`: Minimum distance between points

### UMAP Parameters (Chats)
- `n_neighbors=15`: Local neighborhood size
- `min_dist=0.1`: Minimum distance between points
- `scaling=50`: Scale factor for chat coordinates
- `topic_offset`: Offset by topic anchor position

### TF-IDF Parameters
- `max_features=1000`: Maximum vocabulary size
- `stop_words='english'`: Remove common words
- `min_df=2`: Minimum document frequency
- `max_df=0.95`: Maximum document frequency

## 🔍 Fallback Strategy

1. **UMAP** (preferred): Best semantic preservation
2. **TSNE** (fallback): Good for smaller datasets
3. **Random** (emergency): Uniform distribution

## 📈 Performance

- **Topic Processing Time**: ~30-60 seconds for 1000+ topics
- **Chat Processing Time**: ~60-120 seconds for 1000+ chats
- **Memory Usage**: ~500MB for large datasets
- **Output Size**: ~1-5MB for coordinate data

## 🎯 Benefits

- **Frontend Performance**: No runtime layout calculations
- **Consistent Layouts**: Reproducible positioning
- **Semantic Clustering**: Related topics and chats appear near each other
- **Hierarchical Visualization**: Topics as anchors, chats as semantic webs
- **Scalable**: Handles large topic and chat sets efficiently
- **Efficient**: Uses existing message embeddings for chat positioning 