from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from triagit.domains.triage.dependencies import TriageServiceDep
from triagit.infrastructure.github.exceptions import GitHubAPIError


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


def _fmt_datetime(dt: datetime | None) -> str:
    if dt is None:
        return "—"
    return dt.strftime("%b %d, %Y")


templates.env.globals["lang_color"] = _lang_color
templates.env.filters["fmt_number"] = _fmt_number
templates.env.filters["fmt_datetime"] = _fmt_datetime


@router.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse(request, "landing.html")


@router.post("/analyze", response_class=HTMLResponse)
async def analyze(request: Request, url: str = Form(...)):
    url = url.strip()
    if not url.startswith("http"):
        url = "https://" + url

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
async def report(request: Request, url: str, service: TriageServiceDep):
    parsed = urlparse(url)
    path_parts = parsed.path.strip("/").split("/")
    slug = f"{path_parts[0]}/{path_parts[1]}" if len(path_parts) >= 2 else url

    try:
        triage_report = await service.get_triage_report(url)
    except GitHubAPIError as e:
        title = "Repository not found" if e.status_code == 404 else "GitHub API error"
        message = (
            "This repository may be private or the URL may be incorrect."
            if e.status_code == 404
            else str(e)
        )
        return templates.TemplateResponse(
            request,
            "error.html",
            {"title": title, "message": message, "slug": slug},
            status_code=e.status_code,
        )
    except Exception:
        return templates.TemplateResponse(
            request,
            "error.html",
            {"title": "Analysis failed", "message": "Something went wrong. Please try again.", "slug": slug},
            status_code=500,
        )

    return templates.TemplateResponse(
        request,
        "report.html",
        {"slug": slug, "url": url, "report": triage_report},
    )
