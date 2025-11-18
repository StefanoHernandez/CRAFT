"""Configuration management for CRAFT."""

import os
import json
import yaml
from pathlib import Path
from typing import Any, Dict, Optional, Union
from pydantic import BaseModel, Field


class Config(BaseModel):
    """Main configuration class for CRAFT."""

    # Provider settings
    provider: str = Field(default="anthropic", description="Default LLM provider")
    provider_config: Dict[str, Any] = Field(default_factory=dict)

    # RAG settings
    rag_enabled: bool = Field(default=False)
    rag_config: Dict[str, Any] = Field(default_factory=dict)

    # Memory settings
    memory_enabled: bool = Field(default=True)
    memory_config: Dict[str, Any] = Field(default_factory=dict)

    # API settings
    api_key: Optional[str] = Field(default=None)
    api_base_url: Optional[str] = Field(default=None)

    # Feature flags
    streaming: bool = Field(default=True)
    multilingual: bool = Field(default=True)
    analytics: bool = Field(default=False)

    # Logging
    log_level: str = Field(default="INFO")
    log_file: Optional[str] = Field(default=None)

    class Config:
        extra = "allow"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Config":
        """Create config from dictionary."""
        return cls(**data)

    @classmethod
    def from_file(cls, path: Union[str, Path]) -> "Config":
        """Load configuration from YAML or JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, "r") as f:
            if path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            elif path.suffix == ".json":
                data = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {path.suffix}")

        return cls.from_dict(data)

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        return cls(
            provider=os.getenv("CRAFT_PROVIDER", "anthropic"),
            api_key=os.getenv("CRAFT_API_KEY"),
            api_base_url=os.getenv("CRAFT_API_BASE_URL"),
            streaming=os.getenv("CRAFT_STREAMING", "true").lower() == "true",
            multilingual=os.getenv("CRAFT_MULTILINGUAL", "true").lower() == "true",
            log_level=os.getenv("CRAFT_LOG_LEVEL", "INFO"),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.model_dump()

    def to_file(self, path: Union[str, Path], format: str = "yaml") -> None:
        """Save configuration to file."""
        path = Path(path)
        data = self.to_dict()

        with open(path, "w") as f:
            if format in ["yaml", "yml"]:
                yaml.dump(data, f, default_flow_style=False)
            elif format == "json":
                json.dump(data, f, indent=2)
            else:
                raise ValueError(f"Unsupported format: {format}")


def load_config(
    config_path: Optional[Union[str, Path]] = None,
    use_env: bool = True,
    **kwargs: Any,
) -> Config:
    """
    Load configuration from file, environment, or kwargs.

    Priority: kwargs > file > env > defaults

    Args:
        config_path: Path to config file (YAML or JSON)
        use_env: Whether to load from environment variables
        **kwargs: Additional config overrides

    Returns:
        Config instance
    """
    # Start with defaults
    config_data: Dict[str, Any] = {}

    # Load from environment
    if use_env:
        env_config = Config.from_env()
        config_data.update(env_config.to_dict())

    # Load from file
    if config_path:
        file_config = Config.from_file(config_path)
        config_data.update(file_config.to_dict())

    # Apply kwargs overrides
    config_data.update(kwargs)

    return Config.from_dict(config_data)
