FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY main.py api.py scheduler.py ./

# Install dependencies
RUN uv sync --frozen

# Create data directory for legacy scheduler mode
RUN mkdir -p /app/data

# Expose API port
EXPOSE 8000

# Default: run API server
CMD ["uv", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
