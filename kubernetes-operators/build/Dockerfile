FROM python:3.10-slim

WORKDIR /app

RUN pip install kopf kubernetes

COPY mysql_operator.py /app/mysql_operator.py

CMD ["kopf", "run", "/app/mysql_operator.py", "--verbose"]
