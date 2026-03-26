"""Tests for skill-build platform service."""

from pathlib import Path

from mini_agent.platform.service import SkillBuildService


def test_seed_data_and_skill_lab_analysis(tmp_path: Path):
    db_path = tmp_path / "platform.db"
    skills_dir = Path.cwd() / "mini_agent" / "skills"
    service = SkillBuildService(db_path=str(db_path), skills_dir=str(skills_dir), redis_url=None)

    categories = service.list_categories()
    tasks = service.list_tasks()
    skills = service.list_skills()

    assert len(categories) >= 3
    assert len(tasks) >= 3
    assert any(skill.name == "geely-quality-rootcause-copilot" for skill in skills)

    response = service.analyze_skill_lab(task_ids=[tasks[0].id, tasks[1].id], include_industry_knowledge=True)
    assert response.analyzed_task_count == 2
    assert len(response.suggestions) >= 1
    assert response.evidence_summary


def test_post_user_message_generates_assistant_reply(tmp_path: Path):
    db_path = tmp_path / "platform.db"
    skills_dir = Path.cwd() / "mini_agent" / "skills"
    service = SkillBuildService(db_path=str(db_path), skills_dir=str(skills_dir), redis_url=None)
    task = service.list_tasks()[0]

    created = service.post_user_message(task_id=task.id, content="Please create 8D root cause summary")
    assert len(created) >= 2
    assert any(message.source == "assistant" for message in created)


def test_update_category_and_builtin_skill_binding(tmp_path: Path):
    db_path = tmp_path / "platform.db"
    skills_dir = Path.cwd() / "mini_agent" / "skills"
    service = SkillBuildService(db_path=str(db_path), skills_dir=str(skills_dir), redis_url=None)

    category = service.list_categories()[0]
    updated_category = service.update_category(
        category_id=category.id,
        name=category.name,
        description="Updated category description",
        default_skill_ids=["builtin::geely-ops-report-agent"],
    )
    assert "Updated" in updated_category.description
    assert "builtin::geely-ops-report-agent" in updated_category.default_skill_ids

    updated_skill = service.update_platform_skill(
        skill_id="builtin::geely-ops-report-agent",
        name="geely-ops-report-agent",
        description="Enhanced reporting guidance",
        content="## Enhanced\nUse additional KPI bands.",
        category_bindings=[category.id],
    )
    assert updated_skill.type == "platform_enhanced"
    assert category.id in updated_skill.category_bindings

