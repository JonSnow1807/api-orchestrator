# Multi-stage build for frontend and backend
# Stage 1: Build frontend
FROM node:18-slim as frontend-builder

WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Python backend with frontend
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create data directory for SQLite persistence
RUN mkdir -p /app/data && chmod 777 /app/data

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY . .

# Copy built frontend from stage 1
COPY --from=frontend-builder /frontend/dist /app/frontend/dist

# Make entrypoint script executable
RUN chmod +x /app/entrypoint.sh

# Expose port (Railway will override with PORT env var)
EXPOSE 8000

# Start the application
ENTRYPOINT ["/usr/local/bin/python", "-u", "/app/start.py"]
CMD []