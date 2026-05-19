import uvicorn


def dev():
    uvicorn.run("triagit.main:app", reload=True)
