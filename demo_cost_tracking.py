#!/usr/bin/env python3
"""
Demo: Cost Tracking

This script demonstrates the cost tracking functionality for ChatMind.
"""

import json
import time
from pathlib import Path
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent))

def test_cost_tracker():
    """Test the cost tracker functionality."""
    
    print("💰 ChatMind Cost Tracker Demo")
    print("=" * 50)
    
    try:
        # Import cost tracker
        from chatmind.cost_tracker.tracker import CostTracker, track_api_call
        
        # Initialize tracker
        tracker = CostTracker()
        
        print("✅ Cost tracker initialized")
        
        # Simulate some API calls
        print("\n🔍 Simulating API calls...")
        
        # Simulate successful chunking call
        track_api_call(
            model="gpt-4",
            operation="chunking",
            input_tokens=1500,
            output_tokens=800,
            success=True,
            metadata={
                'chat_id': 'demo_chat_1',
                'chunk_count': 3,
                'attempt': 1
            }
        )
        
        # Simulate successful tagging call
        track_api_call(
            model="gpt-4",
            operation="tagging",
            input_tokens=500,
            output_tokens=200,
            success=True,
            metadata={
                'chunk_id': 'demo_chunk_1',
                'attempt': 1
            }
        )
        
        # Simulate failed call
        track_api_call(
            model="gpt-4",
            operation="chunking",
            input_tokens=1200,
            output_tokens=0,
            success=False,
            error_message="Rate limit exceeded",
            metadata={
                'chat_id': 'demo_chat_2',
                'attempt': 1
            }
        )
        
        # Simulate another successful call
        track_api_call(
            model="gpt-3.5-turbo",
            operation="tagging",
            input_tokens=300,
            output_tokens=150,
            success=True,
            metadata={
                'chunk_id': 'demo_chunk_2',
                'attempt': 1
            }
        )
        
        print("✅ Simulated API calls completed")
        
        # Get statistics
        print("\n📊 Cost Statistics:")
        stats = tracker.get_statistics()
        
        print(f"  - Total calls: {stats['total_calls']}")
        print(f"  - Successful calls: {stats['successful_calls']}")
        print(f"  - Failed calls: {stats['failed_calls']}")
        print(f"  - Success rate: {stats['success_rate']:.1%}")
        print(f"  - Total cost: ${stats['total_cost_usd']:.4f}")
        print(f"  - Total input tokens: {stats['total_input_tokens']:,}")
        print(f"  - Total output tokens: {stats['total_output_tokens']:,}")
        
        # Show model statistics
        if stats['model_statistics']:
            print(f"\n📈 Model Statistics:")
            for model, model_stats in stats['model_statistics'].items():
                print(f"  - {model}:")
                print(f"    Calls: {model_stats['calls']}")
                print(f"    Cost: ${model_stats['cost']:.4f}")
                print(f"    Input tokens: {model_stats['input_tokens']:,}")
                print(f"    Output tokens: {model_stats['output_tokens']:,}")
        
        # Show operation statistics
        if stats['operation_statistics']:
            print(f"\n🔧 Operation Statistics:")
            for operation, op_stats in stats['operation_statistics'].items():
                print(f"  - {operation}:")
                print(f"    Calls: {op_stats['calls']}")
                print(f"    Cost: ${op_stats['cost']:.4f}")
                print(f"    Input tokens: {op_stats['input_tokens']:,}")
                print(f"    Output tokens: {op_stats['output_tokens']:,}")
        
        # Get recent calls
        print(f"\n🕒 Recent Calls:")
        recent_calls = tracker.get_recent_calls(limit=5)
        for call in recent_calls:
            status = "✅" if call['success'] else "❌"
            print(f"  {status} {call['operation']} ({call['model']}) - ${call['cost_usd']:.4f}")
        
        # Get daily costs
        print(f"\n📅 Daily Costs (Last 7 days):")
        daily_costs = tracker.get_daily_costs(days=7)
        for daily in daily_costs:
            print(f"  - {daily['date']}: ${daily['daily_cost']:.4f} ({daily['daily_calls']} calls)")
        
        # Export data
        print(f"\n💾 Exporting cost data...")
        tracker.export_data("data/cost_demo_export.json")
        print("✅ Cost data exported to data/cost_demo_export.json")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure you have installed the required dependencies:")
        print("   pip install sqlite3")
    except Exception as e:
        print(f"❌ Error during cost tracking: {e}")


