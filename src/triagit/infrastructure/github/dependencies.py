from typing import Annotated

from fastapi import Depends

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.config import get_github_config


async def get_github_client():
    async with GitHubClient(get_github_config()) as client:
        yield client


GitHubClientDep = Annotated[GitHubClient, Depends(get_github_client)]
