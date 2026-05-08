from pydantic import BaseModel, ConfigDict


class GitHubOwnerResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    login: str
    html_url: str
    type: str


class GitHubRepoResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str
    full_name: str
    private: bool
    html_url: str
    description: str | None = None
    default_branch: str
    stargazers_count: int
    forks_count: int
    open_issues_count: int
    owner: GitHubOwnerResponse


class GitHubErrorResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    message: str
    documentation_url: str | None = None
