"""
Openclaw CLI — command-line interface for the compliance platform.

Usage:
    openclaw scan -f urls.txt            # Run Gods Eye scan + ONSA audit
    openclaw verify --chain <id>         # Verify audit chain integrity
    openclaw export --chain <id>         # Export audit package as ZIP
    openclaw incidents                   # List incidents
    openclaw assess --incident <id>      # Show materiality score
    openclaw draft --incident <id>       # Generate disclosure draft
    openclaw serve                       # Start web portal
"""
from __future__ import annotations

import asyncio
import json
import sys

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BANNER = r"""[bold cyan]
   ██████  ██████  ███████ ███    ██  ██████ ██       █████  ██     ██
  ██    ██ ██   ██ ██      ████   ██ ██      ██      ██   ██ ██     ██
  ██    ██ ██████  █████   ██ ██  ██ ██      ██      ███████ ██  █  ██
  ██    ██ ██      ██      ██  ██ ██ ██      ██      ██   ██ ██ ███ ██
   ██████  ██      ███████ ██   ████  ██████ ███████ ██   ██  ███ ███
[/]
[dim]  Compliance & Disclosure Platform | Powered by Gods Eye[/]
"""


def _run(coro):
    """Run an async coroutine from sync CLI context."""
    return asyncio.run(coro)


@click.group()
@click.version_option(package_name="openclaw")
def cli():
    """Openclaw — compliance & disclosure platform built on Gods Eye."""
    console.print(BANNER)


# ── scan ─────────────────────────────────────────────────────────────

@cli.command()
@click.option("-f", "--file", "url_file", required=True, help="File containing URLs to scan")
@click.option("--threads", default=5, help="Concurrent browser threads")
@click.option("--timeout", default=8000, help="Page timeout in ms")
@click.option("--wait-mode", type=click.Choice(["fast", "balanced", "thorough"]), default="balanced")
@click.option("-o", "--out", "out_dir", default=None, help="Output directory")
@click.option("--tenant", default="default", help="Tenant ID for audit chain")
def scan(url_file, threads, timeout, wait_mode, out_dir, tenant):
    """Run a Gods Eye scan and log results to ONSA audit trail."""
    import time
    from openclaw.bridge.scanner import run_scan
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.onsa.models import AuditAction

    # Read URLs
    with open(url_file, "r", encoding="utf-8") as f:
        urls = [
            line.strip() if line.strip().startswith("http") else f"http://{line.strip()}"
            for line in f if line.strip() and not line.strip().startswith("#")
        ]

    if not urls:
        console.print("[red]No URLs found in file.[/]")
        raise SystemExit(1)

    console.print(f"[cyan]Loaded {len(urls)} URLs from {url_file}[/]")

    # Init ONSA
    onsa = ONSAEngine()
    chain = onsa.create_chain(tenant_id=tenant, description=f"Scan from {url_file}")
    console.print(f"[green]ONSA chain created:[/] {chain.chain_id}")

    # Log scan start
    onsa.append(
        chain.chain_id,
        AuditAction.SCAN_STARTED,
        actor="cli",
        data={"urls_count": len(urls), "source_file": url_file, "threads": threads},
    )

    # Run scan
    result = _run(run_scan(
        urls=urls,
        out_dir=out_dir,
        threads=threads,
        timeout=timeout,
        wait_mode=wait_mode,
    ))

    # Log each finding
    for finding in result.findings:
        onsa.append(
            chain.chain_id,
            AuditAction.FINDING_RECORDED,
            actor="gods_eye",
            data={
                "url": finding.url,
                "status": str(finding.status),
                "sec_grade": finding.sec_grade,
                "techs": finding.techs,
                "category": finding.category,
            },
        )

    # Log scan completion
    onsa.append(
        chain.chain_id,
        AuditAction.SCAN_COMPLETED,
        actor="cli",
        data={
            "scan_id": result.scan_id,
            "total": result.total,
            "success": result.success,
            "warn": result.warn,
            "fail": result.fail,
            "runtime_seconds": result.runtime_seconds,
            "output_dir": result.output_dir,
        },
    )

    # Summary
    chain_info = onsa.get_chain(chain.chain_id)
    console.print(Panel.fit(
        f"[bold green]Scan complete[/]\n"
        f"Targets: {result.total} | Success: {result.success} | "
        f"Warn: {result.warn} | Fail: {result.fail}\n"
        f"ONSA chain: {chain.chain_id} ({chain_info.length} records)\n"
        f"Output: {result.output_dir}",
        title="Openclaw Scan Results",
        border_style="green",
    ))


