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

COPY . .

## Копируем статику sqladmin в доступное для FastAPI место
#RUN mkdir -p /app/static/sqladmin && \
#    cp -r $(python -c "import os, sqladmin; print(os.path.join(os.path.dirname(sqladmin.__file__), 'statics'))")/* /app/static/sqladmin/

# Открываем порты
EXPOSE 8000

# Запуск Nginx и Uvicorn
CMD alembic upgrade head && uvicorn src.application:app --host 0.0.0.0 --port 8000
