from fastapi import FastAPI

from backend.api.routers.licenses__route import router as licenses_router


app = FastAPI(
    title="LR License Service",
    version="1.0.0",
)

app.include_router(licenses_router)


@app.get("/health")
def health():
    return {"service": "license-service", "status": "ok"}
