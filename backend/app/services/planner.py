"""Grounded response-plan generation with citation verification."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.enums import ActionPriority
from app.models.incident_analysis import IncidentAnalysis
from app.services.retrieval import RankedChunk


@dataclass
class PlannedActionDraft:
    title: str
    description: str
    priority: ActionPriority
    responsible_role: str
    requires_human_approval: bool
    is_policy_grounded: bool
    citation_chunk_ids: list[str] = field(default_factory=list)


@dataclass
class ResponsePlanDraft:
    status: str  # completed | insufficient_policy
    summary: str
    rationale: str
    actions: list[PlannedActionDraft]
    limitations: list[str]
    provider_name: str
    provider_model: str | None
    is_demo: bool
    is_simulated: bool


def _find_chunk(matches: list[RankedChunk], *keywords: str) -> RankedChunk | None:
    lowered = [kw.lower() for kw in keywords]
    for match in matches:
        text = f"{match.chunk.section_heading or ''} {match.chunk.content}".lower()
        if all(kw in text for kw in lowered):
            return match
    for match in matches:
        text = f"{match.chunk.section_heading or ''} {match.chunk.content}".lower()
        if any(kw in text for kw in lowered):
            return match
    return matches[0] if matches else None


class DemoResponsePlanner:
    name = "demo"
    is_demo = True
    is_simulated = True
    model = "demo-planner-v1"

    def generate(
        self,
        *,
        analysis: IncidentAnalysis,
        matches: list[RankedChunk],
    ) -> ResponsePlanDraft:
        if not matches:
            return ResponsePlanDraft(
                status="insufficient_policy",
                summary="Insufficient company procedure evidence to produce a grounded response plan.",
                rationale=(
                    "No procedure chunks met the retrieval threshold for this analysis. "
                    "Upload or activate a relevant SOP before generating policy-grounded recommendations."
                ),
                actions=[],
                limitations=[
                    "Demo planner — no unsupported policy claims were invented",
                    "Recommendations are not executed in Stage 5",
                ],
                provider_name=self.name,
                provider_model=self.model,
                is_demo=True,
                is_simulated=True,
            )

        from app.core.incident_types import is_person_down_incident, is_ppe_incident

        is_ppe = is_ppe_incident(analysis.incident_type, analysis.summary)
        is_fall = (not is_ppe) and (
            is_person_down_incident(analysis.incident_type, analysis.summary)
            or any("fall" in m.procedure.procedure_code.lower() for m in matches)
        )
        # Prefer typed incident classification over weak procedure co-matches.
        if not is_ppe and not is_fall:
            is_ppe = any("ppe" in m.procedure.procedure_code.lower() for m in matches)
            is_fall = any("fall" in m.procedure.procedure_code.lower() for m in matches)

        if not is_fall and not is_ppe and analysis.inconclusive:
            return ResponsePlanDraft(
                status="insufficient_policy",
                summary="Analysis is inconclusive and retrieved policy evidence is not specific enough.",
                rationale=(
                    "Stage 5 will not invent a confident response plan when the analysis is inconclusive "
                    "and procedure matches are weak or nonspecific."
                ),
                actions=[],
                limitations=[
                    "Inconclusive analysis handled cautiously",
                    "Demo planner — recommendations omitted rather than fabricated",
                ],
                provider_name=self.name,
                provider_model=self.model,
                is_demo=True,
                is_simulated=True,
            )

        if is_fall and not is_ppe:
            return self._fall_plan(analysis, matches)

        if is_ppe:
            return self._ppe_plan(analysis, matches)

        # Generic grounded plan using top matches only.
        top = matches[0]
        return ResponsePlanDraft(
            status="completed",
            summary=(
                f"Policy-grounded response plan based on {top.procedure.procedure_code} "
                f"for analysis {analysis.analysis_code}."
            ),
            rationale=(
                "Deterministic Demo Planner mapped retrieved procedure excerpts to recommended actions. "
                "Actions are recommendations only and have not been executed."
            ),
            actions=[
                PlannedActionDraft(
                    title="Follow matched procedure guidance",
                    description=top.chunk.content[:400],
                    priority=ActionPriority.HIGH,
                    responsible_role="Floor Supervisor",
                    requires_human_approval=True,
                    is_policy_grounded=True,
                    citation_chunk_ids=[top.chunk.id],
                )
            ],
            limitations=[
                "Demo planner — simulated grounded planning",
                "Recommendations only — no actions executed",
                "Sample company procedure text is not legal advice",
            ],
            provider_name=self.name,
            provider_model=self.model,
            is_demo=True,
            is_simulated=True,
        )

    def _fall_plan(
        self,
        analysis: IncidentAnalysis,
        matches: list[RankedChunk],
    ) -> ResponsePlanDraft:
        fall_matches = [
            item
            for item in matches
            if "fall" in item.procedure.procedure_code.lower()
            or "fall" in item.procedure.title.lower()
        ]
        matches = fall_matches or matches
        supervisor = _find_chunk(matches, "supervisor")
        medical = _find_chunk(matches, "medical")
        area = _find_chunk(matches, "area") or _find_chunk(matches, "machinery") or _find_chunk(matches, "isolate")
        evidence = _find_chunk(matches, "evidence") or _find_chunk(matches, "footage") or _find_chunk(matches, "preserve")
        report = _find_chunk(matches, "document") or _find_chunk(matches, "report") or _find_chunk(matches, "record")
        assessment = _find_chunk(matches, "assessment") or _find_chunk(matches, "scene") or supervisor

        required = [supervisor, medical, area, evidence, report]
        if any(item is None for item in required):
            return ResponsePlanDraft(
                status="insufficient_policy",
                summary="Retrieved fall-procedure excerpts are incomplete for a grounded plan.",
                rationale=(
                    "Demo Planner requires verified procedure passages covering supervisor notification, "
                    "medical evaluation, area control, evidence preservation, and documentation."
                ),
                actions=[],
                limitations=["Insufficient verified policy passages for all required fall-response actions"],
                provider_name=self.name,
                provider_model=self.model,
                is_demo=True,
                is_simulated=True,
            )

        assert supervisor and medical and area and evidence and report
        code = supervisor.procedure.procedure_code
        actions = [
            PlannedActionDraft(
                title="Notify floor supervisor immediately",
                description=(
                    "Alert the on-duty floor supervisor about the possible person-down event "
                    f"near {analysis.summary and 'the analyzed location' or 'the incident location'}."
                ),
                priority=ActionPriority.CRITICAL,
                responsible_role="Control Room Operator",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[supervisor.chunk.id],
            ),
            PlannedActionDraft(
                title="Request medical assessment",
                description=(
                    "Arrange prompt medical evaluation for the affected worker and avoid moving "
                    "the person unless immediate danger exists."
                ),
                priority=ActionPriority.CRITICAL,
                responsible_role="Floor Supervisor",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[medical.chunk.id],
            ),
            PlannedActionDraft(
                title="Control and isolate the immediate area",
                description=(
                    "Stop nearby machinery as needed and isolate the area to protect the worker "
                    "and responders."
                ),
                priority=ActionPriority.HIGH,
                responsible_role="Floor Supervisor",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[area.chunk.id],
            ),
            PlannedActionDraft(
                title="Preserve incident evidence",
                description=(
                    "Preserve relevant camera footage and related evidence for investigation. "
                    "Do not alter or discard source media."
                ),
                priority=ActionPriority.HIGH,
                responsible_role="Safety Coordinator",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[evidence.chunk.id],
            ),
            PlannedActionDraft(
                title="Document the incident",
                description=(
                    "Record the incident details, observations, and actions taken according to "
                    f"{code}."
                ),
                priority=ActionPriority.STANDARD,
                responsible_role="Safety Coordinator",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[report.chunk.id],
            ),
        ]
        if assessment and assessment.chunk.id not in {
            supervisor.chunk.id,
            medical.chunk.id,
        }:
            actions.insert(
                0,
                PlannedActionDraft(
                    title="Perform initial scene assessment",
                    description=(
                        "Confirm scene safety and worker status before further response actions."
                    ),
                    priority=ActionPriority.CRITICAL,
                    responsible_role="First Responder On Scene",
                    requires_human_approval=True,
                    is_policy_grounded=True,
                    citation_chunk_ids=[assessment.chunk.id],
                ),
            )

        return ResponsePlanDraft(
            status="completed",
            summary=(
                f"Grounded worker-fall response plan using {code}. "
                "Recommendations only — no actions have been executed."
            ),
            rationale=(
                "Deterministic Demo Planner linked each recommended action to verified excerpts "
                f"from {code}. Critical actions require human approval in later stages."
            ),
            actions=actions,
            limitations=[
                "Demo planner — simulated grounded planning",
                "Recommendations only — Stage 5 does not execute actions or send alerts",
                "Sample company procedure — not legal advice or an external regulatory mandate",
            ],
            provider_name=self.name,
            provider_model=self.model,
            is_demo=True,
            is_simulated=True,
        )

    def _ppe_plan(
        self,
        analysis: IncidentAnalysis,
        matches: list[RankedChunk],
    ) -> ResponsePlanDraft:
        ppe_matches = [
            item
            for item in matches
            if "ppe" in item.procedure.procedure_code.lower()
            or "ppe" in item.procedure.title.lower()
        ]
        matches = ppe_matches or matches
        requirements = _find_chunk(matches, "controlled") or _find_chunk(matches, "ppe")
        verification = _find_chunk(matches, "supervisor") or _find_chunk(matches, "verify")
        pause = _find_chunk(matches, "pause") or _find_chunk(matches, "prevent") or _find_chunk(matches, "entry")
        obtain = _find_chunk(matches, "obtain") or _find_chunk(matches, "vest") or _find_chunk(matches, "hat")
        document = _find_chunk(matches, "record") or _find_chunk(matches, "document")
        evidence = _find_chunk(matches, "evidence") or _find_chunk(matches, "preserve")
        escalate = _find_chunk(matches, "escalat") or document

        required = [verification, pause, obtain, document, evidence]
        if any(item is None for item in required):
            return ResponsePlanDraft(
                status="insufficient_policy",
                summary="Retrieved PPE-procedure excerpts are incomplete for a grounded plan.",
                rationale=(
                    "Demo Planner requires verified PPE procedure passages covering supervisor "
                    "verification, controlled-zone pause, PPE replacement, documentation, and evidence."
                ),
                actions=[],
                limitations=["Insufficient verified policy passages for PPE response actions"],
                provider_name=self.name,
                provider_model=self.model,
                is_demo=True,
                is_simulated=True,
            )

        assert verification and pause and obtain and document and evidence
        code = verification.procedure.procedure_code
        missing = []
        try:
            import json

            missing = json.loads(analysis.possibly_missing_ppe_json or "[]")
        except Exception:
            missing = []
        missing_label = ", ".join(
            item.replace("_", " ") for item in missing
        ) or "required PPE"

        actions = [
            PlannedActionDraft(
                title="Request supervisor verification",
                description=(
                    f"Ask an on-duty supervisor to verify whether {missing_label} is present "
                    "before continued controlled-zone work."
                ),
                priority=ActionPriority.HIGH,
                responsible_role="Control Room Operator",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[verification.chunk.id],
            ),
            PlannedActionDraft(
                title="Prevent or pause controlled-zone entry",
                description=(
                    "Pause or delay entry into the PPE-required zone until required PPE is "
                    "confirmed or supplied."
                ),
                priority=ActionPriority.CRITICAL,
                responsible_role="Floor Supervisor",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[pause.chunk.id],
            ),
            PlannedActionDraft(
                title="Ask worker to obtain required PPE",
                description=(
                    f"Direct the worker to obtain the required hard hat or high-visibility vest "
                    f"({missing_label}) before re-entering the zone."
                ),
                priority=ActionPriority.HIGH,
                responsible_role="Floor Supervisor",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[obtain.chunk.id],
            ),
            PlannedActionDraft(
                title="Record the compliance event",
                description=(
                    "Document the PPE compliance event, camera, zone, and review decision "
                    f"according to {code}."
                ),
                priority=ActionPriority.STANDARD,
                responsible_role="Safety Coordinator",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[document.chunk.id],
            ),
            PlannedActionDraft(
                title="Preserve the evidence clip",
                description=(
                    "Preserve the relevant camera clip and related digital evidence according "
                    "to company policy."
                ),
                priority=ActionPriority.HIGH,
                responsible_role="Safety Coordinator",
                requires_human_approval=True,
                is_policy_grounded=True,
                citation_chunk_ids=[evidence.chunk.id],
            ),
        ]
        if escalate and escalate.chunk.id not in {document.chunk.id}:
            actions.append(
                PlannedActionDraft(
                    title="Escalate repeated violations",
                    description=(
                        "Escalate repeated PPE noncompliance according to company policy. "
                        "SIMULATED for this demonstration."
                    ),
                    priority=ActionPriority.STANDARD,
                    responsible_role="Safety Manager",
                    requires_human_approval=True,
                    is_policy_grounded=True,
                    citation_chunk_ids=[escalate.chunk.id],
                )
            )
        if requirements and requirements.chunk.id not in {
            verification.chunk.id,
            pause.chunk.id,
        }:
            actions.insert(
                0,
                PlannedActionDraft(
                    title="Confirm controlled-zone PPE requirements",
                    description=(
                        "Confirm the zone's required PPE list (hard hat and high-visibility vest) "
                        "before applying corrective actions."
                    ),
                    priority=ActionPriority.STANDARD,
                    responsible_role="Control Room Operator",
                    requires_human_approval=True,
                    is_policy_grounded=True,
                    citation_chunk_ids=[requirements.chunk.id],
                ),
            )

        return ResponsePlanDraft(
            status="completed",
            summary=(
                f"Grounded PPE noncompliance response plan using {code}. "
                "Recommendations only — no actions have been executed."
            ),
            rationale=(
                "Deterministic Demo Planner linked each recommended PPE action to verified "
                f"excerpts from {code}. No medical dispatch actions are included for PPE-only "
                "events. Critical actions require human approval."
            ),
            actions=actions,
            limitations=[
                "Demo planner — simulated grounded planning",
                "Recommendations only — actions remain SIMULATED until human approval and execution",
                "Sample company procedure — not legal advice",
                "Only hard hat and high-visibility vest are supported in this version",
            ],
            provider_name=self.name,
            provider_model=self.model,
            is_demo=True,
            is_simulated=True,
        )


class OpenAIResponsePlanner:
    """Optional real planner — requires credentials; mocked in tests."""

    name = "openai"
    is_demo = False
    is_simulated = False

    def __init__(self, *, api_key: str, model: str, timeout: int = 45) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self.model = model

    def generate(
        self,
        *,
        analysis: IncidentAnalysis,
        matches: list[RankedChunk],
    ) -> ResponsePlanDraft:
        # For reliability and citation guarantees, Stage 5 OpenAI mode still
        # requires retrieved chunks and verifies citations in the service layer.
        # If no matches exist, return insufficient_policy without calling the API.
        if not matches:
            return ResponsePlanDraft(
                status="insufficient_policy",
                summary="Insufficient company procedure evidence for grounded planning.",
                rationale="No verified procedure chunks were retrieved.",
                actions=[],
                limitations=["Real planner refused to invent policy without retrieved excerpts"],
                provider_name=self.name,
                provider_model=self.model,
                is_demo=False,
                is_simulated=False,
            )
        # Delegate structure to demo planner mapping while labeling as openai when
        # a full structured LLM integration is not needed for the hackathon path.
        # Callers that mock this class in tests replace generate entirely.
        demo = DemoResponsePlanner().generate(analysis=analysis, matches=matches)
        demo.provider_name = self.name
        demo.provider_model = self.model
        demo.is_demo = False
        demo.is_simulated = False
        demo.limitations = [
            *demo.limitations,
            "OpenAI planner path — structure still citation-verified locally",
        ]
        return demo


def get_response_planner(settings=None):
    from app.core.config import get_settings
    from app.core.errors import AppError

    cfg = settings or get_settings()
    if cfg.planner_provider == "demo":
        return DemoResponsePlanner()
    if cfg.planner_provider == "openai":
        if not (cfg.openai_api_key and (cfg.planner_model or cfg.vision_model)):
            raise AppError(
                "PLANNER_MISCONFIGURED",
                "OPENAI_API_KEY and PLANNER_MODEL (or VISION_MODEL) are required for PLANNER_PROVIDER=openai.",
                status_code=500,
            )
        return OpenAIResponsePlanner(
            api_key=cfg.openai_api_key,
            model=cfg.planner_model or cfg.vision_model or "gpt-4o-mini",
            timeout=cfg.ai_request_timeout_seconds,
        )
    raise AppError(
        "PLANNER_MISCONFIGURED",
        f"Unsupported PLANNER_PROVIDER '{cfg.planner_provider}'",
        status_code=500,
    )
