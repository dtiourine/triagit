from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel

from .utils import validate_github_url

GitHubRepoUrl = Annotated[str, AfterValidator(validate_github_url)]


class GetRepoResponse(BaseModel):
    full_name: str
    description: str | None
    default_branch: str
    pushed_at: datetime | None
    size: int
    language: str | None
    archived: bool
    disabled: bool
