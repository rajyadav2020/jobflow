from fastapi import FastAPI

from app.api import jobs

app = FastAPI(title="JobFlow")
app.include_router(jobs.router)


@app.get("/health")
def health():
    return {"status": "ok"}