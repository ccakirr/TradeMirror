from fastapi import FastAPI
from .api.predictor import router as predictor_router
from .api.auth import router as auth_router
from .api.trading_accounts import router as trading_account_router

app = FastAPI(
    title="TradeMiror API",
    version="0.1.0"
)

app.include_router(
    predictor_router,
    prefix="/api/v1"
)

app.include_router(
    router=auth_router,
    prefix="/api/v1"
)

app.include_router(
    router=trading_account_router,
    prefix="/api/v1"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "trademirror-api"
    }
