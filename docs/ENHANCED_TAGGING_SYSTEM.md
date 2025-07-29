# Enhanced Tagging System

## Overview

The enhanced tagging system addresses the critical issues found in the original tagging implementation, specifically the systematic bias that caused medical tags to be incorrectly applied to web development content. The system is now organized into multiple approaches to accommodate different needs and constraints.

## Directory Structure

```
chatmind/tagger/
├── run_tagging.py              # Main selection script (unified orchestrator)
├── deprecated/                 # Original basic tagger (not used)
│   ├── tagger.py
│   ├── prompts.py
│   ├── run_tagging.py
│   └── run_tagging_incremental.py
├── cloud_api/                  # Enhanced tagger using OpenAI API
│   ├── enhanced_tagger.py
│   ├── enhanced_prompts.py
│   ├── run_enhanced_tagging.py
│   └── run_enhanced_tagging_incremental.py
└── local/                      # Enhanced tagger using local models
    ├── local_enhanced_tagger.py
    ├── local_prompts.py        # Optimized Gemma-2B prompts
    ├── run_local_enhanced_tagging.py
    └── run_tag_validation.py   # Optional validation step
```

## Key Improvements

### 1. **Optimized Prompts for Gemma-2B**
- **100% JSON compliance** with Gemma-specific prompts
- **Clear instruction format** that Gemma-2B follows perfectly
- **No conversational prefixes** or explanations
- **Domain-specific guidance** (technical, personal, medical, etc.)
- **Validation rules** to prevent systematic bias

### 2. **Conversation-Level Context Awareness**
- **Analyzes entire conversations** before tagging individual chunks
- **Identifies primary domain** (technical, personal, medical, etc.)
- **Extracts key topics** to provide context for chunk tagging
- **Prevents domain confusion** across chunks in the same conversation

### 3. **Robust JSON Parsing System**
- **Multiple extraction strategies** for handling varied responses
- **Fallback to hashtag extraction** when JSON parsing fails
- **Graceful handling** of malformed or conversational responses
- **Comprehensive error recovery** with detailed logging

### 4. **Incremental Processing with Auto-Saving**
- **Saves progress every 500 chunks** to prevent data loss
- **Resumes from interruptions** automatically
- **Detailed progress logging** for monitoring
- **State management** for efficient reprocessing

### 5. **Enhanced Metadata**
- **Domain classification** (technical, personal, medical, etc.)
- **Confidence scoring** (high, medium, low)
- **Conversation context** stored with each chunk
- **JSON parsing success** tracking for debugging

## Tagging Methods

### 1. Cloud API (OpenAI)
- **Speed**: Fast
- **Cost**: ~$42-65 for 32K chunks
- **Quality**: Excellent
- **Setup**: Requires OpenAI API key

### 2. Local Model (Ollama)
- **Speed**: Fast (3-4 hours for 32K chunks with Gemma-2B)
- **Cost**: $0
- **Quality**: Excellent (100% JSON compliance)
- **Setup**: Requires Ollama + Gemma-2B model

## Architecture

### Core Components

1. **`run_tagging.py`** (Main Selection Script)
   - Unified interface for choosing tagging method
   - Setup validation for both cloud and local
   - Automatic model selection (Gemma-2B for local)
   - Optimized defaults (0.1s delays, conversation context enabled)

2. **`local/local_prompts.py`**
   - Gemma-2B optimized prompts for 100% JSON compliance
   - Clear instruction format without conversational prefixes
   - Domain-specific guidance and validation rules

3. **`local/local_enhanced_tagger.py`**
   - `LocalEnhancedChunkTagger` class for local models
   - Same features as cloud API but using Ollama
   - Optimized for Gemma-2B with robust JSON parsing
   - Incremental saving and comprehensive logging

## Usage

### Main Interface

Use the unified tagging script to choose your method:

```bash
# Interactive selection
python3 chatmind/tagger/run_tagging.py

# Direct method selection (recommended)
python3 chatmind/tagger/run_tagging.py --method local
python3 chatmind/tagger/run_tagging.py --method cloud

# Check setup only
python3 chatmind/tagger/run_tagging.py --method local --check-only
```

