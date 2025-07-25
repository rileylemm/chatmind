import json
import sqlite3
from pathlib import Path
from typing import Dict, Any, List
import logging
import os

logger = logging.getLogger(__name__)

class StatsCalculator:
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            # Get the absolute path to the data directory
            current_dir = Path(__file__).parent
            self.data_dir = current_dir.parent.parent / "data"
        else:
            self.data_dir = Path(data_dir)
        
    def get_chat_stats(self) -> Dict[str, Any]:
        """Get real chat statistics from processed data"""
        try:
            chats_file = self.data_dir / "processed" / "chats.jsonl"
            if not chats_file.exists():
                return {"total_chats": 0, "total_messages": 0}
                
            total_chats = 0
            total_messages = 0
            
            with open(chats_file, 'r') as f:
                for line in f:
                    if line.strip():
                        chat = json.loads(line)
                        total_chats += 1
                        # Count messages in the messages array
                        total_messages += len(chat.get('messages', []))
            
            return {
                "total_chats": total_chats,
                "total_messages": total_messages
            }
        except Exception as e:
            logger.error(f"Error reading chat stats: {e}")
            return {"total_chats": 0, "total_messages": 0}
    
    def get_tag_stats(self) -> Dict[str, Any]:
        """Get real tag statistics from master list"""
        try:
            tags_file = self.data_dir / "tags" / "tags_master_list.json"
            if not tags_file.exists():
                return {"active_tags": 0}
                
            with open(tags_file, 'r') as f:
                tags = json.load(f)
            
            return {
                "active_tags": len(tags)
            }
        except Exception as e:
            logger.error(f"Error reading tag stats: {e}")
            return {"active_tags": 0}
    
    def get_cost_stats(self) -> Dict[str, Any]:
        """Get real cost statistics from the cost tracker database"""
        try:
            db_file = self.data_dir / "cost_tracker.db"
            if not db_file.exists():
                return {"total_cost": 0.0, "total_calls": 0}
                
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()
            
            # Get total cost
            cursor.execute("SELECT SUM(cost_usd) FROM api_calls WHERE success = 1")
            total_cost = cursor.fetchone()[0] or 0.0
            
            # Get total calls
            cursor.execute("SELECT COUNT(*) FROM api_calls")
            total_calls = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                "total_cost": round(total_cost, 2),
                "total_calls": total_calls
            }
        except Exception as e:
            logger.error(f"Error reading cost stats: {e}")
            return {"total_cost": 0.0, "total_calls": 0}
    
    def get_cluster_stats(self) -> Dict[str, Any]:
        """Get real cluster statistics from embeddings"""
        try:
            cluster_file = self.data_dir / "embeddings" / "cluster_summaries.json"
            if not cluster_file.exists():
                return {"total_clusters": 0}
                
            with open(cluster_file, 'r') as f:
                clusters = json.load(f)
            
            return {
                "total_clusters": len(clusters)
            }
        except Exception as e:
            logger.error(f"Error reading cluster stats: {e}")
            return {"total_clusters": 0}
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Get all real statistics"""
        chat_stats = self.get_chat_stats()
        tag_stats = self.get_tag_stats()
        cost_stats = self.get_cost_stats()
        cluster_stats = self.get_cluster_stats()
        
        return {
            **chat_stats,
            **tag_stats,
            **cost_stats,
            **cluster_stats
        }

# Global instance
stats_calculator = StatsCalculator()

def get_dashboard_stats() -> Dict[str, Any]:
    """API endpoint to get dashboard statistics"""
    try:
        stats = stats_calculator.get_all_stats()
        
        # Format the stats for the frontend
        return {
            "success": True,
            "data": {
                "total_chats": stats.get("total_chats", 0),
                "total_messages": stats.get("total_messages", 0),
                "active_tags": stats.get("active_tags", 0),
                "total_cost": f"${stats.get('total_cost', 0.0):.4f}",
                "total_clusters": stats.get("total_clusters", 0),
                "total_calls": stats.get("total_calls", 0)
            }
        }
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        return {
            "success": False,
            "error": str(e),
            "data": {
                "total_chats": 0,
                "total_messages": 0,
                "active_tags": 0,
                "total_cost": "$0.00",
                "total_clusters": 0,
                "total_calls": 0
            }
        } 