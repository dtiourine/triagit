from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from codescope.analysis.router import router as analysis_router
from codescope.github.exceptions import GitHubAPIError, GitHubTransportError

app = FastAPI()

app.include_router(analysis_router, prefix="/api/v1")


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
