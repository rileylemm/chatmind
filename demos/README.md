# ChatMind Demos

This directory contains demonstration scripts that showcase specific features of ChatMind.

## 📋 Available Demos

### `demo_cost_tracking.py`
**Purpose:** Demonstrates the cost tracking functionality for OpenAI API calls
**Usage:** `python demos/demo_cost_tracking.py`
**What it shows:**
- How API calls are tracked and costed
- Cost statistics and reporting
- Error handling and retry logic

### `demo_data_lake.py`
**Purpose:** Demonstrates navigating from Neo4j graph to specific data
**Usage:** `python demos/demo_data_lake.py`
**Prerequisites:** API server must be running (`python chatmind/api/main.py`)
**What it shows:**
- Graph → Chat → Message navigation
- API endpoint usage
- Data lake structure exploration

## 🚀 Running Demos

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   cp env.example .env
   # Edit .env with your OpenAI API key
   ```

3. **Run a demo:**
   ```bash
   python demos/demo_cost_tracking.py
   ```

## 💡 Demo Notes

- **Cost tracking demo** works independently
- **Data lake demo** requires the API server to be running
- All demos use sample/test data
- Demos are for educational purposes and showcase specific features

## 🔧 Customization

You can modify these demos to:
- Test with your own data
- Explore different API parameters
- Understand the system architecture
- Debug specific functionality 