FROM python:3.11-slim

WORKDIR /app

# Copy requirements
COPY backend/requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY backend/ ./backend/

# Set PYTHONPATH
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8002

# Run orchestrator
CMD ["python", "-m", "uvicorn", "backend.orchestrator.main:app", "--host", "0.0.0.0", "--port", "8002"]
