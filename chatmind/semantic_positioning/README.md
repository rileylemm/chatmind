# Semantic Positioning Module

This module provides 2D coordinate generation for topic nodes using UMAP dimensionality reduction. This enables clean layouts in the frontend without requiring runtime calculations.

## 🎯 Purpose

Attach 2D coordinates (x, y) to each topic node based on its semantic content, preparing the data for clean layout in the frontend.

## 🔧 How It Works

### 1. Load Tagged Chunks
- Reads from `data/processed/tagged_chunks.jsonl`
- Extracts all tagged message chunks

### 2. Aggregate Topics
- Groups chunks by topic/cluster
- Combines all related text per topic
- Creates topic summaries with combined content

### 3. Compute Embeddings
- Uses TF-IDF vectorization for topic texts
- Creates high-dimensional feature vectors
- Handles text preprocessing and feature extraction

### 4. Apply UMAP Reduction
- Reduces high-dimensional embeddings to 2D
- Uses UMAP algorithm for semantic preservation
- Falls back to TSNE or random coordinates if needed

### 5. Attach Coordinates
- Adds x/y coordinates to topic nodes
- Saves to `data/processed/topics_with_coords.jsonl`

### 6. Neo4j Integration
- Updated Neo4j loader reads coordinates
- Sets `t.x` and `t.y` properties on Topic nodes

## 🚀 Usage

### Run as Part of Pipeline
```bash
python run_pipeline.py
```

### Run Standalone
```bash
python chatmind/semantic_positioning/apply_topic_layout.py
```

### Test the Module
```bash
python chatmind/semantic_positioning/test_positioning.py
```

## 📊 Output Format

Each topic in the output JSONL file contains:
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

## 🔄 Pipeline Integration

The semantic positioning step is integrated into the main pipeline:

1. **Data Ingestion** → `chats.jsonl`
2. **Embedding & Clustering** → `chunks_with_clusters.jsonl`
3. **Auto-Tagging** → `tagged_chunks.jsonl`
4. **🗺️ Semantic Positioning** → `topics_with_coords.jsonl` ← **NEW STEP**
5. **Neo4j Loading** → Database with coordinates

## 🛠️ Dependencies

- `scikit-learn`: TF-IDF vectorization
- `umap-learn`: Dimensionality reduction
- `numpy`: Numerical operations
- `jsonlines`: File I/O

## ⚙️ Configuration

### UMAP Parameters
- `n_components=2`: 2D output
- `random_state=42`: Reproducible results
- `n_neighbors=15`: Local neighborhood size
- `min_dist=0.1`: Minimum distance between points

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

- **Processing Time**: ~30-60 seconds for 1000+ topics
- **Memory Usage**: ~500MB for large datasets
- **Output Size**: ~1-5MB for coordinate data

## 🎯 Benefits

- **Frontend Performance**: No runtime layout calculations
- **Consistent Layouts**: Reproducible positioning
- **Semantic Clustering**: Related topics appear near each other
- **Scalable**: Handles large topic sets efficiently 