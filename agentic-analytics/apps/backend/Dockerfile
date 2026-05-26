FROM ghcr.io/astral-sh/uv:python3.12-slim AS builder

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy dependency files and lockfile
COPY pyproject.toml uv.lock ./

# Install dependencies using uv (without installing the project itself yet)
RUN uv sync --no-install-project --no-dev

# Final stage
FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy the virtual environment from the builder
COPY --from=builder /app/.venv /app/.venv

# Set up PATH to use the virtual environment
ENV PATH="/app/.venv/bin:$PATH"

# Copy the application code
COPY app /app/app
COPY data /app/data

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
