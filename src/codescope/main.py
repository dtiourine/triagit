from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from codescope.analysis.router import router as analysis_router

app = FastAPI()

app.include_router(analysis_router)


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0]
    return JSONResponse(status_code=422, content={"detail": first_error["msg"]})
