from fastapi import APIRouter

from codescope.github.schemas import RepoInfo

from .dependencies import AnalysisServiceDep

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/repos/{owner}/{repo}", response_model=RepoInfo)
async def get_repo(
    owner: str,
    repo: str,
    service: AnalysisServiceDep,
) -> RepoInfo:
    return await service.get_repo(owner, repo)
