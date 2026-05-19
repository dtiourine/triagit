from typing import Annotated

from fastapi import Depends

from triagit.infrastructure.github.client import GitHubClient
from triagit.infrastructure.github.dependencies import get_github_client
from triagit.infrastructure.llm.base import LLMClient
from triagit.infrastructure.llm.dependencies import get_llm_client

from .service import TriageService


async def get_triage_service(
    github: GitHubClient = Depends(get_github_client),
    llm: LLMClient = Depends(get_llm_client),
) -> TriageService:
    return TriageService(github, llm)


TriageServiceDep = Annotated[TriageService, Depends(get_triage_service)]
