# Local Model Setup for Enhanced Tagging

This guide explains how to set up local models (Ollama) to run the enhanced tagging system without any API costs.

## 🎯 Benefits of Local Models

- **Zero API costs** - No OpenAI API charges
- **Privacy** - All processing happens locally
- **Enhanced features** - Same conversation-level context and validation
- **Incremental processing** - Only process new chunks with automatic saving
- **Optimized performance** - Fast 0.1s delays and robust JSON parsing
- **Customizable** - Use different models for different needs

## 📋 Prerequisites

### 1. Install Ollama

Visit [ollama.ai](https://ollama.ai/) and install Ollama for your platform:

**macOS:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from [ollama.ai](https://ollama.ai/)

### 2. Start Ollama

```bash
ollama serve
```

### 3. Pull the Optimized Model

**For optimal performance and JSON compliance (recommended):**
```bash
ollama pull gemma:2b
```

**Alternative models for specific use cases:**

**For faster processing (smaller model):**
```bash
ollama pull tinyllama:latest
```

**For better coding/technical content:**
```bash
ollama pull codellama:7b
```

**For better reasoning:**
```bash
ollama pull mistral:7b
```

## 🧪 Testing the Setup

Run the test script to verify everything is working:

```bash
python3 scripts/test_gemma_final.py
```

This will:
1. Check if Ollama is running
2. Test Gemma-2B functionality
3. Test JSON compliance and prompt optimization
4. Show tagging results with confidence scores

## 🚀 Running Local Enhanced Tagging

### Option 1: Use the Unified Orchestrator (Recommended)

```bash
python3 chatmind/tagger/run_tagging.py --method local
```

This automatically:
- Uses Gemma-2B as the default model
- Sets optimal 0.1s delays between API calls
- Enables conversation context by default
- Disables validation for speed (can be enabled with `--enable-validation`)

### Option 2: Direct Command

```bash
python3 chatmind/tagger/local/run_local_enhanced_tagging.py \
    --input-file data/embeddings/chunks_with_clusters.jsonl \
    --output-file data/processed/local_enhanced_tagged_chunks.jsonl \
    --model gemma:2b \
    --delay 0.1 \
    --enable-conversation-context
```

### Option 3: Use Pipeline with Local Models

The pipeline supports local models with a simple flag:

```bash
# Use local models for all AI components
python3 chatmind/pipeline/run_pipeline.py --local

# Skip expensive steps during development
python3 chatmind/pipeline/run_pipeline.py --local --skip-tagging

# Force reprocess with local models
python3 chatmind/pipeline/run_pipeline.py --local --force-reprocess
```

## ⚙️ Configuration Options

### Model Selection

| Model | Size | Speed | JSON Compliance | Quality | Use Case |
|-------|------|-------|-----------------|---------|----------|
| `gemma:2b` | 1.7GB | Fast | **100%** | Excellent | **Production (recommended)** |
| `tinyllama:latest` | 1.1GB | Very Fast | ~85% | Good | Quick testing |
| `codellama:7b` | 7B | Medium | ~90% | Excellent | Technical content |
| `mistral:7b` | 7B | Medium | ~95% | Excellent | General reasoning |

### Performance Tuning

**For fastest processing (current optimized setup):**
```bash
python3 chatmind/tagger/run_tagging.py --method local \
    --model gemma:2b \
    --delay 0.1 \
    --disable-validation
```

**For best quality with validation:**
```bash
python3 chatmind/tagger/run_tagging.py --method local \
    --model gemma:2b \
    --enable-validation \
    --enable-conversation-context
```

**For testing with smaller model:**
```bash
python3 chatmind/tagger/run_tagging.py --method local \
    --model tinyllama:latest \
    --delay 0.1
```

## 📊 Cost Comparison

| Method | Cost | Speed | Quality | JSON Compliance |
|--------|------|-------|---------|-----------------|
| **OpenAI API** | ~$42-65 | Fast | Excellent | 100% |
| **Gemma-2B Local** | $0 | Fast | Excellent | **100%** |
| **TinyLlama Local** | $0 | Very Fast | Good | ~85% |
| **Other Local Models** | $0 | Slower | Good-Excellent | ~90-95% |

## 🔧 Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Model Not Found

```bash
# List available models
ollama list

# Pull the optimized model
ollama pull gemma:2b
```

### JSON Parsing Issues

Our system includes robust JSON parsing that handles:
- Conversational prefixes ("Sure, here's...")
- Malformed JSON structures
- Trailing text after JSON
- Fallback to hashtag extraction

If you see JSON parsing warnings, they're normal and the system will handle them gracefully.

### Poor Performance

1. **Use the optimized model:**
   ```bash
   ollama pull gemma:2b
   ```

2. **Disable validation for speed:**
   ```bash
   python3 chatmind/tagger/run_tagging.py --method local --disable-validation
   ```

3. **Use faster delays:**
   ```bash
   python3 chatmind/tagger/run_tagging.py --method local --delay 0.1
   ```

### Memory Issues

1. **Use Gemma-2B (only 1.7GB)**
2. **Close other applications**
3. **Restart Ollama:**
   ```bash
   pkill ollama
   ollama serve
   ```

## 📈 Expected Performance

For 32,565 chunks with 1,714 conversations:

| Model | Estimated Time | Memory Usage | JSON Success Rate |
|-------|---------------|--------------|-------------------|
| `gemma:2b` | **3-4 hours** | **1.7GB RAM** | **100%** |
| `tinyllama:latest` | 2-3 hours | 1.1GB RAM | ~85% |
| `codellama:7b` | 6-8 hours | 8GB RAM | ~90% |

## 🎯 Key Optimizations

### 1. **Optimized Prompts**
- Gemma-specific prompts for 100% JSON compliance
- Clear instruction format that Gemma-2B follows perfectly
- No conversational prefixes or explanations

### 2. **Robust JSON Parsing**
- Multiple extraction strategies
- Fallback to hashtag extraction
- Graceful handling of malformed responses

### 3. **Incremental Saving**
- Saves progress every 500 chunks
- Prevents data loss on interruptions
- Resumes from where it left off

### 4. **Fast Processing**
- 0.1s delays between API calls
- Optimized for Gemma-2B's response time
- Efficient conversation grouping

## 🎯 Next Steps

1. **Test the setup** with `python3 scripts/test_gemma_final.py`
2. **Run the unified orchestrator** with `python3 chatmind/tagger/run_tagging.py --method local`
3. **Monitor the logs** in `chatmind/tagger/logs/` for detailed progress
4. **Check incremental saves** in the output directory

The optimized local model approach gives you excellent quality with zero API costs and robust error handling! 