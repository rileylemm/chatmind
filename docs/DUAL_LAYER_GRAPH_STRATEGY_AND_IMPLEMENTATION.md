# Dual Layer Graph Strategy & Implementation for ChatMind

> **See also:** [API_DOCUMENTATION.md](API_DOCUMENTATION.md), [PIPELINE_OVERVIEW.md](PIPELINE_OVERVIEW.md), [NEO4J_QUERY_GUIDE.md](NEO4J_QUERY_GUIDE.md)

---

## 🚀 Overview & Rationale

The Dual Layer Graph Strategy is the foundation of ChatMind's knowledge graph, enabling both traditional conversation analysis and advanced AI-powered semantic search. By separating raw conversation data from semantic processing, ChatMind supports:
- **Preservation of original conversation structure**
- **Semantic search and clustering**
- **Flexible, high-performance querying**
- **Easy migration and extensibility**

---

## 🏗️ Architecture & Schema

### Layer 1: Raw Layer (No Chunking)
- **Purpose:** Preserve original conversation structure and threading
- **Nodes:**
  - `(:Chat {chat_id, title, create_time, update_time, data_lake_id, x, y})`
  - `(:Message {message_id, content, role, timestamp, chat_id})`
- **Relationships:**
  - `(Chat)-[:CONTAINS]->(Message)`
  - `(Message)-[:REPLIES_TO]->(Message)` (optional threading)

### Layer 2: Chunk Layer (Chunked + Embedded)
- **Purpose:** Enable semantic search, clustering, and AI-powered analysis
- **Nodes:**
  - `(:Chunk {chunk_id, text, embedding, source_message_id, cluster_id, chat_id})`
- **Relationships:**
  - `(Message)-[:HAS_CHUNK]->(Chunk)`

### Semantic Layer (Tags & Topics)
- **Purpose:** Provide categorization and clustering
- **Nodes:**
  - `(:Tag {name, count})`
  - `(:Topic {topic_id, name, size, top_words, sample_titles, x, y})`
- **Relationships:**
  - `(Chunk)-[:TAGGED_WITH]->(Tag)`
  - `(Topic)-[:SUMMARIZES]->(Chunk)`
  - `(Chat)-[:HAS_TOPIC]->(Topic)`
  - `(Chat)-[:SIMILAR_TO]->(Chat)`

---

## 🔄 Data Flow & Implementation Details

### Data Flow
1. **Data Ingestion:** Raw ChatGPT exports → `chats.jsonl`
2. **Embedding & Clustering:** `chats.jsonl` → `chunks_with_clusters.jsonl`
3. **Auto-Tagging:** `chunks_with_clusters.jsonl` → `tagged_chunks.jsonl` → `processed_tagged_chunks.jsonl`
4. **Neo4j Loading:**
   - Layer 1: `chats.jsonl` → Chat/Message nodes
   - Layer 2: `processed_tagged_chunks.jsonl` → Chunk nodes with HAS_CHUNK relationships
   - Semantic: Tags and Topics with their relationships

### Core Components
- **Neo4j Loader:** `chatmind/neo4j_loader/load_graph.py`
  - `load_raw_layer()`, `load_chunk_layer()`, `create_constraints()`, `load_pipeline()`
- **API Services:** `chatmind/api/services.py`
  - Layer-specific and cross-layer methods
- **API Endpoints:** `chatmind/api/main.py`
  - Layer-specific, semantic, and graph endpoints
- **Test Suite:** `scripts/test_dual_layer.py`
  - Connection, node count, relationship, API, and cross-layer query tests

---

## 🗂️ Schema & Indexes (Cypher)
```cypher
// Raw Layer
CREATE CONSTRAINT chat_id IF NOT EXISTS FOR (c:Chat) REQUIRE c.chat_id IS UNIQUE;
CREATE CONSTRAINT message_id IF NOT EXISTS FOR (m:Message) REQUIRE m.message_id IS UNIQUE;
// Chunk Layer
CREATE CONSTRAINT chunk_id IF NOT EXISTS FOR (ch:Chunk) REQUIRE ch.chunk_id IS UNIQUE;
// Semantic Layer
CREATE CONSTRAINT topic_id IF NOT EXISTS FOR (t:Topic) REQUIRE t.topic_id IS UNIQUE;
CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (tag:Tag) REQUIRE tag.name IS UNIQUE;
// Performance Indexes
CREATE INDEX chat_title IF NOT EXISTS FOR (c:Chat) ON (c.title);
CREATE INDEX message_role IF NOT EXISTS FOR (m:Message) ON (m.role);
CREATE INDEX message_timestamp IF NOT EXISTS FOR (m:Message) ON (m.timestamp);
CREATE INDEX chunk_source_message IF NOT EXISTS FOR (ch:Chunk) ON (ch.source_message_id);
CREATE INDEX topic_name IF NOT EXISTS FOR (t:Topic) ON (t.name);
CREATE INDEX tag_name IF NOT EXISTS FOR (tag:Tag) ON (tag.name);
```

