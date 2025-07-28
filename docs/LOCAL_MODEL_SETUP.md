# Local Model Setup for Enhanced Tagging

This guide explains how to set up local models (Ollama) to run the enhanced tagging system without any API costs.

## 🎯 Benefits of Local Models

- **Zero API costs** - No OpenAI API charges
- **Privacy** - All processing happens locally
- **Enhanced features** - Same conversation-level context and validation
- **Incremental processing** - Only process new chunks
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

### 3. Pull a Model

Choose one of these models based on your needs:

**For general tagging (recommended):**
```bash
ollama pull llama3.1:8b
```

**For faster processing (smaller model):**
```bash
ollama pull llama3.1:3b
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
python3 scripts/test_local_model.py
```

This will:
1. Check if Ollama is running
2. Test model functionality
3. Test with sample chunks
4. Show tagging results

## 🚀 Running Local Enhanced Tagging

### Option 1: Direct Command

```bash
python3 chatmind/tagger/run_local_enhanced_tagging.py \
    --input-file data/embeddings/chunks_with_clusters.jsonl \
    --output-file data/processed/local_enhanced_tagged_chunks.jsonl \
    --model llama3.1:8b \
    --enable-validation \
    --enable-conversation-context
```

### Option 2: Use Pipeline with Local Models (Recommended)

The pipeline now supports local models with a simple flag:

```bash
# Use local models for all AI components
python3 run_pipeline.py --local

# Skip expensive steps during development
python3 run_pipeline.py --local --skip-tagging

# Force reprocess with local models
python3 run_pipeline.py --local --force-reprocess
```

## ⚙️ Configuration Options

### Model Selection

| Model | Size | Speed | Quality | Use Case |
|-------|------|-------|---------|----------|
| `llama3.1:3b` | 3B | Fast | Good | Quick testing |
| `llama3.1:8b` | 8B | Medium | Better | Production (recommended) |
| `codellama:7b` | 7B | Medium | Excellent | Technical content |
| `mistral:7b` | 7B | Medium | Excellent | General reasoning |

### Performance Tuning

**For faster processing:**
```bash
python3 chatmind/tagger/run_local_enhanced_tagging.py \
    --model llama3.1:3b \
    --delay 0.1 \
    --disable-validation
```

**For better quality:**
```bash
python3 chatmind/tagger/run_local_enhanced_tagging.py \
    --model llama3.1:8b \
    --temperature 0.1 \
    --enable-validation \
    --enable-conversation-context
```

## 📊 Cost Comparison

| Method | Cost | Speed | Quality |
|--------|------|-------|---------|
| **OpenAI API** | ~$42-65 | Fast | Excellent |
| **Local Model** | $0 | Slower | Good-Excellent |
| **Local + Validation** | $0 | Slower | Excellent |

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

# Pull the model if not available
ollama pull llama3.1:8b
```

### Poor Performance

1. **Use a smaller model:**
   ```bash
   ollama pull llama3.1:3b
   ```

2. **Disable validation:**
   ```bash
   python3 chatmind/tagger/run_local_enhanced_tagging.py --disable-validation
   ```

3. **Reduce delay:**
   ```bash
   python3 chatmind/tagger/run_local_enhanced_tagging.py --delay 0.1
   ```

### Memory Issues

1. **Use a smaller model**
2. **Close other applications**
3. **Restart Ollama:**
   ```bash
   pkill ollama
   ollama serve
   ```

## 📈 Expected Performance

For 32,565 chunks with 1,714 conversations:

| Model | Estimated Time | Memory Usage |
|-------|---------------|--------------|
| `llama3.1:3b` | 4-6 hours | 4GB RAM |
| `llama3.1:8b` | 6-8 hours | 8GB RAM |
| `codellama:7b` | 6-8 hours | 8GB RAM |

## 🎯 Next Steps

1. **Test the setup** with `python3 scripts/test_local_model.py`
2. **Run on a small sample** first to verify quality
3. **Update your pipeline** to use local models
4. **Monitor the results** and adjust model/parameters as needed

The local model approach gives you the same enhanced features as the OpenAI version but with zero API costs! 