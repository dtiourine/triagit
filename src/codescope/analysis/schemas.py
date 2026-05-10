from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from .utils import validate_github_url

GitHubRepoUrl = Annotated[str, AfterValidator(validate_github_url)]


class RepoRequest(BaseModel):
    url: GitHubRepoUrl


class ListCommitsRequest(RepoRequest):
    since: datetime | None = None


class ListIssuesRequest(RepoRequest):
    state: str = "all"


class ListPullsRequest(RepoRequest):
    state: str = "all"


class GetTreeRequest(RepoRequest):
    tree_sha: str


class GetFileContentRequest(RepoRequest):
    file_path: str
    ref: str | None = None


class GetRepoResponse(BaseModel):
    full_name: str
    description: str | None
    default_branch: str
    pushed_at: datetime | None
    size: int
    language: str | None
    archived: bool
    disabled: bool
    stars: int = 0
    forks: int = 0


class CommitResponse(BaseModel):
    sha: str
    author: str
    authored_at: datetime


class ContributorResponse(BaseModel):
    login: str
    contributions: int
    type: str


class IssueResponse(BaseModel):
    number: int
    state: str
    created_at: datetime
    closed_at: datetime | None
    is_pull_request: bool


class PullRequestResponse(BaseModel):
    number: int
    state: str
    draft: bool
    created_at: datetime
    merged_at: datetime | None
    was_merged: bool


class TreeEntryResponse(BaseModel):
    path: str
    type: str
    sha: str


class FileContentResponse(BaseModel):
    name: str
    path: str
    sha: str
    size: int
    content: str


class LanguageBreakdownResponse(BaseModel):
    bytes_per_language: dict[str, int]


class AnalysisRequest(BaseModel):
    repo_url: GitHubRepoUrl


class HygieneCheck(BaseModel):
    ok: bool
    label: str
    note: str | None = None


class MetricsReport(BaseModel):
    # Repo identity
    slug: str
    repo: GetRepoResponse
    size_fmt: str
    # Health
    score: int
    score_label: str
    breakdown: dict[str, int]
    # Activity
    commits_90d: int
    unique_authors: int
    days_since_last: int
    bus_factor_pct: int
    per_week: list[int]
    top_contributors: list[ContributorResponse]
    # Issues / PRs
    open_issues: int
    closed_issues: int
    open_prs: int
    closed_prs: int
    # Hygiene
    hygiene: list[HygieneCheck]
    hygiene_passed: int
    # Languages
    language_pcts: dict[str, int]