# ── verify ───────────────────────────────────────────────────────────

@cli.command()
@click.option("--chain", "chain_id", required=True, help="Chain ID to verify")
def verify(chain_id):
    """Verify the integrity of an ONSA audit chain."""
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.onsa.verify import verify_chain as do_verify

    onsa = ONSAEngine()
    result = do_verify(onsa, chain_id)

    if result.valid:
        console.print(Panel.fit(
            f"[bold green]CHAIN VALID[/]\n"
            f"Chain: {chain_id}\n"
            f"Records checked: {result.records_checked}\n"
            f"{result.message}",
            border_style="green",
        ))
    else:
        console.print(Panel.fit(
            f"[bold red]CHAIN INVALID[/]\n"
            f"Chain: {chain_id}\n"
            f"Records checked: {result.records_checked}\n"
            f"Failed at sequence: {result.first_invalid_seq}\n"
            f"{result.message}",
            border_style="red",
        ))
        raise SystemExit(1)


# ── export ───────────────────────────────────────────────────────────

@cli.command("export")
@click.option("--chain", "chain_id", required=True, help="Chain ID to export")
@click.option("-o", "--output", "output_path", default=None, help="Output ZIP path")
def export_cmd(chain_id, output_path):
    """Export an ONSA audit chain as a verifiable ZIP package."""
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.onsa.export import export_package

    onsa = ONSAEngine()
    path = export_package(onsa, chain_id, output_path)
    console.print(f"[green bold]Audit package exported to:[/] {path}")


# ── chains ───────────────────────────────────────────────────────────

@cli.command()
@click.option("--tenant", default=None, help="Filter by tenant")
def chains(tenant):
    """List all ONSA audit chains."""
    from openclaw.onsa.engine import ONSAEngine

    onsa = ONSAEngine()
    chain_list = onsa.list_chains(tenant_id=tenant)

    if not chain_list:
        console.print("[yellow]No chains found.[/]")
        return

    table = Table(title="ONSA Audit Chains", show_header=True, header_style="bold cyan")
    table.add_column("Chain ID", width=34)
    table.add_column("Tenant", width=12)
    table.add_column("Records", justify="right", width=8)
    table.add_column("Created", width=22)
    table.add_column("Description", width=30)

    for c in chain_list:
        table.add_row(c.chain_id, c.tenant_id, str(c.length), c.created_at[:19], c.description[:30])

    console.print(table)


