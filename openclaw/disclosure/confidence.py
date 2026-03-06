"""
Confidence scoring for disclosure draft sections.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class ConfidenceScore:
    """Confidence assessment for a disclosure section."""
    level: ConfidenceLevel
    score: float  # 0.0 - 1.0
    reason: str = ""

    @property
    def label(self) -> str:
        if self.score >= 0.8:
            return "HIGH"
        if self.score >= 0.5:
            return "MEDIUM"
        return "LOW"


def score_section(section_text: str, evidence_count: int) -> ConfidenceScore:
    """Score the confidence of a generated section based on evidence density.

    Heuristics:
    - More evidence references -> higher confidence
    - Hedging language ("may", "could", "potentially") -> lower confidence
    - Specific data points (numbers, grades, URLs) -> higher confidence
    """
    if not section_text:
        return ConfidenceScore(level=ConfidenceLevel.LOW, score=0.0, reason="Empty section")

    score = 0.5  # Base

    # Evidence density boost
    if evidence_count >= 5:
        score += 0.25
    elif evidence_count >= 2:
        score += 0.15
    elif evidence_count >= 1:
        score += 0.05

    # Specific data points (numbers, grades, percentages)
    specifics = len(re.findall(r'\b(?:\d+%?|grade [A-F]|score [\d.]+)\b', section_text, re.I))
    score += min(specifics * 0.03, 0.15)

    # Hedging language penalty
    hedges = len(re.findall(r'\b(?:may|might|could|potentially|possibly|unclear|uncertain)\b', section_text, re.I))
    score -= min(hedges * 0.05, 0.2)

    score = max(0.0, min(1.0, score))

    if score >= 0.8:
        level = ConfidenceLevel.HIGH
    elif score >= 0.5:
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW

    return ConfidenceScore(
        level=level,
        score=round(score, 2),
        reason=f"{evidence_count} evidence refs, {specifics} data points, {hedges} hedges",
    )


def parse_confidence_from_llm(text: str) -> ConfidenceLevel:
    """Extract a confidence tag from LLM-generated text like [CONFIDENCE: HIGH]."""
    match = re.search(r'\[CONFIDENCE:\s*(HIGH|MEDIUM|LOW)\]', text, re.I)
    if match:
        return ConfidenceLevel(match.group(1).lower())
    return ConfidenceLevel.MEDIUM
