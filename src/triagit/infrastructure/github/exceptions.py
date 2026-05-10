class GitHubClientError(Exception):
    """Base exception for GitHub client failures."""


class GitHubTransportError(GitHubClientError):
    """Raised when the request could not reach GitHub successfully."""


class GitHubAPIError(GitHubClientError):
    """Raised for non-success GitHub API responses."""

    def __init__(self, message: str, status_code: int, response_data: dict | None = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data or {}


class GitHubUnauthorizedError(GitHubAPIError):
    """Raised when GitHub rejects the configured credentials."""


class GitHubForbiddenError(GitHubAPIError):
    """Raised when access is forbidden."""


class GitHubRateLimitError(GitHubForbiddenError):
    """Raised when the client is rate limited by GitHub."""

    def __init__(
        self,
        message: str,
        status_code: int,
        response_data: dict | None = None,
        reset_at: str | None = None,
    ):
        super().__init__(message, status_code, response_data=response_data)
        self.reset_at = reset_at


class GitHubNotFoundError(GitHubAPIError):
    """Raised when the requested GitHub resource does not exist."""


class GitHubValidationError(GitHubAPIError):
    """Raised when GitHub rejects the request payload or parameters."""


class GitHubServerError(GitHubAPIError):
    """Raised when GitHub returns a 5xx response."""
