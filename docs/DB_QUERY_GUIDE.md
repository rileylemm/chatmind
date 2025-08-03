# Database Query Guide for ChatMind - Hybrid Architecture

This guide provides comprehensive information about querying the ChatMind knowledge graph using the **hybrid Neo4j + Qdrant architecture**. It covers both graph database operations (Neo4j) and vector database operations (Qdrant), along with hybrid queries that combine both systems.

## 🏗️ Architecture Overview

ChatMind uses a hybrid database architecture:

- **Neo4j**: Graph database for relationships, metadata, and complex queries
- **Qdrant**: Vector database for semantic search and similarity operations
- **Hybrid Queries**: Combine both databases for rich semantic exploration

## 📊 Database Schema

### Neo4j Graph Schema

#### **Core Node Types**

#### **Chat** Node
Represents individual ChatGPT conversations.

**Properties:**
- `chat_id` (String, Unique): Unique identifier for the chat
- `title` (String): Title of the conversation
- `create_time` (DateTime): When the chat was created
- `update_time` (DateTime): When the chat was last updated
- `position_x`, `position_y` (Float, Optional): Semantic positioning coordinates
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (c:Chat)
RETURN c.chat_id, c.title, c.create_time
LIMIT 5
```

#### **Message** Node
Represents individual messages within chats.

**Properties:**
- `message_id` (String, Unique): Unique identifier for the message
- `content` (String): The message content
- `role` (String): "user" or "assistant"
- `timestamp` (DateTime): When the message was sent
- `chat_id` (String): Associated chat ID
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (m:Message)
RETURN m.message_id, m.content, m.role
LIMIT 5
```

#### **Chunk** Node
Represents semantic chunks of messages.

**Properties:**
- `chunk_id` (String, Unique): Unique identifier for the chunk
- `content` (String): The chunk text content
- `role` (String): "user" or "assistant"
- `message_id` (String): Associated message ID
- `chat_id` (String): Associated chat ID
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (ch:Chunk)
RETURN ch.chunk_id, ch.content
LIMIT 5
```

#### **Cluster** Node
Represents semantic clusters of related chunks.

**Properties:**
- `cluster_id` (Integer, Unique): Unique cluster identifier
- `umap_x`, `umap_y` (Float): UMAP positioning coordinates
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (cl:Cluster)
RETURN cl.cluster_id, cl.umap_x, cl.umap_y
LIMIT 5
```

#### **Tag** Node
Represents semantic tags/categories applied to messages.

**Properties:**
- `tag_hash` (String, Unique): Unique hash for the tag
- `tags` (List[String]): List of tag names (e.g., ["#technology", "#python", "#api"])
- `domain` (String): Domain classification (e.g., "technology", "health", "business")
- `sentiment` (String): Sentiment classification
- `complexity` (String): Complexity classification
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (t:Tag)
RETURN t.tags, t.domain, t.sentiment
LIMIT 5
```

#### **Summary** Node
Represents cluster summaries.

**Properties:**
- `summary_hash` (String, Unique): Unique hash for the summary
- `summary` (String): Summary text
- `key_points` (List[String]): Key points from the summary
- `common_tags` (List[String]): Common tags in the cluster
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (s:Summary)
RETURN s.summary, s.key_points
LIMIT 5
```

### Neo4j Relationship Types

#### **Core Relationships**
- **CONTAINS**: `(Chat)-[:CONTAINS]->(Message)` - Chat contains this message
- **HAS_CHUNK**: `(Message)-[:HAS_CHUNK]->(Chunk)` - Message has been chunked into semantic pieces
- **CONTAINS_CHUNK**: `(Cluster)-[:CONTAINS_CHUNK]->(Chunk)` - Cluster contains this chunk
- **TAGS**: `(Tag)-[:TAGS]->(Message)` - Tag is applied to this message
- **SUMMARIZES**: `(Summary)-[:SUMMARIZES]->(Cluster)` - Summary summarizes this cluster

#### **Similarity Relationships**
- **SIMILAR_TO_CHAT_HIGH**: `(Chat)-[:SIMILAR_TO_CHAT_HIGH]->(Chat)` - Chats are highly similar
- **SIMILAR_TO_CHAT_MEDIUM**: `(Chat)-[:SIMILAR_TO_CHAT_MEDIUM]->(Chat)` - Chats are moderately similar

### Qdrant Vector Schema

#### **Collection: `chatmind_embeddings`**

