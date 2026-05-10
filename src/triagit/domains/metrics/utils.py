from urllib.parse import urlparse


def validate_github_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme != "https":
        raise ValueError("URL must start with https://")
    if parsed.netloc.removeprefix("www.") != "github.com":
        raise ValueError("URL must be a GitHub repository URL")
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) < 2:
        raise ValueError("URL must point to a repository (https://github.com/owner/repo)")
    return url
