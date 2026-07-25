FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/backend

WORKDIR /app

COPY pyproject.toml README.md ./
COPY docker/app/requirements.txt ./docker/app/requirements.txt
COPY backend ./backend
COPY docker ./docker

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r docker/app/requirements.txt \
    && pip install --no-cache-dir --no-deps .

EXPOSE 8000

CMD ["sh", "docker/app/start.sh"]
