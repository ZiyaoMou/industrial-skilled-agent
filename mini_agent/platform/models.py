"""Pydantic models for the skill-build platform APIs."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


SkillType = Literal["built_in", "platform_enhanced", "platform_new", "orchestrated"]
MessageSource = Literal["user", "assistant", "skill"]


class TaskCategoryCreate(BaseModel):
    """Payload for creating a task category."""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    default_skill_ids: list[str] = Field(default_factory=list)


class TaskCategoryUpdate(BaseModel):
    """Payload for updating a task category."""

    name: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    default_skill_ids: list[str] = Field(default_factory=list)


class TaskCategory(BaseModel):
    """Task category with default selected skills."""

    id: str
    name: str
    description: str
    default_skill_ids: list[str] = Field(default_factory=list)
    created_at: datetime


class TaskCreate(BaseModel):
    """Payload for creating a task."""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=4000)
    category_id: str
    selected_skill_ids: list[str] = Field(default_factory=list)
    document_name: str | None = None
    document_content: str | None = None


class TaskItem(BaseModel):
    """Task item used for task sidebar."""

    id: str
    name: str
    description: str
    category_id: str
    selected_skill_ids: list[str] = Field(default_factory=list)
    document_name: str | None = None
    created_at: datetime


class ChatMessageCreate(BaseModel):
    """Payload for posting a user chat message."""

    content: str = Field(min_length=1)


class ChatMessage(BaseModel):
    """Stored chat message."""

    id: str
    task_id: str
    role: str
    source: MessageSource
    content: str
    created_at: datetime


class SkillItem(BaseModel):
    """Skill metadata and content."""

    id: str
    name: str
    description: str
    type: SkillType
    category_bindings: list[str] = Field(default_factory=list)
    content: str
    base_skill_ids: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SkillUpdateRequest(BaseModel):
    """Payload to update a platform skill."""

    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=3000)
    content: str = Field(min_length=1)
    category_bindings: list[str] = Field(default_factory=list)


class SkillLabAnalyzeRequest(BaseModel):
    """Payload for skill lab analysis."""

    task_ids: list[str] = Field(min_length=1)
    include_industry_knowledge: bool = False


class SkillProposal(BaseModel):
    """Proposed skill generated from workflow analysis."""

    id: str
    proposal_type: Literal["orchestrated", "new", "enhanced"]
    name: str
    description: str
    rationale: str
    implementation_notes: list[str] = Field(default_factory=list)
    based_on_skill_ids: list[str] = Field(default_factory=list)


class SkillLabAnalyzeResponse(BaseModel):
    """Skill lab analysis output."""

    analyzed_task_count: int
    suggestions: list[SkillProposal] = Field(default_factory=list)
    evidence_summary: str

