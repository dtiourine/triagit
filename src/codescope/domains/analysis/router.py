from fastapi import APIRouter

from .dependencies import AnalysisServiceDep
from .schemas import AnalysisRequest, MetricsReport

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.post("/analyses", response_model=MetricsReport)
async def analyze(body: AnalysisRequest, service: AnalysisServiceDep) -> MetricsReport:
    return await service.get_metrics_report(body.repo_url)
