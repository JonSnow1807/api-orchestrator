# Multi-stage build for production
FROM python:3.11-slim as backend-builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r backend/requirements.txt

# Frontend builder stage
FROM node:20-alpine as frontend-builder

WORKDIR /app

# Copy frontend files
COPY frontend/package*.json frontend/
RUN cd frontend && npm ci

COPY frontend/ frontend/
RUN cd frontend && npm run build

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy application code
COPY backend/ backend/
COPY --from=frontend-builder /app/frontend/dist frontend/dist

# Copy other necessary files
COPY requirements.txt .

# Create startup script before changing user
RUN echo '#!/bin/sh\ncd /app/backend && exec python -m uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}' > /app/start.sh && \
    chmod +x /app/start.sh

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Expose port
EXPOSE ${PORT:-8000}

# Start the application
CMD ["/app/start.sh"]