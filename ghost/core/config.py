"""Configuration models and loading."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import yaml
import os
from dotenv import load_dotenv


@dataclass
class OllamaConfig:
    """Ollama configuration."""
    url: str = "http://localhost:11434"
    model: str = "mistral-nemo"
    timeout_seconds: int = 60
    retry_attempts: int = 3


@dataclass
class PersonaConfig:
    """Persona configuration."""
    name: str = "Korone"
    system_prompt: str = ""
    temperature: float = 0.88
    top_k: int = 50
    repeat_penalty: float = 1.2
    
    # Emotional defaults
    default_pleasure: float = 0.6
    default_arousal: float = 0.7
    default_dominance: float = 0.5


@dataclass
class CryostasisConfig:
    """Resource management configuration."""
    enabled: bool = True
    poll_interval_seconds: int = 5
    gpu_threshold_percent: int = 75
    cpu_threshold_percent: int = 60
    vram_threshold_mb: int = 14000
    blacklist_processes: List[str] = field(default_factory=lambda: ["notepad.exe"])


@dataclass
class MemoryConfig:
    """Memory system configuration."""
    vector_db_path: str = "data/vector_db"
    episodic_buffer_size: int = 50  # Increased from 20
    semantic_search_limit: int = 8  # Increased from 5
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # NEW: Advanced memory settings
    enable_hierarchical: bool = True
    consolidation_threshold: int = 50
    enable_summarization: bool = True
    enable_importance_scoring: bool = True
    importance_threshold: float = 0.4
    enable_redis_cache: bool = False  # Optional
    redis_url: str = "redis://localhost:6379"
    max_context_tokens: int = 3000

@dataclass
class AutonomyConfig:
    """Autonomy configuration."""
    enabled: bool = True
    min_interval_minutes: int = 60
    trigger_probability: float = 0.4
    check_interval_seconds: int = 30


@dataclass
class DiscordConfig:
    """Discord integration configuration."""
    token: str = ""
    owner_id: str = ""
    primary_channel_id: str = ""
    allowed_channels: List[str] = field(default_factory=list)
    command_prefix: str = "!"


@dataclass
class SystemConfig:
    """Main system configuration."""
    debug_mode: bool = False
    log_level: str = "INFO"
    workspace_root: Optional[str] = None
    
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    persona: PersonaConfig = field(default_factory=PersonaConfig)
    cryostasis: CryostasisConfig = field(default_factory=CryostasisConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    autonomy: AutonomyConfig = field(default_factory=AutonomyConfig)
    discord: DiscordConfig = field(default_factory=DiscordConfig)


def load_config() -> SystemConfig:
    """Load configuration from environment and files."""
    load_dotenv()
    
    # Load base config
    config = SystemConfig()
    
    # Load from environment
    config.debug_mode = os.getenv("DEBUG_MODE", "false").lower() == "true"
    config.log_level = os.getenv("LOG_LEVEL", "INFO")
    config.workspace_root = os.getenv("WORKSPACE_ROOT")
    
    # Ollama config
    config.ollama.url = os.getenv("OLLAMA_URL", config.ollama.url)
    config.ollama.model = os.getenv("OLLAMA_MODEL", config.ollama.model)
    
    # Discord config
    config.discord.token = os.getenv("DISCORD_TOKEN", "")
    config.discord.owner_id = os.getenv("DISCORD_OWNER_ID", "")
    config.discord.primary_channel_id = os.getenv("DISCORD_PRIMARY_CHANNEL", "")
    
    # Load persona from YAML if exists
    persona_path = Path("config/personas.yaml")
    if persona_path.exists():
        with open(persona_path) as f:
            persona_data = yaml.safe_load(f)
            if "personas" in persona_data and "default" in persona_data["personas"]:
                p = persona_data["personas"]["default"]
                config.persona = PersonaConfig(**p)
    
    return config


def validate_config(config: SystemConfig) -> List[str]:
    """Validate configuration and return errors."""
    errors = []
    
    if not config.discord.token:
        errors.append("DISCORD_TOKEN not set in environment")
    
    if not config.discord.owner_id:
        errors.append("DISCORD_OWNER_ID not set in environment")
    
    if config.persona.temperature < 0 or config.persona.temperature > 2:
        errors.append("Persona temperature must be between 0 and 2")
    
    return errors