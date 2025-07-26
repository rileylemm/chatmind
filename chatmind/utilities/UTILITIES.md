# ChatMind Utilities

This directory contains utility scripts for maintaining and enhancing the ChatMind Neo4j graph database.

## Scripts

### `create_has_chunk_relationships.py`
Creates `HAS_CHUNK` relationships between `Message` and `Chunk` nodes in the dual layer graph.

**Purpose**: Links raw message data to semantic chunk data, enabling cross-layer queries.

**Usage**:
```bash
python3 chatmind/utilities/create_has_chunk_relationships.py
```

**What it does**:
- Finds all `Chunk` nodes with `source_message_id` properties
- Extracts the actual `message_id` from the `source_message_id`
- Creates `(Message)-[:HAS_CHUNK]->(Chunk)` relationships
- Processes relationships in batches for efficiency

### `create_chat_similarity.py`
Creates `SIMILAR_TO` relationships between `Chat` nodes based on shared topics.

**Purpose**: Enables discovery of related conversations and chat clustering.

**Usage**:
```bash
python3 chatmind/utilities/create_chat_similarity.py
```

**What it does**:
- Finds chats that share common topics via their chunks
- Calculates similarity scores based on topic overlap
- Creates `(Chat)-[:SIMILAR_TO]->(Chat)` relationships
- Uses a threshold of 0.1 (10% topic overlap) by default

## Integration with Pipeline

These utilities are designed to work with the main ChatMind pipeline:

1. **Primary Loading**: The main pipeline (`chatmind/neo4j_loader/load_graph.py`) now includes chat similarity creation
2. **Manual Maintenance**: These scripts can be run manually if relationships need to be recreated
3. **Troubleshooting**: Useful for fixing missing relationships or testing specific functionality

## Dependencies

- Neo4j database connection (via environment variables)
- Python packages: `neo4j`, `python-dotenv`, `jsonlines`
- Existing ChatMind data files in `data/processed/`

## Environment Variables

Ensure these are set in your `.env` file:
- `NEO4J_URI`
- `NEO4J_USER` 
- `NEO4J_PASSWORD` 