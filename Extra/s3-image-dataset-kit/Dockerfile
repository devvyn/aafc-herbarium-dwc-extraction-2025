
FROM python:3.11-slim

ENV PIP_DISABLE_PIP_VERSION_CHECK=1     PYTHONDONTWRITEBYTECODE=1     PYTHONUNBUFFERED=1

# Optional system deps for Pillow if you enable width/height extraction
RUN apt-get update && apt-get install -y --no-install-recommends \ 
    gcc libjpeg62-turbo-dev zlib1g-dev && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml /app/
RUN pip install uv && uv pip install -r <(uv pip compile pyproject.toml) --system
COPY src /app/src

ENV PYTHONPATH=/app/src
CMD ["python", "-m", "dataset_tool.scripts.random_fetch", "--n", "3"]