**Point Structure:**
- **ID**: `chunk_id` (String)
- **Vector**: 384-dimensional embedding vector
- **Payload**:
  - `chunk_id` (String): Unique chunk identifier
  - `message_id` (String): Associated message ID
  - `chat_id` (String): Associated chat ID
  - `content` (String): Chunk text content
  - `role` (String): "user" or "assistant"
  - `tags` (List[String]): Semantic tags
  - `domain` (String): Domain classification
  - `complexity` (String): Complexity level
  - `embedding_hash` (String): Hash of the embedding
  - `message_hash` (String): Hash of the source message
  - `vector_dimension` (Integer): Vector dimension (384)
  - `embedding_method` (String): Method used ("sentence-transformers")
  - `loaded_at` (DateTime): When loaded into Qdrant

## 🔍 Query Patterns by Database

### Neo4j Graph Queries

#### 1. Basic Data Exploration

**Get All Chats with Message Counts:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, c.create_time, c.chat_id, count(m) as message_count
ORDER BY c.create_time DESC
```

**Get Messages in a Chat:**
```cypher
MATCH (c:Chat {chat_id: "your_chat_id"})-[:CONTAINS]->(m:Message)
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp
```

**Get Chunks for a Message:**
```cypher
MATCH (m:Message {message_id: "your_message_id"})-[:HAS_CHUNK]->(ch:Chunk)
RETURN ch.content, ch.chunk_id
```

#### 2. Semantic Analysis Queries

**Get Messages with Tags:**
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
RETURN m.content, m.role, t.tags, t.domain, t.sentiment
ORDER BY m.timestamp DESC
LIMIT 20
```

**Find Messages by Domain:**
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
WHERE t.domain = "technology"
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

**Get Cluster Summaries:**
```cypher
MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
RETURN cl.cluster_id, s.summary, s.key_points, s.common_tags
ORDER BY cl.cluster_id
```

#### 3. Similarity Queries

**Find Similar Chats:**
```cypher
MATCH (c1:Chat {chat_id: "your_chat_id"})-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
RETURN c2.title, c2.chat_id
ORDER BY c2.create_time DESC
```

#### 4. Content Discovery Queries

**Search Messages by Content:**
```cypher
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower("python")
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp DESC
```

**Find Messages by Tags:**
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "programming")
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

**Get Messages by Sentiment:**
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
WHERE t.sentiment = "positive"
RETURN m.content, m.role, t.sentiment
ORDER BY m.timestamp DESC
```

#### 5. Advanced Analysis Queries

**Get Complete Message Context:**
```cypher
MATCH (m:Message {message_id: "your_message_id"})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
RETURN m.content as message_content,
       m.role as message_role,
       c.title as chat_title,
       collect(DISTINCT ch.content) as chunks,
       collect(DISTINCT t.tags) as tags
