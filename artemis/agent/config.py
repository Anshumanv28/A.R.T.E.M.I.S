"""
Configuration for the agent layer.

Handles provider selection, model configuration, and retrieval defaults.
"""

import os
from typing import Literal, Optional
from dataclasses import dataclass


@dataclass
class AgentConfig:
    """
    Configuration for the agent layer.
    
    Attributes:
        provider: LLM provider to use ("groq" or "openai")
        model_name: Model name for the selected provider
        max_tokens: Maximum tokens for LLM responses
        temperature: Temperature for LLM generation
        retrieval_k: Default number of documents to retrieve
        groq_api_key: Groq API key (from env if not provided)
        openai_api_key: OpenAI API key (from env if not provided)
    """
    provider: Literal["groq", "openai"] = "groq"
    model_name: str = "llama-3.3-70b-versatile"
    max_tokens: int = 2048
    temperature: float = 0.7
    retrieval_k: int = 5
    max_tool_steps: int = 10  # Cap on tool calls per turn; planner should move to direct when at limit
    
    groq_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    
    def __post_init__(self):
        """Load API keys from environment if not provided."""
        if self.provider == "groq" and not self.groq_api_key:
            self.groq_api_key = os.getenv("GROQ_API_KEY")
            if not self.groq_api_key:
                raise ValueError(
                    "GROQ_API_KEY not found in environment. "
                    "Set it in .env or pass groq_api_key parameter."
                )
        
        if self.provider == "openai" and not self.openai_api_key:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")
            if not self.openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY not found in environment. "
                    "Set it in .env or pass openai_api_key parameter."
                )
    
    @classmethod
    def from_env(cls, **kwargs) -> "AgentConfig":
        """
        Create config from environment variables with optional overrides.
        
        Args:
            **kwargs: Override any config values
            
        Returns:
            AgentConfig instance
        """
        return cls(
            provider=kwargs.get("provider", os.getenv("ARTEMIS_LLM_PROVIDER", "groq")),
            model_name=kwargs.get("model_name", os.getenv("ARTEMIS_LLM_MODEL", "llama-3.3-70b-versatile")),
            max_tokens=int(kwargs.get("max_tokens", os.getenv("ARTEMIS_MAX_TOKENS", "2048"))),
            temperature=float(kwargs.get("temperature", os.getenv("ARTEMIS_TEMPERATURE", "0.7"))),
            retrieval_k=int(kwargs.get("retrieval_k", os.getenv("ARTEMIS_RETRIEVAL_K", "5"))),
            max_tool_steps=int(kwargs.get("max_tool_steps", os.getenv("ARTEMIS_MAX_TOOL_STEPS", "10"))),
            groq_api_key=kwargs.get("groq_api_key"),
            openai_api_key=kwargs.get("openai_api_key"),
        )
