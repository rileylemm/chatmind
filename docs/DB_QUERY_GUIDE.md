# Database Query Guide for ChatMind - Hybrid Architecture

This guide explains how to query the ChatMind knowledge graph using the hybrid Neo4j + Qdrant architecture, reflecting the current, canonical schema produced by the pipeline.

## 🏗️ Architecture Overview

ChatMind uses a hybrid database architecture:

- Neo4j: Graph database for relationships, metadata, and complex queries
- Qdrant: Vector database for semantic search and similarity operations
- Hybrid Queries: Combine both databases for rich semantic exploration

## 📊 Database Schema (Canonical)

### Neo4j Graph Schema

#### Chat Node
Represents a single conversation.

Properties:
- `chat_id` (String, Unique): Canonical ID in graph (equal to chat hash)
- `external_chat_id` (String, Optional): Original/raw chat ID if available
- `title` (String): Conversation title
- `create_time` (Float seconds): Epoch seconds when chat was created
- `position_x`, `position_y` (Float): 2D layout positions
- `umap_x`, `umap_y` (Float): UMAP coordinates (duplicated for compatibility)
- `loaded_at` (DateTime): When loaded into Neo4j

Example:
```cypher
MATCH (c:Chat)
RETURN c.chat_id, c.title, c.create_time
LIMIT 5
```

#### Message Node
Represents an individual message in a chat.

Properties:
- `message_id` (String, Unique): Canonical message ID
- `message_hash` (String): Hash of message content/metadata
- `content` (String)
- `role` (String): "user" | "assistant"
- `timestamp` (Float seconds): Epoch seconds when the message was sent
- `chat_id` (String): Associated chat ID (equals `Chat.chat_id`)
- `loaded_at` (DateTime)

Example:
```cypher
MATCH (m:Message)
RETURN m.message_id, m.content, m.role
LIMIT 5
```

#### Chunk Node
Represents a semantic chunk of a message.

Properties:
- `chunk_id` (String, Unique)
- `chunk_hash` (String)
- `content` (String)
- `content_length` (Integer)
- `role` (String)
- `token_count` (Integer)
- `message_id` (String)
- `message_hash` (String)
- `chat_id` (String)
- `loaded_at` (DateTime)

Example:
```cypher
MATCH (ch:Chunk)
RETURN ch.chunk_id, ch.content
LIMIT 5
```

#### Cluster Node
Represents a semantic cluster of related chunks.

Properties:
- `cluster_id` (Integer, Unique)
- `x`, `y` (Float): Legacy position fields (present for compatibility)
- `position_x`, `position_y` (Float): Canonical positions
- `umap_x`, `umap_y` (Float): UMAP coordinates
- `cluster_hash` (String)
- `summary_hash` (String)
- `loaded_at` (DateTime)

Example:
```cypher
MATCH (cl:Cluster)
RETURN cl.cluster_id, cl.position_x, cl.position_y, cl.umap_x, cl.umap_y
LIMIT 5
```

#### Tag Node
Represents semantic tags/categories applied to messages.

Properties:
- `tag_hash` (String, Unique)
- `tags` (List[String])
- `domain` (String)
- `sentiment` (String)
- `complexity` (String)
- `loaded_at` (DateTime)

Example:
```cypher
MATCH (t:Tag)
RETURN t.tags, t.domain, t.sentiment
LIMIT 5
```

#### Summary Node
Represents a summary for a cluster.

Properties:
- `summary_hash` (String, Unique)
- `summary` (String)
- `key_points` (List[String])
- `common_tags` (List[String])
- `loaded_at` (DateTime)

Example:
```cypher
MATCH (s:Summary)
RETURN s.summary, s.key_points
LIMIT 5
```

### Neo4j Relationship Types (Canonical)

