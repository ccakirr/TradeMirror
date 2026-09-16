from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from .api.predictor import router as predictor_router
from .api.auth import router as auth_router
from .api.trading_accounts import router as trading_account_router
from .api.instruments import router as instruments_router

app = FastAPI(
    title="TradeMiror API",
    version="0.1.0"
)

# The instrument catalog is a few hundred KB of JSON; everything else is small.
app.add_middleware(GZipMiddleware, minimum_size=1024)

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

app.include_router(
    router=instruments_router,
    prefix="/api/v1"
)


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "trademirror-api"
    }


# In Railway production the React build is copied into this same container.
# API routes above keep their /api prefix, while every other browser request
# receives the SPA entry point.
frontend_dir = Path("frontend/dist")
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
