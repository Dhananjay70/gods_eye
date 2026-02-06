# Gods Eye - Parallel Web Reconnaissance Screenshot Tool
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

LABEL maintainer="Gods Eye Contributors"
LABEL description="Parallel Web Reconnaissance Screenshot Tool"
LABEL version="1.0.0"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY gods_eye.py .

# Install Playwright browsers (Chromium only to keep image small)
RUN playwright install chromium

# Create non-root user for security
RUN groupadd -r godseye && useradd -r -g godseye -m godseye

# Default output directory (mount a volume here)
RUN mkdir -p /output && chown godseye:godseye /output
VOLUME ["/output"]

# Switch to non-root user
USER godseye

ENTRYPOINT ["python", "gods_eye.py"]
CMD ["--help"]
