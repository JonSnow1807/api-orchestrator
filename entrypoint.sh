#!/bin/bash
set -e

echo "🚀 API Orchestrator GitHub Action Starting..."
echo "Working directory: $(pwd)"
echo "Arguments: $@"

# Debug environment
echo "Environment variables:"
echo "INPUT_COLLECTION: ${INPUT_COLLECTION}"
echo "INPUT_ENVIRONMENT: ${INPUT_ENVIRONMENT}"
echo "INPUT_REPORTERS: ${INPUT_REPORTERS}"

# Parse GitHub Action inputs
COLLECTION="${1}"
shift

echo "Collection file: ${COLLECTION}"

# Check if collection file exists
if [[ ! -f "${COLLECTION}" ]]; then
    echo "❌ Error: Collection file '${COLLECTION}' not found"
    echo "Available files:"
    ls -la
    exit 1
fi

echo "✅ Collection file found"

# Build CLI command
CMD="python /app/github_action_runner.py test ${COLLECTION}"

# Add optional parameters
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --environment|--reporters|--timeout|--delay|--iterations|--folder)
            CMD="${CMD} $1 $2"
            shift
            shift
            ;;
        --bail)
            # Handle boolean flag - only add if value is "true"
            if [[ "$2" == "true" ]]; then
                CMD="${CMD} $1"
            fi
            shift
            shift
            ;;
        *)
            shift
            ;;
    esac
done

echo "Executing command: ${CMD}"

# Execute command and capture results
set +e  # Don't exit on command failure
OUTPUT=$(${CMD} 2>&1)
EXIT_CODE=$?
set -e

echo "Command output:"
echo "${OUTPUT}"
echo "Exit code: ${EXIT_CODE}"

# Parse output for GitHub Actions outputs (basic parsing)
TOTAL=$(echo "${OUTPUT}" | grep -oE "Total: [0-9]+" | grep -oE "[0-9]+" || echo "0")
PASSED=$(echo "${OUTPUT}" | grep -oE "Passed: [0-9]+" | grep -oE "[0-9]+" || echo "0")
FAILED=$(echo "${OUTPUT}" | grep -oE "Failed: [0-9]+" | grep -oE "[0-9]+" || echo "0")
DURATION=$(echo "${OUTPUT}" | grep -oE "Duration: [0-9]+" | grep -oE "[0-9]+" || echo "0")

echo "Parsed results:"
echo "Total: ${TOTAL}"
echo "Passed: ${PASSED}"
echo "Failed: ${FAILED}"
echo "Duration: ${DURATION}"

# Set GitHub Actions outputs
if [[ -n "${GITHUB_OUTPUT}" ]]; then
    echo "total=${TOTAL}" >> ${GITHUB_OUTPUT}
    echo "passed=${PASSED}" >> ${GITHUB_OUTPUT}
    echo "failed=${FAILED}" >> ${GITHUB_OUTPUT}
    echo "duration=${DURATION}" >> ${GITHUB_OUTPUT}
    echo "✅ GitHub Actions outputs set"
else
    echo "⚠️ GITHUB_OUTPUT not set, skipping output generation"
fi

# Check if should fail on error
FAIL_ON_ERROR="${INPUT_FAIL_ON_ERROR:-true}"
if [[ "${EXIT_CODE}" -ne 0 ]] && [[ "${FAIL_ON_ERROR}" == "true" ]]; then
    echo "❌ Test execution failed with exit code ${EXIT_CODE}"
    exit ${EXIT_CODE}
fi

echo "✅ API Orchestrator GitHub Action completed successfully"
exit 0