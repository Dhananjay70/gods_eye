# Gods Eye + Openclaw — Compliance & Disclosure Platform
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

LABEL maintainer="Dhananjay Pathak"
LABEL description="Gods Eye Recon + Openclaw Compliance Platform"
LABEL version="1.1.0"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gods_eye.py report_template.html ./
COPY openclaw/ ./openclaw/
COPY pyproject.toml ./

# Install Playwright browsers (Chromium only to keep image small)
RUN playwright install chromium

# Create non-root user for security
RUN groupadd -r godseye && useradd -r -g godseye -m godseye

# Default directories
RUN mkdir -p /output /data && chown -R godseye:godseye /output /data
VOLUME ["/output", "/data"]

ENV OPENCLAW_DATA_DIR=/data

# Switch to non-root user
USER godseye

# Expose portal port
EXPOSE 8000

# Default: show help. Override with `gods_eye.py` or `openclaw serve`
ENTRYPOINT ["python", "-m"]
CMD ["openclaw.cli", "--help"]
