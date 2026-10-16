from fastapi import FastAPI

app = FastAPI(title="JobFlow")


@app.get("/health")
def health():
    return {"status": "ok"}