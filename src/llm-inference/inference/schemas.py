from datetime import datetime

from pydantic import BaseModel


class LLMRequest(BaseModel):
    model: str
    prompt: str
    max_tokens: int = 100
    temperature: float = 0.7


class LLMResponse(BaseModel):
    job_id: str
    status: str
    model: str
    created_at: datetime = datetime.now()
