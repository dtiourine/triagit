from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from .utils import validate_github_url

GitHubRepoUrl = Annotated[str, AfterValidator(validate_github_url)]


# --- Requests ---

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


# --- Responses ---

class GetRepoResponse(BaseModel):
    full_name: str
    description: str | None
    default_branch: str
    pushed_at: datetime | None
    size: int
    language: str | None
    archived: bool
    disabled: bool


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
