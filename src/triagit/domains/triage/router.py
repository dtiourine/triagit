from fastapi import APIRouter

from .dependencies import TriageServiceDep
from .schemas import TriageReport

router = APIRouter(tags=["triage"])


@router.get("/triage/reports", response_model=TriageReport)
async def get_triage_report(
    url: str,
    service: TriageServiceDep,
) -> TriageReport:
    return await service.get_triage_report(url)
