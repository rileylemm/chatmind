# Neo4j Query Guide for ChatMind - Dual Layer Graph Strategy

This guide provides comprehensive information about querying the ChatMind knowledge graph in Neo4j with the **Dual Layer Graph Strategy**. It covers the graph schema, common query patterns, and practical examples for exploring your ChatGPT conversations across both raw and semantic layers.

## 📊 Graph Schema - Dual Layer Strategy

### Layer 1: Raw Layer (No Chunking)

#### **Chat** Node
Represents individual ChatGPT conversations.

**Properties:**
- `chat_id` (String, Unique): Unique identifier for the chat
- `title` (String): Title of the conversation
- `create_time` (DateTime): When the chat was created
- `update_time` (DateTime): When the chat was last updated
- `data_lake_id` (String): Internal data lake identifier
- `x`, `y` (Float, Optional): Semantic positioning coordinates

**Example:**
```cypher
MATCH (c:Chat {chat_id: "chat_123"})
RETURN c
```

#### **Message** Node
Represents individual messages within chats.

**Properties:**
- `message_id` (String, Unique): Unique identifier for the message
- `content` (String): The message content
- `role` (String): "user" or "assistant"
- `timestamp` (DateTime): When the message was sent
- `chat_id` (String): Associated chat ID

**Example:**
```cypher
MATCH (m:Message {message_id: "msg_456"})
RETURN m
```

### Layer 2: Chunk Layer (Chunked + Embedded)

#### **Chunk** Node
Represents semantic chunks of messages with embeddings.

**Properties:**
- `chunk_id` (String, Unique): Unique identifier for the chunk
- `text` (String): The chunk text content
- `embedding` (List[Float]): Vector embedding for semantic search
- `source_message_id` (String): ID of the original message
- `cluster_id` (Integer): Associated topic cluster ID
- `chat_id` (String): Associated chat ID

**Example:**
```cypher
MATCH (ch:Chunk {chunk_id: "msg_456_abc123"})
RETURN ch
```

### Semantic Layer (Tags & Topics)

#### **Topic** Node
Represents semantic clusters of related chunks.

**Properties:**
- `topic_id` (Integer, Unique): Unique topic identifier
- `name` (String): Human-readable topic name
- `size` (Integer): Number of chunks in this topic
- `top_words` (List[String]): Most representative words
- `sample_titles` (List[String]): Sample chat titles
- `x`, `y` (Float, Optional): Semantic positioning coordinates

**Example:**
```cypher
MATCH (t:Topic {topic_id: 5})
RETURN t
```

#### **Tag** Node
Represents tags/categories applied to chunks.

**Properties:**
- `name` (String, Unique): Tag name (e.g., "#python", "#philosophy")
- `count` (Integer): Number of chunks with this tag

**Example:**
```cypher
MATCH (tag:Tag {name: "python"})
RETURN tag
```

### Relationship Types

#### **Raw Layer Relationships**
- **CONTAINS**: `(Chat)-[:CONTAINS]->(Message)` - Chat contains this message
- **REPLIES_TO**: `(Message)-[:REPLIES_TO]->(Message)` - Message is a reply to another message

#### **Cross-Layer Relationships**
- **HAS_CHUNK**: `(Message)-[:HAS_CHUNK]->(Chunk)` - Message has been chunked into semantic pieces

#### **Semantic Layer Relationships**
- **TAGGED_WITH**: `(Chunk)-[:TAGGED_WITH]->(Tag)` - Chunk is tagged with category
- **SUMMARIZES**: `(Topic)-[:SUMMARIZES]->(Chunk)` - Topic summarizes/represents this chunk
- **HAS_TOPIC**: `(Chat)-[:HAS_TOPIC]->(Topic)` - Chat contains messages from this topic
- **SIMILAR_TO**: `(Chat)-[:SIMILAR_TO]->(Chat)` - Chats are semantically similar

## 🔍 Common Query Patterns - Dual Layer

### 1. Raw Layer Queries

#### Get All Chats with Message Counts
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, c.create_time, c.chat_id, count(m) as message_count
ORDER BY c.create_time DESC
```

#### Get Messages in a Chat
```cypher
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
RETURN m.content, m.role, m.timestamp
ORDER BY m.timestamp
```

#### Get Conversation Thread
```cypher
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:REPLIES_TO]->(parent:Message)
RETURN m.content, m.role, m.timestamp, parent.message_id as parent_id
ORDER BY m.timestamp
```

### 2. Chunk Layer Queries

#### Get All Chunks with Embeddings
```cypher
MATCH (ch:Chunk)
WHERE ch.embedding IS NOT NULL
RETURN ch.text, ch.source_message_id, ch.cluster_id
LIMIT 100
```

#### Get Chunks for a Specific Message
```cypher
MATCH (m:Message {message_id: "msg_456"})-[:HAS_CHUNK]->(ch:Chunk)
RETURN ch.text, ch.chunk_id, ch.cluster_id
```

#### Get Chunks by Topic
```cypher
MATCH (t:Topic {topic_id: 5})-[:SUMMARIZES]->(ch:Chunk)
RETURN ch.text, ch.source_message_id, t.name
```

### 3. Cross-Layer Queries

#### Get Message with Its Chunks
```cypher
MATCH (m:Message {message_id: "msg_456"})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
RETURN m.content, m.role, 
       collect(DISTINCT ch.text) as chunks,
       collect(DISTINCT tag.name) as tags
