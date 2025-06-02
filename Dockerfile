FROM python:3.11-slim AS builder
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app/requirements.txt .
RUN pip install --user -r requirements.txt
COPY app/ /app

FROM python:3.11-slim
RUN apt-get update && apt-get install -y postgresql-client && \
    rm -rf /var/lib/apt/lists/*
COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app
ENV PATH=/root/.local/bin:$PATH

WORKDIR /app
RUN chmod +x wait-for-postgres.sh

CMD ["sh", "-c", "app/wait-for-postgres.sh postgres python app/init_db.py && uvicorn main:app --host 0.0.0.0 --port 8000 --limit-concurrency 100 --timeout-keep-alive 10"]
