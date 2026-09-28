# FE-EKG REST API
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PORT=5001

WORKDIR /app

COPY requirements-api.txt .
RUN pip install -r requirements-api.txt

# Only the packages the API imports at runtime.
COPY api/ api/
COPY shared/ shared/
COPY feekg_core/__init__.py feekg_core/__init__.py
COPY feekg_core/query/ feekg_core/query/
COPY gunicorn.conf.py .

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 5001
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.environ.get(\"PORT\",\"5001\")}/health', timeout=4)"

CMD ["gunicorn", "-c", "gunicorn.conf.py", "api.wsgi:app"]