Core relationships:
- `(:Chat)-[:CONTAINS]->(:Message)`
- `(:Message)-[:HAS_CHUNK]->(:Chunk)`
- `(:Cluster)-[:HAS_CHUNK]->(:Chunk)`  // Canonical (older data may contain `:CONTAINS_CHUNK`; queries should allow both)
- `(:Tag)-[:TAGS]->(:Message)`
- `(:Summary)-[:SUMMARIZES]->(:Cluster)`

Similarity relationships:
- `(:Chat)-[:SIMILAR_TO_CHAT_HIGH]->(:Chat)`
- `(:Chat)-[:SIMILAR_TO_CHAT_MEDIUM]->(:Chat)`

### Qdrant Vector Schema

Collection: `chatmind_embeddings`

Point structure:
- ID: `chunk_id` (String)
- Vector: 384-dimensional embedding vector
- Payload:
  - `chunk_id` (String)
  - `message_id` (String)
  - `chat_id` (String)
  - `content` (String)
  - `role` (String)
  - `tags` (List[String])
  - `domain` (String)
  - `complexity` (String)
  - `embedding_hash` (String)
  - `message_hash` (String)
  - `vector_dimension` (Integer) = 384
  - `embedding_method` (String)
  - `original_timestamp` (Float seconds): Epoch timestamp sourced from raw message
  - `loaded_at` (DateTime)

## 🔍 Query Patterns by Database

### Neo4j Graph Queries

1) Basic data exploration

Get all chats with message counts:
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, c.create_time, c.chat_id, count(m) as message_count
ORDER BY c.create_time DESC
```

Get messages in a chat:
```cypher
MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp
```

Get chunks for a message:
```cypher
MATCH (m:Message {message_id: $message_id})-[:HAS_CHUNK]->(ch:Chunk)
RETURN ch.content, ch.chunk_id
```

2) Semantic analysis queries

Get messages with tags:
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
RETURN m.content, m.role, t.tags, t.domain, t.sentiment
ORDER BY m.timestamp DESC
LIMIT 20
```

Find messages by domain:
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
WHERE t.domain = $domain
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

Get cluster summaries:
```cypher
MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
RETURN cl.cluster_id, s.summary, s.key_points, s.common_tags
ORDER BY cl.cluster_id
```

3) Similarity queries

Find similar chats:
```cypher
MATCH (c1:Chat {chat_id: $chat_id})-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
RETURN c2.title, c2.chat_id
ORDER BY c2.create_time DESC
```

4) Content discovery queries

Search messages by content:
```cypher
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower($query)
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp DESC
```

Find messages by tags:
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
WHERE ANY(tag IN t.tags WHERE toLower(tag) CONTAINS toLower($needle))
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

Get complete message context:
```cypher
MATCH (m:Message {message_id: $message_id})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
OPTIONAL MATCH (cl:Cluster)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch)
RETURN m.content as message_content,
       m.role as message_role,
       c.title as chat_title,
       collect(DISTINCT ch.content) as chunks,
       collect(DISTINCT t.tags) as tags,
       collect(DISTINCT cl.cluster_id) as cluster_ids
```

5) Time-based queries (epoch seconds)

Last 30 days of messages:
```cypher
MATCH (m:Message)
WHERE m.timestamp > timestamp()/1000 - 30*24*3600
RETURN count(m)
```

Range query (messages):
```cypher
MATCH (m:Message)
WHERE m.timestamp >= $start AND m.timestamp < $end
RETURN count(m)
```

Recent chats by creation time:
```cypher
MATCH (c:Chat)
WHERE c.create_time > timestamp()/1000 - 7*24*3600
RETURN c.chat_id, c.title
ORDER BY c.create_time DESC
```

6) Statistics and analytics

Node counts:
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

Relationship counts:
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

Average chunks per message:
```cypher
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH count(m) as message_count, count(ch) as chunk_count
RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message
```

### Qdrant Vector Queries (host: http://localhost:6335)

1) Basic semantic search:
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

