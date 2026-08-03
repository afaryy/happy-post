from datetime import UTC, date, datetime
from typing import Annotated, cast
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from app.domain.auth import AuthCredentials, CurrentUser
from app.domain.entries import DailyEntry, SaveDailyEntry
from app.repositories.entries import DailyEntryRepository
from app.repositories.sessions import SessionRepository
from app.repositories.users import DuplicateEmailError, UserRepository
from app.security import (
    SESSION_COOKIE_NAME,
    create_session_token,
    hash_password,
    verify_password,
)
from app.settings import Settings

router = APIRouter()


def health_response(request: Request) -> dict[str, str]:
    settings = cast(Settings, request.app.state.settings)
    return {"status": "ok", "version": settings.app_version}


def version_response(request: Request) -> dict[str, str]:
    settings = cast(Settings, request.app.state.settings)
    return {"version": settings.app_version}


router.add_api_route("/healthz", health_response, methods=["GET"])
router.add_api_route("/backend/healthz", health_response, methods=["GET"])
router.add_api_route("/version", version_response, methods=["GET"])
router.add_api_route("/backend/version", version_response, methods=["GET"])


def get_entry_repository(request: Request) -> DailyEntryRepository:
    return cast(DailyEntryRepository, request.app.state.entry_repository)


def get_user_repository(request: Request) -> UserRepository:
    return cast(UserRepository, request.app.state.user_repository)


def get_session_repository(request: Request) -> SessionRepository:
    return cast(SessionRepository, request.app.state.session_repository)


EntryRepositoryDependency = Annotated[DailyEntryRepository, Depends(get_entry_repository)]
SessionRepositoryDependency = Annotated[SessionRepository, Depends(get_session_repository)]
UserRepositoryDependency = Annotated[UserRepository, Depends(get_user_repository)]


def current_user(
    request: Request,
    session_repository: SessionRepositoryDependency,
    user_repository: UserRepositoryDependency,
) -> CurrentUser:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    user_id = session_repository.get_user_id(token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    user = user_repository.get_by_id(user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    return user


CurrentUserDependency = Annotated[CurrentUser, Depends(current_user)]


def current_entry_date(settings: Settings, now: datetime | None = None) -> date:
    try:
        timezone = ZoneInfo(settings.app_timezone)
    except ZoneInfoNotFoundError:
        timezone = ZoneInfo("Australia/Melbourne")
    instant = now or datetime.now(UTC)
    return instant.astimezone(timezone).date()


def use_secure_cookie(request: Request) -> bool:
    return request.headers.get("x-forwarded-proto", request.url.scheme) == "https"


def set_session_cookie(
    request: Request,
    response: Response,
    user: CurrentUser,
    session_repository: SessionRepository,
) -> None:
    settings = cast(Settings, request.app.state.settings)
    token = create_session_token()
    session_repository.create(user.id, token, settings.session_ttl_seconds)
    response.set_cookie(
        SESSION_COOKIE_NAME,
        token,
        httponly=True,
        max_age=settings.session_ttl_seconds,
        samesite="lax",
        secure=use_secure_cookie(request),
    )


@router.post("/api/auth/signup", response_model=CurrentUser, status_code=status.HTTP_201_CREATED)
def signup(
    payload: AuthCredentials,
    response: Response,
    request: Request,
    session_repository: SessionRepositoryDependency,
    user_repository: UserRepositoryDependency,
) -> CurrentUser:
    try:
        user = user_repository.create(payload.email, hash_password(payload.password))
    except DuplicateEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        ) from exc
    set_session_cookie(request, response, user, session_repository)
    return user


@router.post("/api/auth/signin", response_model=CurrentUser)
def signin(
    payload: AuthCredentials,
    response: Response,
    request: Request,
    session_repository: SessionRepositoryDependency,
    user_repository: UserRepositoryDependency,
) -> CurrentUser:
    stored = user_repository.get_by_email(payload.email)
    if stored is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sign in")
    user, password_hash = stored
    if not verify_password(payload.password, password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid sign in")
    set_session_cookie(request, response, user, session_repository)
    return user


@router.post("/api/auth/signout", status_code=status.HTTP_204_NO_CONTENT)
def signout(
    response: Response,
    request: Request,
    session_repository: SessionRepositoryDependency,
) -> Response:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token:
        session_repository.delete(token)
    response.delete_cookie(SESSION_COOKIE_NAME, httponly=True, samesite="lax")
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/api/auth/me", response_model=CurrentUser)
def me(user: CurrentUserDependency) -> CurrentUser:
    return user


@router.put("/api/entries/today", response_model=DailyEntry, status_code=status.HTTP_200_OK)
def save_today_entry(
    payload: SaveDailyEntry,
    repository: EntryRepositoryDependency,
    request: Request,
    user: CurrentUserDependency,
) -> DailyEntry:
    settings = cast(Settings, request.app.state.settings)
    return repository.save(user.id, current_entry_date(settings), payload)


@router.get("/api/entries/today", response_model=DailyEntry)
def get_today_entry(
    repository: EntryRepositoryDependency, request: Request, user: CurrentUserDependency
) -> DailyEntry:
    settings = cast(Settings, request.app.state.settings)
    entry = repository.get(user.id, current_entry_date(settings))
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry


@router.get("/api/entries", response_model=list[DailyEntry])
def list_entries(
    month: str,
    repository: EntryRepositoryDependency,
    request: Request,
    user: CurrentUserDependency,
) -> list[DailyEntry]:
    try:
        year_text, month_text = month.split("-", 1)
        year = int(year_text)
        month_number = int(month_text)
        if month_number < 1 or month_number > 12:
            raise ValueError
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="month must use YYYY-MM format",
        ) from exc

    return repository.list_month(user.id, year, month_number)


@router.get("/api/entries/{entry_date}", response_model=DailyEntry)
def get_entry(
    entry_date: str,
    repository: EntryRepositoryDependency,
    request: Request,
    user: CurrentUserDependency,
) -> DailyEntry:
    try:
        parsed_date = date.fromisoformat(entry_date)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="entry_date must use YYYY-MM-DD format",
        ) from exc

    entry = repository.get(user.id, parsed_date)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Entry not found")
    return entry
