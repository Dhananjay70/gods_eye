"""
COPS Incident State Machine — manages the lifecycle of a security incident.

States flow:
  MONITORING -> INVESTIGATING -> ASSESSING -> MATERIAL_LIKELY ->
  MATERIAL_CONFIRMED -> DISCLOSURE_DRAFTING -> UNDER_REVIEW -> FILED -> CLOSED
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class IncidentState(str, Enum):
    MONITORING = "monitoring"
    INVESTIGATING = "investigating"
    ASSESSING = "assessing"
    MATERIAL_LIKELY = "material_likely"
    MATERIAL_CONFIRMED = "material_confirmed"
    DISCLOSURE_DRAFTING = "disclosure_drafting"
    UNDER_REVIEW = "under_review"
    FILED = "filed"
    CLOSED = "closed"


# Valid transitions: current_state -> set of allowed next states
TRANSITIONS: dict[IncidentState, set[IncidentState]] = {
    IncidentState.MONITORING: {
        IncidentState.INVESTIGATING,
        IncidentState.CLOSED,
    },
    IncidentState.INVESTIGATING: {
        IncidentState.ASSESSING,
        IncidentState.MONITORING,
        IncidentState.CLOSED,
    },
    IncidentState.ASSESSING: {
        IncidentState.MATERIAL_LIKELY,
        IncidentState.INVESTIGATING,
        IncidentState.CLOSED,
    },
    IncidentState.MATERIAL_LIKELY: {
        IncidentState.MATERIAL_CONFIRMED,
        IncidentState.ASSESSING,
    },
    IncidentState.MATERIAL_CONFIRMED: {
        IncidentState.DISCLOSURE_DRAFTING,
    },
    IncidentState.DISCLOSURE_DRAFTING: {
        IncidentState.UNDER_REVIEW,
        IncidentState.MATERIAL_CONFIRMED,
    },
    IncidentState.UNDER_REVIEW: {
        IncidentState.FILED,
        IncidentState.DISCLOSURE_DRAFTING,
    },
    IncidentState.FILED: {
        IncidentState.CLOSED,
    },
    IncidentState.CLOSED: set(),
}


@dataclass
class TransitionResult:
    """Outcome of a state transition attempt."""
    success: bool
    from_state: str
    to_state: str
    message: str = ""


class IncidentStateMachine:
    """Validates and records incident state transitions."""

    @staticmethod
    def can_transition(current: str | IncidentState, target: str | IncidentState) -> bool:
        current_state = IncidentState(current)
        target_state = IncidentState(target)
        return target_state in TRANSITIONS.get(current_state, set())

    @staticmethod
    def transition(
        current: str | IncidentState,
        target: str | IncidentState,
        actor: str = "system",
    ) -> TransitionResult:
        """Attempt a state transition.

        Returns a TransitionResult indicating success/failure.
        The caller is responsible for persisting the new state and
        logging the transition to ONSA.
        """
        current_state = IncidentState(current)
        target_state = IncidentState(target)

        if target_state not in TRANSITIONS.get(current_state, set()):
            allowed = ", ".join(s.value for s in TRANSITIONS.get(current_state, set()))
            return TransitionResult(
                success=False,
                from_state=current_state.value,
                to_state=target_state.value,
                message=f"Invalid transition from '{current_state.value}' to '{target_state.value}'. "
                        f"Allowed: [{allowed}]",
            )

        return TransitionResult(
            success=True,
            from_state=current_state.value,
            to_state=target_state.value,
            message=f"Transitioned from '{current_state.value}' to '{target_state.value}' by {actor}",
        )

    @staticmethod
    def get_allowed_transitions(current: str | IncidentState) -> list[str]:
        current_state = IncidentState(current)
        return [s.value for s in TRANSITIONS.get(current_state, set())]