### Cloud API Usage

```bash
# Run enhanced tagging with OpenAI API
python3 chatmind/tagger/run_tagging.py --method cloud \
    --input-file data/embeddings/chunks_with_clusters.jsonl \
    --output-file data/processed/enhanced_tagged_chunks.jsonl \
    --model gpt-3.5-turbo \
    --enable-validation \
    --enable-conversation-context
```

### Local Model Usage (Optimized)

```bash
# Run enhanced tagging with Gemma-2B (recommended)
python3 chatmind/tagger/run_tagging.py --method local \
    --input-file data/embeddings/chunks_with_clusters.jsonl \
    --output-file data/processed/local_enhanced_tagged_chunks.jsonl \
    --model gemma:2b \
    --delay 0.1 \
    --enable-conversation-context
```

### Testing the System

```bash
# Test Gemma-2B setup and performance
python3 scripts/test_gemma_final.py

# Check setup only
python3 chatmind/tagger/run_tagging.py --method local --check-only
python3 chatmind/tagger/run_tagging.py --method cloud --check-only
```

### Programmatic Usage

```python
# Local Model with Gemma-2B
from chatmind.tagger.local.local_enhanced_tagger import LocalEnhancedChunkTagger

# Initialize optimized local tagger
tagger = LocalEnhancedChunkTagger(
    model="gemma:2b",
    delay_between_calls=0.1,
    enable_validation=False,  # Disabled for speed
    enable_conversation_context=True
)

# Tag chunks with conversation context
tagged_chunks = tagger.tag_conversation_chunks(chunks)

# Get enhanced statistics
stats = tagger.get_enhanced_tagging_stats(tagged_chunks)
```

## Key Features

### Conversation-Level Analysis
- Analyzes the first 10 chunks of each conversation
- Identifies primary domain and key topics
- Provides context for individual chunk tagging

### Robust JSON Parsing
- Multiple extraction strategies for varied responses
- Fallback to hashtag extraction when JSON fails
- Graceful handling of conversational prefixes
- Comprehensive error recovery

### Incremental Processing
- Saves progress every 500 chunks
- Resumes from interruptions automatically
- Detailed progress logging
- State management for efficiency

### Enhanced Output Format
```json
{
  "tags": ["#web-development", "#react", "#frontend"],
  "category": "Web Development Project Planning",
  "domain": "technical",
  "confidence": "high",
  "conversation_context": {
    "primary_domain": "technical",
    "key_topics": ["web development", "react", "portfolio"]
  }
}
```

### Statistics and Monitoring
- **Domain distribution** tracking
- **Confidence scoring** analysis
- **JSON parsing success** rates
- **Tag frequency** analysis
- **Processing progress** monitoring

## Comparison

### Enhanced vs Original System

| Feature | Original System | Enhanced System |
|---------|----------------|-----------------|
| **Prompt Quality** | Generic, no examples | Gemma-optimized, 100% JSON compliance |
| **Context Awareness** | Chunk-level only | Conversation-level + chunk-level |
| **JSON Parsing** | Basic | Robust with multiple fallbacks |
| **Domain Classification** | None | Explicit domain tracking |
| **Error Detection** | Basic | Comprehensive with logging |
| **Incremental Saving** | None | Every 500 chunks |
| **Statistics** | Basic counts | Comprehensive analysis |

### Cloud API vs Local Model

| Feature | Cloud API | Local Model (Gemma-2B) |
|---------|-----------|------------------------|
| **Cost** | $42-65 | $0 |
| **Speed** | Fast | Fast (3-4 hours for 32K chunks) |
| **Quality** | Excellent | Excellent (100% JSON compliance) |
| **Privacy** | Data sent to OpenAI | Fully local |
| **Setup** | API key | Ollama + Gemma-2B |
| **Validation** | ✅ | ✅ (optional) |
| **Conversation Context** | ✅ | ✅ |
| **Incremental Processing** | ✅ | ✅ |
| **JSON Compliance** | 100% | **100%** |

