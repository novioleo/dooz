"""LLM API client for task decomposition."""
import logging
from typing import Optional
import json

from .config import LLMConfig

logger = logging.getLogger("dooz_server.agent.llm_client")


class LLMClient:
    """Client for calling LLM APIs (OpenAI/Anthropic/openai-compatible)."""
    
    def __init__(self, config: LLMConfig):
        """Initialize LLM client."""
        self.provider = config.provider.lower()
        self.model = config.model
        self.api_key = config.api_key
        self.base_url = config.base_url
        self.temperature = config.temperature
        self.max_tokens = config.max_tokens
        self.timeout = config.timeout_seconds
        
        self._client = None
        self._init_client()
    
    def _init_client(self):
        """Initialize the underlying LLM client."""
        if self.provider in ("openai", "openai-compatible"):
            try:
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    base_url=self.base_url,
                    timeout=self.timeout
                )
                logger.info(f"Initialized OpenAI client with model {self.model}, base_url={self.base_url}")
            except ImportError:
                logger.error("openai package not installed")
                raise ImportError("Please install openai: pip install openai")
        elif self.provider == "anthropic":
            try:
                import anthropic
                self._client = anthropic.AsyncAnthropic(
                    api_key=self.api_key,
                    timeout=self.timeout
                )
                logger.info(f"Initialized Anthropic client with model {self.model}")
            except ImportError:
                logger.error("anthropic package not installed")
                raise ImportError("Please install anthropic: pip install anthropic")
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def call(
        self,
        system_prompt: str,
        context_info: str,
        user_message: str
    ) -> str:
        """Call LLM to get task decomposition."""
        full_user_message = f"""Context Information:
{context_info}

User Task:
{user_message}"""
        
        if self.provider in ("openai", "openai-compatible"):
            return await self._call_openai(system_prompt, full_user_message)
        elif self.provider == "anthropic":
            return await self._call_anthropic(system_prompt, full_user_message)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    async def _call_openai(self, system: str, user: str) -> str:
        """Call OpenAI API."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            content = response.choices[0].message.content
            logger.debug(f"OpenAI response: {content[:100]}...")
            return content
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    async def _call_anthropic(self, system: str, user: str) -> str:
        """Call Anthropic API."""
        try:
            response = await self._client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                system=system,
                messages=[
                    {"role": "user", "content": user}
                ]
            )
            
            content = response.content[0].text
            logger.debug(f"Anthropic response: {content[:100]}...")
            return content
            
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
