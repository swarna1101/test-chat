# Stage 1: Build Frontend
FROM mcr.microsoft.com/mirror/docker/library/node:18-alpine AS frontend-builder
WORKDIR /frontend
COPY chat-ui/ .
RUN npm install
RUN npm run build

# Stage 2: Build Backend
FROM mcr.microsoft.com/mirror/docker/library/python:3.11-slim AS backend-builder
WORKDIR /flare-ai-social

# Install build dependencies and uv globally
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install uv

# Create and activate virtual environment
RUN python -m venv .venv && \
    . .venv/bin/activate && \
    python -m pip install --upgrade pip

ENV PATH="/flare-ai-social/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/flare-ai-social/.venv"
ENV PYTHONPATH="/flare-ai-social/.venv/lib/python3.11/site-packages"

# Copy project files
COPY pyproject.toml ./
COPY . .

# Install dependencies based on the file type
RUN if [ -f "requirements.txt" ]; then \
        uv pip install -r requirements.txt; \
    elif [ -f "pyproject.toml" ]; then \
        uv sync --frozen; \
    fi

# Stage 3: Final Image
FROM mcr.microsoft.com/mirror/docker/library/python:3.11-slim

# Install runtime dependencies and uv
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    curl && \
    rm -rf /var/lib/apt/lists/* && \
    pip install uv

WORKDIR /app

# Copy virtual environment and project files
COPY --from=backend-builder /flare-ai-social/.venv ./.venv
COPY --from=backend-builder /flare-ai-social/src ./src
COPY --from=backend-builder /flare-ai-social/pyproject.toml .
COPY --from=backend-builder /flare-ai-social/README.md .

# Set up Python environment in the final stage
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONPATH="/app/.venv/lib/python3.11/site-packages"

# Copy frontend files
COPY --from=frontend-builder /frontend/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/sites-enabled/default

# Setup supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Allow workload operator to override environment variables
LABEL "tee.launch_policy.allow_env_override"="GEMINI_API_KEY,TUNED_MODEL_NAME,SIMULATE_ATTESTATION"
LABEL "tee.launch_policy.log_redirect"="always"

EXPOSE 80

# Start supervisor (which will start both nginx and the backend)
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]