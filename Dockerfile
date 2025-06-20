# Базовый образ с Python
FROM python:3.11-slim

# Установка переменных окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /usr/src/app

# Копирование зависимостей
COPY requirements.txt ./

# Установка зависимостей
RUN pip install --no-cache-dir -r requirements.txt

# Копирование исходников
COPY . .

# Команда запуска (можно переопределить в docker-compose)
CMD ["python", "-m", "app.main"]