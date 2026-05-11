from fastapi import APIRouter

from .dependencies import ReviewServiceDep
from .schemas import ReviewReport, ReviewRequest

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/analyses", response_model=ReviewReport)
async def review(body: ReviewRequest, service: ReviewServiceDep) -> ReviewReport:
    return await service.get_review_report(body.repo_url)
