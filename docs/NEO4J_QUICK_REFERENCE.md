# Neo4j Quick Reference for ChatMind

## 🚀 Most Common Queries

### Basic Node Queries
```cypher
-- Get all chats
MATCH (c:Chat) RETURN c.title, c.create_time ORDER BY c.create_time DESC

-- Get all topics
MATCH (t:Topic) RETURN t.name, t.size ORDER BY t.size DESC

-- Get all tags
MATCH (tag:Tag) RETURN tag.name, tag.count ORDER BY tag.count DESC
```

### Visualization & UMAP Queries
```cypher
-- Chats with UMAP positions
MATCH (c:Chat)
WHERE c.x IS NOT NULL AND c.y IS NOT NULL
RETURN c.chat_id, c.title, c.x, c.y ORDER BY c.create_time DESC

-- Topics with UMAP positions
MATCH (t:Topic)
WHERE t.x IS NOT NULL AND t.y IS NOT NULL
RETURN t.topic_id, t.name, t.size, t.x, t.y ORDER BY t.size DESC

-- All nodes with coordinates
MATCH (n)
WHERE n.x IS NOT NULL AND n.y IS NOT NULL
RETURN labels(n)[0] as node_type, n.x, n.y ORDER BY node_type, n.x
```

### Relationship Queries
```cypher
-- Get messages in a chat
MATCH (c:Chat {chat_id: "chat_123"})-[:CONTAINS]->(m:Message)
RETURN m.content, m.role ORDER BY m.timestamp

-- Get tags for a message
MATCH (m:Message {message_id: "msg_456"})-[:TAGGED_WITH]->(tag:Tag)
RETURN tag.name

-- Get topic for a message
MATCH (t:Topic)-[:SUMMARIZES]->(m:Message {message_id: "msg_456"})
RETURN t.name, t.top_words
```

### Search Queries
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

### Aggregation Queries
```cypher
-- Count messages per chat
MATCH (c:Chat)-[:CONTAINS]->(m:Message)
RETURN c.title, count(m) as message_count ORDER BY message_count DESC

-- Most popular tags
MATCH (tag:Tag) RETURN tag.name, tag.count ORDER BY tag.count DESC LIMIT 10

-- Topic distribution
MATCH (t:Topic) RETURN t.name, t.size ORDER BY t.size DESC
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

## 📊 Statistics Queries

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

## 🔍 Debugging Queries

```cypher
-- Test connection
RETURN 1 as test

-- Check data exists
MATCH (n) RETURN labels(n)[0] as type, count(n) as count

-- Profile query performance
PROFILE MATCH (c:Chat)-[:CONTAINS]->(m:Message) RETURN c.title, count(m)
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

## ⚡ Performance Tips

1. **Always use LIMIT** for large result sets
2. **Use parameters** for better performance: `{chat_id: $chat_id}`
3. **Avoid Cartesian products** with OPTIONAL MATCH
4. **Use indexes** (automatically created on unique properties)
5. **Use `IS NOT NULL`** instead of `exists()` for property checks
6. **Use `WITH` clauses** for complex aggregations to avoid window functions

## 🔗 API Endpoints

- `GET /graph?limit=100&node_types=Topic,Chat`
- `GET /topics`
- `GET /chats`
- `GET /chats/{chat_id}/messages`
- `GET /search?query=python&limit=50`

## 📚 Resources

- **Neo4j Browser**: http://localhost:7474
- **API Docs**: http://localhost:8000/docs
- **Graph View**: http://localhost:3000
- **Full Guide**: [NEO4J_QUERY_GUIDE.md](NEO4J_QUERY_GUIDE.md) 