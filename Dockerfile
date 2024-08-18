# Стадия сборки зависимостей
FROM python:3.11-slim as builder

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    gcc \
    g++ \
    libffi-dev \
    make && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Финальная стадия
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /app /app
COPY . .

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8000"]
