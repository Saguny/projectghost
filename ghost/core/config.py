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
    temperature: float = 0.72
    top_k: int = 40
    repeat_penalty: float = 1.2
    
    # Emotional defaults
    default_pleasure: float = 0.6
    default_arousal: float = 0.7
    default_dominance: float = 0.5

    max_output_tokens: int = 150  # Default low to prevent rambling
    stop_tokens: List[str] = field(default_factory=lambda: [
        "<|im_end|>", 
        "<|im_start|>", 
        "User:", 
        "user:", 
        "System:",
        "\nUser", 
        "\n\n"
    ])


@dataclass
class CryostasisConfig:
    """Resource management configuration."""
    enabled: bool = True
    poll_interval_seconds: int = 5
    gpu_threshold_percent: int = 75
    cpu_threshold_percent: int = 60
    vram_threshold_mb: int = 14000
    blacklist_processes: List[str] = field(default_factory=lambda: ["notepad.exe"])
    wake_cooldown_seconds: int = 10  # Reduced from 30


@dataclass
class MemoryConfig:
    """Memory system configuration."""
    vector_db_path: str = "data/vector_db"
    episodic_buffer_size: int = 50
    semantic_search_limit: int = 8
    embedding_model: str = "all-MiniLM-L6-v2"
    
    # Advanced memory settings
    enable_hierarchical: bool = True
    consolidation_threshold: int = 40  # FIXED: Was 50, same as buffer size
    enable_summarization: bool = True
    enable_importance_scoring: bool = True
    importance_threshold: float = 0.4
    
    # Redis cache (optional)
    enable_redis_cache: bool = False
    redis_url: str = "redis://localhost:6379"
    
    # Token management
    max_context_tokens: int = 3000
    
    # Auto-snapshots
    auto_snapshot_enabled: bool = True
    auto_snapshot_interval_hours: int = 24


@dataclass
class AutonomyConfig:
    """Autonomy configuration."""
    enabled: bool = True
    min_interval_minutes: int = 60
    trigger_probability: float = 0.4
    check_interval_seconds: int = 30
    silence_threshold_minutes: int = 180  # 3 hours


@dataclass
class DiscordConfig:
    """Discord integration configuration."""
    token: str = ""
    owner_id: str = ""
    primary_channel_id: str = ""
    allowed_channels: List[str] = field(default_factory=list)
    command_prefix: str = "!"


@dataclass
class EmotionConfig:
    """Emotion system configuration."""
    pad_decay_rate: float = 0.05
    time_based_decay: bool = True  # Decay based on time, not messages
    decay_interval_seconds: int = 300  # 5 minutes
    enable_circadian: bool = True
    circadian_update_interval_seconds: int = 3600  # 1 hour


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
    emotion: EmotionConfig = field(default_factory=EmotionConfig)


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
    
    # Cryostasis config
    config.cryostasis.enabled = os.getenv("CRYOSTASIS_ENABLED", "true").lower() == "true"
    config.cryostasis.gpu_threshold_percent = int(
        os.getenv("GPU_THRESHOLD_PERCENT", str(config.cryostasis.gpu_threshold_percent))
    )
    config.cryostasis.cpu_threshold_percent = int(
        os.getenv("CPU_THRESHOLD_PERCENT", str(config.cryostasis.cpu_threshold_percent))
    )
    config.cryostasis.vram_threshold_mb = int(
        os.getenv("VRAM_THRESHOLD_MB", str(config.cryostasis.vram_threshold_mb))
    )
    
    # Memory config
    config.memory.episodic_buffer_size = int(
        os.getenv("EPISODIC_BUFFER_SIZE", str(config.memory.episodic_buffer_size))
    )
    config.memory.semantic_search_limit = int(
        os.getenv("SEMANTIC_SEARCH_LIMIT", str(config.memory.semantic_search_limit))
    )
    
    # Autonomy config
    config.autonomy.enabled = os.getenv("AUTONOMY_ENABLED", "true").lower() == "true"
    config.autonomy.min_interval_minutes = int(
        os.getenv("MIN_INTERVAL_MINUTES", str(config.autonomy.min_interval_minutes))
    )
    config.autonomy.trigger_probability = float(
        os.getenv("TRIGGER_PROBABILITY", str(config.autonomy.trigger_probability))
    )
    
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
    
    # Discord validation
    if not config.discord.token:
        errors.append("DISCORD_TOKEN not set in environment")
    
    if not config.discord.owner_id:
        errors.append("DISCORD_OWNER_ID not set in environment")
    
    # Persona validation
    if config.persona.temperature < 0 or config.persona.temperature > 2:
        errors.append("Persona temperature must be between 0 and 2")
    
    if not -1.0 <= config.persona.default_pleasure <= 1.0:
        errors.append("default_pleasure must be between -1 and 1")
    
    if not -1.0 <= config.persona.default_arousal <= 1.0:
        errors.append("default_arousal must be between -1 and 1")
    
    if not -1.0 <= config.persona.default_dominance <= 1.0:
        errors.append("default_dominance must be between -1 and 1")
    
    # Memory validation
    if config.memory.consolidation_threshold >= config.memory.episodic_buffer_size:
        errors.append(
            f"consolidation_threshold ({config.memory.consolidation_threshold}) "
            f"must be less than episodic_buffer_size ({config.memory.episodic_buffer_size})"
        )
    
    if config.memory.importance_threshold < 0 or config.memory.importance_threshold > 1:
        errors.append("importance_threshold must be between 0 and 1")
    
    # Autonomy validation
    if config.autonomy.trigger_probability < 0 or config.autonomy.trigger_probability > 1:
        errors.append("trigger_probability must be between 0 and 1")
    
    # Cryostasis validation
    if config.cryostasis.gpu_threshold_percent < 0 or config.cryostasis.gpu_threshold_percent > 100:
        errors.append("gpu_threshold_percent must be between 0 and 100")
    
    if config.cryostasis.cpu_threshold_percent < 0 or config.cryostasis.cpu_threshold_percent > 100:
        errors.append("cpu_threshold_percent must be between 0 and 100")
    
    return errors