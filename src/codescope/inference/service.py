from .client import HuggingFaceClient
from .schemas import LLMInferenceRequest, LLMInferenceResponse


class LLMInferenceService:
    def __init__(self, client: HuggingFaceClient):
        self._client = client

    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        return self._client.generate(
            prompt=prompt,
            max_tokens=max_tokens,
            temperature=temperature,
        )
