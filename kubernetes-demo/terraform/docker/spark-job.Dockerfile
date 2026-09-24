# Compatibility image for the existing DAG's KubernetesPodOperator.
# The DAG passes a path that is local to the Airflow task pod. The wrapper
# creates the same CBR JSON batch inside the Spark pod when that path is not
# present, so the unmodified DAG remains runnable on Kubernetes.
FROM python:3.11.9-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64

RUN apt-get update \
    && apt-get install -y --no-install-recommends openjdk-17-jre-headless ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY kubernetes-demo/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir \
      pyspark==3.5.1 pymongo==4.8.0 pandas==2.2.2 requests==2.32.3 \
    && python -m pip cache purge || true

COPY kubernetes-demo/src ./src
COPY terraform/docker/spark-entrypoint.py ./spark-entrypoint.py

RUN groupadd --gid 1000 spark \
    && useradd --uid 1000 --gid spark --shell /usr/sbin/nologin --create-home spark \
    && chown -R spark:spark /app
USER spark

ENTRYPOINT ["python3", "/app/spark-entrypoint.py"]
