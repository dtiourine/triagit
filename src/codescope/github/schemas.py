import base64
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator


class GitHubModel(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True, frozen=True)


# ---- get_repo ----
class License(GitHubModel):
    spdx_id: str | None
    name: str | None


class RepoInfo(GitHubModel):
    full_name: str
    description: str | None
    default_branch: str
    pushed_at: datetime | None
    size: int
    language: str | None
    archived: bool
    disabled: bool
    license: License | None
    stargazers_count: int = 0
    forks_count: int = 0


# ---- list_commits ----
class GitAuthor(GitHubModel):
    name: str | None
    email: str | None
    date: datetime


class GitHubUser(GitHubModel):
    login: str
    id: int


class CommitDetail(GitHubModel):
    author: GitAuthor


class Commit(GitHubModel):
    sha: str
    commit: CommitDetail
    author: GitHubUser | None = None

    @field_validator("author", mode="before")
    @classmethod
    def coerce_empty_user(cls, v):
        if isinstance(v, dict) and not v:
            return None
        return v

    @property
    def author_identity(self) -> str:
        if self.author:
            return f"gh:{self.author.login}"
        if self.commit.author.email:
            return f"email:{self.commit.author.email}"
        return f"name:{self.commit.author.name or 'unknown'}"

    @property
    def authored_at(self) -> datetime:
        return self.commit.author.date


# ---- list_contributors ----
class Contributor(GitHubModel):
    login: str
    contributions: int
    type: Literal["User", "Bot", "Anonymous", "Organization"] = "User"


# ---- list_issues / list_pulls ----
class PullRequestRef(GitHubModel):
    url: str


class Issue(GitHubModel):
    number: int
    state: Literal["open", "closed"]
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    pull_request: PullRequestRef | None = None

    @property
    def is_pull_request(self) -> bool:
        return self.pull_request is not None


class PullRequest(GitHubModel):
    number: int
    state: Literal["open", "closed"]
    draft: bool
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None
    merged_at: datetime | None

    @property
    def was_merged(self) -> bool:
        return self.merged_at is not None


# ---- get_tree ----
class TreeEntry(GitHubModel):
    path: str
    type: Literal["blob", "tree", "commit"]
    size: int | None = None
    sha: str

    @property
    def is_file(self) -> bool:
        return self.type == "blob"


class RepoTree(GitHubModel):
    sha: str
    truncated: bool
    tree: list[TreeEntry]

    def files(self) -> list[TreeEntry]:
        return [e for e in self.tree if e.is_file]

    def has_path(self, path: str) -> bool:
        return any(e.path == path for e in self.tree)

    def has_directory(self, dir_path: str) -> bool:
        prefix = dir_path.rstrip("/") + "/"
        return any(e.path.startswith(prefix) for e in self.tree)


# ---- get_file_content ----
class FileContent(GitHubModel):
    name: str
    path: str
    sha: str
    size: int
    encoding: Literal["base64", "none"]
    content: str

    def decoded_text(self) -> str:
        if self.encoding == "none":
            return self.content
        return base64.b64decode(self.content).decode("utf-8")

    def decoded_bytes(self) -> bytes:
        if self.encoding == "none":
            return self.content.encode("utf-8")
        return base64.b64decode(self.content)


# ---- get_languages ----
class LanguageBreakdown(GitHubModel):
    bytes_per_language: dict[str, int]

    @property
    def primary(self) -> str | None:
        if not self.bytes_per_language:
            return None
        return max(self.bytes_per_language.items(), key=lambda x: x[1])[0]

    @model_validator(mode="before")
    @classmethod
    def wrap_raw(cls, v):
        if isinstance(v, dict) and "bytes_per_language" not in v:
            return {"bytes_per_language": v}
        return v
