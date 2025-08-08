#!/usr/bin/env python3
"""
Pipeline Configuration Module

Loads environment variables with precedence:
1. Pipeline-specific settings (highest priority)
2. Root .env file (fallback)
3. Default values (lowest priority)
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

def load_pipeline_config():
    """Load configuration with proper precedence."""
    
    # Load root .env first (fallback)
    root_env = Path(__file__).parent.parent.parent / ".env"
    if root_env.exists():
        logger.info(f"Loading root .env from: {root_env}")
        load_dotenv(root_env)
    else:
        logger.warning(f"Root .env not found at: {root_env}")
    
    # Load pipeline-specific .env if it exists (override)
    pipeline_env = Path(__file__).parent / ".env"
    if pipeline_env.exists():
        logger.info(f"Loading pipeline .env from: {pipeline_env}")
        load_dotenv(pipeline_env, override=True)
    else:
        logger.info(f"Pipeline .env not found at: {pipeline_env}")
    
    # Pipeline-specific overrides (highest priority)
    pipeline_overrides = {
        'NEO4J_URI': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        'NEO4J_USER': os.getenv('NEO4J_USER', 'neo4j'),
        'NEO4J_PASSWORD': os.getenv('NEO4J_PASSWORD', 'chatmind123'),  # Use correct password
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
        'PIPELINE_DEBUG': os.getenv('PIPELINE_DEBUG', 'True'),
        'PIPELINE_LOG_LEVEL': os.getenv('PIPELINE_LOG_LEVEL', 'INFO'),
    }
    
    # Set environment variables
    for key, value in pipeline_overrides.items():
        os.environ[key] = value
    
    logger.info(f"Neo4j config: URI={pipeline_overrides['NEO4J_URI']}, USER={pipeline_overrides['NEO4J_USER']}, PASSWORD={'*' * len(pipeline_overrides['NEO4J_PASSWORD']) if pipeline_overrides['NEO4J_PASSWORD'] else 'NOT_SET'}")
    
    return pipeline_overrides

def get_neo4j_config() -> dict:
    """Get Neo4j configuration."""
    load_pipeline_config()
    return {
        'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
        'user': os.getenv('NEO4J_USER', 'neo4j'),
        'password': os.getenv('NEO4J_PASSWORD', 'password'),
    }

def get_openai_config() -> dict:
    """Get OpenAI configuration."""
    load_pipeline_config()
    return {
        'api_key': os.getenv('OPENAI_API_KEY', ''),
    }

def get_pipeline_config() -> dict:
    """Get pipeline-specific configuration."""
    load_pipeline_config()
    return {
        'debug': os.getenv('PIPELINE_DEBUG', 'True').lower() == 'true',
        'log_level': os.getenv('PIPELINE_LOG_LEVEL', 'INFO'),
    } 