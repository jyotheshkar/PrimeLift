# PrimeLift AI — Backend (Fly.io)
FROM python:3.12-slim

WORKDIR /app

# System deps for LightGBM / scipy
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full project layout so paths.py resolves REPO_ROOT = /app
COPY backend/ ./backend/
COPY artifacts/ ./artifacts/
COPY data/ ./data/
COPY docs/ ./docs/

# Generate the dataset at build time (deterministic, fixed seed)
# This bakes the 100k CSV into the image so the container starts instantly
RUN PYTHONPATH=/app/backend/src python /app/backend/scripts/generate_dataset.py

ENV PYTHONPATH=/app/backend/src

EXPOSE 8080

CMD ["uvicorn", "primelift.api.app:app", "--host", "0.0.0.0", "--port", "8080"]
