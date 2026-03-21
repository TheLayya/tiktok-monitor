from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, Base
from app.core.scheduler import start_scheduler, stop_scheduler
from app.api import projects, accounts, history, proxies, videos, settings, import_export
import logging

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时创建数据库表
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="TikTok Monitor",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
# Note: import_export must be registered before accounts to avoid route conflicts
# (export/import-file are more specific than {account_id})
app.include_router(projects.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(accounts.router, prefix="/api")
app.include_router(history.router, prefix="/api")
app.include_router(proxies.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(settings.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok"}
