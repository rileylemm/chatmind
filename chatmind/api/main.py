#!/usr/bin/env python3
"""
ChatMind API - Simple Working Version

A clean, simple FastAPI application that works (based on the working simple_main.py).
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import logging
import os
from typing import Dict, List, Any, Optional
from models import ApiResponse
from utils import convert_neo4j_to_json, get_config
from routes.health import router as health_router, set_global_connections
from routes.search import router as search_router, set_global_connections as set_search_connections
from routes.graph import router as graph_router, set_global_connections as set_graph_connections
from routes.debug import router as debug_router, set_global_connections as set_debug_connections
from routes.data import router as data_router, set_global_connections as set_data_connections
from routes.advanced import router as advanced_router, set_global_connections as set_advanced_connections
from routes.analytics import router as analytics_router, set_global_connections as set_analytics_connections
from routes.discovery import router as discovery_router, set_global_connections as set_discovery_connections

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)



# Initialize FastAPI app
app = FastAPI(
    title="ChatMind API",
    description="Hybrid search API for chat data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database connection (simple approach)
neo4j_driver = None
qdrant_client = None
embedding_model = None

@app.on_event("startup")
async def startup_event():
    """Initialize the API"""
    global neo4j_driver, qdrant_client, embedding_model
    
    logger.info("🚀 Starting ChatMind API...")
    
    # Initialize Neo4j connection
    try:
        from neo4j import GraphDatabase
        config = get_config()
        
        neo4j_driver = GraphDatabase.driver(
            config["neo4j"]["uri"], 
            auth=(config["neo4j"]["user"], config["neo4j"]["password"])
        )
        
        # Test connection
        with neo4j_driver.session() as session:
            session.run("RETURN 1")
        
        logger.info("✅ Neo4j connected successfully")
        
    except Exception as e:
        logger.error(f"❌ Neo4j connection failed: {e}")
        neo4j_driver = None
    
    # Initialize Qdrant connection
    try:
        from qdrant_client import QdrantClient
        from sentence_transformers import SentenceTransformer
        
        qdrant_url = f"http://{config['qdrant']['host']}:{config['qdrant']['port']}"
        qdrant_client = QdrantClient(url=qdrant_url)
        
        # Test connection
        collections = qdrant_client.get_collections()
        logger.info(f"✅ Qdrant connected successfully. Collections: {[c.name for c in collections.collections]}")
        
        # Initialize embedding model
        embedding_model = SentenceTransformer(config["embedding"]["model_name"])
        logger.info("✅ Embedding model loaded successfully")
        
    except Exception as e:
        logger.error(f"❌ Qdrant connection failed: {e}")
        qdrant_client = None
        embedding_model = None
    
    # Set global connections for modules
    set_global_connections(neo4j_driver, qdrant_client, embedding_model)
    set_search_connections(neo4j_driver, qdrant_client, embedding_model)
    set_graph_connections(neo4j_driver, qdrant_client, embedding_model)
    set_debug_connections(neo4j_driver, qdrant_client, embedding_model)
    set_data_connections(neo4j_driver, qdrant_client, embedding_model)
    set_advanced_connections(neo4j_driver, qdrant_client, embedding_model)
    set_analytics_connections(neo4j_driver, qdrant_client, embedding_model)
    set_discovery_connections(neo4j_driver, qdrant_client, embedding_model)
    
    logger.info("🎉 API startup complete!")

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources"""
    global neo4j_driver, qdrant_client, embedding_model
    
    logger.info("Shutting down ChatMind API...")
    
    if neo4j_driver:
        neo4j_driver.close()
        logger.info("✅ Neo4j connection closed")
    
    if qdrant_client:
        qdrant_client.close()
        logger.info("✅ Qdrant connection closed")
    
    embedding_model = None
    logger.info("✅ Embedding model unloaded")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "ChatMind API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/api/health"
    }

# Include routers
app.include_router(health_router)
app.include_router(search_router)
app.include_router(graph_router)
app.include_router(debug_router)
app.include_router(data_router)
app.include_router(advanced_router)
app.include_router(analytics_router)
app.include_router(discovery_router)













if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 