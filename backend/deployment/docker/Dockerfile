# HeatGuard Predictive Safety System - Production Dockerfile
# Multi-stage build for optimized production container

# Build stage
FROM python:3.9-slim as builder

LABEL maintainer="HeatGuard Development Team" \
      version="1.0.0" \
      description="HeatGuard Predictive Safety System API"

# Set environment variables for build
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    libc6-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create app user and directory
RUN groupadd -r heatguard && useradd -r -g heatguard heatguard
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim as production

# Security and optimization environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/heatguard/.local/bin:$PATH" \
    PORT=8000 \
    HOST=0.0.0.0 \
    WORKERS=4 \
    LOG_LEVEL=info \
    ENVIRONMENT=production

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd -r heatguard && useradd -r -g heatguard heatguard

# Set working directory
WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /home/heatguard/.local

# Copy application code with proper ownership
COPY --chown=heatguard:heatguard . .

# Ensure the models directory exists and has proper permissions
RUN mkdir -p /app/thermal_comfort_model && \
    chown -R heatguard:heatguard /app && \
    chmod -R 755 /app

# Create logs directory
RUN mkdir -p /app/logs && chown -R heatguard:heatguard /app/logs

# Switch to non-root user
USER heatguard

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/v1/health || exit 1

# Expose port
EXPOSE ${PORT}

# Use tini as entrypoint for proper signal handling
ENTRYPOINT ["tini", "--"]

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# Metadata labels for container management
LABEL org.opencontainers.image.title="HeatGuard Predictive Safety System" \
      org.opencontainers.image.description="Production container for heat exposure prediction API" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="HeatGuard Technologies" \
      org.opencontainers.image.url="https://heatguard.ai" \
      org.opencontainers.image.source="https://github.com/company/heatguard" \
      org.opencontainers.image.documentation="https://docs.heatguard.ai" \
      org.opencontainers.image.licenses="Proprietary"