client = QdrantClient(url="http://localhost:6335")
model = SentenceTransformer('all-MiniLM-L6-v2')

query = "python programming"
query_vector = model.encode(query).tolist()

results = client.search(
    collection_name="chatmind_embeddings",
    query_vector=query_vector,
    limit=5,
    with_payload=True
)

for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.payload['content']}")
    print(f"Tags: {result.payload.get('tags', [])}")
```

2) Search with filters:
```python
results = client.search(
    collection_name="chatmind_embeddings",
    query_vector=query_vector,
    query_filter={
        "must": [
            {"key": "domain", "match": {"value": "technology"}}
        ]
    },
    limit=5,
    with_payload=True
)
```

3) Search by tags:
```python
results = client.search(
    collection_name="chatmind_embeddings",
    query_vector=query_vector,
    query_filter={
        "must": [
            {"key": "tags", "match": {"any": ["#python", "#programming"]}}
        ]
    },
    limit=5,
    with_payload=True
)
```

4) Time-based filtering:
```python
import time
cutoff = time.time() - 30*24*3600
recent_points, _ = client.scroll(
    collection_name="chatmind_embeddings",
    scroll_filter={"must": [{"key": "original_timestamp", "range": {"gte": cutoff}}]},
    limit=10,
    with_payload=False
)
print("Recent points:", len(recent_points))
```

5) Collection statistics:
```python
collection_info = client.get_collection("chatmind_embeddings")
print("Total points:", collection_info.points_count)
print("Vector size:", collection_info.config.params.vectors.size)
```

## 🔗 Hybrid Queries

1) Semantic search with graph context

```python
def semantic_search_with_context(query: str, limit: int = 5):
    # 1) Qdrant semantic search
    client = QdrantClient(url="http://localhost:6335")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    query_vector = model.encode(query).tolist()
    search_results = client.search(
        collection_name="chatmind_embeddings",
        query_vector=query_vector,
        limit=limit,
        with_payload=True
    )

    # 2) Neo4j graph context
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "chatmind123"))

    with driver.session() as session:
        for result in search_results:
            chunk_id = result.payload['chunk_id']
            context_result = session.run(
                """
                MATCH (ch:Chunk {chunk_id: $chunk_id})
                OPTIONAL MATCH (m:Message)-[:HAS_CHUNK]->(ch)
                OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                OPTIONAL MATCH (cl:Cluster)-[:HAS_CHUNK|:CONTAINS_CHUNK]->(ch)
                RETURN m.message_id as message_id,
                       c.title as chat_title,
                       collect(DISTINCT t.tags) as tags,
                       cl.cluster_id as cluster_id
                """,
                chunk_id=chunk_id,
            )
            ctx = context_result.single()
            if ctx:
                yield {
                    "chunk_id": chunk_id,
                    "content": result.payload['content'],
                    "similarity": result.score,
                    "message_id": ctx["message_id"],
                    "chat_title": ctx["chat_title"],
                    "tags": ctx["tags"],
                    "cluster_id": ctx["cluster_id"],
                }
```

2) Graph query with vector similarity

```python
def graph_query_with_similarity(chat_id: str, limit: int = 5):
    # 1) Get chat chunk IDs from Neo4j
    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "chatmind123"))

    with driver.session() as session:
        chat_result = session.run(
            """
            MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            RETURN c.title as title, collect(DISTINCT ch.chunk_id) as chunk_ids
            """,
            chat_id=chat_id,
        )
        record = chat_result.single()
        if not record:
            return []
        chunk_ids = [cid for cid in record["chunk_ids"] if cid]

    # 2) For a few chunk vectors, find similar chunks in Qdrant
    client = QdrantClient(url="http://localhost:6335")
    similar_results = []
    for cid in chunk_ids[:3]:
        points, _ = client.scroll(
            collection_name="chatmind_embeddings",
            scroll_filter={"must": [{"key": "chunk_id", "match": {"value": cid}}]},
            limit=1,
            with_vectors=True,
        )
        if not points:
            continue
        vector = points[0].vector
        similar = client.search(
            collection_name="chatmind_embeddings",
            query_vector=vector,
            limit=limit,
            with_payload=True,
        )
        similar_results.extend(similar)
    return similar_results