```

**Get Chat with Full Analysis:**
```cypher
MATCH (c:Chat {chat_id: "your_chat_id"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
RETURN c.title,
       count(DISTINCT m) as message_count,
       count(DISTINCT ch) as chunk_count,
       collect(DISTINCT t.domain) as domains
```

#### 6. Statistics and Analytics

**Node Counts:**
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

**Relationship Counts:**
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

**Average Chunks per Message:**
```cypher
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH count(m) as message_count, count(ch) as chunk_count
RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message
```

**Tag Distribution:**
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
UNWIND t.tags as tag
RETURN tag, count(*) as usage_count
ORDER BY usage_count DESC
LIMIT 20
```

**Domain Distribution:**
```cypher
MATCH (t:Tag)-[:TAGS]->(m:Message)
RETURN t.domain, count(*) as message_count
ORDER BY message_count DESC
```

### Qdrant Vector Queries

#### 1. Semantic Search

**Basic Semantic Search:**
```python
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

# Initialize
client = QdrantClient("localhost", port=6333)
model = SentenceTransformer('all-MiniLM-L6-v2')

# Search
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
    print(f"Tags: {result.payload['tags']}")
```

**Search with Filters:**
```python
# Search only technology domain
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

**Search by Tags:**
```python
# Search for content with specific tags
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

#### 2. Similarity Search

**Find Similar Content:**
```python
# Get a reference chunk
reference_chunk = client.scroll(
    collection_name="chatmind_embeddings",
    limit=1,
    with_payload=True
)[0][0]

# Find similar chunks
similar_results = client.search(
    collection_name="chatmind_embeddings",
    query_vector=reference_chunk.vector,
    limit=10,
    with_payload=True
)
```

#### 3. Batch Operations

**Get All Embeddings:**
```python
# Scroll through all points
all_points = client.scroll(
    collection_name="chatmind_embeddings",
    limit=1000,
    with_payload=True,
    with_vectors=True
)[0]

for point in all_points:
    print(f"ID: {point.id}")
    print(f"Content: {point.payload['content']}")
    print(f"Vector dimension: {len(point.vector)}")
```

**Get Collection Statistics:**
```python
# Get collection info
collection_info = client.get_collection("chatmind_embeddings")
print(f"Total points: {collection_info.points_count}")
print(f"Vector size: {collection_info.config.params.vectors.size}")
```

## 🔗 Hybrid Queries

### 1. Semantic Search with Graph Context

**Python Implementation:**
```python
def semantic_search_with_context(query: str, limit: int = 5):
    # 1. Semantic search in Qdrant
    query_vector = model.encode(query).tolist()
    search_results = client.search(
        collection_name="chatmind_embeddings",
        query_vector=query_vector,
        limit=limit,
        with_payload=True
    )
    
    # 2. Get graph context from Neo4j
    with neo4j_driver.session() as session:
        for result in search_results:
            chunk_id = result.payload['chunk_id']
            
            # Get additional context
            context_result = session.run("""
                MATCH (ch:Chunk {chunk_id: $chunk_id})
                OPTIONAL MATCH (m:Message)-[:HAS_CHUNK]->(ch)
                OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
                OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
                RETURN m.message_id, c.title as chat_title, 
                       collect(DISTINCT t.tags) as tags,
                       ch.cluster_id
            """, chunk_id=chunk_id)
            
            context = context_result.single()
            if context:
                yield {
                    "chunk_id": chunk_id,
                    "content": result.payload['content'],
                    "similarity": result.score,
                    "message_id": context["m.message_id"],
                    "chat_title": context["chat_title"],
                    "tags": context["tags"],
                    "cluster_id": context["ch.cluster_id"]
                }
```

### 2. Graph Query with Vector Similarity

**Python Implementation:**
```python
def graph_query_with_similarity(chat_id: str, limit: int = 5):
    # 1. Get chat from Neo4j
    with neo4j_driver.session() as session:
        chat_result = session.run("""
            MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
            RETURN c.title, collect(DISTINCT ch.chunk_id) as chunk_ids
        """, chat_id=chat_id)
        
        chat_data = chat_result.single()
        if not chat_data:
            return []
        
        # 2. Find similar content in Qdrant
        similar_results = []
        for chunk_id in chat_data["chunk_ids"][:3]:  # Use first 3 chunks
            # Get chunk vector
            chunk_result = client.scroll(
                collection_name="chatmind_embeddings",
                scroll_filter={"must": [{"key": "chunk_id", "match": {"value": chunk_id}}]},
                limit=1,
                with_vectors=True
            )[0]
            
            if chunk_result:
                chunk_vector = chunk_result[0].vector
                
                # Find similar chunks
                similar = client.search(
                    collection_name="chatmind_embeddings",
                    query_vector=chunk_vector,
                    limit=limit,
                    with_payload=True
                )
                
                similar_results.extend(similar)
        
        return similar_results
```

### 3. Content Discovery Workflow

**Python Implementation:**
```python
def content_discovery_workflow(query: str, domain_filter: str = None):
    # 1. Semantic search
    query_vector = model.encode(query).tolist()
    search_filter = None
    if domain_filter:
        search_filter = {"must": [{"key": "domain", "match": {"value": domain_filter}}]}
    
    semantic_results = client.search(
        collection_name="chatmind_embeddings",
        query_vector=query_vector,
        query_filter=search_filter,
        limit=10,
        with_payload=True
    )
    
    # 2. Get related chats from Neo4j
    with neo4j_driver.session() as session:
        chat_ids = set()
        for result in semantic_results:
            chat_ids.add(result.payload['chat_id'])
        
        # Get chat details
        chat_details = session.run("""
            MATCH (c:Chat)
            WHERE c.chat_id IN $chat_ids
            OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
            OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
            RETURN c.title, c.chat_id, 
                   count(DISTINCT m) as message_count,
                   collect(DISTINCT t.domain) as domains
        """, chat_ids=list(chat_ids))
        
        return {
            "semantic_results": semantic_results,
            "related_chats": [dict(record) for record in chat_details]
        }
```

## 🎯 Practical Use Cases

### 1. Content Discovery

**Find all content about Python programming:**
```python
# Qdrant semantic search
query = "python programming"
results = semantic_search_with_context(query, limit=10)

# Neo4j tag-based search
with neo4j_driver.session() as session:
    tag_results = session.run("""
        MATCH (t:Tag)-[:TAGS]->(m:Message)
        WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
        RETURN m.content, m.role, t.tags
        ORDER BY m.timestamp DESC
        LIMIT 10
    """)
```

### 2. Semantic Analysis

**Get semantic breakdown of a conversation:**
```cypher
MATCH (c:Chat {chat_id: "your_chat_id"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
RETURN c.title,
       count(DISTINCT m) as messages,
       count(DISTINCT ch) as chunks,
       collect(DISTINCT t.domain) as domains
```

**Find semantically similar conversations:**
```python
# Get chat embedding
chat_vector = get_chat_embedding(chat_id)

# Find similar chats
similar_chats = client.search(
    collection_name="chatmind_embeddings",
    query_vector=chat_vector,
    query_filter={"must": [{"key": "chat_id", "match": {"any": other_chat_ids}}]},
    limit=5,
    with_payload=True
)
```

### 3. Quality Analysis

**Find conversations with rich semantic content:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (t:Tag)-[:TAGS]->(m)
WITH c, count(DISTINCT m) as message_count, 
     count(DISTINCT ch) as chunk_count, 
     count(DISTINCT t) as tag_count
WHERE chunk_count > 10 AND tag_count > 5
RETURN c.title, message_count, chunk_count, tag_count
ORDER BY tag_count DESC
```

## 🔧 Performance Tips

### Neo4j Performance

1. **Use Indexes**: The system creates indexes on key properties
2. **Limit Results**: Always use `LIMIT` for large result sets
3. **Use Specific Node Types**: Query specific node types for better performance
4. **Profile Queries**: Use `PROFILE` to analyze query performance

### Qdrant Performance

1. **Batch Operations**: Use batch operations for multiple queries
2. **Filter Early**: Apply filters before search for better performance
3. **Vector Dimensions**: Ensure consistent vector dimensions (384 for this setup)
4. **Collection Management**: Monitor collection size and optimize as needed

### Hybrid Performance

1. **Parallel Queries**: Run Neo4j and Qdrant queries in parallel when possible
2. **Caching**: Cache frequently accessed data
3. **Connection Pooling**: Use connection pools for database connections
4. **Result Limiting**: Limit results from both databases

## 📊 Database Statistics

### Neo4j Statistics

**Node Counts:**
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

**Relationship Counts:**
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

### Qdrant Statistics

**Collection Information:**
```python
collection_info = client.get_collection("chatmind_embeddings")
print(f"Total points: {collection_info.points_count}")
print(f"Vector size: {collection_info.config.params.vectors.size}")
```

**Payload Statistics:**
```python
# Get sample points for analysis
sample_points = client.scroll(
    collection_name="chatmind_embeddings",
    limit=1000,
    with_payload=True
)[0]

# Analyze payload distribution
domains = {}
tags = {}
for point in sample_points:
    domain = point.payload.get('domain', 'unknown')
    domains[domain] = domains.get(domain, 0) + 1
    
    for tag in point.payload.get('tags', []):
        tags[tag] = tags.get(tag, 0) + 1

print("Domain distribution:", domains)
print("Top tags:", sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10])
```

## 🚀 API Integration

The ChatMind API provides these endpoints that use both databases:

- `GET /api/search/semantic` - Semantic search using Qdrant + Neo4j context
- `GET /api/graph` - Graph data from Neo4j
- `GET /api/conversations` - Raw conversations from Neo4j
- `GET /api/chunks` - Semantic chunks with embeddings
- `GET /api/similar` - Similarity search using both databases

### Example API Usage

**Semantic Search:**
```bash
curl "http://localhost:8000/api/search/semantic?query=python programming&limit=5"
```

**Graph Data:**
```bash
curl "http://localhost:8000/api/graph?limit=100"
```

**Similar Content:**
```bash
curl "http://localhost:8000/api/similar?chunk_id=your_chunk_id&limit=5"
```

## 🔍 Debugging and Monitoring

### Neo4j Debugging

**Check Database Connection:**
```cypher
RETURN 1 as test
```

**Verify Data Structure:**
```cypher
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
```

**Profile Query Performance:**
```cypher
PROFILE MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, count(m) as message_count
```

### Qdrant Debugging

**Check Collection Status:**
```python
collections = client.get_collections()
print("Available collections:", [c.name for c in collections.collections])
```

**Verify Collection Data:**
```python
collection_info = client.get_collection("chatmind_embeddings")
print(f"Collection status: {collection_info.status}")
print(f"Total points: {collection_info.points_count}")
```

**Test Vector Search:**
```python
# Test with a simple query
test_vector = [0.1] * 384  # 384-dimensional vector
results = client.search(
    collection_name="chatmind_embeddings",
    query_vector=test_vector,
    limit=1
)
print(f"Search test successful: {len(results) > 0}")
```

## 📚 Additional Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Qdrant Python Client](https://qdrant.tech/documentation/guides/python/)
- [Sentence Transformers](https://www.sbert.net/)
- [Neo4j Browser](http://localhost:7474) - Web interface for Neo4j
- [ChatMind API Documentation](http://localhost:8000/docs) - API endpoints
- [Pipeline Overview Documentation](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)

---

*This guide covers the hybrid database architecture for ChatMind. For advanced queries or specific use cases, refer to the individual database documentation or explore the data interactively through the web interfaces.* 