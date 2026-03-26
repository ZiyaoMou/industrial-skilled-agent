"""Skill catalog utilities for built-in and platform skills."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from mini_agent.tools.skill_loader import SkillLoader

from .models import SkillItem
from .repository import PlatformRepository, utc_now


@dataclass
class CatalogSkill:
    """Simplified skill info used by recommendation workflows."""

    id: str
    name: str
    description: str
    type: str


class SkillRegistry:
    """Unified registry for built-in skill files and platform managed skills."""

    def __init__(self, repository: PlatformRepository, skills_dir: Path):
        self.repository = repository
        self.skills_dir = skills_dir

    def list_all_skills(self) -> list[SkillItem]:
        builtins = {item.id: item for item in self._list_builtin_skills()}
        platform_items = {item.id: item for item in self.repository.list_platform_skills()}

        merged: dict[str, SkillItem] = {}
        merged.update(builtins)
        merged.update(platform_items)
        return list(merged.values())

    def get_catalog(self) -> list[CatalogSkill]:
        skills = self.list_all_skills()
        return [CatalogSkill(id=skill.id, name=skill.name, description=skill.description, type=skill.type) for skill in skills]

    def _list_builtin_skills(self) -> list[SkillItem]:
        loader = SkillLoader(str(self.skills_dir))
        discovered = loader.discover_skills()
        now = utc_now()
        items: list[SkillItem] = []
        for skill in discovered:
            skill_id = f"builtin::{skill.name}"
            category_bindings = []
            metadata = skill.metadata or {}
            if isinstance(metadata.get("category_bindings"), list):
                category_bindings = [str(item) for item in metadata["category_bindings"]]
            items.append(
                SkillItem(
                    id=skill_id,
                    name=skill.name,
                    description=skill.description,
                    type="built_in",
                    category_bindings=category_bindings,
                    content=skill.content,
                    base_skill_ids=[],
                    created_at=now,
                    updated_at=now,
                )
            )
        return items

