# Enhanced Tagging System

## Overview

The enhanced tagging system addresses the critical issues found in the original tagging implementation, specifically the systematic bias that caused medical tags to be incorrectly applied to web development content. The system is now organized into multiple approaches to accommodate different needs and constraints.

## Directory Structure

```
chatmind/tagger/
├── run_tagging.py              # Main selection script
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
    └── run_local_enhanced_tagging.py
```

## Key Improvements

### 1. **Enhanced Prompts with Examples**
- **Clear examples** of correct vs incorrect tagging
- **Domain-specific guidance** (technical, personal, medical, etc.)
- **Validation rules** to prevent systematic bias
- **Explicit instructions** to avoid applying medical tags to non-medical content

### 2. **Conversation-Level Context Awareness**
- **Analyzes entire conversations** before tagging individual chunks
- **Identifies primary domain** (technical, personal, medical, etc.)
- **Extracts key topics** to provide context for chunk tagging
- **Prevents domain confusion** across chunks in the same conversation

### 3. **Tag Validation System**
- **Validates proposed tags** against content domain
- **Detects systematic bias** and suggests corrections
- **Provides reasoning** for validation decisions
- **Falls back to better tags** when validation fails

### 4. **Enhanced Metadata**
- **Domain classification** (technical, personal, medical, etc.)
- **Confidence scoring** (high, medium, low)
- **Conversation context** stored with each chunk
- **Validation issues** tracked for debugging

### 5. **Better Error Handling**
- **Comprehensive retry logic** for API failures
- **Graceful fallbacks** when validation fails
- **Detailed logging** for debugging
- **Statistics tracking** for monitoring

## Tagging Methods

### 1. Cloud API (OpenAI)
- **Speed**: Fast
- **Cost**: ~$42-65 for 32K chunks
- **Quality**: Excellent
- **Setup**: Requires OpenAI API key

### 2. Local Model (Ollama)
- **Speed**: Slower (6-8 hours for 32K chunks)
- **Cost**: $0
- **Quality**: Good-Excellent
- **Setup**: Requires Ollama + model

## Architecture

### Core Components

1. **`run_tagging.py`** (Main Selection Script)
   - Unified interface for choosing tagging method
   - Setup validation for both cloud and local
   - Automatic model selection and configuration

2. **`cloud_api/enhanced_prompts.py`**
   - Enhanced prompts with examples and validation rules
   - Conversation-level analysis prompts
   - Tag validation prompts

3. **`cloud_api/enhanced_tagger.py`**
   - `EnhancedChunkTagger` class with conversation context
   - Tag validation system
   - Conversation-level analysis
   - Enhanced statistics and monitoring

4. **`local/local_enhanced_tagger.py`**
   - `LocalEnhancedChunkTagger` class for local models
   - Same features as cloud API but using Ollama
   - Optimized for local model performance

## Usage

### Main Interface

Use the unified tagging script to choose your method:

```bash
# Interactive selection
python3 chatmind/tagger/run_tagging.py

# Direct method selection
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

### Local Model Usage

```bash
# Run enhanced tagging with local model
python3 chatmind/tagger/run_tagging.py --method local \
    --input-file data/embeddings/chunks_with_clusters.jsonl \
    --output-file data/processed/local_enhanced_tagged_chunks.jsonl \
    --model mistral:latest \
    --enable-validation \
    --enable-conversation-context
```

### Testing the System

```bash
# Test local model setup
python3 scripts/test_local_model.py

# Check setup only
python3 chatmind/tagger/run_tagging.py --method local --check-only
python3 chatmind/tagger/run_tagging.py --method cloud --check-only
```

### Programmatic Usage

```python
# Cloud API
from chatmind.tagger.cloud_api.enhanced_tagger import EnhancedChunkTagger

# Initialize tagger
tagger = EnhancedChunkTagger(
    model="gpt-3.5-turbo",
    enable_validation=True,
    enable_conversation_context=True
)

# Local Model
from chatmind.tagger.local.local_enhanced_tagger import LocalEnhancedChunkTagger

# Initialize local tagger
tagger = LocalEnhancedChunkTagger(
    model="mistral:latest",
    enable_validation=True,
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

### Tag Validation
- Validates tags against content domain
- Detects systematic bias (e.g., medical tags on technical content)
- Suggests better tags when validation fails

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
- **Potential issues** detection
- **Tag frequency** analysis

## Comparison

### Enhanced vs Original System

| Feature | Original System | Enhanced System |
|---------|----------------|-----------------|
| **Prompt Quality** | Generic, no examples | Specific examples and validation rules |
| **Context Awareness** | Chunk-level only | Conversation-level + chunk-level |
| **Validation** | None | Comprehensive tag validation |
| **Domain Classification** | None | Explicit domain tracking |
| **Error Detection** | Basic | Systematic bias detection |
| **Statistics** | Basic counts | Comprehensive analysis |

### Cloud API vs Local Model

| Feature | Cloud API | Local Model |
|---------|-----------|-------------|
| **Cost** | $42-65 | $0 |
| **Speed** | Fast | Slower |
| **Quality** | Excellent | Good-Excellent |
| **Privacy** | Data sent to OpenAI | Fully local |
| **Setup** | API key | Ollama + model |
| **Validation** | ✅ | ✅ |
| **Conversation Context** | ✅ | ✅ |
| **Incremental Processing** | ✅ | ✅ |

## Migration from Original System

### Step 1: Test the Enhanced System
```bash
# Test local setup
python3 chatmind/tagger/run_tagging.py --method local --check-only

# Test cloud setup
python3 chatmind/tagger/run_tagging.py --method cloud --check-only
```

### Step 2: Run Enhanced Tagging
```bash
# For zero cost, start with local
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
- `mistral:latest` (default, good quality)
- `llama3.2:latest` (faster, smaller)
- `qwen2.5:latest` (excellent quality)
- `codellama:7b` (great for technical content)

### Feature Toggles
- `--enable-validation`: Enable tag validation (default: True)
- `--disable-validation`: Disable tag validation
- `--enable-conversation-context`: Enable conversation-level context (default: True)
- `--disable-conversation-context`: Disable conversation-level context
- `--force`: Force reprocess all chunks (ignore state)

### Performance Settings
- `--delay`: Delay between API calls in seconds (default: 1.0 for cloud, 0.5 for local)
- `--max-retries`: Maximum retries for API calls (default: 3)
- `--check-only`: Only check setup, don't run tagging

## Troubleshooting

### Common Issues

1. **High frequency of medical tags**
   - Check if validation is enabled
   - Review conversation context analysis
   - Verify prompt examples are being used

2. **Validation failures**
   - Check API key and model availability (cloud)
   - Check Ollama is running (local)
   - Review validation prompt examples
   - Monitor confidence scores

3. **Performance issues**
   - Reduce conversation context sampling
   - Disable validation for faster processing
   - Increase delay between API calls
   - Use smaller local models for speed

4. **Local model issues**
   - Ensure Ollama is running: `ollama serve`
   - Check available models: `ollama list`
   - Pull required model: `ollama pull mistral:latest`

### Debugging

1. **Check setup**
   ```bash
   python3 chatmind/tagger/run_tagging.py --method local --check-only
   python3 chatmind/tagger/run_tagging.py --method cloud --check-only
   ```

2. **Check statistics**
   ```python
   stats = tagger.get_enhanced_tagging_stats(tagged_chunks)
   print(stats['potential_issues'])
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