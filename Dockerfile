FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --create-home --home-dir /home/app --shell /usr/sbin/nologin app \
    && mkdir -p /app \
    && chown app:app /app

RUN pip install --upgrade pip

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /app/scripts
COPY --chown=app:app alembic.ini ./
COPY --chown=app:app alembic ./alembic
COPY --chown=app:app scripts/platform_foundation_smoke.py ./scripts/platform_foundation_smoke.py
COPY --chown=app:app scripts/business_catalog_search_index_readiness.py ./scripts/business_catalog_search_index_readiness.py
COPY --chown=app:app scripts/reindex_business_catalog_search.py ./scripts/reindex_business_catalog_search.py
COPY --chown=app:app src ./src
# Fail fast if the application sources were not copied. This typically happens
# when the build context is set to ./src instead of the repository root, which
# would produce an image without the src/ package and break python -m src.main.
RUN test -d src \
    && chown -R app:app /app

USER app

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD curl -fsS http://127.0.0.1:8080/health || exit 1

CMD ["python", "-m", "src.main"]
