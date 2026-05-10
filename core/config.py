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
            'llm': {
                'provider': os.getenv('LLM_PROVIDER', 'openai'),
                'api_key': os.getenv('LLM_API_KEY', os.getenv('OPENAI_API_KEY', '')),
                'base_url': os.getenv('LLM_BASE_URL', ''),
                'model': os.getenv('LLM_MODEL', os.getenv('OPENAI_MODEL', 'gpt-4o'))
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
    def llm_provider(self) -> str:
        return self._llm_value('provider', 'openai')

    @property
    def llm_api_key(self) -> str:
        return self._llm_value('api_key', '')

    @property
    def llm_base_url(self) -> str:
        provider = self.llm_provider
        return self._llm_value('base_url', self._provider_default(provider, 'base_url'))

    @property
    def llm_model(self) -> str:
        provider = self.llm_provider
        return self._llm_value('model', self._provider_default(provider, 'model'))

    @property
    def openai_api_key(self) -> str:
        return self.llm_api_key

    @property
    def openai_model(self) -> str:
        return self.llm_model

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

    def _llm_value(self, key: str, default: str) -> str:
        """Read new llm config with legacy openai config fallback."""
        llm_config = self._config.get('llm', {}) or {}
        openai_config = self._config.get('openai', {}) or {}
        value = llm_config.get(key)
        if value:
            return value
        if key == 'api_key':
            return openai_config.get('api_key', default)
        if key == 'model':
            return openai_config.get('model', default)
        return default

    @staticmethod
    def _provider_default(provider: str, key: str) -> str:
        presets = {
            'openai': {
                'base_url': '',
                'model': 'gpt-4o',
            },
            'deepseek': {
                'base_url': 'https://api.deepseek.com',
                'model': 'deepseek-chat',
            },
            'siliconflow': {
                'base_url': 'https://api.siliconflow.cn/v1',
                'model': 'Qwen/Qwen2.5-72B-Instruct',
            },
            'ark': {
                'base_url': 'https://ark.cn-beijing.volces.com/api/v3',
                'model': 'kimi-k2.5',
            },
        }
        return presets.get(provider, {}).get(key, '')
