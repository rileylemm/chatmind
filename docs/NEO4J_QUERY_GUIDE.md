# Neo4j Query Guide for ChatMind - Current Implementation

This guide provides comprehensive information about querying the ChatMind knowledge graph in Neo4j with the **current implementation**. It covers the graph schema, common query patterns, and practical examples for exploring your ChatGPT conversations and their semantic analysis.

## 📊 Graph Schema - Current Implementation

### Core Node Types

#### **Chat** Node
Represents individual ChatGPT conversations.

**Properties:**
- `chat_id` (String, Unique): Unique identifier for the chat
- `chat_hash` (String): Hash of the chat content
- `title` (String): Title of the conversation
- `create_time` (DateTime): When the chat was created
- `message_count` (Integer): Number of messages in the chat
- `source_file` (String): Source file path
- `position_x`, `position_y` (Float, Optional): Semantic positioning coordinates
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (c:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})
RETURN c
```

#### **Message** Node
Represents individual messages within chats.

**Properties:**
- `message_id` (String, Unique): Unique identifier for the message
- `message_hash` (String): Hash of the message content
- `content` (String): The message content
- `role` (String): "user" or "assistant"
- `timestamp` (DateTime): When the message was sent
- `chat_id` (String): Associated chat ID
- `content_length` (Integer): Length of message content
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (m:Message {message_id: "974dc9c9-ed5a-4346-8d8f-75eec5ddbabc"})
RETURN m
```

#### **Chunk** Node
Represents semantic chunks of messages.

