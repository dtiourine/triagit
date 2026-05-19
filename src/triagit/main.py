from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from triagit.domains.sampling.router import router as sampling_router
from triagit.domains.triage.router import router as triage_router
from triagit.infrastructure.github.exceptions import GitHubAPIError, GitHubTransportError
from triagit.domains.web.router import router as web_router, templates

app = FastAPI()

_web_static = Path(__file__).parent / "domains" / "web" / "static"
app.mount("/static", StaticFiles(directory=_web_static), name="static")
app.include_router(web_router)
app.include_router(triage_router, prefix="/api/v1")
app.include_router(sampling_router, prefix="/api/v1")


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    if request.url.path.startswith("/api/"):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if exc.status_code == 404:
        return templates.TemplateResponse(
            request, "error.html",
            {"title": "Page not found", "message": "The page you're looking for doesn't exist."},
            status_code=404,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    return JSONResponse(status_code=422, content={"detail": first_error["msg"]})


@app.exception_handler(GitHubAPIError)
async def github_api_error_handler(request: Request, exc: GitHubAPIError):
    return JSONResponse(status_code=exc.status_code, content={"detail": str(exc)})


@app.exception_handler(GitHubTransportError)
async def github_transport_error_handler(request: Request, exc: GitHubTransportError):
    return JSONResponse(status_code=503, content={"detail": str(exc)})
