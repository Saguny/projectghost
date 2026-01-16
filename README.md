# Project Ghost

A production-grade autonomous AI companion with dynamic resource management, emotional modeling, and semantic memory.

## Features

- **Tri-Layer Architecture**: Decoupled event-driven design
- **Semantic Memory**: ChromaDB-powered long-term memory with RAG
- **Emotional State**: PAD (Pleasure-Arousal-Dominance) model with circadian rhythms
- **Cryostasis**: Dynamic GPU/CPU resource management
- **Discord Integration**: Natural conversation interface
- **Robust Error Handling**: Retry logic, graceful degradation, health checks

## Prerequisites

### Required
- Python 3.10+
- [Ollama](https://ollama.ai/) installed and running
- Discord Bot Token

### Recommended
- NVIDIA GPU with 16GB+ VRAM (for local LLM)
- 16GB+ System RAM

### For GPU Monitoring (Optional)
- NVIDIA drivers
- `nvidia-ml-py` (install with `pip install nvidia-ml-py`)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd project_ghost
```

### 2. Install Dependencies

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

Required environment variables:
- `DISCORD_TOKEN`: Your Discord bot token
- `DISCORD_OWNER_ID`: Your Discord user ID
- `OLLAMA_URL`: Ollama server URL (default: http://localhost:11434)

### 4. Setup Ollama

```bash
# Install Ollama (if not already installed)
# See: https://ollama.ai/

# Pull a model
ollama pull mistral-nemo

# Or use a custom fine-tuned model
ollama create korone-v2 -f Modelfile
```

### 5. Create Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create New Application
3. Go to "Bot" section
4. Create bot and copy token to `.env`
5. Enable "Message Content Intent"
6. Invite bot to server with permissions:
   - Send Messages
   - Read Message History
   - View Channels

### 6. Run

```bash
python main.py
```

## Configuration

### Personas

Edit `config/personas.yaml` to customize personality:

```yaml
personas:
  default:
    name: "Your AI Name"
    system_prompt: |
      Your personality definition here...
    temperature: 0.88
    default_pleasure: 0.6
    default_arousal: 0.7
    default_dominance: 0.5
```

### Cryostasis Thresholds

Adjust resource thresholds in `.env` or code:

```python
# In ghost/core/config.py
class CryostasisConfig:
    gpu_threshold_percent: int = 75
    cpu_threshold_percent: int = 60
    blacklist_processes: List[str] = ["game.exe"]
```

### Memory Settings

Adjust in `ghost/core/config.py`:

```python
class MemoryConfig:
    episodic_buffer_size: int = 20  # Recent messages
    semantic_search_limit: int = 5   # RAG results
```

## Usage

### Basic Interaction

Send messages in Discord:
```
User: hey, how are you?
Bot: hey! i'm good, just hanging out here
```

### Commands (Future)

```
!health - System health check
!memory clear - Clear memory (owner only)
!snapshot - Create memory snapshot
```

### Monitoring

Logs are written to `data/logs/ghost.log`:

```bash
tail -f data/logs/ghost.log
```

## Architecture

```
┌─────────────────────────────────────────┐
│         Discord Interface                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│           Event Bus                      │
│  (MessageReceived, StateChanged, etc)   │
└───┬─────────┬──────────┬────────────┬───┘
    │         │          │            │
┌───▼────┐ ┌──▼─────┐ ┌─▼────────┐ ┌─▼──────┐
│Memory  │ │Emotion │ │Inference │ │Cryo    │
│Service │ │Service │ │Service   │ │stasis  │
└────────┘ └────────┘ └──────────┘ └────────┘
```

### Key Components

- **Event Bus**: Decoupled pub/sub communication
- **Memory Service**: Vector DB + Episodic Buffer
- **Emotion Service**: PAD model + Circadian rhythm
- **Inference Service**: Ollama client + Prompt building
- **Cryostasis**: Resource monitoring + Model unloading

## Development

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

### Code Quality

```bash
# Format
black ghost/ tests/

# Lint
ruff ghost/ tests/

# Type Check
mypy ghost/
```

### Adding Sensors

Create a new sensor in `ghost/sensors/`:

```python
from ghost.core.interfaces import ISensor

class CustomSensor(ISensor):
    def get_context(self) -> str:
        return "Custom context here"
    
    def get_name(self) -> str:
        return "CustomSensor"
```

Register in `main.py`:

```python
sensors = [
    HardwareSensor(config.cryostasis),
    TimeSensor(),
    CustomSensor()  # Add here
]
```

## Deployment

### Docker

```bash
# Build
docker-compose build

# Run
docker-compose up -d

# Logs
docker-compose logs -f

# Stop
docker-compose down
```

### Production Considerations

1. **Secrets Management**: Use Docker secrets or vault
2. **Monitoring**: Add Prometheus/Grafana for metrics
3. **Backup**: Automate `data/` backups
4. **Rate Limiting**: Implement per-user limits
5. **Scaling**: Use Redis for event bus in multi-instance setup

## Troubleshooting

### Bot not responding

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Check logs
tail -f data/logs/ghost.log

# Verify token
echo $DISCORD_TOKEN
```

### Model fails to load

- Check GPU VRAM: `nvidia-smi`
- Try smaller model: `ollama pull mistral:7b`
- Increase swap space

### High memory usage

- Reduce `episodic_buffer_size`
- Lower `semantic_search_limit`
- Enable cryostasis

## Contributing

1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

## License

MIT License - See LICENSE file

## Support

- Issues: GitHub Issues
