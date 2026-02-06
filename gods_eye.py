#!/usr/bin/env python3
"""
Gods Eye – Parallel Web Reconnaissance Screenshot Tool
-------------------------------------------------------
Captures screenshots of multiple websites simultaneously and generates
interactive HTML reports with technology fingerprinting, security grading,
page categorization, redirect chain tracking, and multi-format export.
"""
from __future__ import annotations

__version__ = "1.0.0"

import argparse
import asyncio
import csv
import html
import ipaddress
import json
import logging
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

try:
    from PIL import Image, ImageChops
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Response
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TimeRemainingColumn, TextColumn

console = Console()
log = logging.getLogger("gods_eye")

BANNER = r"""[bold cyan]
   ██████   ██████  ██████  ███████     ███████ ██    ██ ███████
  ██       ██    ██ ██   ██ ██          ██       ██  ██  ██
  ██   ███ ██    ██ ██   ██ ███████     █████     ████   █████
  ██    ██ ██    ██ ██   ██      ██     ██         ██    ██
   ██████   ██████  ██████  ███████     ███████    ██    ███████
[/]
[dim]  v{version} | Parallel Web Reconnaissance Screenshot Tool
                                              By Dhananjay Pathak[/]
"""

# =================== HTML TEMPLATE ===================
HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Gods Eye Screenshot Report</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root {{ --accent:#00e6a8; --bg-dark:#0b0f14; --bg-light:#f9fafb; --text-dark:#e6eef6; --text-light:#111; }}
body {{ margin:0;font-family:Inter,system-ui,Arial,sans-serif;transition:background .3s,color .3s;scroll-behavior:smooth;}}
body.dark {{ background:var(--bg-dark);color:var(--text-dark);}}
body.light {{ background:var(--bg-light);color:var(--text-light);}}
.header {{position:sticky;top:0;background:rgba(0,0,0,0.12);backdrop-filter:blur(8px);display:flex;flex-wrap:wrap;align-items:center;justify-content:space-between;padding:14px 20px;border-bottom:1px solid rgba(255,255,255,0.04);z-index:100;}}
.title {{font-weight:700;font-size:18px;}}
.controls {{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}}
button, input {{font-size:14px;border:none;outline:none;border-radius:8px;padding:6px 10px;}}
button {{cursor:pointer;transition:transform .1s,opacity .1s;}}
button:hover {{opacity:0.9;transform:translateY(-1px);}}
input[type='text'] {{background:rgba(255,255,255,0.05);color:inherit;padding-left:10px;width:220px;}}
.container {{padding:20px;max-width:1400px;margin:auto;}}
.grid {{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:20px;margin-top:18px;}}
.card {{border-radius:14px;overflow:hidden;padding:14px;border:1px solid rgba(255,255,255,0.03);box-shadow:0 6px 20px rgba(0,0,0,0.6);background:rgba(255,255,255,0.02);transition:transform .18s,box-shadow .18s;}}
.card:hover {{transform:translateY(-6px);box-shadow:0 10px 28px rgba(0,0,0,0.7);}}
.thumb {{width:100%;height:180px;object-fit:cover;border-radius:10px;background:#222;cursor:pointer;}}
.meta {{margin-top:12px;}}
.url {{font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;display:block;margin-bottom:4px;text-decoration:none;}}
.dark .card[data-status="2"] .url {{color:#00e68a;}}
.dark .card[data-status="3"] .url {{color:#33aaff;}}
.dark .card[data-status="4"] .url {{color:#ffb86b;}}
.dark .card[data-status="5"] .url {{color:#ff6b6b;}}
.dark .card[data-status="E"] .url {{color:#ff4757;}}
.light .card[data-status="2"] .url {{color:#00b36b;}}
.light .card[data-status="3"] .url {{color:#0b76ff;}}
.light .card[data-status="4"] .url {{color:#ff8c00;}}
.light .card[data-status="5"] .url {{color:#e63946;}}
.light .card[data-status="E"] .url {{color:#c41e3a;}}
.small {{font-size:12px;opacity:0.85;}}
.card-title {{overflow:hidden;text-overflow:ellipsis;white-space:nowrap;margin-bottom:4px;opacity:0.7;}}
.line {{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:8px;}}
.badge {{padding:5px 8px;border-radius:999px;font-size:12px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.05);}}
.tech-badge {{background:rgba(0,230,168,0.1);border:1px solid rgba(0,230,168,0.2);color:#00e6a8;}}
.light .tech-badge {{background:rgba(0,150,100,0.1);border:1px solid rgba(0,150,100,0.25);color:#007a52;}}
.cat-badge {{background:rgba(255,184,107,0.12);border:1px solid rgba(255,184,107,0.25);color:#ffb86b;}}
.light .cat-badge {{background:rgba(200,120,0,0.1);border:1px solid rgba(200,120,0,0.25);color:#a06000;}}
.sec-grade {{font-weight:700;padding:4px 10px;border-radius:999px;font-size:11px;}}
.sec-A {{background:rgba(0,230,138,0.2);color:#00e68a;}} .sec-B {{background:rgba(0,162,255,0.2);color:#33aaff;}}
.sec-C {{background:rgba(255,184,107,0.2);color:#ffb86b;}} .sec-D {{background:rgba(255,107,107,0.2);color:#ff6b6b;}}
.sec-F {{background:rgba(255,71,87,0.25);color:#ff4757;}}
.redirect-chain {{font-size:11px;opacity:0.7;word-break:break-all;margin-top:4px;}}
.tls-info {{font-size:11px;opacity:0.6;margin-top:2px;}}
.footer {{margin:26px 0;text-align:center;font-size:13px;opacity:0.7;}}
.light .header{{background:rgba(255,255,255,0.9);}}
.light .card{{background:#fff;border:1px solid #eee;box-shadow:0 4px 12px rgba(0,0,0,0.08);}}
.light .badge{{background:#f6f7fb;color:#222;}}
#topBtn {{display:none;position:fixed;bottom:28px;right:28px;z-index:999;font-size:18px;border:none;outline:none;background:var(--accent);color:#041012;cursor:pointer;padding:12px;border-radius:50%;box-shadow:0 6px 18px rgba(0,0,0,0.5);transition:transform .18s,opacity .18s;}}
#topBtn:hover {{transform:translateY(-4px);opacity:0.92;}}
#lightbox {{display:none;position:fixed;z-index:1200;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);align-items:center;justify-content:center;padding:20px;}}
#lightbox img {{max-width:96%;max-height:92%;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,0.8);transform:scale(0.98);opacity:0;transition:transform .22s ease,opacity .22s ease;}}
#lightbox.show img {{transform:scale(1);opacity:1;}}
#lightbox span {{position:absolute;top:18px;right:28px;font-size:42px;color:white;cursor:pointer;}}
.status-btn[data-status^="2"] {{background:rgba(0,230,138,0.15);color:#00e68a;}}
.status-btn[data-status^="3"] {{background:rgba(0,162,255,0.15);color:#33aaff;}}
.status-btn[data-status^="4"] {{background:rgba(255,184,107,0.15);color:#ffb86b;}}
.status-btn[data-status^="5"] {{background:rgba(255,107,107,0.15);color:#ff6b6b;}}
.status-btn.active {{border:1px solid currentColor;}}
.cat-btn.active {{border:1px solid currentColor;}}
.diff-badge {{font-weight:700;padding:4px 10px;border-radius:999px;font-size:11px;cursor:pointer;}}
.diff-high {{background:rgba(255,71,87,0.25);color:#ff4757;}}
.diff-med {{background:rgba(255,184,107,0.25);color:#ffb86b;}}
.diff-low {{background:rgba(0,230,168,0.15);color:#00e68a;}}
.diff-new {{background:rgba(0,162,255,0.2);color:#33aaff;}}
.diff-summary {{text-align:center;padding:10px;font-size:14px;opacity:0.9;margin-bottom:6px;}}
.sev-critical {{background:rgba(200,0,0,0.3);border:2px solid rgba(255,0,0,0.5);}}
.content-changes {{font-size:11px;margin-top:4px;opacity:0.85;line-height:1.7;}}
.content-changes .ca {{color:var(--accent);}}
.diff-thumbs {{display:flex;gap:6px;margin-top:6px;}}
.diff-thumbs img {{height:48px;border-radius:6px;cursor:pointer;opacity:0.8;border:1px solid rgba(255,255,255,0.06);transition:opacity .15s,transform .15s;}}
.diff-thumbs img:hover {{opacity:1;transform:scale(1.05);}}
</style>
</head>
<body class="dark">
<div class="header">
  <div class="title">Gods Eye Screenshot Report</div>
  <div class="controls">
    <input id="search" type="text" placeholder="Search URL / title / tech..." onkeyup="filterCards()">
    <button onclick="setFilter('all')" class="status-btn">All</button>
    <button class="status-btn" data-status="2" onclick="setFilter('2')">2xx</button>
    <button class="status-btn" data-status="3" onclick="setFilter('3')">3xx</button>
    <button class="status-btn" data-status="4" onclick="setFilter('4')">4xx</button>
    <button class="status-btn" data-status="5" onclick="setFilter('5')">5xx</button>
    {diff_buttons}
    <button onclick="sortCards('status')" title="Sort by status">Sort</button>
    <button onclick="toggleMode()">Theme</button>
  </div>
</div>
<div class="container">
  {diff_summary}
  <div class="grid" id="grid">
    {cards}
  </div>
  <div class="footer">Generated: {generated_time} | Total: {total} | Success: {success} | Warn: {warn} | Fail: {fail} | Runtime: {runtime}</div>
</div>
<button onclick="topFunction()" id="topBtn" title="Back to top">&#8593;</button>
<div id="lightbox"><span onclick="closeLightbox()">&times;</span><img id="lightbox-img" src=""></div>
<script>
function toggleMode(){{const b=document.body;b.classList.toggle('light');b.classList.toggle('dark');localStorage.setItem('theme',b.classList.contains('light')?'light':'dark');}}
window.onload=function(){{const t=localStorage.getItem('theme');if(t){{document.body.className=t;}}}}
function setFilter(status){{
  document.querySelectorAll('.card').forEach(c=>{{
    if(status==='all') c.style.display='';
    else if(status==='changed'){{let d=parseFloat(c.dataset.diff||'0');c.style.display=d>0.5?'':'none';}}
    else if(status==='new'){{c.style.display=c.dataset.diff==='-1'?'':'none';}}
    else if(c.dataset.status.startsWith(status)) c.style.display='';
    else c.style.display='none';
  }});
  document.querySelectorAll('.status-btn').forEach(btn=>btn.classList.remove('active'));
  const active=document.querySelector('.status-btn[data-status="'+status+'"]');
  if(active) active.classList.add('active');
}}
function filterCards(){{let val=document.getElementById('search').value.toLowerCase();document.querySelectorAll('.card').forEach(c=>{{let text=c.innerText.toLowerCase();c.style.display=text.includes(val)?'':'none';}});}}
let sortAsc=true;
function sortCards(key){{
  const grid=document.getElementById('grid');
  const cards=[...grid.querySelectorAll('.card')];
  cards.sort((a,b)=>{{
    let av=a.dataset.status||'Z',bv=b.dataset.status||'Z';
    return sortAsc?av.localeCompare(bv):bv.localeCompare(av);
  }});
  sortAsc=!sortAsc;
  cards.forEach(c=>grid.appendChild(c));
}}
let topBtn=document.getElementById('topBtn');window.onscroll=function(){{scrollFunction();}};
function scrollFunction(){{if(document.body.scrollTop>300||document.documentElement.scrollTop>300){{topBtn.style.display='block';}}else{{topBtn.style.display='none';}}}}
function topFunction(){{window.scrollTo({{top:0,behavior:'smooth'}});}}
const imgs=document.querySelectorAll('.thumb');const lightbox=document.getElementById('lightbox');const lightImg=document.getElementById('lightbox-img');
imgs.forEach(i=>{{i.addEventListener('click',()=>{{lightbox.style.display='flex';lightbox.classList.add('show');lightImg.src=i.src;}});}});
function closeLightbox(){{lightbox.classList.remove('show');setTimeout(()=>{{lightbox.style.display='none';lightImg.src='';}},220);}}
window.addEventListener('click',e=>{{if(e.target==lightbox)closeLightbox();}});
window.addEventListener('keydown',e=>{{if(e.key==='Escape')closeLightbox();}});
function openDiff(src){{lightbox.style.display='flex';lightbox.classList.add('show');lightImg.src=src;}}
</script>
</body>
</html>
"""

CARD_TEMPLATE = """
<div class="card" data-status="{status_code}" data-cat="{category}" data-diff="{diff_pct}">
  <img class="thumb" src="{screenshot_relpath}" alt="{display_url}">
  <div class="meta">
    <a class="url" href="{url}" target="_blank">{display_url}</a>
    <div class="card-title small">{page_title}</div>
    <div class="small">Status: {status_text} | Load: {load_ms} ms | <span class="sec-grade sec-{sec_grade}">{sec_grade}</span></div>
    <div class="line small">
      <div class="badge">{notes}</div>
      <div class="badge">{server}</div>
      {cat_badge}
      {tech_badges}
    </div>
    {diff_html}
    {redirect_html}
    {tls_html}
  </div>
</div>
"""

# =================== Technology Fingerprinting ===================
TECH_HEADER_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("server", re.compile(r"nginx", re.I), "Nginx"),
    ("server", re.compile(r"apache", re.I), "Apache"),
    ("server", re.compile(r"cloudflare", re.I), "Cloudflare"),
    ("server", re.compile(r"microsoft-iis", re.I), "IIS"),
    ("server", re.compile(r"LiteSpeed", re.I), "LiteSpeed"),
    ("server", re.compile(r"openresty", re.I), "OpenResty"),
    ("server", re.compile(r"caddy", re.I), "Caddy"),
    ("server", re.compile(r"gunicorn", re.I), "Gunicorn"),
    ("server", re.compile(r"envoy", re.I), "Envoy"),
    ("x-powered-by", re.compile(r"php", re.I), "PHP"),
    ("x-powered-by", re.compile(r"asp\.net", re.I), "ASP.NET"),
    ("x-powered-by", re.compile(r"express", re.I), "Express"),
    ("x-powered-by", re.compile(r"next\.?js", re.I), "Next.js"),
    ("x-powered-by", re.compile(r"nuxt", re.I), "Nuxt.js"),
    ("via", re.compile(r"varnish", re.I), "Varnish"),
    ("via", re.compile(r"cloudfront", re.I), "CloudFront"),
    ("x-generator", re.compile(r"drupal", re.I), "Drupal"),
    ("x-generator", re.compile(r"wordpress", re.I), "WordPress"),
]

TECH_HTML_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"wp-content|wp-includes|/wp-json", re.I), "WordPress"),
    (re.compile(r"Joomla!", re.I), "Joomla"),
    (re.compile(r"sites/default/files|drupal\.js", re.I), "Drupal"),
    (re.compile(r"cdn\.shopify\.com|Shopify\.theme", re.I), "Shopify"),
    (re.compile(r"__next|_next/static", re.I), "Next.js"),
    (re.compile(r"__nuxt|_nuxt/", re.I), "Nuxt.js"),
    (re.compile(r"react(?:\.production|dom)", re.I), "React"),
    (re.compile(r"vue\.?js|v-cloak|__vue", re.I), "Vue.js"),
    (re.compile(r"ng-version|angular", re.I), "Angular"),
    (re.compile(r"laravel|csrf.*laravel", re.I), "Laravel"),
    (re.compile(r"csrfmiddlewaretoken.*django|__django", re.I), "Django"),
    (re.compile(r"csrf-token.*authenticity_token|rails", re.I), "Rails"),
    (re.compile(r"jquery", re.I), "jQuery"),
    (re.compile(r"bootstrap(?:\.min)?\.(?:css|js)", re.I), "Bootstrap"),
    (re.compile(r"tailwindcss|tailwind", re.I), "Tailwind"),
    (re.compile(r"google-analytics|gtag|ga\.js", re.I), "Google Analytics"),
    (re.compile(r"googleapis\.com/ajax|fonts\.googleapis", re.I), "Google APIs"),
    (re.compile(r"cloudflare", re.I), "Cloudflare"),
    (re.compile(r"gatsby", re.I), "Gatsby"),
    (re.compile(r"svelte", re.I), "Svelte"),
]

def fingerprint_tech(headers: dict[str, str], page_html: str) -> list[str]:
    """Detect technologies from response headers and page HTML."""
    techs: list[str] = []
    seen: set[str] = set()
    for hdr_name, pattern, label in TECH_HEADER_PATTERNS:
        val = headers.get(hdr_name, "")
        if val and pattern.search(val) and label not in seen:
            techs.append(label)
            seen.add(label)
    snippet = page_html[:80000]
    for pattern, label in TECH_HTML_PATTERNS:
        if label not in seen and pattern.search(snippet):
            techs.append(label)
            seen.add(label)
    return techs

# =================== Security Header Grading ===================
SECURITY_HEADERS: list[str] = [
    "strict-transport-security",
    "content-security-policy",
    "x-frame-options",
    "x-content-type-options",
    "referrer-policy",
    "permissions-policy",
]

def grade_security_headers(headers: dict[str, str]) -> tuple[str, list[str]]:
    """Grade security headers A-F. Returns (grade, list_of_present_headers)."""
    present = [h for h in SECURITY_HEADERS if h in headers]
    count = len(present)
    if count >= 5: grade = "A"
    elif count >= 4: grade = "B"
    elif count >= 3: grade = "C"
    elif count >= 1: grade = "D"
    else: grade = "F"
    return grade, present

# =================== Page Categorization ===================
PAGE_CATEGORIES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"<input[^>]*type=['\"]password['\"]", re.I), "Login Page"),
    (re.compile(r"sign.?in|log.?in|auth", re.I), "Login Page"),
    (re.compile(r"admin|dashboard|cpanel|wp-admin|phpmyadmin", re.I), "Admin Panel"),
    (re.compile(r"swagger|api.?doc|redoc|openapi", re.I), "API Docs"),
    (re.compile(r"it works!|default.*page|welcome to nginx|apache.*default|iis.*windows", re.I), "Default Page"),
    (re.compile(r"403 forbidden|401 unauthorized|access denied", re.I), "Access Denied"),
    (re.compile(r"404 not found|page not found", re.I), "Not Found"),
    (re.compile(r"parked.*domain|buy this domain|domain.*sale|sedoparking|godaddy", re.I), "Parked Domain"),
    (re.compile(r"under construction|coming soon|maintenance", re.I), "Under Construction"),
    (re.compile(r"blocked|firewall|waf|captcha|challenge|cf-browser-verification|attention required", re.I), "WAF/Firewall"),
]

def categorize_page(title: str, page_html: str) -> str:
    """Categorize a page based on title and HTML content."""
    combined = (title or "") + " " + page_html[:30000]
    for pattern, category in PAGE_CATEGORIES:
        if pattern.search(combined):
            return category
    return ""

# =================== Screenshot Diff ===================
def compute_screenshot_diff(
    old_path: str, new_path: str, diff_dir: str, index: int, threshold: int = 10,
) -> tuple[float, str, str]:
    """Block-based screenshot diff with heatmap + side-by-side comparison.

    Returns (diff_pct, heatmap_relpath, sidebyside_relpath).
    Uses 8x8 block averaging via fast PIL downscale for noise-resistant comparison.
    Generates a green/yellow/red heatmap and a BEFORE|DIFF|AFTER composite.
    """
    if not HAS_PIL:
        log.warning("Pillow not installed – install with: pip install Pillow")
        return -1.0, "", ""
    try:
        from PIL import ImageDraw

        img_old = Image.open(old_path).convert("RGB")
        img_new = Image.open(new_path).convert("RGB")
        if img_old.size != img_new.size:
            img_new = img_new.resize(img_old.size, Image.LANCZOS)

        w, h = img_old.size
        diff = ImageChops.difference(img_old, img_new)
        gray = diff.convert("L")

        # Block-based comparison (8x8) via fast downscale – ignores anti-aliasing noise
        block = 8
        small = gray.resize((max(w // block, 1), max(h // block, 1)), Image.BOX)
        small_px = list(small.getdata())
        changed_blocks = sum(1 for p in small_px if p > threshold)
        total_blocks = len(small_px)
        diff_pct = round((changed_blocks / total_blocks) * 100, 1) if total_blocks else 0.0

        heatmap_rel = ""
        compare_rel = ""

        if diff_pct > 0.5:
            # ---- Heatmap: green (minor) → yellow (moderate) → red (major) ----
            low_mask = gray.point(lambda x: 255 if threshold < x < 60 else 0).convert("L")
            med_mask = gray.point(lambda x: 255 if 60 <= x < 140 else 0).convert("L")
            high_mask = gray.point(lambda x: 255 if x >= 140 else 0).convert("L")

            base = img_new.point(lambda x: int(x * 0.35))
            green = Image.new("RGB", (w, h), (0, 220, 100))
            yellow = Image.new("RGB", (w, h), (255, 200, 0))
            red = Image.new("RGB", (w, h), (255, 40, 40))

            heatmap = Image.composite(Image.blend(img_new, green, 0.45), base, low_mask)
            heatmap = Image.composite(Image.blend(img_new, yellow, 0.50), heatmap, med_mask)
            heatmap = Image.composite(Image.blend(img_new, red, 0.55), heatmap, high_mask)

            hm_name = f"diff_{index:03d}_heatmap.png"
            heatmap.save(os.path.join(diff_dir, hm_name))
            heatmap_rel = os.path.join("diffs", hm_name)

            # ---- Side-by-side: BEFORE | HEATMAP | AFTER ----
            gap = 4
            canvas_w = w * 3 + gap * 2
            canvas_h = h + 32
            canvas = Image.new("RGB", (canvas_w, canvas_h), (15, 18, 25))
            draw = ImageDraw.Draw(canvas)

            draw.text((w // 2 - 25, 6), "BEFORE", fill=(180, 180, 180))
            draw.text((w + gap + w // 2 - 15, 6), "DIFF", fill=(255, 100, 100))
            draw.text((w * 2 + gap * 2 + w // 2 - 20, 6), "AFTER", fill=(100, 230, 160))

            canvas.paste(img_old, (0, 28))
            canvas.paste(heatmap, (w + gap, 28))
            canvas.paste(img_new, (w * 2 + gap * 2, 28))

            cmp_name = f"diff_{index:03d}_compare.png"
            canvas.save(os.path.join(diff_dir, cmp_name), quality=85)
            compare_rel = os.path.join("diffs", cmp_name)

        return diff_pct, heatmap_rel, compare_rel
    except Exception as e:
        log.debug("Diff computation failed for %s: %s", old_path, e)
        return -1.0, "", ""


def compute_content_diff(old_result: dict, new_result: dict) -> list[dict[str, str]]:
    """Compare non-visual properties between two scan results."""
    changes: list[dict[str, str]] = []
    old_st = str(old_result.get("status", ""))
    new_st = str(new_result.get("status", ""))
    if old_st != new_st:
        changes.append({"field": "Status", "old": old_st, "new": new_st, "severity": "high"})
    old_title = (old_result.get("title") or "")[:60]
    new_title = (new_result.get("title") or "")[:60]
    if old_title != new_title:
        changes.append({"field": "Title", "old": old_title or "(empty)", "new": new_title or "(empty)", "severity": "medium"})
    old_cat = old_result.get("category", "") or ""
    new_cat = new_result.get("category", "") or ""
    if old_cat != new_cat:
        sev = "high" if new_cat in ("Login Page", "Admin Panel", "WAF/Firewall") else "medium"
        changes.append({"field": "Category", "old": old_cat or "—", "new": new_cat or "—", "severity": sev})
    old_grade = old_result.get("sec_grade", "")
    new_grade = new_result.get("sec_grade", "")
    if old_grade != new_grade:
        changes.append({"field": "Grade", "old": old_grade or "—", "new": new_grade or "—", "severity": "medium"})
    old_techs = set(old_result.get("techs") or [])
    new_techs = set(new_result.get("techs") or [])
    added = new_techs - old_techs
    removed = old_techs - new_techs
    if added or removed:
        parts = []
        if added:
            parts.append("+" + ", ".join(added))
        if removed:
            parts.append("-" + ", ".join(removed))
        changes.append({"field": "Tech", "old": ", ".join(sorted(old_techs)) or "—", "new": " ".join(parts), "severity": "low"})
    return changes


def calculate_diff_severity(visual_pct: float, content_changes: list[dict[str, str]]) -> str:
    """Classify overall change severity: critical / high / medium / low / none."""
    has_high = any(c.get("severity") == "high" for c in content_changes)
    if visual_pct > 50 and has_high:
        return "critical"
    if visual_pct > 30 or has_high:
        return "high"
    if visual_pct > 5 or content_changes:
        return "medium"
    if visual_pct > 0.5:
        return "low"
    return "none"


# =================== Input Parsing ===================
def sanitize_filename(s: str) -> str:
    keep = "-_.() abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    return "".join(ch if ch in keep else "_" for ch in s)[:200]

def _normalize_urls(lines: list[str]) -> list[str]:
    """Filter comments/blanks and add protocol if missing."""
    urls = [ln.strip() for ln in lines if ln.strip() and not ln.strip().startswith("#")]
    return [u if u.startswith("http") else "http://" + u for u in urls]

def read_urls_stdin() -> list[str]:
    return _normalize_urls(sys.stdin.read().splitlines())

def read_urls(path: str) -> list[str]:
    encodings = ["utf-8-sig", "utf-8", "utf-16", "cp1252", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return _normalize_urls(f.readlines())
        except Exception:
            continue
    raise RuntimeError("Cannot read URL file – unsupported encoding.")

def read_nmap_xml(path: str) -> list[str]:
    """Parse Nmap XML output and extract HTTP/HTTPS service URLs."""
    urls: list[str] = []
    tree = ET.parse(path)
    for host in tree.findall(".//host"):
        addr_el = host.find("address")
        if addr_el is None:
            continue
        addr = addr_el.get("addr", "")
        for port_el in host.findall(".//port"):
            state_el = port_el.find("state")
            if state_el is None or state_el.get("state") != "open":
                continue
            portid = port_el.get("portid", "")
            service_el = port_el.find("service")
            svc_name = service_el.get("name", "") if service_el is not None else ""
            tunnel = service_el.get("tunnel", "") if service_el is not None else ""
            if not any(k in svc_name for k in ("http", "https", "ssl")):
                continue
            scheme = "https" if ("ssl" in svc_name or "https" in svc_name or tunnel == "ssl") else "http"
            urls.append(f"{scheme}://{addr}:{portid}")
    return urls

def expand_cidr(cidr: str, ports: list[int]) -> list[str]:
    """Expand a CIDR range + port list into URLs."""
    network = ipaddress.ip_network(cidr, strict=False)
    urls: list[str] = []
    for ip in network.hosts():
        for port in ports:
            scheme = "https" if port == 443 else "http"
            urls.append(f"{scheme}://{ip}:{port}")
    return urls

# =================== Report ===================
def make_report(cards_html: str, out_path: str, total: int, success: int, warn: int, fail: int, runtime: str, diff_buttons: str = "", diff_summary: str = "") -> None:
    html_content = HTML_TEMPLATE.format(
        generated_time=time.strftime("%Y-%m-%d %H:%M:%S"),
        cards=cards_html, total=total, success=success, warn=warn, fail=fail, runtime=runtime,
        diff_buttons=diff_buttons, diff_summary=diff_summary,
    )
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html_content)

def classify_status_color(code: int | str) -> str:
    try:
        code = int(code)
        if 200 <= code < 300: return "[green]" + str(code) + "[/]"
        elif 300 <= code < 400: return "[cyan]" + str(code) + "[/]"
        elif 400 <= code < 500: return "[yellow]" + str(code) + "[/]"
        else: return "[red]" + str(code) + "[/]"
    except Exception:
        return "[red]ERR[/]"

# =================== Load Wait Strategy ===================
WAIT_MODES: dict[str, dict[str, int]] = {
    "fast":     {"load": 500,  "idle": 1000},
    "balanced": {"load": 2000, "idle": 3000},
    "thorough": {"load": 4000, "idle": 6000},
}

VIEWPORT_PRESETS: dict[str, dict[str, int]] = {
    "desktop":  {"width": 1920, "height": 1080},
    "laptop":   {"width": 1366, "height": 768},
    "tablet":   {"width": 768,  "height": 1024},
    "mobile":   {"width": 375,  "height": 812},
}

async def best_effort_wait(page: Page, mode: str) -> None:
    load_ms = WAIT_MODES.get(mode, WAIT_MODES["balanced"])["load"]
    idle_ms = WAIT_MODES.get(mode, WAIT_MODES["balanced"])["idle"]
    try: await page.wait_for_load_state("load", timeout=load_ms)
    except Exception: pass
    try: await page.wait_for_load_state("networkidle", timeout=idle_ms)
    except Exception: pass
    try:
        ready = await page.evaluate("document.readyState")
        if ready != "complete": await asyncio.sleep(0.5)
    except Exception: pass

# =================== Capture Logic ===================
HEADER_KEYS_CAPTURE: list[str] = [
    "server", "x-powered-by", "content-type", "via", "x-generator",
    "strict-transport-security", "content-security-policy",
    "x-frame-options", "x-content-type-options", "referrer-policy", "permissions-policy",
]

async def capture_page(
    browser: Browser, url: str, index: int, out_dir: str, timeout: int,
    viewport: dict[str, int], full_page: bool, retries: int, wait_mode: str,
    proxy: str | None = None, extra_headers: dict[str, str] | None = None,
    cookies: list[dict[str, str]] | None = None, img_format: str = "png",
    img_quality: int | None = None, user_agent: str | None = None,
    js_inject: str | None = None,
) -> dict[str, object]:
    short = sanitize_filename(urlparse(url).netloc or f"host{index}")
    ext = "jpg" if img_format == "jpeg" else img_format
    screenshot_path = os.path.join(out_dir, f"{index:03d}_{short}.{ext}")
    rel_path = os.path.join("screenshots", os.path.basename(screenshot_path))
    status: int | str = 0
    screenshot_taken = False
    load_time = 0
    page_title = ""
    headers: dict[str, str] = {}
    techs: list[str] = []
    category = ""
    sec_grade = "F"
    sec_headers: list[str] = []
    redirect_chain: list[str] = []
    tls_info: dict[str, str] = {}
    console_logs: list[str] = []
    captured_cookies: list[dict[str, object]] = []
    final_url = url

    ctx_opts: dict[str, object] = {"ignore_https_errors": True, "viewport": viewport}
    if proxy:
        ctx_opts["proxy"] = {"server": proxy}
    if extra_headers:
        ctx_opts["extra_http_headers"] = extra_headers
    if user_agent:
        ctx_opts["user_agent"] = user_agent

    for attempt in range(retries + 1):
        context: BrowserContext | None = None
        try:
            context = await browser.new_context(**ctx_opts)
            if cookies:
                await context.add_cookies(cookies)
            pg: Page = await context.new_page()

            # Console log capture
            console_logs = []
            pg.on("console", lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))

            # Redirect tracking
            redirect_chain = []
            def _track_redirect(resp: Response) -> None:
                redirect_chain.append(resp.url)
            pg.on("response", _track_redirect)

            start_time = time.time()
            log.debug("[%03d] Navigating to %s (attempt %d)", index, url, attempt + 1)
            resp = await pg.goto(url, timeout=timeout, wait_until="domcontentloaded")
            await best_effort_wait(pg, wait_mode)

            # Custom JS injection before screenshot
            if js_inject:
                try:
                    await pg.evaluate(js_inject)
                    await asyncio.sleep(0.3)
                except Exception as je:
                    log.debug("[%03d] JS inject error: %s", index, je)

            # Screenshot
            shot_opts: dict[str, object] = {"path": screenshot_path, "full_page": full_page, "type": img_format}
            if img_quality is not None and img_format == "jpeg":
                shot_opts["quality"] = img_quality
            await pg.screenshot(**shot_opts)

            load_time = int((time.time() - start_time) * 1000)
            status = resp.status if resp else 0
            screenshot_taken = True
            final_url = pg.url

            # Page title
            try: page_title = await pg.title()
            except Exception: page_title = ""

            # Response headers (expanded set for security grading)
            if resp:
                all_h = await resp.all_headers()
                headers = {k: all_h[k] for k in HEADER_KEYS_CAPTURE if k in all_h}

            # TLS certificate info
            if resp and url.startswith("https"):
                try:
                    sec = await resp.security_details()
                    if sec:
                        tls_info = {
                            "issuer": sec.get("issuer", ""),
                            "subject": sec.get("subjectName", ""),
                            "valid_from": sec.get("validFrom", ""),
                            "valid_to": sec.get("validTo", ""),
                            "protocol": sec.get("protocol", ""),
                        }
                except Exception:
                    pass

            # Security header grading
            sec_grade, sec_headers = grade_security_headers(headers)

            # Tech fingerprinting + page categorization
            page_html = ""
            try:
                page_html = await pg.content()
                techs = fingerprint_tech(headers, page_html)
                category = categorize_page(page_title, page_html)
            except Exception:
                pass

            # Capture cookies set by the target
            try:
                captured_cookies = await context.cookies()
            except Exception:
                pass

            log.debug("[%03d] OK %s -> %s (%dms) grade=%s techs=%s cat=%s", index, url, status, load_time, sec_grade, techs, category)
            break
        except Exception as e:
            screenshot_taken = False
            status = "ERR"
            log.warning("[%03d] Attempt %d failed for %s: %s", index, attempt + 1, url, e)
            if attempt == retries: break
            await asyncio.sleep(0.3)
        finally:
            if context:
                try: await context.close()
                except Exception: pass

    return {
        "index": index, "url": url, "final_url": final_url, "status": status,
        "screenshot_taken": screenshot_taken, "screenshot_path": rel_path,
        "load_ms": load_time, "title": page_title, "headers": headers,
        "techs": techs, "category": category,
        "sec_grade": sec_grade, "sec_headers": sec_headers,
        "redirect_chain": redirect_chain, "tls": tls_info,
        "console_logs": console_logs[:50],
        "cookies": [{"name": c.get("name",""), "domain": c.get("domain",""), "secure": c.get("secure",False), "httpOnly": c.get("httpOnly",False)} for c in captured_cookies[:30]],
    }

# =================== Parallel Runner ===================
async def run_parallel(
    urls: list[str], out_dir: str, threads: int, timeout: int,
    viewport: dict[str, int], full_page: bool, retries: int, wait_mode: str,
    proxy: str | None = None, extra_headers: dict[str, str] | None = None,
    cookies: list[dict[str, str]] | None = None, resume: bool = False,
    img_format: str = "png", img_quality: int | None = None,
    user_agent: str | None = None, js_inject: str | None = None,
    rate_limit: float = 0,
) -> tuple[int, int, int, int, list[dict[str, object]]]:
    screenshots_dir = os.path.join(out_dir, "screenshots")
    os.makedirs(screenshots_dir, exist_ok=True)

    previous_results: list[dict[str, object]] = []
    done_urls: set[str] = set()
    if resume:
        prev_json = os.path.join(out_dir, "results.json")
        if os.path.isfile(prev_json):
            try:
                with open(prev_json, "r", encoding="utf-8") as f:
                    prev_data = json.load(f)
                for r in prev_data:
                    if r.get("status") != "ERR":
                        done_urls.add(r["url"])
                        previous_results.append(r)
                log.info("Resume: loaded %d completed results", len(done_urls))
            except Exception as e:
                log.warning("Resume: could not load previous results: %s", e)
        if done_urls:
            console.print(f"[cyan]Resume mode:[/] skipping {len(done_urls)} already-captured URLs")

    pending_urls = [(i, u) for i, u in enumerate(urls) if u not in done_urls]
    results: list[dict[str, object]] = []

    if pending_urls:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
            sem = asyncio.Semaphore(threads)

            with Progress(TextColumn("{task.description}"), BarColumn(), TimeRemainingColumn(), console=console) as progress:
                task = progress.add_task("[green]Scanning...", total=len(pending_urls))

                async def sem_task(i: int, url: str) -> dict[str, object]:
                    async with sem:
                        if rate_limit > 0:
                            await asyncio.sleep(rate_limit)
                        result = await capture_page(
                            browser, url, i + 1, screenshots_dir, timeout, viewport,
                            full_page, retries, wait_mode, proxy, extra_headers, cookies,
                            img_format, img_quality, user_agent, js_inject,
                        )
                        progress.advance(task)
                        return result

                results = list(await asyncio.gather(*(sem_task(i, u) for i, u in pending_urls)))
            await browser.close()

    if previous_results:
        results = previous_results + results
    results.sort(key=lambda r: r["index"])

    success = warn = fail = 0
    for r in results:
        st = r["status"]
        if st == "ERR":
            fail += 1; r["notes"] = "Failed to load"
        elif isinstance(st, int) and 200 <= st < 400:
            success += 1; r["notes"] = "Success"
        elif isinstance(st, int) and 400 <= st < 500:
            warn += 1; r["notes"] = "Client Error"
        else:
            fail += 1; r["notes"] = "Server Error"

    # CLI table
    table = Table(show_header=True, header_style="bold cyan", title="Gods Eye Screenshot Results")
    table.add_column("#", justify="right", width=4)
    table.add_column("URL", justify="left", width=40)
    table.add_column("Title", justify="left", width=22)
    table.add_column("Status", justify="center", width=8)
    table.add_column("Grade", justify="center", width=6)
    table.add_column("Tech", justify="left", width=16)
    table.add_column("Cat", justify="left", width=14)
    table.add_column("OK", justify="center", width=4)
    for r in results:
        emoji = "Y" if r.get("screenshot_taken", r.get("status") != "ERR") else "N"
        table.add_row(
            str(r["index"]), str(r["url"])[:40], (str(r.get("title", "")) or "")[:22],
            classify_status_color(r["status"]), str(r.get("sec_grade", "")),
            ", ".join(r.get("techs", []) or [])[:16], str(r.get("category", ""))[:14], emoji,
        )

    console.print()
    console.print(Panel.fit(table, border_style="bright_blue"))
    console.print(f"\n Done: {len(urls)} URLs | [green]{success} success[/] | [yellow]{warn} warn[/] | [red]{fail} fail[/]\n")
    return len(urls), success, warn, fail, results

# =================== Export ===================
def export_json(results: list[dict[str, object]], path: str) -> None:
    data = []
    for r in results:
        data.append({
            "index": r["index"], "url": r["url"], "final_url": r.get("final_url", ""),
            "status": r["status"], "title": r.get("title", ""), "load_ms": r.get("load_ms", 0),
            "headers": r.get("headers", {}), "techs": r.get("techs", []),
            "category": r.get("category", ""),
            "sec_grade": r.get("sec_grade", ""), "sec_headers": r.get("sec_headers", []),
            "redirect_chain": r.get("redirect_chain", []),
            "tls": r.get("tls", {}), "cookies": r.get("cookies", []),
            "console_logs": r.get("console_logs", []),
            "diff_pct": r.get("diff_pct", 0),
            "diff_heatmap": r.get("diff_heatmap", ""),
            "diff_compare": r.get("diff_compare", ""),
            "diff_severity": r.get("diff_severity", ""),
            "content_changes": r.get("content_changes", []),
            "screenshot": r.get("screenshot_path", r.get("screenshot", "")),
            "notes": r.get("notes", ""),
        })
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def export_csv(results: list[dict[str, object]], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["index", "url", "final_url", "status", "title", "load_ms", "server", "techs", "category", "sec_grade", "tls_issuer", "screenshot", "notes"])
        for r in results:
            hdrs = r.get("headers", {}) or {}
            tls = r.get("tls", {}) or {}
            writer.writerow([
                r["index"], r["url"], r.get("final_url", ""), r["status"], r.get("title", ""),
                r.get("load_ms", 0), hdrs.get("server", ""),
                " | ".join(r.get("techs", []) or []), r.get("category", ""),
                r.get("sec_grade", ""), tls.get("issuer", ""),
                r.get("screenshot_path", r.get("screenshot", "")), r.get("notes", ""),
            ])

# =================== CLI Helpers ===================
def setup_logging(verbose: bool, out_dir: str) -> None:
    log.setLevel(logging.DEBUG)
    os.makedirs(out_dir, exist_ok=True)
    fh = logging.FileHandler(os.path.join(out_dir, "scan.log"), encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S"))
    log.addHandler(fh)
    if verbose:
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        log.addHandler(ch)

def parse_cookies_cli(cookie_strings: list[str]) -> list[dict[str, str]]:
    cookies: list[dict[str, str]] = []
    for cs in cookie_strings:
        parts = [p.strip() for p in cs.split(";")]
        if not parts or "=" not in parts[0]:
            continue
        name, value = parts[0].split("=", 1)
        cookie: dict[str, str] = {"name": name.strip(), "value": value.strip(), "url": "http://localhost"}
        for part in parts[1:]:
            if "=" in part:
                k, v = part.split("=", 1)
                k = k.strip().lower()
                if k == "domain":
                    cookie["domain"] = v.strip()
                    cookie.pop("url", None)
                elif k == "path":
                    cookie["path"] = v.strip()
        cookies.append(cookie)
    return cookies

def parse_headers_cli(header_strings: list[str]) -> dict[str, str]:
    headers: dict[str, str] = {}
    for hs in header_strings:
        if ":" in hs:
            k, v = hs.split(":", 1)
            headers[k.strip()] = v.strip()
    return headers

# =================== Main ===================
def main() -> None:
    console.print(BANNER.format(version=__version__))

    parser = argparse.ArgumentParser(
        usage=argparse.SUPPRESS,
        description="Gods Eye - Parallel Web Reconnaissance Screenshot Tool",
        epilog="Pipe URLs via stdin: cat urls.txt | python gods_eye.py -o out_dir",
    )
    # Input
    parser.add_argument("-f", "--file", default=None, help="File containing URLs (omit to read from stdin)")
    parser.add_argument("--nmap", default=None, metavar="XML", help="Parse Nmap XML output for HTTP targets")
    parser.add_argument("--cidr", default=None, help="Scan CIDR range (e.g. 192.168.1.0/24)")
    parser.add_argument("--ports", default="80,443,8080,8443", help="Ports for CIDR scan (default: 80,443,8080,8443)")
    parser.add_argument("--exclude", action="append", default=[], metavar="PATTERN", help="Exclude URLs matching regex pattern. Repeatable.")
    parser.add_argument("--diff", default=None, metavar="PREV_DIR", help="Diff against previous scan directory (needs results.json in that dir)")
    parser.add_argument("--diff-threshold", type=int, default=10, metavar="0-255", help="Pixel change threshold for diff sensitivity (default: 10, lower=more sensitive)")
    # Output
    parser.add_argument("-o", "--out", default="gods_eye_report", help="Output directory")
    parser.add_argument("--json", action="store_true", help="Export results as JSON")
    parser.add_argument("--csv", action="store_true", help="Export results as CSV")
    parser.add_argument("--format", choices=["png", "jpeg"], default="png", dest="img_format", help="Screenshot format (default: png)")
    parser.add_argument("--quality", type=int, default=None, metavar="1-100", help="JPEG quality 1-100")
    # Scan behavior
    parser.add_argument("--threads", type=int, default=5, help="Concurrent threads")
    parser.add_argument("--timeout", type=int, default=8000, help="Page timeout in ms")
    parser.add_argument("--viewport", default="1920x1080", help="Viewport WxH or preset: desktop, laptop, tablet, mobile")
    parser.add_argument("--full-page", action="store_true", help="Capture full page screenshot")
    parser.add_argument("--retries", type=int, default=2, help="Retries on failure")
    parser.add_argument("--wait-mode", choices=["fast", "balanced", "thorough"], default="balanced", help="Page wait behavior")
    parser.add_argument("--resume", action="store_true", help="Skip already-captured URLs from previous run")
    parser.add_argument("--rate-limit", type=float, default=0, metavar="SEC", help="Delay in seconds between each request (e.g. 0.5). Prevents IP bans on large scans.")
    # Auth & stealth
    parser.add_argument("--proxy", default=None, help="Proxy server (e.g. http://127.0.0.1:8080)")
    parser.add_argument("-H", "--header", action="append", default=[], metavar="HEADER", help="Custom header. Repeatable.")
    parser.add_argument("-c", "--cookie", action="append", default=[], metavar="COOKIE", help="Cookie string. Repeatable.")
    parser.add_argument("--user-agent", default=None, metavar="UA", help="Custom User-Agent string")
    parser.add_argument("--js-inject", default=None, metavar="JS", help="JavaScript to run before screenshot (e.g. dismiss cookie banners)")
    # Misc
    parser.add_argument("--version", action="version", version=f"Gods Eye v{__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging to console")
    args = parser.parse_args()

    setup_logging(args.verbose, args.out)

    # Collect URLs from all input sources
    urls: list[str] = []
    if args.nmap:
        urls.extend(read_nmap_xml(args.nmap))
        log.info("Nmap XML: parsed %d URLs", len(urls))
    if args.cidr:
        ports = [int(p.strip()) for p in args.ports.split(",")]
        cidr_urls = expand_cidr(args.cidr, ports)
        urls.extend(cidr_urls)
        log.info("CIDR %s: expanded to %d URLs", args.cidr, len(cidr_urls))
    if args.file:
        urls.extend(read_urls(args.file))
    elif not args.nmap and not args.cidr:
        if not sys.stdin.isatty():
            urls.extend(read_urls_stdin())
        else:
            console.print("[red]No input: use -f, --nmap, --cidr, or pipe URLs via stdin.[/]")
            sys.exit(1)

    # Apply --exclude filters
    if args.exclude:
        exclude_patterns = [re.compile(p) for p in args.exclude]
        before = len(urls)
        urls = [u for u in urls if not any(ep.search(u) for ep in exclude_patterns)]
        excluded = before - len(urls)
        if excluded:
            console.print(f"[cyan]Excluded:[/] {excluded} URLs matched --exclude patterns")

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            deduped.append(u)
    urls = deduped

    if not urls:
        console.print("[red]No URLs found.[/]")
        sys.exit(1)

    log.info("Total URLs to scan: %d", len(urls))

    # Parse viewport (preset or WxH)
    if args.viewport.lower() in VIEWPORT_PRESETS:
        vp = VIEWPORT_PRESETS[args.viewport.lower()]
    else:
        try:
            w, h = (int(x) for x in args.viewport.lower().split("x"))
            vp = {"width": w, "height": h}
        except Exception:
            console.print("[red]Invalid viewport. Use WIDTHxHEIGHT or preset: desktop, laptop, tablet, mobile[/]")
            sys.exit(1)

    if args.quality is not None and (args.quality < 1 or args.quality > 100):
        console.print("[red]--quality must be between 1 and 100[/]")
        sys.exit(1)

    extra_headers = parse_headers_cli(args.header) if args.header else None
    cookies_cli = parse_cookies_cli(args.cookie) if args.cookie else None

    proxy_info = f" | Proxy: {args.proxy}" if args.proxy else ""
    rate_info = f" | Rate: {args.rate_limit}s/req" if args.rate_limit > 0 else ""
    console.print(Panel.fit(
        f"[bold cyan]Gods Eye[/]\n"
        f"Targets: {len(urls)} | Threads: {args.threads} | Mode: {args.wait_mode} | Viewport: {args.viewport}{proxy_info}{rate_info}"
    ))

    os.makedirs(args.out, exist_ok=True)
    start = time.time()
    total, success, warn, fail, results = asyncio.run(
        run_parallel(urls, args.out, args.threads, args.timeout, vp,
                     args.full_page, args.retries, args.wait_mode, args.proxy,
                     extra_headers, cookies_cli, args.resume, args.img_format, args.quality,
                     args.user_agent, args.js_inject, args.rate_limit)
    )
    runtime = f"{int(time.time() - start)}s"

    # ---- Diff computation ----
    diff_buttons = ""
    diff_summary = ""
    if args.diff:
        prev_json = os.path.join(args.diff, "results.json")
        if not os.path.isfile(prev_json):
            console.print(f"[red]--diff: {prev_json} not found. Previous scan must use --json.[/]")
        else:
            with open(prev_json, "r", encoding="utf-8") as f:
                prev_data = json.load(f)
            prev_by_url = {r["url"]: r for r in prev_data}
            diffs_dir = os.path.join(args.out, "diffs")
            os.makedirs(diffs_dir, exist_ok=True)

            n_critical = n_high = n_medium = n_low = n_new = n_unchanged = 0

            with Progress(TextColumn("{task.description}"), BarColumn(), TimeRemainingColumn(), console=console) as progress:
                diff_task = progress.add_task("[cyan]Computing diffs...", total=len(results))
                for r in results:
                    url = r["url"]
                    if url in prev_by_url:
                        prev_r = prev_by_url[url]
                        old_shot = os.path.join(args.diff, prev_r.get("screenshot", prev_r.get("screenshot_path", "")))
                        new_shot = os.path.join(args.out, r.get("screenshot_path", ""))

                        # Visual diff (heatmap + side-by-side)
                        if os.path.isfile(old_shot) and os.path.isfile(new_shot):
                            pct, heatmap_rel, compare_rel = compute_screenshot_diff(
                                old_shot, new_shot, diffs_dir, r["index"], args.diff_threshold,
                            )
                            r["diff_pct"] = pct
                            r["diff_heatmap"] = heatmap_rel
                            r["diff_compare"] = compare_rel
                        else:
                            r["diff_pct"] = -1.0
                            r["diff_heatmap"] = ""
                            r["diff_compare"] = ""

                        # Content diff (title, status, category, grade, tech changes)
                        content_changes = compute_content_diff(prev_r, r)
                        r["content_changes"] = content_changes

                        # Severity classification
                        severity = calculate_diff_severity(r["diff_pct"], content_changes)
                        r["diff_severity"] = severity

                        if severity == "critical":
                            n_critical += 1
                        elif severity == "high":
                            n_high += 1
                        elif severity == "medium":
                            n_medium += 1
                        elif severity == "low":
                            n_low += 1
                        else:
                            n_unchanged += 1
                    else:
                        r["diff_pct"] = -1.0
                        r["diff_heatmap"] = ""
                        r["diff_compare"] = ""
                        r["content_changes"] = []
                        r["diff_severity"] = "new"
                        n_new += 1

                    progress.advance(diff_task)

            n_changed = n_critical + n_high + n_medium + n_low
            console.print(
                f"\n[cyan]Diff:[/] [red bold]{n_critical} critical[/] | [red]{n_high} high[/] | "
                f"[yellow]{n_medium} medium[/] | [green]{n_low} low[/] | [blue]{n_new} new[/] | [dim]{n_unchanged} unchanged[/]"
            )
            diff_buttons = '<button class="status-btn" data-status="changed" onclick="setFilter(\'changed\')">Changed</button> <button class="status-btn" data-status="new" onclick="setFilter(\'new\')">New</button>'
            diff_summary = (
                f'<div class="diff-summary">Diff vs <b>{html.escape(args.diff)}</b>: '
                f'<span style="color:#ff2020">{n_critical} critical</span> | '
                f'<span style="color:#ff4757">{n_high} high</span> | '
                f'<span style="color:#ffb86b">{n_medium} medium</span> | '
                f'<span style="color:#00e68a">{n_low} low</span> | '
                f'<span style="color:#33aaff">{n_new} new</span> | '
                f'<span style="opacity:0.5">{n_unchanged} unchanged</span></div>'
            )

    # Generate HTML cards
    cards_html = ""
    for result in results:
        status_code = str(result['status'])[0] if isinstance(result['status'], int) else "E"
        hdrs = result.get("headers", {}) or {}
        server_badge = hdrs.get("server", hdrs.get("x-powered-by", ""))
        tech_badges = " ".join(
            f'<div class="badge tech-badge">{html.escape(t)}</div>' for t in (result.get("techs", []) or [])
        )
        cat = result.get("category", "") or ""
        cat_badge = f'<div class="badge cat-badge">{html.escape(cat)}</div>' if cat else ""
        # Redirect chain display
        chain = result.get("redirect_chain", []) or []
        if len(chain) > 1:
            chain_str = " -> ".join(html.escape(u)[:60] for u in chain[:6])
            redirect_html = f'<div class="redirect-chain">Redirects: {chain_str}</div>'
        else:
            redirect_html = ""
        # TLS info display
        tls = result.get("tls", {}) or {}
        if tls.get("issuer"):
            tls_html = f'<div class="tls-info">TLS: {html.escape(tls["issuer"])} | {html.escape(tls.get("protocol",""))}</div>'
        else:
            tls_html = ""

        # Diff display
        diff_pct_val = result.get("diff_pct", 0)
        severity = result.get("diff_severity", "")
        content_changes = result.get("content_changes", [])
        diff_heatmap = result.get("diff_heatmap", "")
        diff_compare = result.get("diff_compare", "")

        diff_html = ""
        if severity and severity != "none":
            sev_cls = {"critical": "diff-high sev-critical", "high": "diff-high", "medium": "diff-med", "low": "diff-low", "new": "diff-new"}
            sev_lbl = {"critical": "CRITICAL", "high": "HIGH", "medium": "MEDIUM", "low": "LOW", "new": "NEW"}
            badge_cls = sev_cls.get(severity, "diff-med")
            badge_txt = sev_lbl.get(severity, severity.upper())
            pct_txt = f" {diff_pct_val}%" if isinstance(diff_pct_val, (int, float)) and diff_pct_val > 0 else ""
            diff_html += f'<div class="line small"><span class="diff-badge {badge_cls}">{badge_txt}{pct_txt}</span></div>'

            # Content changes (title, status, category, grade, tech diffs)
            if content_changes:
                lines = []
                for c in content_changes:
                    fld = html.escape(c.get("field", ""))
                    old_v = html.escape(c.get("old", ""))
                    new_v = html.escape(c.get("new", ""))
                    lines.append(f"{fld}: {old_v} <span class='ca'>&rarr;</span> {new_v}")
                diff_html += '<div class="content-changes">' + "<br>".join(lines) + "</div>"

            # Heatmap + side-by-side thumbnails
            if diff_heatmap or diff_compare:
                thumbs = ""
                if diff_heatmap:
                    thumbs += f'<img src="{html.escape(diff_heatmap)}" alt="heatmap" onclick="openDiff(\'{html.escape(diff_heatmap)}\')" title="Heatmap">'
                if diff_compare:
                    thumbs += f'<img src="{html.escape(diff_compare)}" alt="compare" onclick="openDiff(\'{html.escape(diff_compare)}\')" title="Before | Diff | After">'
                diff_html += f'<div class="diff-thumbs">{thumbs}</div>'

        cards_html += CARD_TEMPLATE.format(
            url=html.escape(str(result['url'])),
            display_url=html.escape(str(result['url'])[:60]),
            screenshot_relpath=html.escape(str(result.get('screenshot_path', result.get('screenshot', '')))),
            status_code=status_code, status_text=result['status'],
            load_ms=result.get('load_ms', 0),
            page_title=html.escape((str(result.get('title', '')) or "")[:80]),
            server=html.escape(server_badge), tech_badges=tech_badges,
            category=html.escape(cat), cat_badge=cat_badge,
            sec_grade=result.get("sec_grade", "F"),
            diff_pct=diff_pct_val, diff_html=diff_html,
            redirect_html=redirect_html, tls_html=tls_html,
            notes=html.escape(str(result.get('notes', ''))),
        )

    report_path = os.path.join(args.out, "report.html")
    make_report(cards_html, report_path, total, success, warn, fail, runtime, diff_buttons, diff_summary)
    console.print(f"[green bold]Report saved to:[/] {report_path}")

    if args.json or args.resume:
        json_path = os.path.join(args.out, "results.json")
        export_json(results, json_path)
        if args.json:
            console.print(f"[green bold]JSON saved to:[/] {json_path}")
    if args.csv:
        csv_path = os.path.join(args.out, "results.csv")
        export_csv(results, csv_path)
        console.print(f"[green bold]CSV saved to:[/] {csv_path}")

    log.info("Scan complete: %d total, %d success, %d warn, %d fail (%s)", total, success, warn, fail, runtime)
    console.print()

if __name__ == "__main__":
    main()
