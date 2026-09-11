FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py init_db.py start.py ./
COPY templates ./templates
COPY static ./static

RUN mkdir -p /app/data

ENV DB_PATH=/app/data/nftducks.db
ENV PYTHONUNBUFFERED=1

EXPOSE 5555

CMD ["python", "start.py"]
