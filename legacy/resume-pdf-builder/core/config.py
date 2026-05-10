"""
Configuration management for resume PDF builder.
Supports YAML config files and .env environment variables.
"""

import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuration manager that loads from YAML and environment variables."""

    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from YAML file."""
        config_path = BASE_DIR / "config.yaml"

        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f)
        else:
            self._config = self._default_config()

        # Resolve environment variables in config
        self._resolve_env_vars(self._config)

    def _resolve_env_vars(self, obj):
        """Recursively resolve ${ENV_VAR} placeholders in config."""
        if isinstance(obj, dict):
            for key, value in obj.items():
                obj[key] = self._resolve_env_vars(value)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                obj[i] = self._resolve_env_vars(item)
        elif isinstance(obj, str) and obj.startswith('${') and obj.endswith('}'):
            env_var = obj[2:-1]
            return os.getenv(env_var, '')
        return obj

    def _default_config(self):
        """Return default configuration."""
        return {
            'openai': {
                'api_key': os.getenv('OPENAI_API_KEY', ''),
                'model': 'gpt-4o'
            },
            'paths': {
                'templates_dir': str(BASE_DIR / 'templates'),
                'output_dir': str(BASE_DIR / 'output')
            },
            'pdf': {
                'default_template': 'default.html',
                'page_size': 'A4'
            }
        }

    @property
    def openai_api_key(self) -> str:
        return self._config.get('openai', {}).get('api_key', '')

    @property
    def openai_model(self) -> str:
        return self._config.get('openai', {}).get('model', 'gpt-4o')

    @property
    def templates_dir(self) -> str:
        return self._config.get('paths', {}).get('templates_dir', str(BASE_DIR / 'templates'))

    @property
    def output_dir(self) -> str:
        return self._config.get('paths', {}).get('output_dir', str(BASE_DIR / 'output'))

    @property
    def default_template(self) -> str:
        return self._config.get('pdf', {}).get('default_template', 'default.html')

    @property
    def page_size(self) -> str:
        return self._config.get('pdf', {}).get('page_size', 'A4')

    def get(self, *keys, default=None):
        """Get a nested config value by keys."""
        value = self._config
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return default
            if value is None:
                return default
        return value
