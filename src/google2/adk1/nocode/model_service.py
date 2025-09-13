"""
Model Service for handling multiple LLM providers via LiteLLM
"""

import os
import logging
from typing import Dict, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)

class ModelProvider(str, Enum):
    """Supported model providers"""
    GOOGLE = "google"
    OPENAI = "openai"
    AZURE_OPENAI = "azure_openai"
    ANTHROPIC = "anthropic"
    COHERE = "cohere"
    MISTRAL = "mistral"
    OLLAMA = "ollama"

class ModelService:
    """Service for managing different LLM providers"""
    
    def __init__(self):
        self.available_models = self._get_available_models()
        self.provider_configs = self._get_provider_configs()
    
    def _get_available_models(self) -> Dict[str, Dict[str, Any]]:
        """Get available models for each provider"""
        return {
            "google": {
                "gemini-1.5-pro": {"max_tokens": 8192, "context_length": 2000000},
                "gemini-1.5-flash": {"max_tokens": 8192, "context_length": 1000000},
                "gemini-2.0-flash": {"max_tokens": 8192, "context_length": 1000000},
                "gemini-pro": {"max_tokens": 2048, "context_length": 30720}
            },
            "openai": {
                "gpt-4o": {"max_tokens": 4096, "context_length": 128000},
                "gpt-4o-mini": {"max_tokens": 16384, "context_length": 128000},
                "gpt-4-turbo": {"max_tokens": 4096, "context_length": 128000},
                "gpt-3.5-turbo": {"max_tokens": 4096, "context_length": 16385}
            },
            "azure_openai": {
                "gpt-4o": {"max_tokens": 4096, "context_length": 128000},
                "gpt-4o-mini": {"max_tokens": 16384, "context_length": 128000},
                "gpt-4-turbo": {"max_tokens": 4096, "context_length": 128000},
                "gpt-3.5-turbo": {"max_tokens": 4096, "context_length": 16385}
            },
            "anthropic": {
                "claude-3-5-sonnet-20241022": {"max_tokens": 8192, "context_length": 200000},
                "claude-3-opus-20240229": {"max_tokens": 4096, "context_length": 200000},
                "claude-3-sonnet-20240229": {"max_tokens": 4096, "context_length": 200000},
                "claude-3-haiku-20240307": {"max_tokens": 4096, "context_length": 200000}
            },
            "cohere": {
                "command-r-plus": {"max_tokens": 4096, "context_length": 128000},
                "command-r": {"max_tokens": 4096, "context_length": 128000},
                "command": {"max_tokens": 4096, "context_length": 4096}
            },
            "mistral": {
                "mistral-large": {"max_tokens": 32768, "context_length": 128000},
                "mistral-medium": {"max_tokens": 32768, "context_length": 128000},
                "mistral-small": {"max_tokens": 32768, "context_length": 128000}
            },
            "ollama": {
                "llama3.1": {"max_tokens": 4096, "context_length": 128000},
                "llama3.1:8b": {"max_tokens": 4096, "context_length": 128000},
                "llama3.1:70b": {"max_tokens": 4096, "context_length": 128000},
                "codellama": {"max_tokens": 4096, "context_length": 128000}
            }
        }
    
    def _get_provider_configs(self) -> Dict[str, Dict[str, str]]:
        """Get environment variable configurations for each provider"""
        return {
            "google": {
                "api_key": "GOOGLE_API_KEY",
                "project_id": "GOOGLE_CLOUD_PROJECT"
            },
            "openai": {
                "api_key": "OPENAI_API_KEY",
                "base_url": "OPENAI_BASE_URL"
            },
            "azure_openai": {
                "api_key": "AZURE_OPENAI_API_KEY",
                "base_url": "AZURE_OPENAI_BASE_URL",
                "api_version": "AZURE_OPENAI_API_VERSION"
            },
            "anthropic": {
                "api_key": "ANTHROPIC_API_KEY"
            },
            "cohere": {
                "api_key": "COHERE_API_KEY"
            },
            "mistral": {
                "api_key": "MISTRAL_API_KEY"
            },
            "ollama": {
                "base_url": "OLLAMA_BASE_URL"
            }
        }
    
    def get_available_models_for_provider(self, provider: str) -> Dict[str, Any]:
        """Get available models for a specific provider"""
        return self.available_models.get(provider, {})
    
    def get_model_info(self, provider: str, model: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        provider_models = self.available_models.get(provider, {})
        return provider_models.get(model)
    
    def validate_provider_config(self, provider: str) -> bool:
        """Validate if provider configuration is available"""
        config = self.provider_configs.get(provider, {})
        
        if provider == "google":
            # Google uses service account, check for credentials file
            return os.path.exists("svcacct.json") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # Check for required environment variables
        for env_var in config.values():
            if not os.getenv(env_var):
                logger.warning(f"Missing environment variable: {env_var}")
                return False
        
        return True
    
    def get_litellm_model_name(self, provider: str, model: str) -> str:
        """Convert provider and model to LiteLLM format"""
        if provider == "google":
            return f"gemini/{model}"
        elif provider == "openai":
            return f"openai/{model}"
        elif provider == "azure_openai":
            return f"azure/{model}"
        elif provider == "anthropic":
            return f"anthropic/{model}"
        elif provider == "cohere":
            return f"cohere/{model}"
        elif provider == "mistral":
            return f"mistral/{model}"
        elif provider == "ollama":
            return f"ollama/{model}"
        else:
            return model
    
    def get_provider_display_name(self, provider: str) -> str:
        """Get display name for provider"""
        display_names = {
            "google": "Google (Gemini)",
            "openai": "OpenAI (GPT)",
            "azure_openai": "Azure OpenAI",
            "anthropic": "Anthropic (Claude)",
            "cohere": "Cohere",
            "mistral": "Mistral AI",
            "ollama": "Ollama (Local)"
        }
        return display_names.get(provider, provider.title())
    
    def get_model_display_name(self, provider: str, model: str) -> str:
        """Get display name for model"""
        if provider == "google":
            return f"Gemini {model.split('-')[-1].title()}"
        elif provider == "openai":
            return f"GPT {model.replace('gpt-', '').replace('-', ' ').title()}"
        elif provider == "anthropic":
            return f"Claude {model.split('-')[-1].title()}"
        else:
            return model.replace('-', ' ').title()
