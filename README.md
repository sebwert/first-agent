cat > README.md << 'EOF'
# LangChain MCP Agent

A LangChain agent with Ollama, HuggingFace models, and MCP server integration.

## Setup

1. Install dependencies:
```bash
uv sync

## Environment Configuration

### Quick Setup

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Edit .env with your actual values
nano .env  # or use your preferred editor
```

**Required changes:**
- Replace placeholder URLs with your actual server addresses
- Update model names to match your available models  
- Set correct file paths for your system

### Environment Variables Reference

#### MongoDB MCP Server

| Variable | Description | Example |
|----------|-------------|---------|
| `MCP_MONGODB_CONNECTION_STRING` | Full MongoDB connection string with credentials | `mongodb://username:password@host:port/database` |
| `MCP_MONGODB_SERVER_PATH` | Absolute path to MongoDB MCP server executable | `/path/to/mongodb-mcp-server/dist/index.js` |

#### Browser-Use MCP Server

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `MCP_BROWSER_USE_LLM_PROVIDER` | LLM provider | `ollama` | `ollama` |
| `MCP_BROWSER_USE_LLM_MODEL_NAME` | Model for browser automation | - | Any Ollama model |
| `MCP_BROWSER_USE_LLM_OLLAMA_NUM_CTX` | Context window size | `40000` | Number of tokens |
| `MCP_BROWSER_USE_LLM_TEMPERATURE` | Model temperature | `0.0` | `0.0-1.0` |
| `MCP_BROWSER_USE_LLM_BASE_URL` | Ollama server URL | `http://localhost:11434` | Valid HTTP URL |
| `MCP_BROWSER_USE_LLM_OLLAMA_NUM_PREDICT` | Max tokens to generate | `-2` | `-2` (unlimited) or positive number |
| `MCP_BROWSER_USE_BROWSER_HEADLESS` | Run browser headlessly | `true` | `true`, `false` |
| `MCP_BROWSER_USE_BROWSER_WINDOW_WIDTH` | Browser window width | `900` | Pixels |
| `MCP_BROWSER_USE_AGENT_TOOL_MAX_INPUT_TOKENS` | Max input tokens for tools | `40000` | Number of tokens |
| `MCP_BROWSER_USE_SERVER_LOGGING_LEVEL` | Logging level | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

#### Model Configuration

**Variable:** `MCP_MODEL_CONFIG`  
**Format:** JSON string containing model definitions

**Example structure:**
```json
{
    "model-name": {
        "class_name": "ChatOllama",
        "kwargs": {
            "model": "actual-model-name",
            "temperature": 0.0,
            "num_ctx": 40000,
            "base_url": "http://localhost:11434"
        }
    }
}
```

**Model Parameters:**

| Parameter | Description | Type | Example |
|-----------|-------------|------|---------|
| `model` | Exact model name in Ollama | string | `"qwen3:30b"` |
| `temperature` | Response randomness | float | `0.0` (deterministic) to `1.0` |
| `num_ctx` | Context window size | integer | `40000` |
| `num_predict` | Max tokens to generate | integer | `-2` (unlimited) or positive number |
| `base_url` | Ollama server endpoint | string | `"http://localhost:11434"` |
| `think` | Enable thinking mode | boolean | `true` or `false` |

#### Global Settings

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `ANONYMIZED_TELEMETRY` | Disable telemetry collection | `false` | `true`, `false` |

---

### Configuration Examples

#### Local Development
```bash
MCP_MONGODB_CONNECTION_STRING=mongodb://root:password@localhost:27017/testdb
MCP_BROWSER_USE_LLM_BASE_URL=http://localhost:11434
```

#### Remote Servers
```bash
MCP_MONGODB_CONNECTION_STRING=mongodb://user:pass@192.168.1.100:27017/proddb
MCP_BROWSER_USE_LLM_BASE_URL=http://192.168.1.200:11434
```

---

### Troubleshooting

#### Common Issues

**🚫 "Model not found" errors:**
- Verify model names match exactly with `ollama list`
- Check that Ollama server is running and accessible

**🔌 Connection errors:**
- Verify URLs are reachable from your machine
- Check firewall settings for the specified ports  
- Ensure MongoDB server is running and accessible

**📝 JSON parsing errors:**
- Validate your `MCP_MODEL_CONFIG` JSON syntax
- Use single quotes around the entire JSON value
- Ensure no trailing commas in JSON

#### Testing Your Configuration

```python
# Test environment loading
from dotenv import load_dotenv
import os
import json

load_dotenv()

# Test MongoDB connection
print("MongoDB:", os.getenv("MCP_MONGODB_CONNECTION_STRING"))

# Test model config parsing  
try:
    config = json.loads(os.getenv("MCP_MODEL_CONFIG", "{}"))
    print(f"✅ Found {len(config)} models configured")
except json.JSONDecodeError as e:
    print(f"❌ JSON error: {e}")
```