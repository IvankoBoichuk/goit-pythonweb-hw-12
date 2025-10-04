# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.10

# Встановимо змінну середовища
ENV APP_HOME /app

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Оновимо pip до останньої версії
RUN pip install --upgrade pip

# Спочатку скопіюємо тільки pyproject.toml для кешування шарів
COPY pyproject.toml .

# Встановимо залежності з pyproject.toml
RUN pip install -e .

# Скопіюємо решту файлів проекту (включаючи .env)
COPY . .

# Переконаємося що .env файл копіюється
COPY .env* ./

# Позначимо порт, де працює застосунок всередині контейнера (FastAPI зазвичай використовує 8000)
EXPOSE 8000

# Запустимо FastAPI застосунок з uvicorn через Python модуль
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]