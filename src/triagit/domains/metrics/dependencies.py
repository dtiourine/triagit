from typing import Annotated

from fastapi import Depends

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.dependencies import get_github_client

from .service import AnalysisService


async def get_analysis_service(
    github: GitHubClient = Depends(get_github_client),
) -> AnalysisService:
    return AnalysisService(github)


AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
