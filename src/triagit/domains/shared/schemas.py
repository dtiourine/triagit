from typing import Annotated

from pydantic import AfterValidator

from .utils import validate_github_url

GitHubRepoUrl = Annotated[str, AfterValidator(validate_github_url)]
