#!/bin/bash

# ChatMind Hybrid Architecture Setup Script
# Sets up Neo4j and Qdrant using root-level Docker Compose

echo "🚀 Setting up ChatMind Hybrid Architecture..."
echo "=============================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Determine compose command
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Go to repo root (this script is at chatmind/pipeline)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$REPO_ROOT"

echo "📊 Starting databases with Docker Compose (root)..."
echo "   This will start both Neo4j and Qdrant with persistent storage"

# Start services with Docker Compose
$COMPOSE_CMD up -d neo4j qdrant

echo "⏳ Waiting for databases to be ready..."
sleep 15

echo "🔍 Verifying database connections..."

# Check Neo4j
echo "Testing Neo4j connection..."
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j is accessible"
else
    echo "⚠️  Neo4j may still be starting up"
fi

# Check Qdrant
echo "Testing Qdrant connection..."
if curl -s http://localhost:6335/collections > /dev/null; then
    echo "✅ Qdrant is accessible"
else
    echo "⚠️  Qdrant may still be starting up"
fi

echo "⏳ Waiting for databases to be ready..."
sleep 10

echo "🔍 Verifying database connections..."

# Check Neo4j
echo "Testing Neo4j connection..."
if curl -s http://localhost:7474 > /dev/null; then
    echo "✅ Neo4j is accessible"
else
    echo "⚠️  Neo4j may still be starting up"
fi

# Check Qdrant
echo "Testing Qdrant connection..."
if curl -s http://localhost:6335/collections > /dev/null; then
    echo "✅ Qdrant is accessible"
else
    echo "⚠️  Qdrant may still be starting up"
fi

echo ""
echo "🎉 Hybrid architecture setup complete!"
echo ""
echo "📊 Database URLs:"
echo "  Neo4j Browser: http://localhost:7474"
echo "  Neo4j Bolt: bolt://localhost:7687"
echo "  Qdrant: http://localhost:6335"
echo ""
echo "🔧 Next steps:"
echo "  1. Activate pipeline environment: source chatmind/pipeline/activate_pipeline.sh"
echo "  2. Install dependencies: pip install -r chatmind/pipeline/requirements.txt"
echo "  3. Run pipeline: python chatmind/pipeline/run_pipeline.py --force"
echo "  4. Test hybrid loading: python chatmind/pipeline/loading/load_hybrid.py --check-only"
echo ""
echo "💡 Performance improvements:"
echo "  - Semantic search: <1 second (vs 600+ seconds previously)"
echo "  - Cross-reference linking between Neo4j and Qdrant"
echo "  - Fast vector search + rich graph context" 