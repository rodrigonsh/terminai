"""Configuration management for terminai."""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration for terminai."""
    
    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager."""
        self.config_dir = Path(config_dir or os.path.expanduser("~/.terminai"))
        self.config_file = self.config_dir / "config.json"
        self.history_file = self.config_dir / "history"
        
        # Ensure directories exist
        self.config_dir.mkdir(exist_ok=True)
        (self.config_dir / "logs").mkdir(exist_ok=True)
        
        self._config = {}
        self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to load config: {e}")
                self._config = self._get_default_config()
        else:
            self._config = self._get_default_config()
            self.save_config()
        
        return self._config
    
    def save_config(self) -> None:
        """Save current configuration to file."""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self._config, f, indent=2)
        except IOError as e:
            logger.error(f"Failed to save config: {e}")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        default_config_path = Path(__file__).parent.parent.parent / "config" / "default.json"
        try:
            with open(default_config_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {
                "llm": {
                    "default_provider": "openai",
                    "providers": {}
                },
                "terminal": {
                    "history_file": str(self.history_file),
                    "prompt": "terminai> "
                }
            }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation."""
        keys = key.split('.')
        config = self._config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        config[keys[-1]] = value
    
    def get_llm_config(self, provider: Optional[str] = None) -> Dict[str, Any]:
        """Get LLM configuration for a specific provider."""
        if provider is None:
            provider = self.get("llm.default_provider", "openai")
        
        providers = self.get("llm.providers", {})
        return providers.get(provider, {})
    
    def get_active_providers(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured LLM providers."""
        return self.get("llm.providers", {})
    
    def update_provider_config(self, provider: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific LLM provider."""
        if "llm" not in self._config:
            self._config["llm"] = {}
        if "providers" not in self._config["llm"]:
            self._config["llm"]["providers"] = {}
        
        self._config["llm"]["providers"][provider] = config
        self.save_config()
    
    def get_history_file(self) -> str:
        """Get path to history file."""
        history_file = self.get("terminal.history_file", str(self.history_file))
        return os.path.expanduser(history_file)
    
    def get_prompt(self) -> str:
        """Get terminal prompt."""
        return self.get("terminal.prompt", "terminai> ")
