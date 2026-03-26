"""LangGraph workflows for skill recommendation and synthesis."""

from __future__ import annotations

from typing import TypedDict
from uuid import uuid4

from .models import SkillProposal
from .skill_registry import CatalogSkill


class WorkflowState(TypedDict):
    """State object passed across graph nodes."""

    conversation_text: str
    include_industry_knowledge: bool
    catalog: list[CatalogSkill]
    matched_skill_ids: list[str]
    suggestions: list[SkillProposal]
    evidence_summary: str


def _build_checkpointer(redis_url: str | None):
    """Build Redis checkpointer when available, fallback to in-memory."""
    try:
        from langgraph.checkpoint.memory import MemorySaver
    except Exception:
        return None

    if not redis_url:
        return MemorySaver()

    try:
        from langgraph.checkpoint.redis import RedisSaver  # type: ignore

        return RedisSaver.from_conn_string(redis_url)
    except Exception:
        return MemorySaver()


class SkillRecommendationWorkflow:
    """LangGraph-driven workflow for orchestrated/new/enhanced skill proposals."""

    def __init__(self, redis_url: str | None = None):
        try:
            self._graph = self._build_graph(redis_url)
        except Exception:
            self._graph = None

    @staticmethod
    def _build_graph(redis_url: str | None):
        from langgraph.graph import END, START, StateGraph

        graph = StateGraph(WorkflowState)
        graph.add_node("detect_existing", _detect_existing_skills)
        graph.add_node("propose_orchestrated", _propose_orchestrated_skill)
        graph.add_node("propose_new", _propose_new_skill)
        graph.add_node("propose_enhanced", _propose_enhanced_skill)
        graph.add_node("summarize_evidence", _summarize_evidence)

        graph.add_edge(START, "detect_existing")
        graph.add_edge("detect_existing", "propose_orchestrated")
        graph.add_edge("propose_orchestrated", "propose_new")
        graph.add_edge("propose_new", "propose_enhanced")
        graph.add_edge("propose_enhanced", "summarize_evidence")
        graph.add_edge("summarize_evidence", END)

        return graph.compile(checkpointer=_build_checkpointer(redis_url))

    def run(
        self,
        conversation_text: str,
        include_industry_knowledge: bool,
        catalog: list[CatalogSkill],
    ) -> tuple[list[SkillProposal], str]:
        initial: WorkflowState = {
            "conversation_text": conversation_text,
            "include_industry_knowledge": include_industry_knowledge,
            "catalog": catalog,
            "matched_skill_ids": [],
            "suggestions": [],
            "evidence_summary": "",
        }
        if self._graph is None:
            result = _summarize_evidence(
                _propose_enhanced_skill(
                    _propose_new_skill(
                        _propose_orchestrated_skill(
                            _detect_existing_skills(initial)
                        )
                    )
                )
            )
            return result["suggestions"], result["evidence_summary"]

        config = {"configurable": {"thread_id": f"skill-lab-{uuid4().hex[:8]}"}}
        result = self._graph.invoke(initial, config=config)
        return result["suggestions"], result["evidence_summary"]


def _detect_existing_skills(state: WorkflowState) -> WorkflowState:
    text = state["conversation_text"].lower()
    matched: list[str] = []
    for item in state["catalog"]:
        keywords = [item.name.lower()] + item.description.lower().split()[:8]
        if any(token and token in text for token in keywords):
            matched.append(item.id)
    state["matched_skill_ids"] = matched[:6]
    return state


def _propose_orchestrated_skill(state: WorkflowState) -> WorkflowState:
    text = state["conversation_text"].lower()
    suggestions = list(state["suggestions"])

    if any(word in text for word in ["8d", "qrqc", "quality", "root cause", "defect"]):
        suggestions.append(
            SkillProposal(
                id=f"proposal_{uuid4().hex[:10]}",
                proposal_type="orchestrated",
                name="quality-rootcause-orchestrator",
                description="Orchestrate defect clustering, workstation trace, and 8D draft generation.",
                rationale="Conversations show repeated quality issue triage and root cause requests.",
                implementation_notes=[
                    "Chain data-fetch skill, defect-cluster skill, and report writer skill.",
                    "Emit a standardized 8D markdown output with owner and due date fields.",
                ],
                based_on_skill_ids=state["matched_skill_ids"][:3],
            )
        )
    state["suggestions"] = suggestions
    return state


def _propose_new_skill(state: WorkflowState) -> WorkflowState:
    text = state["conversation_text"].lower()
    suggestions = list(state["suggestions"])

    if any(word in text for word in ["alarm", "vibration", "downtime", "bearing", "maintenance"]):
        suggestions.append(
            SkillProposal(
                id=f"proposal_{uuid4().hex[:10]}",
                proposal_type="new",
                name="equipment-anomaly-ticket-assistant",
                description="Generate diagnostic path and maintenance ticket from equipment alarms.",
                rationale="Logs contain recurring equipment alert handling with manual handoff delays.",
                implementation_notes=[
                    "Parse alarm code and recent telemetry snapshot.",
                    "Recommend likely root causes with confidence bands.",
                    "Auto-propose work order fields for CMMS/EAM sync.",
                ],
                based_on_skill_ids=[],
            )
        )
    state["suggestions"] = suggestions
    return state


def _propose_enhanced_skill(state: WorkflowState) -> WorkflowState:
    text = state["conversation_text"].lower()
    suggestions = list(state["suggestions"])

    if any(word in text for word in ["daily report", "weekly report", "oee", "ppm", "throughput"]):
        suggestions.append(
            SkillProposal(
                id=f"proposal_{uuid4().hex[:10]}",
                proposal_type="enhanced",
                name="ops-report-agent-plus",
                description="Enhance reporting skill with anomaly explanation and action recommendations.",
                rationale="Current report generation captures metrics but lacks reasoned action follow-up.",
                implementation_notes=[
                    "Add metric outlier interpretation with baseline windows.",
                    "Attach top-3 execution actions for each critical KPI regression.",
                    "Support shift-level and plant-level aggregation templates.",
                ],
                based_on_skill_ids=state["matched_skill_ids"][:2],
            )
        )

    if state["include_industry_knowledge"]:
        for proposal in suggestions:
            proposal.implementation_notes.append(
                "Inject manufacturing ontology context (line/station/process vocabulary) before synthesis."
            )

    state["suggestions"] = suggestions
    return state


def _summarize_evidence(state: WorkflowState) -> WorkflowState:
    matched_count = len(state["matched_skill_ids"])
    proposal_count = len(state["suggestions"])
    state["evidence_summary"] = (
        f"Analyzed conversation logs with {matched_count} similar skills and generated "
        f"{proposal_count} actionable proposals."
    )
    return state