```

#### Get Chat with Messages and Chunks
```cypher
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
RETURN c.title, m.content, m.role,
       collect(DISTINCT ch.text) as chunks,
       collect(DISTINCT tag.name) as tags
```

#### Get Semantic Analysis for a Chat
```cypher
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(ch)
RETURN c.title,
       count(DISTINCT m) as message_count,
       count(DISTINCT ch) as chunk_count,
       collect(DISTINCT tag.name) as all_tags,
       collect(DISTINCT t.name) as all_topics
```

### 4. Semantic Layer Queries

#### Get All Topics with Chunk Counts
```cypher
MATCH (t:Topic)-[:SUMMARIZES]->(ch:Chunk)
RETURN t.name, t.size, count(ch) as chunk_count, t.top_words
ORDER BY chunk_count DESC
```

#### Get Tags with Chunk Counts
```cypher
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag)
RETURN tag.name, count(ch) as chunk_count
ORDER BY chunk_count DESC
```

#### Get Chunks by Tag
```cypher
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN ch.text, ch.source_message_id, tag.name
ORDER BY ch.source_message_id
```

### 5. Advanced Dual Layer Queries

#### Find Similar Content Across Layers
```cypher
MATCH (ch1:Chunk)-[:TAGGED_WITH]->(tag:Tag)
MATCH (ch2:Chunk)-[:TAGGED_WITH]->(tag)
WHERE ch1.chunk_id <> ch2.chunk_id
RETURN ch1.text, ch2.text, tag.name
LIMIT 20
```

#### Get Message Context with Semantic Analysis
```cypher
MATCH (m:Message {message_id: "msg_456"})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(ch)
OPTIONAL MATCH (c:Chat)-[:CONTAINS]->(m)
RETURN m.content as message_content,
       m.role as message_role,
       c.title as chat_title,
       collect(DISTINCT ch.text) as semantic_chunks,
       collect(DISTINCT tag.name) as semantic_tags,
       collect(DISTINCT t.name) as semantic_topics
```

#### Cross-Layer Search
```cypher
MATCH (m:Message)
WHERE toLower(m.content) CONTAINS toLower("python")
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(ch)
RETURN m.content, m.role,
       collect(DISTINCT ch.text) as chunks,
       collect(DISTINCT tag.name) as tags,
       collect(DISTINCT t.name) as topics
```

### 6. Aggregation Queries

#### Message to Chunk Statistics
```cypher
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH m, count(ch) as chunk_count
RETURN avg(chunk_count) as avg_chunks_per_message,
       max(chunk_count) as max_chunks_per_message,
       min(chunk_count) as min_chunks_per_message
```

#### Topic Distribution by Chunks
```cypher
MATCH (t:Topic)-[:SUMMARIZES]->(ch:Chunk)
RETURN t.name, count(ch) as chunk_count,
       round(count(ch) * 100.0 / sum(count(ch)) OVER (), 2) as percentage
ORDER BY chunk_count DESC
```

#### Tag Co-occurrence in Chunks
```cypher
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag1:Tag)
MATCH (ch)-[:TAGGED_WITH]->(tag2:Tag)
WHERE tag1.name < tag2.name
RETURN tag1.name, tag2.name, count(ch) as co_occurrence
ORDER BY co_occurrence DESC
```

### 7. Search and Discovery Queries

#### Semantic Search by Chunk Content
```cypher
MATCH (ch:Chunk)
WHERE toLower(ch.text) CONTAINS toLower("machine learning")
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(ch)
RETURN ch.text, ch.source_message_id,
       collect(DISTINCT tag.name) as tags,
       collect(DISTINCT t.name) as topics
