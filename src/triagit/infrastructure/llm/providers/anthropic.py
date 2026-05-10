from typing import TypeVar, Type

from anthropic import AsyncAnthropic
from pydantic import BaseModel

from triagit.infrastructure.llm.config import LLMConfig

T = TypeVar("T", bound=BaseModel)


class AnthropicLLMClient:
    def __init__(self, llm_config: LLMConfig):
        self._client = AsyncAnthropic(api_key=llm_config.api_key.get_secret_value())
        self.model = llm_config.model

    async def generate_structured_response(self, prompt: str, schema: Type[T], max_tokens: int = 1024) -> T:
        response = await self._client.messages.parse(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            output_format=schema,
        )
        return response.parsed_output
