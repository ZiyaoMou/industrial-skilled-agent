"""FastAPI app for the skill-build platform."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    ChatMessage,
    ChatMessageCreate,
    SkillItem,
    SkillLabAnalyzeRequest,
    SkillLabAnalyzeResponse,
    SkillProposal,
    SkillUpdateRequest,
    TaskCategory,
    TaskCategoryCreate,
    TaskCategoryUpdate,
    TaskCreate,
    TaskItem,
)
from .service import SkillBuildService


def _default_data_dir() -> Path:
    return Path.cwd() / "workspace" / "skill_build_platform"


def _resolve_skills_dir() -> Path:
    """Resolve local skills directory with explicit environment override."""
    env_path = os.getenv("SKILL_BUILD_SKILLS_DIR")
    if env_path:
        return Path(env_path).expanduser().resolve()

    repo_skills = Path.cwd() / "mini_agent" / "skills"
    if repo_skills.exists():
        return repo_skills.resolve()

    return repo_skills.resolve()


@lru_cache
def get_service() -> SkillBuildService:
    data_dir = Path(os.getenv("SKILL_BUILD_DATA_DIR", str(_default_data_dir())))
    db_path = data_dir / "platform.db"
    redis_url = os.getenv("SKILL_BUILD_REDIS_URL", "redis://localhost:6379/0")
    skills_dir = _resolve_skills_dir()
    return SkillBuildService(
        db_path=str(db_path),
        skills_dir=str(skills_dir),
        redis_url=redis_url,
    )


def create_app() -> FastAPI:
    app = FastAPI(
        title="Skill-Build Platform",
        version="0.1.0",
        description="Industrial AI workflow platform for skill orchestration, creation, and enhancement.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {
            "status": "ok",
            "skills_dir": str(_resolve_skills_dir()),
        }

    @app.get("/api/task-categories", response_model=list[TaskCategory])
    def list_categories() -> list[TaskCategory]:
        return get_service().list_categories()

    @app.post("/api/task-categories", response_model=TaskCategory)
    def create_category(payload: TaskCategoryCreate) -> TaskCategory:
        try:
            return get_service().create_category(
                name=payload.name,
                description=payload.description,
                default_skill_ids=payload.default_skill_ids,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.put("/api/task-categories/{category_id}", response_model=TaskCategory)
    def update_category(category_id: str, payload: TaskCategoryUpdate) -> TaskCategory:
        try:
            return get_service().update_category(
                category_id=category_id,
                name=payload.name,
                description=payload.description,
                default_skill_ids=payload.default_skill_ids,
            )
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/tasks", response_model=list[TaskItem])
    def list_tasks() -> list[TaskItem]:
        return get_service().list_tasks()

    @app.post("/api/tasks", response_model=TaskItem)
    def create_task(payload: TaskCreate) -> TaskItem:
        try:
            return get_service().create_task(
                name=payload.name,
                description=payload.description,
                category_id=payload.category_id,
                selected_skill_ids=payload.selected_skill_ids,
                document_name=payload.document_name,
                document_content=payload.document_content,
            )
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/tasks/{task_id}/messages", response_model=list[ChatMessage])
    def list_task_messages(task_id: str) -> list[ChatMessage]:
        return get_service().list_messages(task_id)

    @app.post("/api/tasks/{task_id}/messages", response_model=list[ChatMessage])
    def post_task_message(task_id: str, payload: ChatMessageCreate) -> list[ChatMessage]:
        try:
            return get_service().post_user_message(task_id=task_id, content=payload.content)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/api/skills", response_model=list[SkillItem])
    def list_skills() -> list[SkillItem]:
        return get_service().list_skills()

    @app.put("/api/skills/{skill_id}", response_model=SkillItem)
    def update_skill(skill_id: str, payload: SkillUpdateRequest) -> SkillItem:
        try:
            return get_service().update_platform_skill(
                skill_id=skill_id,
                name=payload.name,
                description=payload.description,
                content=payload.content,
                category_bindings=payload.category_bindings,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.post("/api/skill-lab/analyze", response_model=SkillLabAnalyzeResponse)
    def analyze_skill_lab(payload: SkillLabAnalyzeRequest) -> SkillLabAnalyzeResponse:
        return get_service().analyze_skill_lab(
            task_ids=payload.task_ids,
            include_industry_knowledge=payload.include_industry_knowledge,
        )

    @app.post("/api/skill-lab/apply", response_model=SkillItem)
    def apply_skill_proposal(proposal: SkillProposal) -> SkillItem:
        return get_service().apply_proposal(proposal)

    @app.get("/")
    def index() -> dict[str, str]:
        return {"message": "Skill-Build Platform API is running."}

    return app


app = create_app()

