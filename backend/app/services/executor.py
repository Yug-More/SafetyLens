"""Deterministic simulated action executor — no real external side effects."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.enums import ActionExecutionStatus, SimulatedActionType
from app.database.base import utc_now
from app.models.procedure_policy import PlannedAction


@dataclass
class SimulationOutcome:
    status: ActionExecutionStatus
    message: str
    external_reference: str | None
    failure_code: str | None = None
    failure_reason: str | None = None
    force_fail: bool = False


def infer_action_type(action: PlannedAction) -> SimulatedActionType:
    text = f"{action.title} {action.description}".lower()
    if "supervisor" in text or "notify" in text and "floor" in text:
        return SimulatedActionType.ALERT_SUPERVISOR
    if "medical" in text or "assistance" in text:
        return SimulatedActionType.REQUEST_MEDICAL
    if "ticket" in text or "document" in text or "report" in text or "record the incident" in text:
        return SimulatedActionType.CREATE_TICKET
    if "evidence" in text or "footage" in text or "preserve" in text:
        return SimulatedActionType.PRESERVE_EVIDENCE
    if "isolat" in text or "machinery" in text or "area" in text:
        return SimulatedActionType.AREA_ISOLATION
    if "follow-up" in text or "follow up" in text or "review" in text:
        return SimulatedActionType.FOLLOW_UP_REVIEW
    return SimulatedActionType.GENERIC


def target_for_action(action: PlannedAction, action_type: SimulatedActionType) -> str:
    mapping = {
        SimulatedActionType.ALERT_SUPERVISOR: "floor-supervisor-channel (simulated)",
        SimulatedActionType.REQUEST_MEDICAL: "on-site medical desk (simulated)",
        SimulatedActionType.CREATE_TICKET: "incident-ticket queue (simulated)",
        SimulatedActionType.PRESERVE_EVIDENCE: "evidence vault (simulated)",
        SimulatedActionType.AREA_ISOLATION: "area-control checklist (simulated)",
        SimulatedActionType.FOLLOW_UP_REVIEW: "safety follow-up queue (simulated)",
        SimulatedActionType.GENERIC: action.responsible_role,
    }
    return mapping.get(action_type, action.responsible_role)


class SimulatedActionExecutor:
    """Local deterministic executor. Never contacts real workplace systems."""

    name = "simulated"
    simulation = True

    def __init__(self, *, fail_action_ids: set[str] | None = None) -> None:
        self._fail_action_ids = fail_action_ids or set()

    def execute(self, action: PlannedAction, *, attempt: int = 1) -> SimulationOutcome:
        action_type = infer_action_type(action)
        target = target_for_action(action, action_type)
        ref = f"SIM-{action.id[:8].upper()}-{attempt}"

        if action.id in self._fail_action_ids and attempt == 1:
            return SimulationOutcome(
                status=ActionExecutionStatus.FAILED,
                message=(
                    "Simulated execution failed for demonstration retry coverage. "
                    "No real workplace system was contacted."
                ),
                external_reference=None,
                failure_code="SIMULATED_FAILURE",
                failure_reason="Injected simulated failure",
                force_fail=True,
            )

        messages = {
            SimulatedActionType.ALERT_SUPERVISOR: (
                "Simulated supervisor notification queued for demonstration. "
                "No real message was delivered to a supervisor."
            ),
            SimulatedActionType.REQUEST_MEDICAL: (
                "Simulated medical-assistance request created for demonstration. "
                "Emergency services were not contacted."
            ),
            SimulatedActionType.CREATE_TICKET: (
                "Simulated incident ticket created for demonstration. "
                "No external ticketing system was updated."
            ),
            SimulatedActionType.PRESERVE_EVIDENCE: (
                "Simulated evidence-preservation record created. "
                "Source media paths remain local and were not exported."
            ),
            SimulatedActionType.AREA_ISOLATION: (
                "Simulated area-isolation recommendation recorded for demonstration."
            ),
            SimulatedActionType.FOLLOW_UP_REVIEW: (
                "Simulated follow-up review task scheduled for demonstration."
            ),
            SimulatedActionType.GENERIC: (
                f"Simulated action recorded for '{action.title}'. "
                "No real external system was contacted."
            ),
        }
        return SimulationOutcome(
            status=ActionExecutionStatus.COMPLETED,
            message=messages[action_type],
            external_reference=ref,
        )


def get_action_executor(*, fail_action_ids: set[str] | None = None) -> SimulatedActionExecutor:
    return SimulatedActionExecutor(fail_action_ids=fail_action_ids)
