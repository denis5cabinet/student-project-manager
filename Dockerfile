# Базовый образ Python
FROM python:3.12-slim

# Устанавливаем зависимости системы (для работы с SQLite и PostgreSQL)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements-docker.txt .

# Устанавливаем зависимости Python
RUN pip install --no-cache-dir -r requirements-docker.txt

# Копируем весь проект
COPY . .

# Указываем переменные окружения
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DATABASE_URL=postgresql://user:password@db:5432/project_db

# Открываем порт 5000
EXPOSE 5000

# Команда для запуска приложения
CMD ["python", "app.py"]