## Migration from Original System

### Step 1: Test the Enhanced System
```bash
# Test local setup with Gemma-2B
python3 chatmind/tagger/run_tagging.py --method local --check-only

# Test cloud setup
python3 chatmind/tagger/run_tagging.py --method cloud --check-only
```

### Step 2: Run Enhanced Tagging
```bash
# For zero cost and excellent quality, use local
python3 chatmind/tagger/run_tagging.py --method local

# For best quality, use cloud API
python3 chatmind/tagger/run_tagging.py --method cloud
```

### Step 3: Compare Results
```bash
python scripts/analyze_tag_distribution.py
python scripts/representative_tag_analysis.py
```

## Configuration Options

### Method Selection
- `--method`: Choose between 'cloud' or 'local' (prompted if not specified)

### Model Selection

**Cloud API Models:**
- `gpt-3.5-turbo` (default, fast, cost-effective)
- `gpt-4` (better quality, more expensive)

**Local Models:**
- `gemma:2b` (default, excellent quality, 100% JSON compliance)
- `tinyllama:latest` (faster, smaller, ~85% JSON compliance)
- `codellama:7b` (great for technical content)
- `mistral:7b` (excellent general reasoning)

### Feature Toggles
- `--enable-validation`: Enable tag validation (default: False for speed)
- `--disable-validation`: Disable tag validation
- `--enable-conversation-context`: Enable conversation-level context (default: True)
- `--disable-conversation-context`: Disable conversation-level context
- `--force`: Force reprocess all chunks (ignore state)

### Performance Settings
- `--delay`: Delay between API calls in seconds (default: 0.1 for local, 1.0 for cloud)
- `--max-retries`: Maximum retries for API calls (default: 3)
- `--check-only`: Only check setup, don't run tagging

## Troubleshooting

### Common Issues

1. **High frequency of medical tags**
   - Check if validation is enabled
   - Review conversation context analysis
   - Verify Gemma-2B prompts are being used

2. **JSON parsing failures**
   - Check Ollama is running: `ollama serve`
   - Verify Gemma-2B is available: `ollama list`
   - Review logs in `chatmind/tagger/logs/`
   - System includes robust fallbacks

3. **Performance issues**
   - Use Gemma-2B for optimal speed/quality balance
   - Disable validation for faster processing
   - Use 0.1s delays for local models
   - Monitor logs for bottlenecks

4. **Local model issues**
   - Ensure Ollama is running: `ollama serve`
   - Check available models: `ollama list`
   - Pull required model: `ollama pull gemma:2b`

### Debugging

1. **Check setup**
   ```bash
   python3 chatmind/tagger/run_tagging.py --method local --check-only
   python3 chatmind/tagger/run_tagging.py --method cloud --check-only
   ```

2. **Check statistics**
   ```python
   stats = tagger.get_enhanced_tagging_stats(tagged_chunks)
   print(stats['json_success_rate'])
   ```

3. **Review conversation context**
   ```python
   context = tagger.analyze_conversation(chunks)
   print(context)
   ```

4. **Test individual chunks**
   ```python
   tagged_chunk = tagger.tag_chunk(chunk, conversation_context)
   print(tagged_chunk)
   ```

## Future Enhancements

1. **Custom Domain Classification**
   - Add support for custom domain categories
   - Implement domain-specific validation rules

2. **Advanced Validation**
   - Machine learning-based tag validation
   - Historical pattern analysis
   - User feedback integration

3. **Performance Optimization**
   - Batch processing for large datasets
   - Caching for repeated patterns
   - Parallel processing for multiple conversations

4. **Integration with Tag Master List**
   - Validate against canonical tag list
   - Suggest tag aliases and alternatives
   - Maintain tag consistency across conversations

5. **Additional Local Models**
   - Support for more Ollama models
   - Integration with other local LLM frameworks
   - Model performance benchmarking

6. **Hybrid Approaches**
   - Combine local and cloud models
   - Use local for validation, cloud for generation
   - Fallback strategies for different scenarios 