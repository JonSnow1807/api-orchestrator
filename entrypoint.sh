#!/bin/sh
# Railway entrypoint script
# This bypasses any cached cd commands

echo "Starting API Orchestrator..."
echo "PORT: ${PORT:-8000}"
echo "Working directory: $(pwd)"

# Directly run Python without any cd commands
exec python -u start.py