# Используем официальный образ Python
FROM python:3.11-slim

# Создание директории для хранения данных
RUN mkdir -p /data

# Монтирование volume
VOLUME /data

# Установка переменной окружения для проверки внутри Docker
ENV DOCKER=True

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем Poetry
COPY pyproject.toml poetry.lock ./
RUN pip install poetry && poetry config virtualenvs.create false && poetry install --no-dev

# Копируем весь проект в контейнер
COPY . .

# Указываем команду для запуска приложения
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
