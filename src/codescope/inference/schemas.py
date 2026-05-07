from datetime import datetime

from pydantic import BaseModel


class LLMInferenceRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7


class LLMInferenceResponse(BaseModel):
    job_id: str
    status: str
    model: str
    created_at: datetime = datetime.now()
