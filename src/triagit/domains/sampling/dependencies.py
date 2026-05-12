from typing import Annotated

from fastapi import Depends

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.dependencies import get_github_client

from .service import SamplingService


async def get_sampling_service(
    github: GitHubClient = Depends(get_github_client),
) -> SamplingService:
    return SamplingService(github)


SamplingServiceDep = Annotated[SamplingService, Depends(get_sampling_service)]
