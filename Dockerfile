# Bufferbloat Network Tester Dockerfile
# Lightweight container for testing network bufferbloat via HTTP

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY gunicorn.conf.py .

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application with Gunicorn for proper concurrency
CMD ["gunicorn", "--config", "gunicorn.conf.py", "app:app"]

# Labels for metadata
LABEL maintainer="Network Testing Team"
LABEL description="Containerized bufferbloat testing tool using HTTP-based latency measurements"
LABEL version="1.0.0"
