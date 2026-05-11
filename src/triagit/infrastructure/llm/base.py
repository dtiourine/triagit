from pyexpat import model
from typing import Protocol, Type, TypeVar

from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class LLMClient(Protocol):
    model: str

    async def generate_structured_response(
        self, prompt: str, schema: Type[T], max_tokens: int = ...
    ) -> T: ...
