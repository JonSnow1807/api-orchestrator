FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    bc \
    && rm -rf /var/lib/apt/lists/*

# Create requirements file with essential packages
RUN echo "requests>=2.28.0\nclick>=8.0.0\npyyaml>=6.0\ncolorama>=0.4.0" > /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy standalone CLI script for GitHub Actions
COPY cli/github_action_runner.py /app/

# Make it executable
RUN chmod +x /app/github_action_runner.py

# Create a simple entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]