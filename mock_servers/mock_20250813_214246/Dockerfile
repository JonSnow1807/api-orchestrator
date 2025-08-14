FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN pip install fastapi uvicorn faker

# Copy mock server files
COPY mock_server.py .
COPY mock_data.json .

# Expose port
EXPOSE 8001

# Run the mock server
CMD ["python", "mock_server.py"]