---

## 🔍 Query Patterns

### Raw Layer
```cypher
// Get complete conversation
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
RETURN c, collect(m) as messages
ORDER BY m.timestamp;

// Search raw messages
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower("python")
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp DESC;
```

### Chunk Layer
```cypher
// Get chunks for a message
MATCH (m:Message {message_id: "msg_456"})-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
RETURN ch, collect(tag) as tags;

// Semantic search by tags
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN ch.text, ch.source_message_id, tag.name;
```

### Cross-Layer
```cypher
// Get message with semantic analysis
MATCH (m:Message {message_id: "msg_456"})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (ch)<-[:SUMMARIZES]-(t:Topic)
RETURN m.content, collect(ch.text) as chunks, collect(tag.name) as tags, t.name as topic;
```

---

## 🌐 API Endpoints (Key Examples)
- `GET /api/conversations` - Raw conversation data
- `GET /api/chats` - All chats
- `GET /api/chats/{chat_id}/messages` - Messages for a chat
- `GET /api/messages/{message_id}` - Message with chunks
- `GET /api/chunks` - Semantic chunks
- `GET /api/messages/{message_id}/chunks` - Chunks for a message
- `GET /api/topics` - All topics
- `GET /api/tags` - All tags
- `GET /api/clusters/{cluster_id}` - Cluster details
- `GET /api/search` - Search raw messages
- `GET /api/search/semantic` - Semantic similarity search
- `POST /api/search/advanced` - Advanced search
- `GET /api/graph` - Graph data (layer filtering)
- `GET /api/graph/expand/{node_id}` - Expand node

---

## 💻 Usage Examples

### Load Data
```bash
python run_pipeline.py
# Or load just Neo4j
data
python chatmind/neo4j_loader/load_graph.py --clear
```

### Test Implementation
```bash
python scripts/test_dual_layer.py
```

### Start API
```bash
python scripts/start_services.py
# Or
cd chatmind/api && python main.py
```

### Query API
```bash
curl "http://localhost:8000/api/conversations?limit=5"
curl "http://localhost:8000/api/chunks?limit=10"
curl "http://localhost:8000/api/search/semantic?query=python&limit=20"
curl "http://localhost:8000/api/graph?layer=raw&limit=100"
```

---

## 🔄 Migration Notes
- Existing single-layer data can be migrated by adding Chunk nodes and relationships.
- No information loss; original structure preserved.
- Update queries to use appropriate layer.

---

## ⚡ Performance & Optimization
- Use layer-specific endpoints for targeted queries.
- Leverage indexes for common query patterns.
- Use parameterized queries for better performance.
- Embeddings stored as arrays in Chunk nodes.
- Consider vector similarity extensions for large datasets.
- Implement pagination for large result sets.
- Cache frequently accessed data (e.g., with Redis).

---

## 🧪 Test Coverage & Status
- **Neo4j connectivity**
- **Node count validation**
- **Relationship testing**
- **API endpoint testing**
- **Cross-layer query testing**
- **All tests passing (see scripts/test_dual_layer.py)**

---

## 🔮 Future Enhancements
- Vector similarity search in Neo4j
- Real-time processing and streaming
- Advanced analytics (sentiment, topic evolution)
- Layer-specific and interactive graph visualization

---

## 📚 References
- [API Documentation](API_DOCUMENTATION.md)
- [Pipeline Overview](PIPELINE_OVERVIEW.md)
- [Neo4j Query Guide](NEO4J_QUERY_GUIDE.md)

---

*This document is the single source of truth for the dual layer graph strategy and its implementation in ChatMind. For open source contributors and users, this guide provides everything needed to understand, extend, and operate the dual layer knowledge graph.* 