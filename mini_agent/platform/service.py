"""Business service for the industrial skill-build platform."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable
from uuid import uuid4

from .models import (
    ChatMessage,
    SkillItem,
    SkillLabAnalyzeResponse,
    SkillProposal,
    TaskCategory,
    TaskItem,
)
from .llm_chat import LangChainChatRuntime
from .repository import PlatformRepository
from .skill_registry import SkillRegistry
from .workflows import SkillRecommendationWorkflow


class SkillBuildService:
    """Domain service: chat, skill management, and skill-lab analysis."""

    def __init__(
        self,
        db_path: str,
        skills_dir: str,
        redis_url: str | None = None,
    ):
        self.repository = PlatformRepository(db_path=db_path)
        self.skill_registry = SkillRegistry(self.repository, skills_dir=Path(skills_dir))
        self.workflow = SkillRecommendationWorkflow(redis_url=redis_url)
        self.redis_url = redis_url or "redis://localhost:6379/0"
        self.chat_runtime = LangChainChatRuntime(redis_url=self.redis_url)
        self._seed_if_needed()

    def list_categories(self) -> list[TaskCategory]:
        return self.repository.list_categories()

    def create_category(self, name: str, description: str, default_skill_ids: list[str]) -> TaskCategory:
        return self.repository.create_category(name, description, default_skill_ids)

    def update_category(self, category_id: str, name: str, description: str, default_skill_ids: list[str]) -> TaskCategory:
        updated = self.repository.update_category(
            category_id=category_id,
            name=name,
            description=description,
            default_skill_ids=default_skill_ids,
        )
        if not updated:
            raise ValueError(f"Category '{category_id}' does not exist")
        return updated

    def list_tasks(self) -> list[TaskItem]:
        return self.repository.list_tasks()

    def create_task(
        self,
        name: str,
        description: str,
        category_id: str,
        selected_skill_ids: list[str],
        document_name: str | None,
        document_content: str | None,
    ) -> TaskItem:
        if not selected_skill_ids:
            category = self.repository.get_category(category_id)
            if category:
                selected_skill_ids = category.default_skill_ids
        return self.repository.create_task(
            name=name,
            description=description,
            category_id=category_id,
            selected_skill_ids=selected_skill_ids,
            document_name=document_name,
            document_content=document_content,
        )

    def list_messages(self, task_id: str) -> list[ChatMessage]:
        return self.repository.list_messages(task_id)

    def post_user_message(self, task_id: str, content: str) -> list[ChatMessage]:
        task = self.repository.get_task(task_id)
        if not task:
            raise ValueError(f"Task '{task_id}' does not exist")

        created: list[ChatMessage] = []
        created.append(self.repository.add_message(task_id=task_id, role="user", source="user", content=content))

        selected_skills = self._resolve_skills(task.selected_skill_ids)
        if selected_skills:
            skill_notice = "Activated skills: " + ", ".join(skill.name for skill in selected_skills[:5])
            created.append(
                self.repository.add_message(
                    task_id=task_id,
                    role="assistant",
                    source="skill",
                    content=skill_notice,
                )
            )

        llm_reply = self.chat_runtime.generate_reply(task=task, user_input=content, selected_skills=selected_skills)
        response = llm_reply.content
        if llm_reply.error:
            response = f"{response}\n\nRuntime Error: {llm_reply.error}"
        created.append(
            self.repository.add_message(
                task_id=task_id,
                role="assistant",
                source="assistant",
                content=response,
            )
        )
        return created

    def list_skills(self) -> list[SkillItem]:
        return self.skill_registry.list_all_skills()

    def update_platform_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        content: str,
        category_bindings: list[str],
    ) -> SkillItem:
        existing = self.repository.get_platform_skill(skill_id)
        skill_type = existing.type if existing else "platform_enhanced"
        base_skill_ids = existing.base_skill_ids if existing else []
        if skill_id.startswith("builtin::"):
            skill_type = "platform_enhanced"
            if not base_skill_ids:
                base_skill_ids = [skill_id]

        return self.repository.upsert_platform_skill(
            skill_id=skill_id,
            name=name,
            description=description,
            skill_type=skill_type,
            category_bindings=category_bindings,
            content=content,
            base_skill_ids=base_skill_ids,
        )

    def analyze_skill_lab(self, task_ids: list[str], include_industry_knowledge: bool) -> SkillLabAnalyzeResponse:
        messages: list[ChatMessage] = []
        for task_id in task_ids:
            messages.extend(self.repository.list_messages(task_id))
        conversation_text = "\n".join(f"{m.role}/{m.source}: {m.content}" for m in messages)
        catalog = self.skill_registry.get_catalog()
        suggestions, evidence_summary = self.workflow.run(
            conversation_text=conversation_text,
            include_industry_knowledge=include_industry_knowledge,
            catalog=catalog,
        )
        return SkillLabAnalyzeResponse(
            analyzed_task_count=len(task_ids),
            suggestions=suggestions,
            evidence_summary=evidence_summary,
        )

    def apply_proposal(self, proposal: SkillProposal, category_bindings: list[str] | None = None) -> SkillItem:
        target_type = {
            "orchestrated": "orchestrated",
            "new": "platform_new",
            "enhanced": "platform_enhanced",
        }[proposal.proposal_type]
        skill_id = f"platform::{proposal.name}"
        content = self._proposal_to_skill_markdown(proposal)
        return self.repository.upsert_platform_skill(
            skill_id=skill_id,
            name=proposal.name,
            description=proposal.description,
            skill_type=target_type,
            category_bindings=category_bindings or [],
            content=content,
            base_skill_ids=proposal.based_on_skill_ids,
        )

    def _resolve_skills(self, skill_ids: Iterable[str]) -> list[SkillItem]:
        catalog = {item.id: item for item in self.list_skills()}
        return [catalog[skill_id] for skill_id in skill_ids if skill_id in catalog]

    @staticmethod
    def _proposal_to_skill_markdown(proposal: SkillProposal) -> str:
        notes = "\n".join(f"- {line}" for line in proposal.implementation_notes)
        based_on = ", ".join(proposal.based_on_skill_ids) or "none"
        return (
            f"## Skill: {proposal.name}\n\n"
            f"{proposal.description}\n\n"
            f"### Rationale\n{proposal.rationale}\n\n"
            f"### Implementation Notes\n{notes}\n\n"
            f"### Based On Skills\n{based_on}\n"
        )

    def _seed_if_needed(self) -> None:
        if self.repository.list_categories():
            return

        cat_quality = self.repository.create_category(
            name="Quality Root Cause",
            description="8D and QRQC root cause analysis for manufacturing defects.",
            default_skill_ids=["builtin::geely-quality-rootcause-copilot"],
        )
        cat_maintenance = self.repository.create_category(
            name="Equipment Anomaly",
            description="Lightweight predictive maintenance with alarm diagnosis and work orders.",
            default_skill_ids=["builtin::geely-equipment-anomaly-assistant"],
        )
        cat_ops = self.repository.create_category(
            name="Ops Reporting",
            description="Daily and weekly operations monitoring for line managers.",
            default_skill_ids=["builtin::geely-ops-report-agent"],
        )

        task_quality = self.repository.create_task(
            name="Weld Defect Escalation",
            description="Investigate sudden FPY drop on BIW line.",
            category_id=cat_quality.id,
            selected_skill_ids=cat_quality.default_skill_ids,
            document_name="weld_defect_note.md",
            document_content="Spike in porosity defects from shift-B.",
        )
        self.repository.add_message(
            task_id=task_quality.id,
            role="user",
            source="user",
            content="Please prepare an 8D draft for porosity defect issue and suggest containment.",
        )

        task_maint = self.repository.create_task(
            name="Robot Arm Alarm Cluster",
            description="Recurring vibration alarms on welding robots.",
            category_id=cat_maintenance.id,
            selected_skill_ids=cat_maintenance.default_skill_ids,
            document_name="alarm_history.csv",
            document_content="Mock alarm data attached.",
        )
        self.repository.add_message(
            task_id=task_maint.id,
            role="user",
            source="user",
            content="Summarize probable causes for vibration alarm code ALM-447 and create work order content.",
        )

        task_ops = self.repository.create_task(
            name="Weekly Plant Review",
            description="Generate operations weekly review for plant manager.",
            category_id=cat_ops.id,
            selected_skill_ids=cat_ops.default_skill_ids,
            document_name="weekly_kpi.json",
            document_content='{"oee": 78.2, "fpy": 93.1, "ppm": 420}',
        )
        self.repository.add_message(
            task_id=task_ops.id,
            role="user",
            source="user",
            content="Generate weekly report with anomaly explanation and action items.",
        )

        self.repository.upsert_platform_skill(
            skill_id=f"platform::quick-rootcause-enhancer-{uuid4().hex[:6]}",
            name="quick-rootcause-enhancer",
            description="Enhances existing quality analysis skills with defect Pareto and station trace templates.",
            skill_type="platform_enhanced",
            category_bindings=[cat_quality.id],
            content="## quick-rootcause-enhancer\n- Add Pareto defect ranking.\n- Include station parameter trace checklist.\n",
            base_skill_ids=["builtin::geely-quality-rootcause-copilot"],
        )

