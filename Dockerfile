FROM python:3.12-slim AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLCONFIGDIR=/tmp/matplotlib

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && groupadd --gid 10001 expense \
    && useradd --uid 10001 --gid expense --no-create-home expense \
    && mkdir -p /app/data \
    && chown expense:expense /app/data

COPY *.py ./
COPY templates/ ./templates/
COPY static/ ./static/

USER expense

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/login', timeout=3).close()"

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]

FROM app AS test
COPY tests/ ./tests/
CMD ["python", "-m", "pytest", "-p", "no:cacheprovider", "tests", "-v"]

FROM app AS production