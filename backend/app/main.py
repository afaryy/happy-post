from fastapi import FastAPI

from app.api.routes import router
from app.repositories.posts import InMemoryPostRepository
from app.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    app = FastAPI(title="Happy Post API", version=resolved_settings.app_version)
    app.state.settings = resolved_settings
    app.state.post_repository = InMemoryPostRepository()
    app.include_router(router)
    return app


app = create_app()
