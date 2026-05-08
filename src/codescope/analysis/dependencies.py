from typing import Annotated

from fastapi import Depends

from codescope.github.client import GitHubClient
from codescope.github.config import get_github_config

from .service import AnalysisService


async def get_github_client():
    async with GitHubClient(get_github_config()) as client:
        yield client


async def get_analysis_service(
    github: GitHubClient = Depends(get_github_client),
) -> AnalysisService:
    return AnalysisService(github)


AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
