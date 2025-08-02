# Hash Mapping Analysis Across Pipeline Steps

## 🔍 **Overview**
This document analyzes all hash generation and mapping patterns across the ChatMind pipeline to ensure proper data relationships in Neo4j.

## 📊 **Hash Generation Patterns by Step**

### 1. **Ingestion Step** (`extract_and_flatten.py`)
**File**: `chatmind/pipeline/ingestion/extract_and_flatten.py`

**Hash Generation**:
```python
def _generate_content_hash(self, chat: Dict) -> str:
    normalized_chat = {
        'title': chat['title'],
        'messages': sorted(chat['messages'], key=lambda x: x['content'])
    }
    content = json.dumps(normalized_chat, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `content_hash`: Generated from normalized chat content
- `chat_id`: `f"chat_{content_hash[:16]}"` (for URL mapping)

**Output Structure**:
```json
{
  "content_hash": "abc123...",
  "chat_id": "chat_abc123...",
  "title": "Chat Title",
  "messages": [...]
}
```

### 2. **Chunking Step** (`chunker.py`)
**File**: `chatmind/pipeline/chunking/chunker.py`

**Hash Generation**:
```python
def _generate_message_hash(self, message: Dict) -> str:
    normalized_message = {
        'content': message.get('content', ''),
        'chat_id': message.get('chat_id', ''),
        'message_id': message.get('id', ''),
        'role': message.get('role', '')
    }
    content = json.dumps(normalized_message, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()

def _generate_chunk_hash(self, chunk: Dict) -> str:
    content_str = json.dumps(chunk, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()
```

**Properties Set**:
- `chunk_id`: `f"{chat_id}_msg_{message_index}_chunk_{chunk_index}"`
- `chat_id`: From parent chat
- `message_id`: From parent message
- `message_hash`: Generated from message content
- `chunk_hash`: Generated from chunk content

**Output Structure**:
```json
{
  "chunk_id": "chat_abc123_msg_0_chunk_0",
  "chat_id": "chat_abc123...",
  "message_id": "msg_123...",
  "content": "chunk content",
  "message_hash": "def456...",
  "chunk_hash": "ghi789..."
}
```

### 3. **Tagging Step** (`enhanced_tagger.py`)
**File**: `chatmind/pipeline/tagging/cloud_api/enhanced_tagger.py`

**Hash Generation**:
```python
def _generate_message_hash(self, message: Dict) -> str:
    normalized_message = {
        'content': message.get('content', ''),
        'chat_id': message.get('chat_id', ''),
        'message_id': message.get('id', ''),
        'role': message.get('role', '')
    }
    content = json.dumps(normalized_message, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `message_hash`: Generated from message content (SAME as chunking step)

**Output Structure**:
```json
{
  "message_hash": "def456...",
  "message_id": "msg_123...",
  "chat_id": "chat_abc123...",
  "content": "message content",
  "tags": [...],
  "domain": "technical",
  "complexity": "intermediate"
}
```

### 4. **Tag Propagation Step** (`propagate_tags_to_chunks.py`)
**File**: `chatmind/pipeline/tagging/propagate_tags_to_chunks.py`

**Hash Usage**:
- Uses `message_hash` from chunks to match with tagged messages
- Propagates tags from messages to chunks

**Output Structure**:
```json
{
  "chunk_hash": "ghi789...",
  "chunk_id": "chat_abc123_msg_0_chunk_0",
  "message_id": "msg_123...",
  "chat_id": "chat_abc123...",
  "tags": [...],
  "domain": "technical",
  "complexity": "intermediate",
  "parent_message_hash": "def456..."
}
```

### 5. **Embedding Step** (`embed_chunks.py`)
**File**: `chatmind/pipeline/embedding/local/embed_chunks.py`

**Hash Generation**:
```python
def _generate_chunk_hash(self, chunk: Dict) -> str:
    normalized_chunk = {
        'content': chunk.get('content', ''),
        'chat_id': chunk.get('chat_id', ''),
        'chunk_id': chunk.get('chunk_id', ''),
        'message_ids': chunk.get('message_ids', [])
    }
    content = json.dumps(normalized_chunk, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `chunk_hash`: Generated from chunk content (SAME as chunking step)
- `embedding_hash`: Generated from embedding vector

**Output Structure**:
```json
{
  "chunk_id": "chat_abc123_msg_0_chunk_0",
  "chunk_hash": "ghi789...",
  "embedding": [...],
  "method": "sentence-transformers",
  "embedding_hash": "jkl012..."
}
```

### 6. **Clustering Step** (`clusterer.py`)
**File**: `chatmind/pipeline/clustering/clusterer.py`

**Hash Generation**:
```python
def _generate_embedding_hash(self, embedding: Dict) -> str:
    normalized_embedding = {
        'chunk_id': embedding.get('chunk_id', ''),
        'chat_id': embedding.get('chat_id', ''),
        'content': embedding.get('content', ''),
        'embedding': embedding.get('embedding', [])
    }
    content = json.dumps(normalized_embedding, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `cluster_id`: Generated by HDBSCAN algorithm
- `umap_x`, `umap_y`: 2D coordinates from UMAP
- `chunk_id`: From original embedding

**Output Structure**:
```json
{
  "chunk_id": "chat_abc123_msg_0_chunk_0",
  "cluster_id": 5,
  "umap_x": 0.123,
  "umap_y": 0.456,
  "chunk_hash": "ghi789..."
}
```

### 7. **Chat Summarization Step** (`local_chat_summarizer.py`)
**File**: `chatmind/pipeline/chat_summarization/local/local_chat_summarizer.py`

**Hash Generation**:
```python
def _generate_chat_hash(self, chat_id: str, messages: List[Dict]) -> str:
    normalized_chat = {
        'chat_id': chat_id,
        'message_count': len(messages),
        'message_hashes': [msg.get('id', '') for msg in messages]
    }
    content = json.dumps(normalized_chat, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `chat_id`: Uses `content_hash` from ingestion
- `summary`: Generated summary text
- `domain`, `topics`, `complexity`: Extracted from summary

**Output Structure**:
```json
{
  "chat_id": "abc123...",
  "summary": "This conversation discusses...",
  "domain": "technical",
  "topics": ["programming", "python"],
  "complexity": "intermediate"
}
```

### 8. **Cluster Summarization Step** (`local_enhanced_cluster_summarizer.py`)
**File**: `chatmind/pipeline/cluster_summarization/local/local_enhanced_cluster_summarizer.py`

**Hash Generation**:
```python
def _generate_cluster_hash(self, cluster_id: int, chunk_hashes: List[str]) -> str:
    normalized_cluster = {
        'cluster_id': cluster_id,
        'chunk_hashes': sorted(chunk_hashes)
    }
    content = json.dumps(normalized_cluster, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `cluster_id`: From clustering step
- `summary`: Generated summary text
- `domain`, `topics`, `complexity`: Extracted from summary

**Output Structure**:
```json
{
  "cluster_id": 5,
  "summary": "This cluster contains discussions about...",
  "domain": "technical",
  "topics": ["programming", "python"],
  "complexity": "intermediate"
}
```

### 9. **Chat Positioning Step** (`position_chats.py`)
**File**: `chatmind/pipeline/positioning/position_chats.py`

**Hash Generation**:
```python
def _generate_positioning_hash(self, chat_id: str, summary_hash: str) -> str:
    normalized_positioning = {
        'chat_id': chat_id,
        'summary_hash': summary_hash
    }
    content = json.dumps(normalized_positioning, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `chat_id`: From chat summarization
- `umap_x`, `umap_y`: 2D coordinates from UMAP
- `embedding_hash`: Generated from summary embedding

**Output Structure**:
```json
{
  "chat_id": "abc123...",
  "umap_x": 0.123,
  "umap_y": 0.456,
  "embedding_hash": "mno345..."
}
```

### 10. **Cluster Positioning Step** (`position_clusters.py`)
**File**: `chatmind/pipeline/positioning/position_clusters.py`

**Hash Generation**:
```python
def _generate_positioning_hash(self, cluster_id: str, summary_hash: str) -> str:
    normalized_positioning = {
        'cluster_id': cluster_id,
        'summary_hash': summary_hash
    }
    content = json.dumps(normalized_positioning, sort_keys=True)
    return hashlib.sha256(content.encode()).hexdigest()
```

**Properties Set**:
- `cluster_id`: From cluster summarization
- `umap_x`, `umap_y`: 2D coordinates from UMAP
- `embedding_hash`: Generated from summary embedding

**Output Structure**:
```json
{
  "cluster_id": 5,
  "umap_x": 0.123,
  "umap_y": 0.456,
  "embedding_hash": "pqr678..."
}
```

### 11. **Chat Similarity Step** (`calculate_chat_similarities.py`)
**File**: `chatmind/pipeline/similarity/calculate_chat_similarities.py`

**Hash Generation**:
```python
def _generate_content_hash(self, data: Dict) -> str:
    content_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()
```

**Properties Set**:
- `chat1_id`, `chat2_id`: From chat positioning
- `similarity`: Cosine similarity score
- `hash`: Generated from similarity data

**Output Structure**:
```json
{
  "chat1_id": "abc123...",
  "chat2_id": "def456...",
  "similarity": 0.85,
  "hash": "stu901..."
}
```

### 12. **Cluster Similarity Step** (`calculate_cluster_similarities.py`)
**File**: `chatmind/pipeline/similarity/calculate_cluster_similarities.py`

**Hash Generation**:
```python
def _generate_content_hash(self, data: Dict) -> str:
    content_str = json.dumps(data, sort_keys=True)
    return hashlib.sha256(content_str.encode()).hexdigest()
```

**Properties Set**:
- `cluster1_id`, `cluster2_id`: From cluster positioning
- `similarity`: Cosine similarity score
- `hash`: Generated from similarity data

**Output Structure**:
```json
{
  "cluster1_id": 5,
  "cluster2_id": 12,
  "similarity": 0.78,
  "hash": "vwx234..."
}
```

## 🔗 **Neo4j Relationship Mapping**

### **Complete Node and Relationship Structure**:

1. **Chat Nodes**:
   - ✅ Uses `content_hash` as `chat_hash`
   - ✅ Sets `chat_id` property
   - ✅ Creates `CONTAINS` relationship: `Chat -> Message`

2. **Message Nodes**:
   - ✅ Uses `message_id` as primary key
   - ✅ Sets `message_hash` property
   - ✅ Sets `chat_id` property
   - ✅ Creates `HAS_CHUNK` relationship: `Message -> Chunk`

3. **Chunk Nodes**:
   - ✅ Uses `chunk_id` as primary key
   - ✅ Sets `chunk_hash` property
   - ✅ Sets `chat_id` and `message_hash` properties
   - ✅ Creates `HAS_EMBEDDING` relationship: `Chunk -> Embedding`

4. **Embedding Nodes**:
   - ✅ Uses `embedding_hash` as primary key
   - ✅ Sets `chunk_id` property
   - ✅ Creates `BELONGS_TO_CLUSTER` relationship: `Embedding -> Cluster`

5. **Cluster Nodes**:
   - ✅ Uses `cluster_id` as primary key
   - ✅ Sets `umap_x`, `umap_y` properties
   - ✅ Creates `CONTAINS_CHUNK` relationship: `Cluster -> Chunk`

6. **Tag Nodes**:
   - ✅ Uses `tag_hash` as primary key
   - ✅ Sets `tags`, `domain`, `complexity` properties
   - ✅ Creates `TAGGED_WITH` relationship: `Tag -> Message`

7. **Summary Nodes**:
   - ✅ Uses `summary_hash` as primary key
   - ✅ Sets `summary`, `domain`, `topics` properties
   - ✅ Creates `SUMMARIZES` relationship: `Summary -> Cluster`

8. **Chat Summary Nodes**:
   - ✅ Uses `chat_summary_hash` as primary key
   - ✅ Sets `summary`, `domain`, `topics` properties
   - ✅ Creates `SUMMARIZES_CHAT` relationship: `ChatSummary -> Chat`

9. **Positioning Nodes**:
   - ✅ Chat positions: `umap_x`, `umap_y` properties on Chat nodes
   - ✅ Cluster positions: `umap_x`, `umap_y` properties on Cluster nodes

10. **Similarity Relationships**:
    - ✅ `SIMILAR_TO_CHAT_HIGH`: High similarity between chats
    - ✅ `SIMILAR_TO_CHAT_MEDIUM`: Medium similarity between chats
    - ✅ `SIMILAR_TO_CLUSTER_HIGH`: High similarity between clusters
    - ✅ `SIMILAR_TO_CLUSTER_MEDIUM`: Medium similarity between clusters

## 🚨 **Critical Issues Found**

### **Issue 1: Property Mismatches**
- **Ingestion**: Sets `content_hash` but loading expects `chat_hash`
- **Chunking**: Sets `message_hash` but loading expects `message_id`
- **Embedding**: Sets `chunk_hash` but loading expects `chunk_id`

### **Issue 2: Missing Properties**
- **Chats**: Missing `chat_id` property
- **Messages**: Missing `chat_id` property
- **Chunks**: Missing `chat_id` and `message_hash` properties

### **Issue 3: Relationship Direction**
- **Current**: All relationships are correctly directed
- **Fixed**: `Chat -> Message -> Chunk -> Embedding`

## ✅ **Hash Consistency Verification**

### **Message Hash Consistency**:
- ✅ **Chunking**: Uses same hash generation as tagging
- ✅ **Tagging**: Uses same hash generation as chunking
- ✅ **Propagation**: Uses `message_hash` from chunks to match tags

### **Chunk Hash Consistency**:
- ✅ **Chunking**: Generates `chunk_hash` from chunk content
- ✅ **Embedding**: Uses same `chunk_hash` for tracking
- ✅ **Loading**: Uses `chunk_id` as primary key, `chunk_hash` as property

### **Chat Hash Consistency**:
- ✅ **Ingestion**: Generates `content_hash` from chat content
- ✅ **Loading**: Uses `content_hash` as `chat_hash`

## 🔧 **Required Fixes**

### **1. Update Loading Script Properties**:
```python
# Chat nodes
SET c.chat_id = $chat_id,  # Add this

# Message nodes  
SET m.chat_id = $chat_id,  # Add this

# Chunk nodes
SET ch.chat_id = $chat_id,  # Add this
SET ch.message_hash = $message_hash,  # Add this
```

### **2. Ensure Property Mapping**:
```python
# From ingestion data
chat_id = chat.get('chat_id', chat.get('content_hash', ''))

# From chunking data
message_hash = chunk.get('message_hash', '')

# From embedding data
chunk_id = embedding.get('chunk_id', '')
```

## 📋 **Verification Checklist**

- [ ] **Ingestion**: `content_hash` → `chat_hash` mapping
- [ ] **Chunking**: `message_hash` consistency across steps
- [ ] **Tagging**: `message_hash` matches chunking step
- [ ] **Propagation**: `message_hash` lookup works
- [ ] **Embedding**: `chunk_hash` consistency
- [ ] **Loading**: All properties mapped correctly
- [ ] **Neo4j**: Relationships created with correct directions

## 🎯 **Expected Neo4j Structure**

```
(Chat {chat_hash: "abc123", chat_id: "chat_abc123", umap_x: 0.1, umap_y: 0.2})
    -[:CONTAINS]->
(Message {message_id: "msg_123", message_hash: "def456", chat_id: "chat_abc123"})
    -[:HAS_CHUNK]->
(Chunk {chunk_id: "chunk_0", chunk_hash: "ghi789", chat_id: "chat_abc123", message_hash: "def456"})
    -[:HAS_EMBEDDING]->
(Embedding {embedding_hash: "jkl012", chunk_id: "chunk_0"})
    -[:BELONGS_TO_CLUSTER]->
(Cluster {cluster_id: 5, umap_x: 0.3, umap_y: 0.4})
    -[:CONTAINS_CHUNK]->
(Chunk {chunk_id: "chunk_0"})

(Tag {tag_hash: "tag_123", tags: ["python", "programming"], domain: "technical"})
    -[:TAGGED_WITH]->
(Message {message_id: "msg_123"})

(Summary {summary_hash: "sum_456", summary: "Cluster about Python programming", domain: "technical"})
    -[:SUMMARIZES]->
(Cluster {cluster_id: 5})

(ChatSummary {chat_summary_hash: "chat_sum_789", summary: "Chat about Python", domain: "technical"})
    -[:SUMMARIZES_CHAT]->
(Chat {chat_hash: "abc123"})

(Chat {chat_hash: "abc123"})
    -[:SIMILAR_TO_CHAT_HIGH]->
(Chat {chat_hash: "def456"})

(Cluster {cluster_id: 5})
    -[:SIMILAR_TO_CLUSTER_HIGH]->
(Cluster {cluster_id: 12})
```

This structure ensures proper traversal and relationship integrity across all pipeline steps. 