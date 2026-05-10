from typing import Protocol, TypeVar, Type

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    async def generate_structured_response(self, prompt: str, schema: Type[T], max_tokens: int = ...) -> T: ...
