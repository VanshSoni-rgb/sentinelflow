FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl git \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN pip install -e .

ENV PYTHONPATH=/app/src
EXPOSE 8000 8501

CMD ["uvicorn", "sentinelflow.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