**Properties:**
- `chunk_id` (String, Unique): Unique identifier for the chunk
- `chunk_hash` (String): Hash of the chunk content
- `content` (String): The chunk text content
- `role` (String): "user" or "assistant"
- `token_count` (Integer): Number of tokens in chunk
- `message_hash` (String): Hash of the source message
- `chat_id` (String): Associated chat ID
- `content_length` (Integer): Length of chunk content
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (ch:Chunk {chunk_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a_msg_0_chunk_0"})
RETURN ch
```

#### **Embedding** Node
Represents vector embeddings for chunks.

**Properties:**
- `embedding_hash` (String, Unique): Unique hash for the embedding
- `vector` (List[Float]): Vector embedding for semantic search
- `dimension` (Integer): Dimension of the embedding vector
- `method` (String): Method used for embedding (e.g., "sentence-transformers")
- `chunk_id` (String): Associated chunk ID
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (e:Embedding {embedding_hash: "abc123"})
RETURN e
```

#### **Cluster** Node
Represents semantic clusters of related chunks.

**Properties:**
- `cluster_id` (Integer, Unique): Unique cluster identifier
- `umap_x`, `umap_y` (Float): UMAP positioning coordinates
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (cl:Cluster {cluster_id: 5})
RETURN cl
```

#### **Tag** Node
Represents semantic tags/categories applied to messages.

**Properties:**
- `tag_hash` (String, Unique): Unique hash for the tag
- `tags` (List[String]): List of tag names
- `topics` (List[String]): List of topic names
- `domain` (String): Domain classification
- `intent` (String): Intent classification
- `sentiment` (String): Sentiment classification
- `complexity` (String): Complexity classification
- `tag_count` (Integer): Number of tags
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (t:Tag {tag_hash: "def456"})
RETURN t
```

#### **Summary** Node
Represents cluster summaries.

**Properties:**
- `summary_hash` (String, Unique): Unique hash for the summary
- `summary` (String): Summary text
- `key_points` (List[String]): Key points from the summary
- `common_tags` (List[String]): Common tags in the cluster
- `topics` (List[String]): Topics covered
- `domain` (String): Domain classification
- `complexity` (String): Complexity classification
- `summary_length` (Integer): Length of summary
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (s:Summary {summary_hash: "ghi789"})
RETURN s
```

#### **ChatSummary** Node
Represents chat summaries.

**Properties:**
- `chat_summary_hash` (String, Unique): Unique hash for the chat summary
- `summary` (String): Summary text
- `key_points` (List[String]): Key points from the summary
- `topics` (List[String]): Topics covered
- `domain` (String): Domain classification
- `complexity` (String): Complexity classification
- `summary_length` (Integer): Length of summary
- `loaded_at` (DateTime): When loaded into Neo4j

**Example:**
```cypher
MATCH (cs:ChatSummary {chat_summary_hash: "jkl012"})
RETURN cs
```

### Relationship Types

#### **Core Relationships**
- **CONTAINS**: `(Chat)-[:CONTAINS]->(Message)` - Chat contains this message
- **HAS_CHUNK**: `(Message)-[:HAS_CHUNK]->(Chunk)` - Message has been chunked into semantic pieces
- **HAS_EMBEDDING**: `(Chunk)-[:HAS_EMBEDDING]->(Embedding)` - Chunk has a vector embedding
- **CONTAINS_CHUNK**: `(Cluster)-[:CONTAINS_CHUNK]->(Chunk)` - Cluster contains this chunk
- **TAGS**: `(Message)-[:TAGS]->(Tag)` - Message is tagged with semantic categories
- **SUMMARIZES**: `(Summary)-[:SUMMARIZES]->(Cluster)` - Summary summarizes this cluster
- **SUMMARIZES_CHAT**: `(ChatSummary)-[:SUMMARIZES_CHAT]->(Chat)` - ChatSummary summarizes this chat

#### **Similarity Relationships**
- **SIMILAR_TO_CHAT_HIGH**: `(Chat)-[:SIMILAR_TO_CHAT_HIGH]->(Chat)` - Chats are highly similar
- **SIMILAR_TO_CHAT_MEDIUM**: `(Chat)-[:SIMILAR_TO_CHAT_MEDIUM]->(Chat)` - Chats are moderately similar
- **SIMILAR_TO_CLUSTER_HIGH**: `(Cluster)-[:SIMILAR_TO_CLUSTER_HIGH]->(Cluster)` - Clusters are highly similar
- **SIMILAR_TO_CLUSTER_MEDIUM**: `(Cluster)-[:SIMILAR_TO_CLUSTER_MEDIUM]->(Cluster)` - Clusters are moderately similar

## 🔍 Common Query Patterns

### 1. Basic Data Exploration

#### Get All Chats with Message Counts
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, c.create_time, c.chat_id, count(m) as message_count
ORDER BY c.create_time DESC
```

#### Get Messages in a Chat
```cypher
MATCH (c:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})-[:CONTAINS]->(m:Message)
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp
```

#### Get Chunks for a Message
```cypher
MATCH (m:Message {message_id: "974dc9c9-ed5a-4346-8d8f-75eec5ddbabc"})-[:HAS_CHUNK]->(ch:Chunk)
RETURN ch.content, ch.chunk_id, ch.token_count
```

### 2. Semantic Analysis Queries

#### Get Messages with Tags
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN m.content, m.role, t.tags, t.domain, t.sentiment
ORDER BY m.timestamp DESC
LIMIT 20
```

#### Find Messages by Domain
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE t.domain = "technology"
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

#### Get Cluster Summaries
```cypher
MATCH (s:Summary)-[:SUMMARIZES]->(cl:Cluster)
RETURN cl.cluster_id, s.summary, s.key_points, s.common_tags
ORDER BY cl.cluster_id
```

#### Get Chat Summaries
```cypher
MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c:Chat)
RETURN c.title, cs.summary, cs.key_points, cs.topics
ORDER BY c.create_time DESC
```

### 3. Similarity Queries

#### Find Similar Chats
```cypher
MATCH (c1:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
RETURN c2.title, c2.chat_id
ORDER BY c2.create_time DESC
```

#### Find Similar Clusters
```cypher
MATCH (cl1:Cluster {cluster_id: 5})-[:SIMILAR_TO_CLUSTER_HIGH]->(cl2:Cluster)
WHERE cl1.cluster_id <> cl2.cluster_id
RETURN cl2.cluster_id, cl2.umap_x, cl2.umap_y
```

### 4. Content Discovery Queries

#### Search Messages by Content
```cypher
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower("python")
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp DESC
```

#### Find Messages by Tags
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "programming")
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

#### Get Messages by Sentiment
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE t.sentiment = "positive"
RETURN m.content, m.role, t.sentiment
ORDER BY m.timestamp DESC
```

### 5. Advanced Analysis Queries

#### Get Complete Message Context
```cypher
MATCH (m:Message {message_id: "974dc9c9-ed5a-4346-8d8f-75eec5ddbabc"})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
RETURN m.content as message_content,
       m.role as message_role,
       c.title as chat_title,
       collect(DISTINCT ch.content) as chunks,
       collect(DISTINCT t.tags) as tags
```

#### Get Chat with Full Analysis
```cypher
MATCH (c:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c.title,
       count(DISTINCT m) as message_count,
       count(DISTINCT ch) as chunk_count,
       collect(DISTINCT t.domain) as domains,
       cs.summary as chat_summary
```

#### Get Cluster Analysis
```cypher
MATCH (cl:Cluster {cluster_id: 5})
OPTIONAL MATCH (cl)-[:CONTAINS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (s:Summary)-[:SUMMARIZES]->(cl)
RETURN cl.cluster_id,
       count(ch) as chunk_count,
       s.summary as cluster_summary,
       s.key_points as key_points
```

### 6. Statistics and Analytics

#### Node Counts
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC
```

#### Relationship Counts
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC
```

#### Average Chunks per Message
```cypher
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH count(m) as message_count, count(ch) as chunk_count
RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message
```

#### Tag Distribution
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
UNWIND t.tags as tag
RETURN tag, count(*) as usage_count
ORDER BY usage_count DESC
LIMIT 20
```

#### Domain Distribution
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN t.domain, count(*) as message_count
ORDER BY message_count DESC
```

### 7. Visualization Queries

#### Chats with Positions
```cypher
MATCH (c:Chat)
WHERE c.position_x IS NOT NULL AND c.position_y IS NOT NULL
RETURN c.chat_id, c.title, c.position_x, c.position_y
ORDER BY c.create_time DESC
```

#### Clusters with Positions
```cypher
MATCH (cl:Cluster)
WHERE cl.umap_x IS NOT NULL AND cl.umap_y IS NOT NULL
RETURN cl.cluster_id, cl.umap_x, cl.umap_y
ORDER BY cl.cluster_id
```

#### Embeddings for Visualization
```cypher
MATCH (e:Embedding)
RETURN e.chunk_id, e.vector, e.dimension
LIMIT 100
```

## 🎯 Practical Use Cases

### 1. Content Discovery

**Find all messages about Python programming:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
```

**Find messages with specific sentiment:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE t.sentiment = "positive"
RETURN m.content, m.role, t.sentiment
ORDER BY m.timestamp DESC
```

### 2. Semantic Analysis

**Get semantic breakdown of a conversation:**
```cypher
MATCH (c:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c.title,
       count(DISTINCT m) as messages,
       count(DISTINCT ch) as chunks,
       collect(DISTINCT t.domain) as domains,
       cs.summary as chat_summary
```

**Find semantically similar conversations:**
```cypher
MATCH (c1:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
RETURN c2.title, c2.chat_id
ORDER BY c2.create_time DESC
```

### 3. Quality Analysis

**Find conversations with rich semantic content:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
WITH c, count(DISTINCT m) as message_count, count(DISTINCT ch) as chunk_count, count(DISTINCT t) as tag_count
WHERE chunk_count > 10 AND tag_count > 5
RETURN c.title, message_count, chunk_count, tag_count
ORDER BY tag_count DESC
```

**Find clusters with the most diverse content:**
```cypher
MATCH (cl:Cluster)-[:CONTAINS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)<-[:HAS_CHUNK]-(m:Message)-[:TAGS]->(t:Tag)
WITH cl, count(DISTINCT ch) as chunk_count, count(DISTINCT t) as tag_count
RETURN cl.cluster_id, chunk_count, tag_count, round(tag_count * 100.0 / chunk_count, 2) as tag_diversity
ORDER BY tag_diversity DESC
```

## 🔧 Performance Tips

### 1. Use Indexes
The system automatically creates indexes on:
- `Chat.chat_id`
- `Message.message_id`
- `Chunk.chunk_id`
- `Embedding.embedding_hash`
- `Cluster.cluster_id`
- `Tag.tag_hash`
- `Summary.summary_hash`
- `ChatSummary.chat_summary_hash`

### 2. Limit Results
Always use `LIMIT` for large result sets:
```cypher
MATCH (m:Message)
RETURN m.content
LIMIT 100
```

### 3. Use Specific Node Types
Query specific node types for better performance:
```cypher
-- Chat queries only
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, count(m) as message_count

-- Tag queries only
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN t.domain, count(m) as message_count
```

## 📈 Statistics Queries

### Database Overview
```cypher
// Node counts
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC

// Relationship counts
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC

// Average chunks per message
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH count(m) as message_count, count(ch) as chunk_count
RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message
```

### Content Statistics
```cypher
// Tag usage statistics
MATCH (m:Message)-[:TAGS]->(t:Tag)
UNWIND t.tags as tag
RETURN tag, count(*) as usage_count
ORDER BY usage_count DESC
LIMIT 20

// Domain distribution
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN t.domain, count(*) as message_count
ORDER BY message_count DESC

// Sentiment distribution
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN t.sentiment, count(*) as message_count
ORDER BY message_count DESC
```

## 🚀 API Integration

The ChatMind API provides these endpoints that use Neo4j queries:

- `GET /api/graph` - Get graph data with filtering
- `GET /api/conversations` - Get raw conversations
- `GET /api/chunks` - Get semantic chunks
- `GET /api/messages/{message_id}/chunks` - Get chunks for a message
- `GET /api/search/semantic` - Search chunks by semantic similarity

Example API call:
```bash
curl "http://localhost:8000/api/graph?limit=100"
```

## 🔍 Debugging Queries

### Check Database Connection
```cypher
RETURN 1 as test
```

### Verify Data Structure
```cypher
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
```

### Check Relationships
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
```

### Verify Message-Chunk Links
```cypher
MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
RETURN count(m) as messages_with_chunks,
       count(ch) as total_chunks
```

### Profile Query Performance
```cypher
PROFILE MATCH (c:Chat)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
RETURN c.title, count(m) as message_count, count(ch) as chunk_count
```

## 🎯 Common Use Cases

### Find Related Content
```cypher
-- All messages about programming
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "programming")
RETURN m.content, m.role ORDER BY m.timestamp DESC

-- Similar chats
MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]->(c2:Chat)
WHERE c1.chat_id = "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"
RETURN c2.title, c2.chat_id

-- Get embeddings for similarity analysis
MATCH (e:Embedding)
RETURN e.chunk_id, e.vector LIMIT 10
```

### Content Discovery
```cypher
-- Most active domains
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN t.domain, count(*) as message_count
ORDER BY message_count DESC LIMIT 10

-- Messages with specific tags
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag IN ["python", "javascript", "react"])
RETURN m.content, t.tags ORDER BY m.timestamp DESC

-- Graph overview (cluster-based)
MATCH (cl:Cluster)
WHERE cl.umap_x IS NOT NULL AND cl.umap_y IS NOT NULL
RETURN cl.cluster_id, cl.umap_x, cl.umap_y
ORDER BY cl.cluster_id
```

### Quality Analysis
```cypher
-- Long conversations (>20 messages)
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
WITH c, count(m) as message_count
WHERE message_count > 20
RETURN c.title, message_count ORDER BY message_count DESC

-- Conversations with many tags (>5 unique tags)
MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:TAGS]->(t:Tag)
WITH c, count(DISTINCT t) as unique_tags
WHERE unique_tags > 5
RETURN c.title, unique_tags ORDER BY unique_tags DESC
```

### Advanced Search Patterns
```cypher
-- Search messages by content
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower("python")
RETURN m.content, m.role ORDER BY m.timestamp DESC

-- Search by tag
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
RETURN m.content, m.role ORDER BY m.timestamp DESC

-- Search by domain
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE t.domain = "technology"
RETURN m.content, m.role ORDER BY m.timestamp DESC
```

### Graph Exploration
```cypher
-- Get chat with all related data
MATCH (c:Chat {chat_id: "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"})
OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c, collect(DISTINCT m) as messages, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs

-- Find similar chats
MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]-(c2:Chat)
WHERE c1.chat_id = "d5bffa6d680deac36fc2021478aa7ff80a6a47f82deb03c7e45d571bdf3b1f9a"
RETURN c2.title, c2.chat_id

-- Chat-message-tag full context
MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c, m, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
```

### Additional Statistics
```cypher
-- Node counts
MATCH (n) RETURN labels(n)[0] as type, count(n) as count ORDER BY count DESC

-- Relationship counts
MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC

-- Average messages per chat
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
WITH c, count(m) as message_count
RETURN avg(message_count) as avg_messages_per_chat

-- Tag distribution with percentage
MATCH (m:Message)-[:TAGS]->(t:Tag)
UNWIND t.tags as tag
WITH tag, count(*) as usage_count
RETURN tag, usage_count
ORDER BY usage_count DESC
```

## 🔍 Advanced Analysis Queries

### 1. Semantic Layer Analysis

**Messages with semantic data:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
RETURN count(DISTINCT m) as messages_with_semantic_data,
       count(DISTINCT ch) as chunks_with_embeddings
```

**Chunk-embedding connectivity:**
```cypher
MATCH (ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
RETURN ch.chunk_id, count(e) as embedding_count
ORDER BY embedding_count DESC
LIMIT 5
```

### 2. Quality and Completeness Analysis

**Orphaned messages (no chat parent):**
```cypher
MATCH (m:Message)
WHERE NOT (m)<-[:CONTAINS]-(:Chat)
RETURN count(m) as orphan_messages
```

**Orphaned chunks (no message parent):**
```cypher
MATCH (ch:Chunk)
WHERE NOT (ch)<-[:HAS_CHUNK]-(:Message)
RETURN count(ch) as orphan_chunks
```

**Duplicate detection:**
```cypher
MATCH (m:Message)
WITH m.message_id AS mid, count(*) AS c
WHERE c > 1
RETURN mid, c
ORDER BY c DESC
```

### 3. Graph Connectivity Analysis

**Chat-message connectivity:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.chat_id, count(m) as message_count
ORDER BY message_count DESC
LIMIT 5
```

**Message-chunk connectivity:**
```cypher
MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)
RETURN m.message_id, count(ch) as chunk_count
ORDER BY chunk_count DESC
LIMIT 5
```

**Message-tag connectivity:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
RETURN m.message_id, count(t) as tag_count
ORDER BY tag_count DESC
LIMIT 5
```

**Cluster-chunk connectivity:**
```cypher
MATCH (cl:Cluster)-[:CONTAINS_CHUNK]->(ch:Chunk)
RETURN cl.cluster_id, count(ch) as chunk_count
ORDER BY chunk_count DESC
LIMIT 5
```

### 4. Full Path Connectivity

**Complete semantic path:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
RETURN c.chat_id, m.message_id, ch.chunk_id, e.embedding_hash
LIMIT 5
```

**Chat with full semantic analysis:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c.title,
       count(DISTINCT m) as message_count,
       count(DISTINCT ch) as chunk_count,
       collect(DISTINCT t.domain) as domains,
       cs.summary as chat_summary
LIMIT 3
```

### 5. Edge Case and Data Absence Handling

**Non-existent nodes:**
```cypher
MATCH (n:NonExistent) RETURN count(n) AS count
```

**Empty result sets:**
```cypher
MATCH (m:Message) WHERE m.content = 'NONEXISTENT_CONTENT' RETURN m
```

**Null property handling:**
```cypher
MATCH (m:Message) WHERE m.content IS NULL RETURN count(m) AS null_content_messages
```

**Empty collections:**
```cypher
MATCH (m:Message) WHERE NOT (m)-[:HAS_CHUNK]->() RETURN count(m) AS messages_without_chunks
```

### 6. Schema Validation

**Node type properties:**
```cypher
MATCH (n)
RETURN labels(n)[0] as node_type, 
       keys(n) as properties,
       count(n) as count
ORDER BY node_type
```

**Critical properties validation:**
```cypher
MATCH (m:Message)
WHERE m.message_id IS NULL OR m.content IS NULL
RETURN count(*) AS bad_messages
```

**Chunk properties validation:**
```cypher
MATCH (ch:Chunk)
WHERE ch.chunk_id IS NULL OR ch.content IS NULL
RETURN count(*) AS bad_chunks
```

**Chat properties validation:**
```cypher
MATCH (c:Chat)
WHERE c.chat_id IS NULL OR c.title IS NULL
RETURN count(*) AS bad_chats
```

## 📊 Performance and Optimization Queries

### 1. Performance Safeguards

**Fast node count query:**
```cypher
MATCH (n) RETURN count(n) as total_nodes
```

**Complex aggregation performance:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:HAS_EMBEDDING]->(e:Embedding)
WITH c, count(DISTINCT e) as embedding_count
RETURN avg(embedding_count) as avg_embeddings_per_chat
```

**Large result set handling:**
```cypher
MATCH (ch:Chunk)
RETURN ch.chunk_id, ch.content
LIMIT 1000
```

### 2. Data Quality Metrics

**Average messages per chat:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
WITH c, count(m) as message_count
RETURN avg(message_count) as avg_messages_per_chat
```

**Tag distribution with percentage:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
UNWIND t.tags as tag
WITH tag, count(*) as usage_count
RETURN tag, usage_count
ORDER BY usage_count DESC
LIMIT 10
```

## 🎨 Visualization and Positioning Queries

### 1. Chat Positioning

**Chats with positions:**
```cypher
MATCH (c:Chat)
WHERE c.position_x IS NOT NULL AND c.position_y IS NOT NULL
RETURN c.chat_id, c.title, c.position_x, c.position_y
ORDER BY c.create_time DESC
LIMIT 5
```

### 2. Cluster Positioning

**Clusters with positions:**
```cypher
MATCH (cl:Cluster)
WHERE cl.umap_x IS NOT NULL AND cl.umap_y IS NOT NULL
RETURN cl.cluster_id, cl.umap_x, cl.umap_y
ORDER BY cl.cluster_id
LIMIT 5
```

### 3. Embedding Visualization

**Embeddings for visualization:**
```cypher
MATCH (e:Embedding)
RETURN e.chunk_id, e.vector, e.dimension
LIMIT 5
```

## 🔍 Search and Discovery Patterns

### 1. Content-Based Search

**Search messages by content:**
```cypher
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower("python")
RETURN m.content, m.role
ORDER BY m.timestamp DESC
LIMIT 5
```

**Search by tag:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
RETURN m.content, m.role
ORDER BY m.timestamp DESC
LIMIT 5
```

**Search by domain:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE t.domain = "technology"
RETURN m.content, m.role
ORDER BY m.timestamp DESC
LIMIT 5
```

### 2. Semantic Discovery

**Find all messages about Python programming:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE ANY(tag IN t.tags WHERE tag CONTAINS "python")
RETURN m.content, m.role, t.tags
ORDER BY m.timestamp DESC
LIMIT 5
```

**Find messages with specific sentiment:**
```cypher
MATCH (m:Message)-[:TAGS]->(t:Tag)
WHERE t.sentiment = "positive"
RETURN m.content, m.role, t.sentiment
ORDER BY m.timestamp DESC
LIMIT 5
```

## 🌐 Graph Exploration Queries

### 1. Full Context Retrieval

**Get chat with all related data:**
```cypher
MATCH (c:Chat)
OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c, collect(DISTINCT m) as messages, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
LIMIT 3
```

**Find similar chats:**
```cypher
MATCH (c1:Chat)-[:SIMILAR_TO_CHAT_HIGH]-(c2:Chat)
RETURN c1.title, c2.title, c2.chat_id
LIMIT 5
```

**Chat-message-tag full context:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:TAGS]->(t:Tag)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (cs:ChatSummary)-[:SUMMARIZES_CHAT]->(c)
RETURN c, m, collect(DISTINCT t) as tags, collect(DISTINCT ch) as chunks, cs
LIMIT 3
```

## 📚 Additional Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Browser](http://localhost:7474) - Web interface for querying
- [ChatMind API Documentation](http://localhost:8000/docs) - API endpoints
- [Graph Visualization](http://localhost:3000) - Interactive graph view
- [Pipeline Overview Documentation](docs/PIPELINE_OVERVIEW_AND_INCREMENTAL.md)

---

*This guide covers the most common query patterns for the ChatMind knowledge graph. For advanced queries or specific use cases, refer to the Neo4j Cypher documentation or explore the graph interactively through the web interface.* 