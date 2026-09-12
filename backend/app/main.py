from fastapi import FastAPI
from .api.predictor import router as predictor_router

app = FastAPI(
    title="TradeMiror API",
    version="0.1.0"
)

app.include_router(
    predictor_router,
    prefix="/api/v1"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "trademirror-api"
    }
