FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY main.py scheduler.py ./

# Install dependencies
RUN uv sync --frozen

# Create data directory
RUN mkdir -p /app/data

# Default: run scheduler
CMD ["uv", "run", "python", "scheduler.py"]
