FROM python:3.11-slim

WORKDIR /app

# 1. Копируем только requirements.txt (Docker закэширует этот слой)
COPY requirements.txt .

# 2. Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# 3. Копируем весь код
COPY . .

# 4. Запускаем
CMD ["python", "main.py"]