# ── score ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--chain", "chain_id", required=True, help="Chain ID with scan findings")
def score(chain_id):
    """Calculate materiality score from scan findings in a chain."""
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.cops.engine import COPSEngine
    from openclaw.bridge.scanner import ScanFinding

    onsa = ONSAEngine()
    cops = COPSEngine(onsa)

    records = onsa.get_records(chain_id)
    findings = []
    for rec in records:
        if rec.action == "finding.recorded":
            meta = rec.metadata or {}
            findings.append(ScanFinding(
                url=meta.get("url", ""),
                sec_grade=meta.get("sec_grade", "F"),
                techs=meta.get("techs", []),
                category=meta.get("category", ""),
            ))

    if not findings:
        console.print("[yellow]No findings found in chain.[/]")
        return

    from openclaw.cops.scorer import score_findings
    mat_score = score_findings(findings)

    # Color-code the level
    level_colors = {"critical": "red bold", "high": "red", "medium": "yellow", "low": "green"}
    level_style = level_colors.get(mat_score.level, "white")

    b = mat_score.breakdown
    console.print(Panel.fit(
        f"[bold]Materiality Score: [{level_style}]{mat_score.score}[/] ({mat_score.level.upper()})[/]\n\n"
        f"Grade component:    {b.grade_score}\n"
        f"Category component: {b.category_score}\n"
        f"Tech component:     {b.tech_score}\n"
        f"TLS component:      {b.tls_score}\n"
        f"Diff component:     {b.diff_score}\n"
        f"Composite:          {b.composite}\n\n"
        f"Findings analysed:  {b.findings_count}",
        title="COPS Materiality Assessment",
        border_style="cyan",
    ))

    if cops.check_thresholds(mat_score):
        console.print(f"\n[red bold]ALERT: Score exceeds materiality threshold![/]")


# ── draft ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--chain", "chain_id", required=True, help="Chain ID to generate draft from")
@click.option("--view", is_flag=True, help="Display draft with confidence scores")
def draft(chain_id, view):  # noqa: ARG001 — view reserved for future use
    """Generate a disclosure draft from scan findings."""
    from openclaw.onsa.engine import ONSAEngine
    from openclaw.cops.scorer import score_findings
    from openclaw.cops.timeline import build_timeline
    from openclaw.bridge.scanner import ScanFinding
    from openclaw.disclosure.generator import DisclosureGenerator

    onsa = ONSAEngine()

    # Extract findings from chain
    records = onsa.get_records(chain_id)
    findings = []
    for rec in records:
        if rec.action == "finding.recorded":
            meta = rec.metadata or {}
            findings.append(ScanFinding(
                url=meta.get("url", ""),
                sec_grade=meta.get("sec_grade", "F"),
                techs=meta.get("techs", []),
                category=meta.get("category", ""),
            ))

    if not findings:
        console.print("[yellow]No findings in chain to draft from.[/]")
        return

    mat_score = score_findings(findings)
    timeline = build_timeline(onsa, chain_id)

    console.print("[cyan]Generating disclosure draft via LLM...[/]")
    generator = DisclosureGenerator()
    result = _run(generator.generate_draft(
        incident_id=chain_id[:12],
        findings=findings,
        materiality=mat_score,
        timeline=timeline,
    ))

    console.print(Panel.fit(
        f"[bold]Disclosure Draft[/] (via {result.llm_provider}/{result.llm_model})\n"
        f"Generated: {result.generated_at}\n",
        border_style="magenta",
    ))

    sections = [
        ("Nature & Scope", result.nature_and_scope),
        ("Data Impact", result.data_impact),
        ("Material Impact", result.material_impact),
        ("Remediation", result.remediation),
    ]

    for title, section in sections:
        conf = section.confidence
        conf_color = {"HIGH": "green", "MEDIUM": "yellow", "LOW": "red"}.get(conf.label, "white")
        console.print(f"\n[bold cyan]{title}[/] [dim]| Confidence: [{conf_color}]{conf.label}[/] ({conf.score})[/]")
        console.print(section.content or "[dim]No content generated[/]")

    if result.executive_summary:
        console.print(f"\n[bold magenta]Executive Summary[/]")
        console.print(result.executive_summary)


# ── serve ────────────────────────────────────────────────────────────

@cli.command()
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8000, type=int)
def serve(host, port):
    """Start the Openclaw web portal."""
    import uvicorn
    console.print(f"[green bold]Starting Openclaw Portal on {host}:{port}[/]")
    console.print(f"[dim]API docs: http://{host}:{port}/docs[/]")
    console.print(f"[dim]Health:   http://{host}:{port}/health[/]")
    uvicorn.run("openclaw.portal.app:app", host=host, port=port, reload=False)


def main():
    cli()


if __name__ == "__main__":
    main()
