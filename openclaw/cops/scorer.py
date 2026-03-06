"""
COPS Materiality Scorer — rule-based weighted scoring of scan findings.

Produces a composite 0.0–1.0 score indicating the likely materiality
of security issues discovered by Gods Eye.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from openclaw.bridge.scanner import ScanFinding


# ── Weight tables ────────────────────────────────────────────────────

GRADE_WEIGHTS: dict[str, float] = {
    "F": 0.90,
    "D": 0.70,
    "C": 0.40,
    "B": 0.20,
    "A": 0.05,
}

CATEGORY_WEIGHTS: dict[str, float] = {
    "Admin Panel": 0.80,
    "Login Page": 0.60,
    "API Docs": 0.50,
    "WAF/Firewall": 0.40,
    "Default Page": 0.30,
    "Access Denied": 0.20,
    "Not Found": 0.10,
    "Parked Domain": 0.05,
    "Under Construction": 0.15,
}

VULNERABLE_TECH_PATTERNS: dict[str, float] = {
    "WordPress": 0.30,
    "Joomla": 0.35,
    "Drupal": 0.25,
    "PHP": 0.20,
    "ASP.NET": 0.15,
    "jQuery": 0.10,
    "phpMyAdmin": 0.50,
}

DIFF_SEVERITY_WEIGHTS: dict[str, float] = {
    "critical": 0.90,
    "high": 0.70,
    "medium": 0.40,
    "low": 0.15,
    "new": 0.30,
    "none": 0.00,
}

# Component weights in the final composite
W_GRADE = 0.30
W_CATEGORY = 0.20
W_TECH = 0.15
W_TLS = 0.20
W_DIFF = 0.15


@dataclass
class ScoreBreakdown:
    """Detailed breakdown of a materiality score."""
    grade_score: float = 0.0
    category_score: float = 0.0
    tech_score: float = 0.0
    tls_score: float = 0.0
    diff_score: float = 0.0
    composite: float = 0.0
    findings_count: int = 0
    details: list[dict] = field(default_factory=list)


@dataclass
class MaterialityScore:
    """Final materiality assessment."""
    score: float = 0.0
    level: str = "low"  # low, medium, high, critical
    breakdown: ScoreBreakdown = field(default_factory=ScoreBreakdown)

    @staticmethod
    def classify(score: float) -> str:
        if score >= 0.8:
            return "critical"
        if score >= 0.6:
            return "high"
        if score >= 0.35:
            return "medium"
        return "low"


def _score_tls(finding: ScanFinding) -> float:
    """Score TLS issues for a single finding."""
    tls = finding.tls
    if not tls:
        # No TLS at all — critical for HTTPS URLs
        if finding.url.startswith("https"):
            return 1.0
        return 0.3  # HTTP-only site, moderate concern

    if not tls.get("issuer"):
        return 0.8  # TLS present but no issuer = self-signed or broken

    # Check for known weak configurations
    protocol = tls.get("protocol", "").lower()
    if "tls 1.0" in protocol or "ssl" in protocol:
        return 0.60
    if "tls 1.1" in protocol:
        return 0.40

    return 0.0


def score_finding(finding: ScanFinding) -> dict:
    """Score a single finding across all dimensions."""
    grade_s = GRADE_WEIGHTS.get(finding.sec_grade, 0.5)
    category_s = CATEGORY_WEIGHTS.get(finding.category, 0.1)
    tech_s = max((VULNERABLE_TECH_PATTERNS.get(t, 0.0) for t in finding.techs), default=0.0)
    tls_s = _score_tls(finding)
    diff_s = DIFF_SEVERITY_WEIGHTS.get(finding.diff_severity, 0.0)

    composite = (
        grade_s * W_GRADE
        + category_s * W_CATEGORY
        + tech_s * W_TECH
        + tls_s * W_TLS
        + diff_s * W_DIFF
    )

    return {
        "url": finding.url,
        "grade_score": round(grade_s, 3),
        "category_score": round(category_s, 3),
        "tech_score": round(tech_s, 3),
        "tls_score": round(tls_s, 3),
        "diff_score": round(diff_s, 3),
        "composite": round(composite, 3),
    }


def score_findings(findings: list[ScanFinding]) -> MaterialityScore:
    """Score all findings and produce an aggregate MaterialityScore."""
    if not findings:
        return MaterialityScore()

    details = [score_finding(f) for f in findings]

    # Aggregate: take the max composite (worst case) and average
    max_composite = max(d["composite"] for d in details)
    avg_composite = sum(d["composite"] for d in details) / len(details)

    # Final score: 70% worst-case + 30% average (conservative approach)
    final = 0.7 * max_composite + 0.3 * avg_composite

    breakdown = ScoreBreakdown(
        grade_score=round(max(d["grade_score"] for d in details), 3),
        category_score=round(max(d["category_score"] for d in details), 3),
        tech_score=round(max(d["tech_score"] for d in details), 3),
        tls_score=round(max(d["tls_score"] for d in details), 3),
        diff_score=round(max(d["diff_score"] for d in details), 3),
        composite=round(final, 3),
        findings_count=len(findings),
        details=details,
    )

    return MaterialityScore(
        score=round(final, 3),
        level=MaterialityScore.classify(final),
        breakdown=breakdown,
    )
