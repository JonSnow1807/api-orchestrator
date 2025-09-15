FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    jq \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy CLI and dependencies
COPY cli/api_orchestrator_cli_enhanced.py /app/
COPY cli/requirements.txt /app/cli-requirements.txt
COPY backend/requirements.txt /app/backend-requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir \
    -r cli-requirements.txt \
    -r backend-requirements.txt

# Copy backend source for API client
COPY backend/src /app/src

# Create entrypoint script
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
# Parse GitHub Action inputs\n\
COLLECTION="${1}"\n\
shift\n\
\n\
# Build CLI command\n\
CMD="python /app/api_orchestrator_cli_enhanced.py test ${COLLECTION}"\n\
\n\
# Add optional parameters\n\
while [[ $# -gt 0 ]]; do\n\
    key="$1"\n\
    case $key in\n\
        --environment|--reporters|--bail|--timeout|--delay|--iterations|--folder)\n\
            CMD="${CMD} $1 $2"\n\
            shift\n\
            shift\n\
            ;;\n\
        *)\n\
            shift\n\
            ;;\n\
    esac\n\
done\n\
\n\
# Execute command and capture results\n\
OUTPUT=$(${CMD} 2>&1)\n\
EXIT_CODE=$?\n\
\n\
echo "${OUTPUT}"\n\
\n\
# Parse output for GitHub Actions outputs\n\
TOTAL=$(echo "${OUTPUT}" | grep -oP "Total: \K[0-9]+" || echo "0")\n\
PASSED=$(echo "${OUTPUT}" | grep -oP "Passed: \K[0-9]+" || echo "0")\n\
FAILED=$(echo "${OUTPUT}" | grep -oP "Failed: \K[0-9]+" || echo "0")\n\
DURATION=$(echo "${OUTPUT}" | grep -oP "Duration: \K[0-9]+" || echo "0")\n\
\n\
# Set GitHub Actions outputs\n\
echo "total=${TOTAL}" >> $GITHUB_OUTPUT\n\
echo "passed=${PASSED}" >> $GITHUB_OUTPUT\n\
echo "failed=${FAILED}" >> $GITHUB_OUTPUT\n\
echo "duration=${DURATION}" >> $GITHUB_OUTPUT\n\
\n\
# Check if should fail on error\n\
if [[ "${EXIT_CODE}" -ne 0 ]] && [[ "${FAIL_ON_ERROR}" == "true" ]]; then\n\
    exit ${EXIT_CODE}\n\
fi\n\
\n\
exit 0' > /app/entrypoint.sh && chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]