FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py init_db.py start.py ./
COPY templates ./templates
COPY static ./static

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/duckshop.db
ENV PYTHONUNBUFFERED=1

EXPOSE 7777

CMD ["python", "start.py"]
