from typing import TypeVar, Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from triagit.infrastructure.llm.config import LLMConfig

T = TypeVar("T", bound=BaseModel)


class OpenAILLMClient:
    def __init__(self, llm_config: LLMConfig):
        self._client = AsyncOpenAI(api_key=llm_config.api_key.get_secret_value())
        self.model = llm_config.model

    async def generate_structured_response(self, prompt: str, schema: Type[T], max_tokens: int = 1024) -> T:
        response = await self._client.beta.chat.completions.parse(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
            response_format=schema,
        )
        return response.choices[0].message.parsed
