from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.domain.posts import CreatePost, Post
from app.repositories.posts import PostRepository
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


def get_post_repository(request: Request) -> PostRepository:
    return cast(PostRepository, request.app.state.post_repository)


PostRepositoryDependency = Annotated[PostRepository, Depends(get_post_repository)]


@router.post("/api/posts", response_model=Post, status_code=status.HTTP_201_CREATED)
def create_post(payload: CreatePost, repository: PostRepositoryDependency) -> Post:
    return repository.create(payload.message)


@router.get("/api/posts", response_model=list[Post])
def list_posts(repository: PostRepositoryDependency) -> list[Post]:
    return repository.list()


@router.get("/api/posts/{post_id}", response_model=Post)
def get_post(post_id: UUID, repository: PostRepositoryDependency) -> Post:
    post = repository.get(post_id)
    if post is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Post not found")
    return post
