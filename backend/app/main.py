from fastapi import FastAPI
from sqlalchemy import create_engine

from app.api.routes import router
from app.repositories.entries import InMemoryDailyEntryRepository, SqlAlchemyDailyEntryRepository
from app.repositories.sessions import InMemorySessionRepository, SqlAlchemySessionRepository
from app.repositories.users import InMemoryUserRepository, SqlAlchemyUserRepository
from app.settings import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings = settings or Settings()
    app = FastAPI(title="Happy Post API", version=resolved_settings.app_version)
    app.state.settings = resolved_settings
    if resolved_settings.database_url:
        engine = create_engine(resolved_settings.database_url, pool_pre_ping=True, future=True)
        app.state.entry_repository = SqlAlchemyDailyEntryRepository(engine)
        app.state.session_repository = SqlAlchemySessionRepository(engine)
        app.state.user_repository = SqlAlchemyUserRepository(engine)
    else:
        app.state.entry_repository = InMemoryDailyEntryRepository()
        app.state.session_repository = InMemorySessionRepository()
        app.state.user_repository = InMemoryUserRepository()
    app.include_router(router)
    return app


app = create_app()
