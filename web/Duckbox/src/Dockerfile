FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY init.sql ./init.sql

WORKDIR /app/app

ENV PYTHONUNBUFFERED=1

EXPOSE 3333

CMD ["sh", "-c", "exec gunicorn --workers 4 --threads 16 --worker-class gthread --timeout 30 -b 0.0.0.0:${PORT:-3333} app:app"]
