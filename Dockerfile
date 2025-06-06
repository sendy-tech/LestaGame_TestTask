FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --user -r requirements.txt

COPY app /app/app
COPY init_db.py .
COPY wait-for-postgres.sh .

FROM python:3.11-slim

RUN apt-get update && apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

ENV PATH=/root/.local/bin:$PATH
ENV PYTHONPATH=/app

WORKDIR /app
RUN chmod +x wait-for-postgres.sh