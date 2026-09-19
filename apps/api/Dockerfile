# API image for Azure Container Apps (Phase B). Build from the repository root:
#   az acr build --registry <acr> --image dlp-api:<tag> --file apps/api/Dockerfile .
# Local development uses the virtual environment, not this image.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DLP_CONTENT_DIR=/app/content

# ffmpeg/ffprobe canonicalise the uploads; the Azure providers need nothing else from apt.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY apps/api /app/apps/api
COPY content /app/content
RUN pip install --no-cache-dir "/app/apps/api[azure]"

RUN useradd --create-home --uid 1000 app && chown -R app:app /app
USER app
WORKDIR /app/apps/api
EXPOSE 8000

# Migrations and the mission fixture run on start, so a new revision is applied by the image that needs it.
CMD ["sh", "-c", "python -m alembic upgrade head && python -m dlp.cli load-fixture && python -m uvicorn dlp.main:app --host 0.0.0.0 --port 8000"]
