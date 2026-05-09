from typing import Annotated

from fastapi import APIRouter, Query

from .dependencies import AnalysisServiceDep
from .schemas import GetRepoResponse, GitHubRepoUrl

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/repo", response_model=GetRepoResponse)
async def get_repo(
    url: Annotated[GitHubRepoUrl, Query()],
    service: AnalysisServiceDep,
) -> GetRepoResponse:
    return await service.get_repo(url)