```

#### Find Messages by Semantic Tags
```cypher
MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN m.content, m.role, ch.text, tag.name
ORDER BY m.timestamp DESC
```

#### Find Related Topics
```cypher
MATCH (t1:Topic)-[:SUMMARIZES]->(ch:Chunk)<-[:SUMMARIZES]-(t2:Topic)
WHERE t1.topic_id <> t2.topic_id
RETURN t1.name, t2.name, count(ch) as shared_chunks
ORDER BY shared_chunks DESC
```

### 8. Visualization Queries

#### Chats with UMAP Positions
```cypher
MATCH (c:Chat)
WHERE c.x IS NOT NULL AND c.y IS NOT NULL
RETURN c.chat_id, c.title, c.x, c.y
ORDER BY c.create_time DESC
```

#### Topics with UMAP Positions
```cypher
MATCH (t:Topic)
WHERE t.x IS NOT NULL AND t.y IS NOT NULL
RETURN t.topic_id, t.name, t.size, t.x, t.y, t.top_words
ORDER BY t.size DESC
```

#### Chunk Embeddings for Visualization
```cypher
MATCH (ch:Chunk)
WHERE ch.embedding IS NOT NULL
RETURN ch.chunk_id, ch.text, ch.embedding
LIMIT 100
```

## 🎯 Practical Use Cases - Dual Layer

### 1. Content Discovery

**Find all chunks about Python programming:**
```cypher
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN ch.text, ch.source_message_id
ORDER BY ch.source_message_id
```

**Find messages that contain specific semantic content:**
```cypher
MATCH (m:Message)-[:HAS_CHUNK]->(ch:Chunk)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN m.content, m.role, ch.text
ORDER BY m.timestamp DESC
```

### 2. Semantic Analysis

**Get semantic breakdown of a conversation:**
```cypher
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(ch)
RETURN c.title,
       count(DISTINCT m) as messages,
       count(DISTINCT ch) as chunks,
       collect(DISTINCT tag.name) as semantic_tags,
       collect(DISTINCT t.name) as semantic_topics
```

**Find semantically similar conversations:**
```cypher
MATCH (c1:Chat)-[:HAS_TOPIC]->(t:Topic)<-[:HAS_TOPIC]-(c2:Chat)
WHERE c1.chat_id = "chat_123" AND c1.chat_id <> c2.chat_id
RETURN c2.title, t.name, count(t) as shared_topics
ORDER BY shared_topics DESC
```

### 3. Quality Analysis

**Find conversations with rich semantic content:**
```cypher
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
WITH c, count(DISTINCT m) as message_count, count(DISTINCT ch) as chunk_count, count(DISTINCT tag) as tag_count
WHERE chunk_count > 10 AND tag_count > 5
RETURN c.title, message_count, chunk_count, tag_count
ORDER BY tag_count DESC
```

**Find topics with the most diverse content:**
```cypher
MATCH (t:Topic)-[:SUMMARIZES]->(ch:Chunk)
OPTIONAL MATCH (ch)-[:TAGGED_WITH]->(tag:Tag)
WITH t, count(DISTINCT ch) as chunk_count, count(DISTINCT tag) as tag_count
RETURN t.name, chunk_count, tag_count, round(tag_count * 100.0 / chunk_count, 2) as tag_diversity
ORDER BY tag_diversity DESC
```

## 🔧 Performance Tips

### 1. Use Indexes
The system automatically creates indexes on:
- `Chat.chat_id`
- `Message.message_id`
- `Chunk.chunk_id`
- `Chunk.source_message_id`
- `Topic.topic_id`
- `Tag.name`

### 2. Layer-Specific Queries
For better performance, query specific layers:
```cypher
-- Raw layer only
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, count(m) as message_count

-- Chunk layer only
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag)
RETURN tag.name, count(ch) as chunk_count
```

### 3. Limit Cross-Layer Joins
Use `OPTIONAL MATCH` carefully for cross-layer queries:
```cypher
MATCH (m:Message {message_id: $message_id})
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
RETURN m, collect(ch) as chunks
```

## 📈 Statistics Queries

### Dual Layer Statistics
```cypher
// Node counts by layer
MATCH (n)
RETURN labels(n)[0] as node_type, count(n) as count
ORDER BY count DESC

// Relationship counts
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
ORDER BY count DESC

// Cross-layer statistics
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH count(m) as message_count, count(ch) as chunk_count
RETURN message_count, chunk_count, 
       round(chunk_count * 100.0 / message_count, 2) as chunk_percentage
```

### Content Statistics
```cypher
// Average chunks per message
MATCH (m:Message)
OPTIONAL MATCH (m)-[:HAS_CHUNK]->(ch:Chunk)
WITH count(m) as message_count, count(ch) as chunk_count
RETURN round(chunk_count * 100.0 / message_count, 2) as avg_chunks_per_message

// Tag usage statistics
MATCH (ch:Chunk)-[:TAGGED_WITH]->(tag:Tag)
RETURN avg(tag.count) as avg_tag_usage,
       max(tag.count) as max_tag_usage,
       min(tag.count) as min_tag_usage
