"""
Disclosure Generator — produces structured 8-K draft documents
from incident data using LLM + confidence scoring.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

from openclaw.bridge.scanner import ScanFinding
from openclaw.cops.scorer import MaterialityScore
from openclaw.cops.timeline import TimelineEvent
from openclaw.disclosure.confidence import (
    ConfidenceLevel,
    ConfidenceScore,
    parse_confidence_from_llm,
    score_section,
)
from openclaw.disclosure.llm_router import LLMResponse, LLMRouter
from openclaw.disclosure.prompts import DRAFT_8K_PROMPT, SUMMARY_PROMPT, SYSTEM_PROMPT


@dataclass
class DraftSection:
    """A single section of the disclosure draft."""
    title: str
    content: str
    confidence: ConfidenceScore = field(default_factory=lambda: ConfidenceScore(ConfidenceLevel.LOW, 0.0))
    evidence_refs: list[str] = field(default_factory=list)


@dataclass
class DisclosureDraft:
    """Complete disclosure draft with all sections."""
    draft_id: str = ""
    incident_id: str = ""
    version: int = 1
    status: str = "draft"
    nature_and_scope: DraftSection = field(
        default_factory=lambda: DraftSection(title="Nature and Scope of the Incident", content="")
    )
    data_impact: DraftSection = field(
        default_factory=lambda: DraftSection(title="Impact on Data and Systems", content="")
    )
    material_impact: DraftSection = field(
        default_factory=lambda: DraftSection(title="Material Impact Assessment", content="")
    )
    remediation: DraftSection = field(
        default_factory=lambda: DraftSection(title="Remediation Status", content="")
    )
    executive_summary: str = ""
    llm_model: str = ""
    llm_provider: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DisclosureGenerator:
    """Generates disclosure drafts using LLM + evidence analysis."""

    def __init__(self):
        self.router = LLMRouter()

    async def generate_draft(
        self,
        incident_id: str,
        findings: list[ScanFinding],
        materiality: MaterialityScore,
        timeline: list[TimelineEvent],
        version: int = 1,
    ) -> DisclosureDraft:
        """Generate a full disclosure draft."""
        # Build prompt context
        findings_summary = self._format_findings(findings)
        timeline_summary = self._format_timeline(timeline)
        score_breakdown = self._format_score(materiality)

        incident_summary = (
            f"Incident {incident_id}: {len(findings)} security findings detected. "
            f"Materiality score: {materiality.score} ({materiality.level})."
        )

        prompt = DRAFT_8K_PROMPT.format(
            incident_summary=incident_summary,
            findings_summary=findings_summary,
            materiality_score=materiality.score,
            materiality_level=materiality.level,
            score_breakdown=score_breakdown,
            timeline_summary=timeline_summary,
        )

        # Generate via LLM
        response = await self.router.route(SYSTEM_PROMPT, prompt)

        # Parse sections from LLM response
        sections = self._parse_sections(response.text)

        # Score each section's confidence
        evidence_count = len(findings)
        for section in sections.values():
            # Use LLM's own confidence tag if present
            llm_confidence = parse_confidence_from_llm(section.content)
            # Also compute our own
            computed = score_section(section.content, evidence_count)
            # Take the lower of the two (conservative)
            if llm_confidence == ConfidenceLevel.LOW or computed.level == ConfidenceLevel.LOW:
                section.confidence = ConfidenceScore(ConfidenceLevel.LOW, min(computed.score, 0.4))
            elif llm_confidence == ConfidenceLevel.MEDIUM or computed.level == ConfidenceLevel.MEDIUM:
                section.confidence = computed
            else:
                section.confidence = computed

            # Remove the [CONFIDENCE: ...] tag from the text
            section.content = re.sub(r'\[CONFIDENCE:\s*\w+\]\s*\n?', '', section.content).strip()

        # Generate executive summary
        exec_summary = await self._generate_summary(incident_summary, materiality, findings)

        draft = DisclosureDraft(
            incident_id=incident_id,
            version=version,
            nature_and_scope=sections.get("nature", DraftSection(title="Nature and Scope", content="")),
            data_impact=sections.get("impact", DraftSection(title="Impact on Data and Systems", content="")),
            material_impact=sections.get("material", DraftSection(title="Material Impact Assessment", content="")),
            remediation=sections.get("remediation", DraftSection(title="Remediation Status", content="")),
            executive_summary=exec_summary,
            llm_model=response.model,
            llm_provider=response.provider,
        )

        return draft

    async def _generate_summary(
        self,
        incident_summary: str,
        materiality: MaterialityScore,
        findings: list[ScanFinding],
    ) -> str:
        """Generate an executive summary."""
        details = (
            f"{incident_summary}\n"
            f"Score: {materiality.score} ({materiality.level})\n"
            f"Affected systems: {len(findings)}\n"
            f"Security grades: {', '.join(f.sec_grade for f in findings[:10])}"
        )
        prompt = SUMMARY_PROMPT.format(incident_details=details)
        response = await self.router.route(SYSTEM_PROMPT, prompt)
        return response.text.strip() if response.success else ""

    def _parse_sections(self, text: str) -> dict[str, DraftSection]:
        """Parse the 4 sections from LLM output."""
        sections: dict[str, DraftSection] = {}

        # Try to split by numbered headers
        patterns = [
            (r"###?\s*1\.?\s*Nature\s+and\s+Scope.*?\n(.*?)(?=###?\s*2\.|$)", "nature"),
            (r"###?\s*2\.?\s*Impact\s+on\s+Data.*?\n(.*?)(?=###?\s*3\.|$)", "impact"),
            (r"###?\s*3\.?\s*Material\s+Impact.*?\n(.*?)(?=###?\s*4\.|$)", "material"),
            (r"###?\s*4\.?\s*Remediation.*?\n(.*?)(?=$)", "remediation"),
        ]

        for pattern, key in patterns:
            match = re.search(pattern, text, re.I | re.S)
            content = match.group(1).strip() if match else ""
            title_map = {
                "nature": "Nature and Scope of the Incident",
                "impact": "Impact on Data and Systems",
                "material": "Material Impact Assessment",
                "remediation": "Remediation Status",
            }
            sections[key] = DraftSection(title=title_map[key], content=content)

        return sections

    @staticmethod
    def _format_findings(findings: list[ScanFinding]) -> str:
        lines = []
        for f in findings[:20]:
            lines.append(
                f"- {f.url}: status={f.status}, grade={f.sec_grade}, "
                f"techs=[{', '.join(f.techs)}], category={f.category}"
            )
        return "\n".join(lines) if lines else "No findings available."

    @staticmethod
    def _format_timeline(events: list[TimelineEvent]) -> str:
        lines = []
        for e in events[:30]:
            lines.append(f"- [{e.timestamp}] {e.description} (by {e.actor})")
        return "\n".join(lines) if lines else "No timeline events."

    @staticmethod
    def _format_score(score: MaterialityScore) -> str:
        b = score.breakdown
        return (
            f"Grade: {b.grade_score} | Category: {b.category_score} | "
            f"Tech: {b.tech_score} | TLS: {b.tls_score} | Diff: {b.diff_score}\n"
            f"Composite: {b.composite} | Level: {score.level}"
        )
