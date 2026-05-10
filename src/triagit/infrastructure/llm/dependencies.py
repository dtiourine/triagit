from typing import Annotated

from fastapi import Depends

from triagit.infrastructure.llm.base import LLMClient
from triagit.infrastructure.llm.config import get_llm_config


def get_llm_client() -> LLMClient:
    config = get_llm_config()
    match config.provider:
        case "anthropic":
            from triagit.infrastructure.llm.providers.anthropic import AnthropicLLMClient
            return AnthropicLLMClient(config)
        case "openai":
            from triagit.infrastructure.llm.providers.openai import OpenAILLMClient
            return OpenAILLMClient(config)


LLMClientDep = Annotated[LLMClient, Depends(get_llm_client)]
