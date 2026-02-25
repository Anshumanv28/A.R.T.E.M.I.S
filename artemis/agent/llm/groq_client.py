"""
Groq LLM client wrapper.

Provides a simple interface for generating responses using Groq API.
"""

from typing import Optional, Dict, Any
from groq import Groq

from artemis.utils import get_logger

logger = get_logger(__name__)


class GroqClient:
    """
    Wrapper for Groq LLM API.
    
    Provides a unified generate() interface that matches other LLM clients.
    """
    
    def __init__(self, api_key: str, model_name: str = "llama-3.3-70b-versatile"):
        """
        Initialize Groq client.
        
        Args:
            api_key: Groq API key
            model_name: Model name to use (default: llama-3.3-70b-versatile)
        """
        self.client = Groq(api_key=api_key)
        self.model_name = model_name
        logger.debug(f"Initialized GroqClient with model: {model_name}")
    
    def generate(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[list] = None,
        **kwargs
    ) -> str:
        """
        Generate a response using Groq API.
        
        Args:
            system_prompt: System prompt/instructions
            user_prompt: User query/prompt
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            stop: Optional list of stop sequences
            **kwargs: Additional parameters passed to Groq API
            
        Returns:
            Generated text response
            
        Raises:
            Exception: If API call fails
        """
        try:
            logger.debug(f"Generating response with Groq (model: {self.model_name})")
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stop=stop,
                **kwargs
            )
            
            result = response.choices[0].message.content
            logger.debug(f"Generated response ({len(result)} chars)")
            return result
            
        except Exception as e:
            logger.exception(f"Error generating response with Groq: {e}")
            raise