```

3) Content discovery workflow

```python
def content_discovery_workflow(query: str, domain_filter: str | None = None):
    client = QdrantClient(url="http://localhost:6335")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    query_vector = model.encode(query).tolist()
    q_filter = None
    if domain_filter:
        q_filter = {"must": [{"key": "domain", "match": {"value": domain_filter}}]}

    semantic_results = client.search(
        collection_name="chatmind_embeddings",
        query_vector=query_vector,
        query_filter=q_filter,
        limit=10,
        with_payload=True,
    )

    from neo4j import GraphDatabase
    driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "chatmind123"))

    with driver.session() as session:
        chat_ids = list({res.payload['chat_id'] for res in semantic_results})
        details = session.run(
            """
            MATCH (c:Chat)
            WHERE c.chat_id IN $chat_ids
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
            RETURN c.title as title,
                   c.chat_id as chat_id,
                   count(DISTINCT m) as message_count,
                   count(DISTINCT (m)-[:HAS_CHUNK]->(:Chunk)) as chunk_edges,
                   collect(DISTINCT t.domain) as domains
            """,
            chat_ids=chat_ids,
        )
        return {
            "semantic_results": semantic_results,
            "related_chats": [dict(r) for r in details],
        }
```

## ⏱️ Time Fields: Source of Truth

- Message timestamps come from raw data (message.create_time) as epoch seconds
- Carried through pipeline to:
  - Neo4j: `Message.timestamp`
  - Qdrant: `original_timestamp` (payload)
- Chat creation time stored in Neo4j as `Chat.create_time` (epoch seconds)

## 🔧 Performance Tips

Neo4j
- Use indexes (the loader creates indexes on frequently used properties)
- Limit results for large scans
- Use PROFILE to analyze performance

Qdrant
- Filter early (query_filter) when possible
- Keep vectors consistent (384 dim)
- Use scroll for batch retrieval

Hybrid
- Run Neo4j and Qdrant operations in parallel where appropriate
- Cache frequently accessed results

## 📊 Database Statistics

Neo4j node counts:
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

Neo4j relationship counts:
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

Qdrant collection info:
```python
collection_info = client.get_collection("chatmind_embeddings")
print("Total points:", collection_info.points_count)
print("Vector size:", collection_info.config.params.vectors.size)
```

## 🚀 API Integration (touchpoints)

Endpoints that leverage both databases:
- `GET /api/search/semantic` — Semantic search with graph context
- `GET /api/graph` — Graph data (Neo4j)
- `GET /api/conversations` — Chats + messages
- `GET /api/chunks` — Semantic chunks
- `GET /api/similar` — Similarity via hybrid

Examples:
```bash
curl "http://localhost:8000/api/search/semantic?query=python%20programming&limit=5"
curl "http://localhost:8000/api/graph?limit=100"
```

## 🔍 Debugging and Monitoring

Neo4j
- Connection test: `RETURN 1 AS test`
- Verify structure: `MATCH (n) RETURN labels(n)[0] as type, count(n) as count`
- Profile: `PROFILE MATCH (c:Chat)-[:CONTAINS]->(m:Message) RETURN c.title, count(m)`

Qdrant
- Collections: `client.get_collections()`
- Collection info: `client.get_collection("chatmind_embeddings")`
- Search smoke test: use a trivial vector `[0.1] * 384` and `limit=1`

---

This guide reflects the current schema, property names, relationship types, time field semantics, and host/ports (Neo4j bolt://localhost:7687, Qdrant http://localhost:6335) produced by the default pipeline. After running the pipeline, you can copy/paste these queries to explore your data. 