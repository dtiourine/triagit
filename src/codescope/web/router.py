from pathlib import Path
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from codescope.analysis.service import AnalysisService
from codescope.github.client import GitHubClient
from codescope.github.config import get_github_config
from codescope.github.exceptions import GitHubAPIError, GitHubTransportError

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

_LANG_COLORS: dict[str, str] = {
    "Python": "#3572A5",
    "Go": "#00ADD8",
    "JavaScript": "#F1E05A",
    "TypeScript": "#3178C6",
    "Rust": "#DEA584",
    "Ruby": "#701516",
    "Java": "#B07219",
    "C": "#555555",
    "C++": "#F34B7D",
    "C#": "#178600",
    "Shell": "#89E051",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Scala": "#C22D40",
    "PHP": "#4F5D95",
}


def _lang_color(lang: str) -> str:
    return _LANG_COLORS.get(lang, "#888888")


def _fmt_number(n: int) -> str:
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


templates.env.globals["lang_color"] = _lang_color
templates.env.filters["fmt_number"] = _fmt_number


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html")


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, url: str = Form(...)):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

    from urllib.parse import urlparse
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    if parsed.netloc not in ("github.com", "www.github.com") or len(path_parts) < 2:
        return templates.TemplateResponse(
            request,
            "landing.html",
            {"error": "Enter a github.com/owner/repo URL."},
        )

    slug = f"{path_parts[0]}/{path_parts[1]}"
    return templates.TemplateResponse(
        request,
        "loading.html",
        {"slug": slug, "url": url},
    )


@router.get("/report", response_class=HTMLResponse)
async def report(request: Request, url: str):
    async with GitHubClient(get_github_config()) as github:
        service = AnalysisService(github)
        try:
            r = await service.get_metrics_report(url)
        except GitHubAPIError as exc:
            if exc.status_code == 404:
                title, message = "Repository not found", (
                    "We couldn't find that repository. "
                    "It may be private, deleted, or the URL might be malformed."
                )
            elif exc.status_code == 403:
                title, message = "Rate limited", (
                    "We're temporarily unable to analyze new repos. "
                    "Please try again in a few minutes."
                )
            else:
                title, message = "GitHub API error", str(exc)
            from urllib.parse import urlparse
            path = urlparse(url).path.strip("/")
            slug = "/".join(path.split("/")[:2]) if path else None
            return templates.TemplateResponse(
                request,
                "error.html",
                {"title": title, "message": message, "slug": slug},
                status_code=exc.status_code,
            )
        except GitHubTransportError as exc:
            return templates.TemplateResponse(
                request,
                "error.html",
                {
                    "title": "Connection error",
                    "message": "Unable to reach GitHub. Please check your connection and try again.",
                    "slug": None,
                },
                status_code=503,
            )

    return templates.TemplateResponse(request, "report.html", {"r": r})
