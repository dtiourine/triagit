from pathlib import Path
from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from codescope.domains.metrics.service import AnalysisService
from codescope.infrastructure.github.client import GitHubClient
from codescope.infrastructure.github.config import get_github_config
from codescope.infrastructure.github.exceptions import GitHubAPIError, GitHubTransportError

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

MOCK_REVIEW = {
    "model": "claude-sonnet-4-5",
    "durationSec": 47,
    "filesSampled": 14,
    "filesTotal": 412,
    "samplingNote": "Sampled by recency × churn × public-API surface.",
    "overall": 81,
    "summary": (
        "Code quality is high overall. The framework's public surface is well-typed and consistently "
        "structured. Most findings cluster around defensive error handling in dependency resolution and "
        "a handful of high-complexity functions in routing internals. No critical security issues "
        "surfaced in the sampled files."
    ),
    "severityCounts": {"critical": 0, "major": 2, "minor": 5, "info": 3},
    "categories": ["Error handling", "Complexity", "Testing", "Security", "Style", "Docs"],
    "files": [
        {"path": "fastapi/routing.py",            "loc": 1240, "score": 76, "findings": 2},
        {"path": "fastapi/dependencies/utils.py", "loc":  820, "score": 68, "findings": 2},
        {"path": "fastapi/applications.py",       "loc":  480, "score": 92, "findings": 0},
        {"path": "fastapi/security/oauth2.py",    "loc":  310, "score": 84, "findings": 1},
        {"path": "fastapi/encoders.py",           "loc":  240, "score": 95, "findings": 0},
        {"path": "fastapi/openapi/utils.py",      "loc":  640, "score": 71, "findings": 2},
        {"path": "fastapi/params.py",             "loc":  220, "score": 90, "findings": 0},
        {"path": "fastapi/middleware/cors.py",    "loc":  130, "score": 88, "findings": 0},
        {"path": "tests/test_websockets.py",      "loc":  410, "score": 73, "findings": 1},
        {"path": "tests/test_security_oauth2.py", "loc":  290, "score": 82, "findings": 0},
        {"path": "fastapi/utils.py",              "loc":  180, "score": 86, "findings": 0},
        {"path": "fastapi/exceptions.py",         "loc":   95, "score": 94, "findings": 0},
        {"path": "fastapi/_compat.py",            "loc":  340, "score": 78, "findings": 1},
        {"path": "fastapi/concurrency.py",        "loc":   85, "score": 90, "findings": 0},
    ],
    "findings": [
        {
            "id": "f1", "severity": "major", "category": "Error handling",
            "title": "Bare except masks dependency resolution failures",
            "file": "fastapi/dependencies/utils.py", "lineStart": 412, "lineEnd": 421,
            "description": (
                "The except clause at line 414 catches all exceptions without logging or re-raising, "
                "returning None silently. In production this hides DI configuration errors — dependents "
                "observe a missing dependency rather than the underlying failure, which substantially "
                "increases time-to-diagnose."
            ),
            "suggestion": (
                "Catch specific exception types (ValidationError, HTTPException, RuntimeError) and log "
                "with the dependant context before re-raising or returning a structured failure."
            ),
            "excerpt": [
                {"num": 410, "text": "async def resolve_dependant(request, dependant):"},
                {"num": 411, "text": "    try:"},
                {"num": 412, "text": "        solved = await solve_dependencies("},
                {"num": 413, "text": "            request=request, dependant=dependant,"},
                {"num": 414, "text": "        )"},
                {"num": 415, "text": "    except:", "highlight": True},
                {"num": 416, "text": "        return None", "highlight": True},
                {"num": 417, "text": "    return solved"},
            ],
            "confidence": 0.92,
        },
        {
            "id": "f2", "severity": "major", "category": "Complexity",
            "title": "process_response has cyclomatic complexity of 18",
            "file": "fastapi/routing.py", "lineStart": 184, "lineEnd": 286,
            "description": (
                "process_response handles streaming, JSON, raw bytes, and WebSocket upgrade paths in one "
                "100-line function with nested conditionals. The branching combined with implicit type "
                "coercion makes behavior hard to reason about and difficult to extend without regressions."
            ),
            "suggestion": (
                "Extract per-response-type handlers (handle_streaming_response, handle_json_response, "
                "handle_raw_response). The dispatcher becomes a small switch and each branch is "
                "independently testable."
            ),
            "excerpt": [
                {"num": 184, "text": "def process_response(response, request, route):"},
                {"num": 185, "text": "    if isinstance(response, StreamingResponse):"},
                {"num": 186, "text": "        if request.headers.get('accept') == 'text/event-stream':"},
                {"num": 187, "text": "            ..."},
                {"num": 188, "text": "        elif route.response_class is not None:"},
                {"num": 189, "text": "            if hasattr(route.response_class, 'render'):"},
                {"num": 190, "text": "                ...", "highlight": True},
                {"num": 191, "text": "    elif isinstance(response, JSONResponse):"},
                {"num": 192, "text": "        ..."},
            ],
            "confidence": 0.86,
        },
        {
            "id": "f3", "severity": "minor", "category": "Testing",
            "title": "WebSocket disconnect path lacks coverage on protocol error",
            "file": "tests/test_websockets.py", "lineStart": 312, "lineEnd": 312,
            "description": (
                "Tests cover normal close (code 1000) and abrupt close (1006), but not protocol-level "
                "errors (1002) or message-too-big (1009). The handler in websockets.py:142 has dedicated "
                "branches for both that go untested."
            ),
            "suggestion": (
                "Add a parameterized test that triggers each non-normal close code and asserts the "
                "on_disconnect callback receives the expected exception subtype."
            ),
            "excerpt": [
                {"num": 310, "text": "async def test_websocket_disconnect():"},
                {"num": 311, "text": "    async with client.websocket_connect('/ws') as ws:"},
                {"num": 312, "text": "        await ws.close(code=1000)  # only normal close tested", "highlight": True},
                {"num": 313, "text": "        assert ws.application_state == State.DISCONNECTED"},
            ],
            "confidence": 0.78,
        },
        {
            "id": "f4", "severity": "minor", "category": "Security",
            "title": "OAuth2 password flow does not constant-time compare client_secret",
            "file": "fastapi/security/oauth2.py", "lineStart": 168, "lineEnd": 174,
            "description": (
                "Client secret verification uses == on byte strings rather than secrets.compare_digest. "
                "While Python string comparison short-circuits on length first, equal-length comparisons "
                "remain timing-observable in principle. Low practical impact behind TLS, but trivial to harden."
            ),
            "suggestion": "Replace == with secrets.compare_digest(provided.encode(), expected.encode()).",
            "excerpt": [
                {"num": 167, "text": "def verify_client(provided: str, expected: str) -> bool:"},
                {"num": 168, "text": "    if not provided or not expected:"},
                {"num": 169, "text": "        return False"},
                {"num": 170, "text": "    return provided == expected", "highlight": True},
            ],
            "confidence": 0.71,
        },
        {
            "id": "f5", "severity": "minor", "category": "Complexity",
            "title": "OpenAPI schema generation duplicates field-traversal logic",
            "file": "fastapi/openapi/utils.py", "lineStart": 88, "lineEnd": 142,
            "description": (
                "get_fields_from_routes and get_flat_models walk the same dependant tree with subtly "
                "different filters. Drift between the two has caused at least one historical bug (#4912). "
                "Consolidating reduces surface area and clarifies intent."
            ),
            "suggestion": "Introduce a single traversal that yields (model, field, source) tuples; both consumers filter the stream.",
            "excerpt": [
                {"num": 88, "text": "def get_fields_from_routes(routes):"},
                {"num": 89, "text": "    fields = []"},
                {"num": 90, "text": "    for route in routes:"},
                {"num": 91, "text": "        for d in flatten(route.dependant):"},
                {"num": 92, "text": "            fields.extend(d.body_fields)", "highlight": True},
            ],
            "confidence": 0.74,
        },
        {
            "id": "f6", "severity": "minor", "category": "Docs",
            "title": "Public helper jsonable_encoder is missing param docs",
            "file": "fastapi/encoders.py", "lineStart": 42, "lineEnd": 60,
            "description": (
                "jsonable_encoder is a frequently-used public function; the docstring documents the "
                "function's purpose but not the by_alias, exclude_unset, or custom_encoder parameters. "
                "Users reach for these often based on issue traffic."
            ),
            "suggestion": "Add a Parameters section listing each kwarg, its default, and one-sentence guidance.",
            "excerpt": [
                {"num": 42, "text": "def jsonable_encoder("},
                {"num": 43, "text": "    obj, *, by_alias: bool = True,"},
                {"num": 44, "text": "    exclude_unset: bool = False,"},
                {"num": 45, "text": "    custom_encoder: dict = None,"},
                {"num": 46, "text": ") -> Any:", "highlight": True},
                {"num": 47, "text": '    """Convert any object to a JSON-compatible structure."""'},
            ],
            "confidence": 0.83,
        },
        {
            "id": "f7", "severity": "minor", "category": "Style",
            "title": "Inconsistent type hint syntax across _compat.py",
            "file": "fastapi/_compat.py", "lineStart": 12, "lineEnd": 220,
            "description": (
                "Mixes Optional[X] (PEP 484) and X | None (PEP 604) in the same module. The project "
                "supports Python 3.8+, so PEP 604 only applies in newer paths — but consistency aids readability."
            ),
            "suggestion": "Pick one convention per module (suggest Optional[X] given 3.8 floor) and add a ruff rule.",
            "excerpt": [
                {"num": 12, "text": "def model_dump(model, exclude: Optional[Set[str]] = None):"},
                {"num": 13, "text": "    ..."},
                {"num": 14, "text": "def field_info(name: str, default: Any | None = None):", "highlight": True},
            ],
            "confidence": 0.65,
        },
        {
            "id": "f8", "severity": "info", "category": "Style",
            "title": "Long parameter lists on routing decorators",
            "file": "fastapi/routing.py", "lineStart": 412, "lineEnd": 458,
            "description": (
                "APIRoute.__init__ and the get/post/put decorators accept 18+ keyword arguments. This "
                "mirrors framework convention (Starlette, Flask) and is unlikely to change, but new "
                "contributors find this surface daunting."
            ),
            "suggestion": "Document the rationale in CONTRIBUTING.md and consider a RouteOptions dataclass for new optional fields.",
            "excerpt": [],
            "confidence": 0.55,
        },
        {
            "id": "f9", "severity": "info", "category": "Docs",
            "title": "Internal helper _get_typed_signature lacks usage example",
            "file": "fastapi/dependencies/utils.py", "lineStart": 78, "lineEnd": 94,
            "description": (
                "Internal helper, but called from three places with subtly different inputs. A docstring "
                "example would prevent misuse during refactors."
            ),
            "suggestion": "Add a one-line example showing typical input and the returned Signature object.",
            "excerpt": [],
            "confidence": 0.62,
        },
        {
            "id": "f10", "severity": "info", "category": "Testing",
            "title": "Some integration tests rely on implicit ordering",
            "file": "tests/test_security_oauth2.py", "lineStart": 142, "lineEnd": 142,
            "description": (
                "Two tests in this file pass only when run in declaration order due to shared module-level "
                "fixtures. pytest currently honours order, but parallel execution or fixture refactors "
                "would break this silently."
            ),
            "suggestion": "Convert shared state to function-scoped fixtures, or mark explicitly with @pytest.mark.order.",
            "excerpt": [],
            "confidence": 0.69,
        },
    ],
}

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

    return templates.TemplateResponse(request, "report.html", {"r": r, "review": MOCK_REVIEW})
