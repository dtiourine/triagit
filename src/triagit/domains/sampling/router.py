from fastapi import APIRouter

from .dependencies import SamplingServiceDep
from .schemas import SamplingRequest, SamplingReport

router = APIRouter(prefix="/samples", tags=["samples"])


@router.post("", response_model=SamplingReport)
async def sample(body: SamplingRequest, service: SamplingServiceDep) -> SamplingReport:
    return await service.sample(body.repo_url)