def test_api_integration():
    """Test API integration for cost tracking."""
    
    print("\n" + "="*60)
    print("🔗 Testing API Integration")
    print("="*60)
    
    try:
        import requests
        
        API_BASE = "http://localhost:8000"
        
        # Test cost statistics endpoint
        print("📊 Testing cost statistics endpoint...")
        response = requests.get(f"{API_BASE}/costs/statistics")
        if response.status_code == 200:
            stats = response.json()
            print(f"✅ Cost statistics retrieved: ${stats.get('total_cost_usd', 0):.4f}")
        else:
            print(f"❌ Failed to get cost statistics: {response.status_code}")
        
        # Test recent calls endpoint
        print("🕒 Testing recent calls endpoint...")
        response = requests.get(f"{API_BASE}/costs/recent?limit=5")
        if response.status_code == 200:
            calls = response.json()
            print(f"✅ Recent calls retrieved: {len(calls)} calls")
        else:
            print(f"❌ Failed to get recent calls: {response.status_code}")
        
        # Test daily costs endpoint
        print("📅 Testing daily costs endpoint...")
        response = requests.get(f"{API_BASE}/costs/daily?days=7")
        if response.status_code == 200:
            daily_costs = response.json()
            print(f"✅ Daily costs retrieved: {len(daily_costs)} days")
        else:
            print(f"❌ Failed to get daily costs: {response.status_code}")
        
    except ImportError:
        print("❌ Requests library not available")
        print("💡 Install with: pip install requests")
    except Exception as e:
        print(f"❌ API integration error: {e}")


def test_pricing_calculation():
    """Test pricing calculation logic."""
    
    print("\n" + "="*60)
    print("🧮 Testing Pricing Calculation")
    print("="*60)
    
    try:
        from chatmind.cost_tracker.tracker import CostTracker
        
        tracker = CostTracker()
        
        # Test different models and token counts
        test_cases = [
            ("gpt-4", 1000, 500),
            ("gpt-4-turbo", 1000, 500),
            ("gpt-3.5-turbo", 1000, 500),
            ("gpt-4", 5000, 2000),
            ("gpt-3.5-turbo", 5000, 2000),
        ]
        
        print("📊 Pricing Examples:")
        for model, input_tokens, output_tokens in test_cases:
            cost = tracker._calculate_cost(model, input_tokens, output_tokens)
            print(f"  - {model}: {input_tokens:,} input + {output_tokens:,} output = ${cost:.4f}")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")


if __name__ == "__main__":
    test_cost_tracker()
    test_api_integration()
    test_pricing_calculation()
    
    print("\n" + "="*60)
    print("💰 Cost Tracking Summary")
    print("="*60)
    print("""
✅ What We Built:
- SQLite-based cost tracking database
- Real-time API call monitoring
- Automatic cost calculation
- Multiple model pricing support
- Rich statistics and reporting
- API endpoints for frontend integration

🔧 Features:
- Track input/output tokens
- Calculate costs automatically
- Monitor success/failure rates
- Filter by date and operation
- Export data to JSON
- Daily cost breakdowns

💡 Usage:
- Automatic tracking in semantic chunking
- Automatic tracking in auto-tagging
- API endpoints for frontend display
- Export functionality for analysis

🎯 Benefits:
- Monitor API usage and costs
- Track performance and success rates
- Identify expensive operations
- Budget management
- Usage analytics

🔄 Next Steps:
- Integrate with your actual API calls
- Set up cost alerts and limits
- Add more detailed analytics
- Implement cost optimization suggestions
    """) 