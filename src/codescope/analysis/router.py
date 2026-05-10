from typing import Annotated

from fastapi import APIRouter, Depends

from .dependencies import AnalysisServiceDep
from .schemas import (
    AnalysisRequest,
    CommitResponse,
    ContributorResponse,
    FileContentResponse,
    GetFileContentRequest,
    GetRepoResponse,
    GetTreeRequest,
    IssueResponse,
    LanguageBreakdownResponse,
    ListCommitsRequest,
    ListIssuesRequest,
    ListPullsRequest,
    MetricsReport,
    PullRequestResponse,
    RepoRequest,
    TreeEntryResponse,
)

router = APIRouter(prefix="/analysis", tags=["analysis"])


@router.get("/repo", response_model=GetRepoResponse)
async def get_repo(
    params: Annotated[RepoRequest, Depends()],
    service: AnalysisServiceDep,
) -> GetRepoResponse:
    return await service.get_repo(params.url)


@router.get("/commits", response_model=list[CommitResponse])
async def list_commits(
    params: Annotated[ListCommitsRequest, Depends()],
    service: AnalysisServiceDep,
) -> list[CommitResponse]:
    return await service.list_commits(params.url, since=params.since)


@router.get("/contributors", response_model=list[ContributorResponse])
async def list_contributors(
    params: Annotated[RepoRequest, Depends()],
    service: AnalysisServiceDep,
) -> list[ContributorResponse]:
    return await service.list_contributors(params.url)


@router.get("/issues", response_model=list[IssueResponse])
async def list_issues(
    params: Annotated[ListIssuesRequest, Depends()],
    service: AnalysisServiceDep,
) -> list[IssueResponse]:
    return await service.list_issues(params.url, state=params.state)


@router.get("/pulls", response_model=list[PullRequestResponse])
async def list_pulls(
    params: Annotated[ListPullsRequest, Depends()],
    service: AnalysisServiceDep,
) -> list[PullRequestResponse]:
    return await service.list_pulls(params.url, state=params.state)


@router.get("/tree", response_model=list[TreeEntryResponse])
async def get_tree(
    params: Annotated[GetTreeRequest, Depends()],
    service: AnalysisServiceDep,
) -> list[TreeEntryResponse]:
    return await service.get_tree(params.url, params.tree_sha)


@router.get("/file", response_model=FileContentResponse)
async def get_file_content(
    params: Annotated[GetFileContentRequest, Depends()],
    service: AnalysisServiceDep,
) -> FileContentResponse:
    return await service.get_file_content(params.url, params.file_path, ref=params.ref)


@router.get("/languages", response_model=LanguageBreakdownResponse)
async def get_languages(
    params: Annotated[RepoRequest, Depends()],
    service: AnalysisServiceDep,
) -> LanguageBreakdownResponse:
    return await service.get_languages(params.url)


@router.post("/analyses", response_model=MetricsReport)
async def analyze(
    body: AnalysisRequest,
    service: AnalysisServiceDep,
) -> MetricsReport:
    return await service.get_metrics_report(body.repo_url)
