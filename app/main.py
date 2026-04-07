from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.session import SessionLocal
from app.models.operations import RedirectRule


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    media_root = Path(settings.media_root)
    media_path = media_root / "media"
    media_path.mkdir(parents=True, exist_ok=True)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.cors_origins],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_exception_handlers(app)
    app.mount(settings.media_url, StaticFiles(directory=media_path), name="media")
    app.include_router(api_router, prefix=settings.api_prefix)
    

    @app.middleware("http")
    async def apply_redirect_rules(request: Request, call_next):
        if request.url.path.startswith(settings.api_prefix) or request.url.path.startswith(settings.media_url):
            return await call_next(request)
        try:
            async with SessionLocal() as session:
                result = await session.execute(
                    select(RedirectRule).where(
                        RedirectRule.source_path == request.url.path,
                        RedirectRule.is_active.is_(True),
                    )
                )
                redirect = result.scalar_one_or_none()
        except Exception:
            redirect = None
        if redirect:
            return RedirectResponse(url=redirect.target_path, status_code=redirect.status_code)
        return await call_next(request)

    @app.get("/health", tags=["health"])
    async def healthcheck() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name}

    return app


app = create_app()
