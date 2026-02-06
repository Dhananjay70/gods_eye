# Gods Eye

A powerful parallel web reconnaissance screenshot tool with beautiful dark-themed HTML reports. Built for security researchers, penetration testers, and bug bounty hunters.

![Python](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos%20%7C%20windows-lightgrey.svg)
[![CI](https://github.com/Dhananjay70/gods_eye/actions/workflows/ci.yml/badge.svg)](https://github.com/Dhananjay70/gods_eye/actions/workflows/ci.yml)
![Version](https://img.shields.io/badge/version-1.0.0-brightgreen.svg)

![gods_eye](ReconPro.png)
## Why Gods Eye?

Gods Eye goes beyond simple screenshotting. While tools like Aquatone, EyeWitness, and gowitness capture pages, Gods Eye delivers **actionable intelligence** with every scan:

| Feature | Gods Eye | Aquatone | EyeWitness | gowitness |
|---------|:--------:|:--------:|:----------:|:---------:|
| Parallel async screenshots | Yes | Yes | Yes | Yes |
| Security header grading (A-F) | **Yes** | No | No | No |
| Screenshot diff / change detection | **Yes** | No | No | No |
| Heatmap + side-by-side diff images | **Yes** | No | No | No |
| Content diff (title, status, grade) | **Yes** | No | No | No |
| Severity classification (critical-low) | **Yes** | No | No | No |
| Page categorization (login, admin, WAF...) | **Yes** | No | Partial | No |
| TLS certificate extraction | **Yes** | No | Yes | Yes |
| Redirect chain tracking | **Yes** | No | No | Yes |
| Console log capture | **Yes** | No | No | Yes |
| Cookie capture | **Yes** | No | No | Yes |
| Custom JS injection | **Yes** | No | No | No |
| Rate limiting | **Yes** | No | No | No |
| Nmap XML input | **Yes** | Yes | Yes | Yes |
| CIDR range scanning | **Yes** | No | Yes | Yes |
| Scope filtering (--exclude) | **Yes** | No | No | No |
| Viewport presets | **Yes** | No | No | No |
| Tech fingerprinting (38 patterns) | **Yes** | No | Partial | No |
| Resume interrupted scans | **Yes** | No | No | No |
| Docker support | **Yes** | No | Yes | Yes |
| pip install / CLI entry point | **Yes** | No | No | N/A (Go) |
| Dark/light theme reports | **Yes** | No | No | Yes |

## Features

### Reconnaissance Engine
- **Blazing Fast** - Parallel async screenshot capture using Playwright
- **Smart Retries** - Configurable retry logic for handling unreliable targets
- **Flexible Wait Modes** - Fast, Balanced, or Thorough page loading strategies
- **Rate Limiting** - Configurable delay between requests to prevent IP bans
- **Redirect Chain Tracking** - Full redirect path from initial URL to final destination
- **TLS Certificate Extraction** - Issuer, subject, validity dates, and protocol version
- **Console Log Capture** - Grab browser console output (errors, warnings, debug info)
- **Cookie Capture** - Extract cookies set by the target, including security flags

### Security Analysis
- **Security Header Grading** - Automatic A-F grade based on 6 security headers (HSTS, CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy)
- **Tech Fingerprinting** - Auto-detect 38+ web technologies from headers and HTML (Nginx, WordPress, React, PHP, Cloudflare, Next.js, Django, Rails, and more)
- **Page Categorization** - Classify pages as Login, Admin Panel, API Docs, Default Page, WAF/Firewall, Parked Domain, Under Construction, Access Denied, and more

### Screenshot Diff / Change Detection
- **Visual Diff** - Block-based comparison (8x8) with noise-resistant threshold filtering
- **Heatmap** - Green/yellow/red heatmap overlay showing exactly where changes occurred
- **Side-by-Side** - BEFORE | DIFF | AFTER composite image for easy visual review
- **Content Diff** - Detects changes in title, HTTP status, category, security grade, and tech stack
- **Severity Classification** - Automatic severity rating: Critical, High, Medium, Low, None
- **Report Integration** - Filter by "Changed" / "New" in HTML report, clickable heatmap thumbnails
- **Tunable Sensitivity** - Adjust pixel threshold with `--diff-threshold`

### Input Flexibility
- **Multi-Source Input** - URL files, stdin pipes, Nmap XML, and CIDR ranges — all combinable in a single scan
- **Nmap XML Parsing** - Feed Nmap scan results directly with `--nmap scan.xml`
- **CIDR Range Scanning** - Scan entire subnets with `--cidr 192.168.1.0/24`
- **Pipeline Ready** - Stdin pipe support for chaining with subfinder, httpx, etc.
- **Scope Filtering** - Exclude URLs matching regex patterns with `--exclude`
- **URL Deduplication** - Automatic removal of duplicate URLs preserving input order

### Stealth & Auth
- **Auth Support** - Custom headers and cookies for authenticated page capture
- **Proxy Support** - Route through HTTP/SOCKS5 proxies (Burp, Tor, etc.)
- **Custom User-Agent** - Spoof browser identity with `--user-agent`
- **JS Injection** - Run custom JavaScript before screenshot (dismiss cookie banners, expand accordions, etc.)

### Reporting
- **Beautiful Reports** - Modern dark/light themed HTML reports with interactive features
- **Security Grades** - Color-coded A-F grades on every card
- **Category Badges** - Visual classification of page types
- **Tech Badges** - Detected technologies shown per target
- **Diff Badges** - Severity-coded change badges with heatmap thumbnails
- **Redirect Chains** - Visual redirect path in report cards
- **TLS Info** - Certificate issuer and protocol displayed
- **Sortable Cards** - Sort report cards by status code
- **Interactive Filtering** - Filter by HTTP status code (2xx, 3xx, 4xx, 5xx), Changed, New
- **Search** - Full-text search across URLs, titles, and technologies
- **Lightbox View** - Click to zoom screenshots and diff images in full screen
- **Theme Toggle** - Switch between dark and light modes with preference saving
- **Responsive Design** - Reports work perfectly on mobile and desktop

### Output & Workflow
- **JSON/CSV Export** - Machine-readable output for tool chaining
- **Resume Scans** - Skip already-captured URLs on interrupted large scans
- **Image Optimization** - JPEG format with quality control to reduce storage
- **Viewport Presets** - Desktop, laptop, tablet, and mobile presets
- **Rich CLI Output** - ASCII banner, colorful progress bars and status tables
- **Debug Logging** - Log file + optional verbose console output

## Requirements

- Python 3.10+
- Playwright
- Rich
- Pillow (for screenshot diff)

## Installation

### Option 1: pip install (Recommended)

```bash
git clone https://github.com/gods-eye-tool/gods-eye.git
cd gods-eye
pip install .
playwright install chromium

# Now use it anywhere:
gods-eye -f urls.txt --json -o scan_output
```

### Option 2: Direct run

```bash
git clone https://github.com/gods-eye-tool/gods-eye.git
cd gods-eye
pip install -r requirements.txt
playwright install chromium

python gods_eye.py -f urls.txt
```

### Option 3: Docker

```bash
git clone https://github.com/gods-eye-tool/gods-eye.git
cd gods-eye
docker build -t gods-eye .

# Run with mounted input/output
docker run --rm \
  -v ./urls.txt:/input/urls.txt \
  -v ./output:/output \
  gods-eye -f /input/urls.txt -o /output --json
```

### Verify installation

```bash
gods-eye --version
# or
python gods_eye.py --version
# → Gods Eye v1.0.0
```

## Usage

### Basic Usage

```bash
python gods_eye.py -f urls.txt
```

### Advanced Scanning

```bash
python gods_eye.py -f urls.txt \
  --threads 10 \
  --timeout 10000 \
  --viewport 1920x1080 \
  --full-page \
  --retries 3 \
  --wait-mode thorough \
  --rate-limit 0.5 \
  --proxy http://127.0.0.1:8080 \
  --json --csv \
  --out my_scan_results
```

### Screenshot Diff / Change Detection

```bash
# First scan (baseline)
python gods_eye.py -f urls.txt -o scan_baseline --json

# ... time passes, websites change ...

# Second scan with diff against baseline
python gods_eye.py -f urls.txt -o scan_current --json \
  --diff scan_baseline

# Adjust diff sensitivity (lower = more sensitive, default 10)
python gods_eye.py -f urls.txt -o scan_current --json \
  --diff scan_baseline --diff-threshold 5
```

The diff report shows:
- **Severity badges** on each card (CRITICAL / HIGH / MEDIUM / LOW / NEW)
- **Content changes** (title, status, category, grade, tech stack diffs)
- **Clickable heatmap thumbnails** showing exactly where visual changes occurred
- **Side-by-side BEFORE|DIFF|AFTER** composite images
- **Filter buttons** to show only Changed or New URLs
- **Summary bar** with counts per severity level

### Rate Limiting

```bash
# 0.5 second delay between each request
python gods_eye.py -f urls.txt --rate-limit 0.5

# 2 second delay for sensitive targets
python gods_eye.py -f urls.txt --rate-limit 2 --threads 3
```

### Nmap Integration

```bash
# Run Nmap first, then feed results to Gods Eye
nmap -sV -oX scan.xml 192.168.1.0/24
python gods_eye.py --nmap scan.xml --json -o nmap_recon

# Combine Nmap + URL file
python gods_eye.py --nmap scan.xml -f extra_urls.txt -o combined_scan
```

### CIDR Range Scanning

```bash
# Scan a /24 subnet on default ports (80, 443, 8080, 8443)
python gods_eye.py --cidr 192.168.1.0/24 -o subnet_scan

# Custom ports
python gods_eye.py --cidr 10.0.0.0/24 --ports 80,443,8000,9090 --threads 20

# Combine CIDR with URL file
python gods_eye.py --cidr 192.168.1.0/24 -f additional_urls.txt -o full_scan
```

### Pipeline Usage

```bash
# Pipe from subfinder
subfinder -d target.com -silent | python gods_eye.py --json -o recon_output

# Pipe from httpx
echo target.com | httpx -silent | python gods_eye.py --threads 10 --json

# Pipe from any tool
cat urls.txt | python gods_eye.py --threads 10 --json
```

### Authenticated Scanning

```bash
# With cookies
python gods_eye.py -f urls.txt -c "session=abc123; domain=.target.com"

# With custom headers
python gods_eye.py -f urls.txt -H "Authorization: Bearer eyJhbG..."

# Combine auth + proxy + custom UA
python gods_eye.py -f urls.txt \
  -H "Authorization: Bearer token" \
  -c "session=abc; domain=.target.com" \
  --proxy http://127.0.0.1:8080 \
  --user-agent "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0"
```

### JS Injection (Cookie Banners, UI Manipulation)

```bash
# Dismiss cookie consent banners before screenshot
python gods_eye.py -f urls.txt \
  --js-inject "document.querySelectorAll('[class*=cookie],[class*=consent],[id*=cookie]').forEach(e=>e.remove())"

# Expand all collapsed sections
python gods_eye.py -f urls.txt \
  --js-inject "document.querySelectorAll('details').forEach(d=>d.open=true)"

# Scroll to bottom (useful for lazy-loading pages)
python gods_eye.py -f urls.txt \
  --js-inject "window.scrollTo(0,document.body.scrollHeight)"
```

### Scope Filtering

```bash
# Exclude specific patterns
python gods_eye.py -f urls.txt --exclude "\.gov" --exclude "internal\."

# Exclude multiple patterns
python gods_eye.py --cidr 10.0.0.0/24 \
  --exclude "10\.0\.0\.1:" \
  --exclude "10\.0\.0\.254:"
```

### Viewport Presets

```bash
# Mobile screenshots
python gods_eye.py -f urls.txt --viewport mobile

# Tablet view
python gods_eye.py -f urls.txt --viewport tablet

# Custom dimensions
python gods_eye.py -f urls.txt --viewport 2560x1440
```

### Resume Interrupted Scans

```bash
# First run (crashes at URL 800 of 1000)
python gods_eye.py -f urls.txt --resume --json -o big_scan

# Re-run: automatically skips the 800 completed URLs
python gods_eye.py -f urls.txt --resume --json -o big_scan
```

## Command Line Options

### Input Options

| Option | Description | Default |
|--------|-------------|---------|
| `-f, --file` | File containing URLs (one per line) | stdin |
| `--nmap` | Nmap XML output file to parse for HTTP targets | - |
| `--cidr` | CIDR range to scan (e.g. `192.168.1.0/24`) | - |
| `--ports` | Ports for CIDR scan (comma-separated) | `80,443,8080,8443` |
| `--exclude` | Exclude URLs matching regex (repeatable) | - |
| `--diff` | Diff against previous scan directory (needs `results.json`) | - |
| `--diff-threshold` | Pixel change threshold 0-255 (lower = more sensitive) | `10` |

### Output Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --out` | Output directory | `gods_eye_report` |
| `--json` | Export results as JSON | `False` |
| `--csv` | Export results as CSV | `False` |
| `--format` | Screenshot format: `png`, `jpeg` | `png` |
| `--quality` | JPEG quality 1-100 (only with `--format jpeg`) | - |

### Scan Behavior

| Option | Description | Default |
|--------|-------------|---------|
| `--threads` | Number of concurrent threads | `5` |
| `--timeout` | Page timeout in milliseconds | `8000` |
| `--viewport` | Viewport: `WxH` or preset (`desktop`, `laptop`, `tablet`, `mobile`) | `1920x1080` |
| `--full-page` | Capture full page screenshot | `False` |
| `--retries` | Number of retries on failure | `2` |
| `--wait-mode` | Page wait behavior: `fast`, `balanced`, `thorough` | `balanced` |
| `--resume` | Skip URLs already captured in a previous run | `False` |
| `--rate-limit` | Delay in seconds between each request (e.g. `0.5`) | `0` (off) |

### Auth & Stealth

| Option | Description | Default |
|--------|-------------|---------|
| `--proxy` | Proxy server (e.g. `http://127.0.0.1:8080`, `socks5://proxy:1080`) | - |
| `-H, --header` | Custom HTTP header (repeatable) | - |
| `-c, --cookie` | Cookie string (repeatable) | - |
| `--user-agent` | Custom User-Agent string | - |
| `--js-inject` | JavaScript to execute before screenshot | - |

### Misc

| Option | Description | Default |
|--------|-------------|---------|
| `--version` | Show version and exit | - |
| `-v, --verbose` | Verbose logging to console | `False` |

## Input Formats

### URL File

Create a text file with one URL per line:

```text
https://example.com
https://target1.com
https://target2.com
http://internal-site.local
```

**Notes:**
- Lines starting with `#` are treated as comments
- URLs without protocol will automatically get `http://` prepended
- Empty lines are ignored
- Supports multiple encodings (UTF-8, UTF-16, CP1252, Latin-1)

### Nmap XML

Run Nmap with `-oX` flag and feed the output:

```bash
nmap -sV -p 80,443,8080,8443 -oX scan.xml 192.168.1.0/24
python gods_eye.py --nmap scan.xml
```

Gods Eye extracts all open HTTP/HTTPS services from the Nmap XML, automatically determining the correct protocol (HTTP vs HTTPS) based on service name and tunnel info.

### CIDR Ranges

Scan entire subnets:

```bash
python gods_eye.py --cidr 10.0.0.0/24 --ports 80,443
```

This expands the CIDR range to individual host IPs and generates URLs for each port. Port 443 automatically uses HTTPS.

### Stdin Pipe

```bash
echo "example.com" | python gods_eye.py
subfinder -d target.com -silent | python gods_eye.py --json
```

### Combining Sources

All input sources can be combined in a single scan:

```bash
python gods_eye.py \
  -f urls.txt \
  --nmap scan.xml \
  --cidr 10.0.0.0/28 \
  --exclude "\.example\.com" \
  --json -o combined_recon
```

## Security Header Grading

Gods Eye evaluates 6 critical security headers and assigns a grade:

| Grade | Headers Present | Meaning |
|-------|----------------|---------|
| **A** | 5-6 | Excellent security posture |
| **B** | 4 | Good, minor gaps |
| **C** | 3 | Fair, needs improvement |
| **D** | 1-2 | Poor security headers |
| **F** | 0 | No security headers |

**Headers evaluated:**
1. `Strict-Transport-Security` (HSTS)
2. `Content-Security-Policy` (CSP)
3. `X-Frame-Options`
4. `X-Content-Type-Options`
5. `Referrer-Policy`
6. `Permissions-Policy`

## Page Categorization

Gods Eye automatically classifies pages into categories:

| Category | Detection Method |
|----------|-----------------|
| **Login Page** | Password fields, sign-in/login keywords |
| **Admin Panel** | Admin, dashboard, cpanel, wp-admin, phpMyAdmin |
| **API Docs** | Swagger, ReDoc, OpenAPI patterns |
| **Default Page** | "It works!", default server pages |
| **Access Denied** | 403/401 pages |
| **Not Found** | 404 pages |
| **Parked Domain** | Domain sale/parking indicators |
| **Under Construction** | Coming soon, maintenance pages |
| **WAF/Firewall** | Cloudflare challenges, WAF blocks, CAPTCHAs |

## Diff Severity Levels

When using `--diff`, Gods Eye classifies changes by severity:

| Severity | Criteria | Meaning |
|----------|----------|---------|
| **Critical** | >50% visual change + status/category change | Major site overhaul or compromise |
| **High** | >30% visual change OR status/category change | Significant redesign or state change |
| **Medium** | >5% visual change OR title/grade/tech change | Content updates or config changes |
| **Low** | >0.5% visual change | Minor cosmetic tweaks |
| **None** | No meaningful change | Stable |
| **New** | URL not in previous scan | Newly discovered target |

## Wait Modes

Gods Eye offers three wait strategies to balance speed and reliability:

| Mode | Load Timeout | Network Idle | Best For |
|------|-------------|--------------|----------|
| **Fast** | 500ms | 1000ms | Quick scans, static sites |
| **Balanced** | 2000ms | 3000ms | General purpose (default) |
| **Thorough** | 4000ms | 6000ms | Heavy JS sites, SPAs |

## Viewport Presets

| Preset | Resolution | Use Case |
|--------|-----------|----------|
| `desktop` | 1920x1080 | Default full HD |
| `laptop` | 1366x768 | Common laptop screens |
| `tablet` | 768x1024 | iPad-style portrait |
| `mobile` | 375x812 | iPhone-style portrait |

## Report Features

The generated HTML report includes:

- **Security Grades** - Color-coded A-F security header grades on every card
- **Category Badges** - Visual page type classification
- **Tech Badges** - Detected technologies per target
- **Diff Severity Badges** - CRITICAL/HIGH/MEDIUM/LOW/NEW severity indicators
- **Content Change Details** - Field-by-field diff display (title, status, grade, tech)
- **Heatmap Thumbnails** - Clickable diff heatmaps showing change locations
- **Side-by-Side View** - BEFORE|DIFF|AFTER composite for visual comparison
- **Redirect Chains** - Full redirect path displayed when redirects occur
- **TLS Info** - Certificate issuer and protocol version
- **Search** - Full-text search across URLs, titles, and technologies
- **Status Filters** - Quick filter by HTTP status (2xx, 3xx, 4xx, 5xx)
- **Diff Filters** - Filter by Changed or New URLs
- **Sortable** - Sort cards by status code
- **Theme Toggle** - Switch between dark and light themes
- **Lightbox** - Click any screenshot or diff image for full-screen view
- **Statistics** - Total scans, success/warning/failure counts, runtime
- **Diff Summary** - Severity breakdown bar when using `--diff`

## Output Structure

```
gods_eye_report/
├── report.html          # Interactive HTML report
├── results.json         # JSON export (with --json or --resume)
├── results.csv          # CSV export (with --csv)
├── scan.log             # Debug log file
├── screenshots/         # All captured screenshots
│   ├── 001_example.com.png
│   ├── 002_target1.com.png
│   └── 003_target2.com.png
└── diffs/               # Diff images (when using --diff)
    ├── diff_001_heatmap.png
    ├── diff_001_compare.png
    └── ...
```

### JSON Output Fields

The JSON export includes rich data per target:

```json
{
  "index": 1,
  "url": "https://example.com",
  "final_url": "https://www.example.com/",
  "status": 200,
  "title": "Example Domain",
  "load_ms": 1234,
  "headers": { "server": "nginx", "strict-transport-security": "max-age=31536000" },
  "techs": ["Nginx", "React", "Cloudflare"],
  "category": "Login Page",
  "sec_grade": "B",
  "sec_headers": ["strict-transport-security", "x-frame-options", "x-content-type-options", "referrer-policy"],
  "redirect_chain": ["https://example.com", "https://www.example.com/"],
  "tls": { "issuer": "Let's Encrypt", "subject": "example.com", "protocol": "TLS 1.3" },
  "cookies": [{ "name": "session", "domain": ".example.com", "secure": true, "httpOnly": true }],
  "console_logs": ["[log] App initialized", "[warning] Deprecated API call"],
  "diff_pct": 12.5,
  "diff_heatmap": "diffs/diff_001_heatmap.png",
  "diff_compare": "diffs/diff_001_compare.png",
  "diff_severity": "medium",
  "content_changes": [
    { "field": "Title", "old": "Old Title", "new": "New Title", "severity": "medium" }
  ],
  "screenshot": "screenshots/001_example.com.png",
  "notes": "Success"
}
```

## Project Structure

```
gods_eye-main/
├── .github/workflows/ci.yml   # GitHub Actions CI (syntax + Docker)
├── .dockerignore               # Docker context filter
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Multi-stage Docker build
├── LICENSE                     # MIT License
├── README.md                   # This file
├── gods_eye.py                 # Main tool (single-file)
├── pyproject.toml              # Python packaging (pip install .)
└── requirements.txt            # Dependencies
```

## Use Cases

- **Reconnaissance** - Visual overview of target web infrastructure with security grades
- **Bug Bounty** - Quick asset discovery with page categorization and tech fingerprinting
- **Penetration Testing** - Document target states with TLS, headers, and redirect data
- **Web Monitoring** - Track visual changes over time with screenshot diff and severity alerts
- **Asset Inventory** - Create visual catalogs with technology and security metadata
- **Network Scanning** - Scan entire subnets from Nmap results or CIDR ranges
- **Compliance Auditing** - Security header grading across your web properties
- **Change Detection** - Automated comparison between scan baselines to spot site modifications

## Security Considerations

- **Responsible Usage** - Only scan targets you have permission to test
- **Rate Limiting** - Use `--rate-limit` to avoid overwhelming targets
- **Legal Compliance** - Ensure your scanning activities comply with local laws
- **JS Injection** - The `--js-inject` flag runs JavaScript on target pages; use responsibly

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [Playwright](https://playwright.dev/) for browser automation
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
- [Pillow](https://pillow.readthedocs.io/) for screenshot diff engine
- Inspired by the security research community

## Disclaimer

This tool is for authorized security testing and educational purposes only. The developers assume no liability and are not responsible for any misuse or damage caused by this program. Always obtain proper authorization before scanning systems you don't own.

---

**Made with love for the security community**

*If you find this tool useful, consider giving it a star on GitHub!*