```

## 🚀 API Integration

The ChatMind API provides these endpoints that use Neo4j queries:

- `GET /api/graph` - Get graph data with layer filtering
- `GET /api/conversations` - Get raw conversations
- `GET /api/chunks` - Get semantic chunks
- `GET /api/messages/{message_id}/chunks` - Get chunks for a message
- `GET /api/search/semantic` - Search chunks by semantic similarity

Example API call:
```bash
curl "http://localhost:8000/api/graph?layer=both&limit=100"
```

## 🔍 Debugging Queries

### Check Database Connection
```cypher
RETURN 1 as test
```

### Verify Dual Layer Data
```cypher
MATCH (n)
RETURN labels(n)[0] as type, count(n) as count
```

### Check Cross-Layer Relationships
```cypher
MATCH ()-[r]->()
RETURN type(r) as relationship_type, count(r) as count
```

### Verify Chunk-Message Links
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
-- All messages about Python
MATCH (m:Message)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN m.content, m.role ORDER BY m.timestamp DESC

-- Chats with similar topics
MATCH (c1:Chat)-[:HAS_TOPIC]->(t:Topic)<-[:HAS_TOPIC]-(c2:Chat)
WHERE c1.chat_id = "chat_123" AND c1.chat_id <> c2.chat_id
RETURN c2.title, t.name

-- Get message embeddings (for debugging/similarity)
MATCH (m:Message)
WHERE m.embedding IS NOT NULL
RETURN m.message_id, m.content, m.embedding LIMIT 10
```

### Content Discovery
```cypher
-- Most active topics
MATCH (t:Topic) RETURN t.name, t.size, t.sample_titles ORDER BY t.size DESC LIMIT 10

-- Messages with specific tags
MATCH (m:Message)-[:TAGGED_WITH]->(tag:Tag)
WHERE tag.name IN ["python", "javascript", "react"]
RETURN m.content, tag.name ORDER BY m.timestamp DESC

-- Graph UMAP overview (topic-based)
MATCH (t:Topic)
WHERE t.x IS NOT NULL AND t.y IS NOT NULL
RETURN t.name, t.topic_id, t.size, t.x, t.y, t.top_words ORDER BY t.size DESC
```

### Quality Analysis
```cypher
-- Long conversations (>20 messages)
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
WITH c, count(m) as message_count
WHERE message_count > 20
RETURN c.title, message_count ORDER BY message_count DESC

-- Conversations with many tags (>5 unique tags)
MATCH (c:Chat)-[:CONTAINS]->(m:Message)-[:TAGGED_WITH]->(tag:Tag)
WITH c, count(DISTINCT tag) as unique_tags
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
MATCH (m:Message)-[:TAGGED_WITH]->(tag:Tag {name: "python"})
RETURN m.content, m.role ORDER BY m.timestamp DESC

-- Search by topic
MATCH (t:Topic)-[:SUMMARIZES]->(m:Message)
WHERE t.name CONTAINS "programming"
RETURN t.name, m.content
```

### Graph Exploration
```cypher
-- Get chat with all related data
MATCH (c:Chat {chat_id: "chat_123"})
OPTIONAL MATCH (c)-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (t:Topic)-[:SUMMARIZES]->(m)
RETURN c, collect(DISTINCT m) as messages, collect(DISTINCT tag) as tags

-- Find similar chats
MATCH (c1:Chat)-[:SIMILAR_TO]-(c2:Chat)
WHERE c1.chat_id = "chat_123"
RETURN c2.title, c2.chat_id

-- Chat-topic-message full context
MATCH (c:Chat {chat_id: $chat_id})-[:CONTAINS]->(m:Message)
OPTIONAL MATCH (m)-[:TAGGED_WITH]->(tag:Tag)
OPTIONAL MATCH (c)-[:HAS_TOPIC]->(t:Topic)
RETURN c, m, collect(DISTINCT tag) as tags, collect(DISTINCT t) as topics
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

-- Topic distribution with percentage
MATCH (t:Topic)
WITH t, sum(t.size) as total_size
RETURN t.name, t.size, round(t.size * 100.0 / total_size, 2) as percentage
ORDER BY t.size DESC
```

## 📚 Additional Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Browser](http://localhost:7474) - Web interface for querying
- [ChatMind API Documentation](http://localhost:8000/docs) - API endpoints
- [Graph Visualization](http://localhost:3000) - Interactive graph view
- [Dual Layer Strategy Documentation](docs/DUAL_LAYER_GRAPH_STRATEGY.md)

---

*This guide covers the most common query patterns for the ChatMind dual layer knowledge graph. For advanced queries or specific use cases, refer to the Neo4j Cypher documentation or explore the graph interactively through the web interface.* 