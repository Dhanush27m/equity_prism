from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    chat,
    companies,
    documents,
    health,
    indices,
    market,
    news,
    portfolio,
    screener,
    watchlist,
)
from app.core.auth import install as install_auth
from app.core.config import get_settings
from app.core.observability import install as install_observability

settings = get_settings()

app = FastAPI(title="Equity Prism API", version="0.1.0")

install_auth(app)
install_observability(app)

_origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_router = APIRouter(prefix="/api")
api_router.include_router(health.router)
api_router.include_router(companies.router)
api_router.include_router(market.router)
api_router.include_router(news.router)
api_router.include_router(screener.router)
api_router.include_router(chat.router)
api_router.include_router(documents.router)
api_router.include_router(indices.router)
api_router.include_router(watchlist.router)
api_router.include_router(portfolio.router)

app.include_router(api_router)
