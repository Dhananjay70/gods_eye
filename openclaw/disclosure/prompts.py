"""
Prompt templates for LLM-powered disclosure drafting.
"""

SYSTEM_PROMPT = """You are a cybersecurity compliance assistant specializing in SEC disclosure requirements.
You help draft 8-K Item 1.05 filings for material cybersecurity incidents.

Your outputs must be:
- Factual and evidence-based (cite specific findings)
- Written in formal regulatory language
- Conservative in scope claims (do not speculate beyond evidence)
- Structured according to SEC Form 8-K Item 1.05 requirements

Do NOT include legal advice. Flag sections that require human legal review."""


DRAFT_8K_PROMPT = """Based on the following security findings and incident timeline, draft an 8-K Item 1.05 cybersecurity incident disclosure.

## Incident Summary
{incident_summary}

## Security Findings
{findings_summary}

## Materiality Assessment
Score: {materiality_score} ({materiality_level})
{score_breakdown}

## Timeline
{timeline_summary}

---

Generate a structured disclosure with these four sections:

### 1. Nature and Scope of the Incident
Describe the nature of the cybersecurity incident, when it was discovered, and the scope of impact based on the security findings.

### 2. Impact on Data and Systems
Detail any data or systems affected, based on the technology fingerprinting and security assessment results.

### 3. Material Impact Assessment
Explain the materiality determination, referencing the quantitative score and qualitative factors.

### 4. Remediation Status
Describe current and planned remediation efforts based on the security grades and identified vulnerabilities.

For each section, indicate your confidence level:
- HIGH: Directly supported by evidence in the findings
- MEDIUM: Reasonably inferred from evidence
- LOW: Requires human judgment / legal review

Format each section as:
[CONFIDENCE: HIGH/MEDIUM/LOW]
<section content>
"""


TIMELINE_ANNOTATION_PROMPT = """Annotate the following incident timeline events with legal significance.

For each event, determine:
1. Is it legally significant for SEC disclosure purposes?
2. What is its relevance to materiality determination?
3. Does it trigger any disclosure timing requirements?

Timeline:
{timeline}

Provide annotations in a structured format."""


SUMMARY_PROMPT = """Generate a concise executive summary (3-5 sentences) of the following cybersecurity incident for board-level communication.

Incident Details:
{incident_details}

The summary should:
- State the nature of the incident
- Quantify the scope (number of systems, severity)
- Indicate the materiality assessment
- Note current status and next steps
- Avoid technical jargon"""
