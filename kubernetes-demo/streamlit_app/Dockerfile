# syntax=docker/dockerfile:1
# Pinned to an exact patch tag (never `latest`). To pin by digest as well,
# resolve the current digest for this tag in your registry with
# `docker buildx imagetools inspect python:3.11.9-slim` and append
# `@sha256:<digest>` -- do not hand-write a digest without resolving it.
FROM python:3.11.9-slim AS base

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN groupadd --gid 1000 streamlit \
    && useradd --uid 1000 --gid streamlit --shell /usr/sbin/nologin --create-home streamlit

COPY streamlit_app/requirements.txt ./streamlit_app/requirements.txt
RUN pip install --no-cache-dir -r streamlit_app/requirements.txt

COPY src ./src
COPY streamlit_app ./streamlit_app

RUN chown -R streamlit:streamlit /app
USER streamlit

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health')" || exit 1

ENTRYPOINT ["streamlit", "run", "streamlit_app/app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.headless=true"]
