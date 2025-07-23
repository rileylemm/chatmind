#!/usr/bin/env python3
"""
Cost Tracker for ChatMind

Tracks OpenAI API usage and costs for semantic chunking and auto-tagging.
"""

import json
import logging
from typing import Dict, List, Optional
from pathlib import Path
import time
from datetime import datetime, date
from dataclasses import dataclass, asdict
import sqlite3
from contextlib import contextmanager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class APICall:
    """Represents a single API call with cost tracking."""
    timestamp: float
    model: str
    operation: str  # 'chunking', 'tagging', 'embedding'
    input_tokens: int
    output_tokens: int
    cost_usd: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None


class CostTracker:
    """Tracks OpenAI API usage and costs."""
    
    # OpenAI pricing (as of 2024, update as needed)
    PRICING = {
        'gpt-4': {
            'input': 0.03 / 1000,  # $0.03 per 1K input tokens
            'output': 0.06 / 1000   # $0.06 per 1K output tokens
        },
        'gpt-4-turbo': {
            'input': 0.01 / 1000,  # $0.01 per 1K input tokens
            'output': 0.03 / 1000   # $0.03 per 1K output tokens
        },
        'gpt-3.5-turbo': {
            'input': 0.001 / 1000,  # $0.001 per 1K input tokens
            'output': 0.002 / 1000  # $0.002 per 1K output tokens
        }
    }
    
    def __init__(self, db_path: str = "data/cost_tracker.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
    
    def _init_database(self):
        """Initialize the SQLite database."""
        with self._get_db() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS api_calls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp REAL NOT NULL,
                    model TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    cost_usd REAL NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    metadata TEXT
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON api_calls(timestamp)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_operation ON api_calls(operation)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_model ON api_calls(model)")
    
    @contextmanager
    def _get_db(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def track_call(self, 
                   model: str,
                   operation: str,
                   input_tokens: int,
                   output_tokens: int,
                   success: bool = True,
                   error_message: Optional[str] = None,
                   metadata: Optional[Dict] = None) -> APICall:
        """
        Track a single API call.
        
        Args:
            model: The OpenAI model used
            operation: The operation type ('chunking', 'tagging', 'embedding')
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            success: Whether the call was successful
            error_message: Error message if failed
            metadata: Additional metadata
        
        Returns:
            APICall object with cost information
        """
        # Calculate cost
        cost_usd = self._calculate_cost(model, input_tokens, output_tokens)
        
        # Create API call record
        api_call = APICall(
            timestamp=time.time(),
            model=model,
            operation=operation,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            success=success,
            error_message=error_message,
            metadata=metadata
        )
        
        # Store in database
        self._store_call(api_call)
        
        logger.debug(f"Tracked {operation} call: {cost_usd:.4f} USD")
        return api_call
    
    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate the cost of an API call."""
        if model not in self.PRICING:
            logger.warning(f"Unknown model pricing for {model}, using gpt-4 pricing")
            model = 'gpt-4'
        
        pricing = self.PRICING[model]
        input_cost = (input_tokens / 1000) * pricing['input']
        output_cost = (output_tokens / 1000) * pricing['output']
        
        return input_cost + output_cost
    
    def _store_call(self, api_call: APICall):
        """Store an API call in the database."""
        with self._get_db() as conn:
            conn.execute("""
                INSERT INTO api_calls 
                (timestamp, model, operation, input_tokens, output_tokens, 
                 cost_usd, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                api_call.timestamp,
                api_call.model,
                api_call.operation,
                api_call.input_tokens,
                api_call.output_tokens,
                api_call.cost_usd,
                api_call.success,
                api_call.error_message,
                json.dumps(api_call.metadata) if api_call.metadata else None
            ))
    
    def get_statistics(self, 
                      start_date: Optional[date] = None,
                      end_date: Optional[date] = None,
                      operation: Optional[str] = None) -> Dict:
        """
        Get cost and usage statistics.
        
        Args:
            start_date: Start date for filtering (inclusive)
            end_date: End date for filtering (inclusive)
            operation: Filter by operation type
        
        Returns:
            Dictionary with statistics
        """
        with self._get_db() as conn:
            # Build query
            query = "SELECT * FROM api_calls WHERE 1=1"
            params = []
            
            if start_date:
                start_timestamp = datetime.combine(start_date, datetime.min.time()).timestamp()
                query += " AND timestamp >= ?"
                params.append(start_timestamp)
            
            if end_date:
                end_timestamp = datetime.combine(end_date, datetime.max.time()).timestamp()
                query += " AND timestamp <= ?"
                params.append(end_timestamp)
            
            if operation:
                query += " AND operation = ?"
                params.append(operation)
            
            # Execute query
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            
            if not rows:
                return self._empty_statistics()
            
            # Calculate statistics
            total_calls = len(rows)
            successful_calls = sum(1 for row in rows if row['success'])
            failed_calls = total_calls - successful_calls
            
            total_cost = sum(row['cost_usd'] for row in rows)
            total_input_tokens = sum(row['input_tokens'] for row in rows)
            total_output_tokens = sum(row['output_tokens'] for row in rows)
            
            # Group by model
            model_stats = {}
            for row in rows:
                model = row['model']
                if model not in model_stats:
                    model_stats[model] = {
                        'calls': 0,
                        'cost': 0.0,
                        'input_tokens': 0,
                        'output_tokens': 0
                    }
                
                model_stats[model]['calls'] += 1
                model_stats[model]['cost'] += row['cost_usd']
                model_stats[model]['input_tokens'] += row['input_tokens']
                model_stats[model]['output_tokens'] += row['output_tokens']
            
            # Group by operation
            operation_stats = {}
            for row in rows:
                op = row['operation']
                if op not in operation_stats:
                    operation_stats[op] = {
                        'calls': 0,
                        'cost': 0.0,
                        'input_tokens': 0,
                        'output_tokens': 0
                    }
                
                operation_stats[op]['calls'] += 1
                operation_stats[op]['cost'] += row['cost_usd']
                operation_stats[op]['input_tokens'] += row['input_tokens']
                operation_stats[op]['output_tokens'] += row['output_tokens']
            
            return {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'success_rate': successful_calls / total_calls if total_calls > 0 else 0,
                'total_cost_usd': total_cost,
                'total_input_tokens': total_input_tokens,
                'total_output_tokens': total_output_tokens,
                'model_statistics': model_stats,
                'operation_statistics': operation_stats,
                'date_range': {
                    'start_date': start_date.isoformat() if start_date else None,
                    'end_date': end_date.isoformat() if end_date else None
                }
            }
    
    def _empty_statistics(self) -> Dict:
        """Return empty statistics structure."""
        return {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'success_rate': 0,
            'total_cost_usd': 0.0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'model_statistics': {},
            'operation_statistics': {},
            'date_range': {
                'start_date': None,
                'end_date': None
            }
        }
    
    def get_recent_calls(self, limit: int = 50) -> List[Dict]:
        """Get recent API calls for display."""
        with self._get_db() as conn:
            cursor = conn.execute("""
                SELECT * FROM api_calls 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def get_daily_costs(self, days: int = 30) -> List[Dict]:
        """Get daily cost breakdown for the last N days."""
        with self._get_db() as conn:
            # Get the start timestamp for N days ago
            start_timestamp = time.time() - (days * 24 * 60 * 60)
            
            cursor = conn.execute("""
                SELECT 
                    DATE(datetime(timestamp, 'unixepoch')) as date,
                    SUM(cost_usd) as daily_cost,
                    COUNT(*) as daily_calls,
                    SUM(input_tokens) as daily_input_tokens,
                    SUM(output_tokens) as daily_output_tokens
                FROM api_calls 
                WHERE timestamp >= ?
                GROUP BY DATE(datetime(timestamp, 'unixepoch'))
                ORDER BY date DESC
            """, (start_timestamp,))
            
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def export_data(self, output_file: str = "data/cost_export.json"):
        """Export all cost data to JSON."""
        with self._get_db() as conn:
            cursor = conn.execute("SELECT * FROM api_calls ORDER BY timestamp DESC")
            rows = cursor.fetchall()
            
            data = {
                'export_timestamp': time.time(),
                'total_records': len(rows),
                'calls': [dict(row) for row in rows]
            }
            
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Exported {len(rows)} records to {output_file}")


# Global cost tracker instance
_cost_tracker = None

def get_cost_tracker() -> CostTracker:
    """Get the global cost tracker instance."""
    global _cost_tracker
    if _cost_tracker is None:
        _cost_tracker = CostTracker()
    return _cost_tracker

def track_api_call(**kwargs) -> APICall:
    """Convenience function to track an API call."""
    tracker = get_cost_tracker()
    return tracker.track_call(**kwargs) 