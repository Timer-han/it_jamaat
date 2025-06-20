FROM python:3.11-slim

# Устанавливаем зависимости для Babel (distutils)
RUN apt-get update && apt-get install -y python3-distutils && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN ls
RUN pybabel compile -d locales
COPY . .
CMD ["python", "-u", "app/main.py"]